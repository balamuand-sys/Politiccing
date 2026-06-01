import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from database import get_connection
from models import Document, DocumentList, DocumentCreate, SearchResult
from services.pdf_parser import extract_text, get_preview
from services import claude_client
from services.embeddings import chunk_text, store_embeddings, semantic_search

UPLOAD_DIR = Path.home() / "politikerapp" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/documents", tags=["documents"])


def _extract_metadata(text: str) -> dict:
    preview = get_preview(text, 3000)
    prompt = f"""Analyser dette kommunale saksdokumentet og ekstraher metadata.
Returner kun gyldig JSON med disse feltene:
- title: string (dokumenttittel)
- meeting_date: string (møtedato i format YYYY-MM-DD, eller null)
- committee: string (utvalgets navn, eller null)
- document_type: string (en av: innkalling, saksdokument, protokoll, vedlegg)

Dokument (første del):
{preview}

Svar kun med JSON, ingen forklaringer."""

    try:
        result = claude_client.complete(
            system="Du er en assistent som ekstraherer metadata fra norske kommunale dokumenter.",
            user=prompt,
            max_tokens=256,
        )
        import json
        result = result.strip()
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        return json.loads(result)
    except Exception:
        return {
            "title": "Ukjent dokument",
            "meeting_date": None,
            "committee": None,
            "document_type": "saksdokument",
        }


@router.post("/upload", response_model=dict)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Kun PDF-filer er støttet")

    safe_name = Path(file.filename).name
    save_path = UPLOAD_DIR / safe_name

    # Handle duplicate filenames
    counter = 1
    while save_path.exists():
        stem = Path(file.filename).stem
        save_path = UPLOAD_DIR / f"{stem}_{counter}.pdf"
        counter += 1

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    raw_text = extract_text(str(save_path))
    metadata = _extract_metadata(raw_text)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO documents (title, meeting_date, committee, document_type, source, raw_text, file_path)
               VALUES (?,?,?,?,?,?,?)""",
            (
                metadata.get("title", safe_name),
                metadata.get("meeting_date"),
                metadata.get("committee"),
                metadata.get("document_type", "saksdokument"),
                "upload",
                raw_text,
                str(save_path),
            ),
        )
        doc_id = cur.lastrowid
        conn.commit()

        # Embed asynchronously (non-blocking store)
        try:
            chunks = chunk_text(raw_text)
            store_embeddings(doc_id, chunks, conn)
        except Exception:
            pass

        cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        return dict(row)
    finally:
        conn.close()


@router.get("", response_model=List[dict])
def list_documents(
    committee: Optional[str] = None,
    document_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    conn = get_connection()
    try:
        query = """SELECT id, title, meeting_date, committee, document_type, source, created_at
                   FROM documents WHERE 1=1"""
        params = []

        if committee:
            query += " AND committee LIKE ?"
            params.append(f"%{committee}%")
        if document_type:
            query += " AND document_type = ?"
            params.append(document_type)
        if date_from:
            query += " AND meeting_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND meeting_date <= ?"
            params.append(date_to)

        query += " ORDER BY meeting_date DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = conn.cursor()
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/search")
def search_documents(q: str = Query(..., min_length=2), top_k: int = 10):
    conn = get_connection()
    try:
        results = semantic_search(q, conn, top_k=top_k)
        return results
    finally:
        conn.close()


@router.get("/{doc_id}", response_model=dict)
def get_document(doc_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")
        return dict(row)
    finally:
        conn.close()


@router.delete("/{doc_id}")
def delete_document(doc_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")

        file_path = row["file_path"]
        cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()

        if file_path and Path(file_path).exists():
            try:
                os.remove(file_path)
            except Exception:
                pass

        return {"ok": True}
    finally:
        conn.close()


@router.get("/committees/list")
def list_committees():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT committee FROM documents WHERE committee IS NOT NULL ORDER BY committee")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
