import json
import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from database import get_supabase
from services import claude_client
from services.pdf_parser import extract_text, get_preview
from services.embeddings import chunk_text, embed_documents

router = APIRouter(prefix="/documents", tags=["documents"])

TMP_DIR = "/tmp"


def _extract_metadata(text: str) -> dict:
    preview = get_preview(text, 3000)
    prompt = f"""Analyser dette kommunale saksdokumentet og ekstraher metadata.
Returner kun gyldig JSON med disse feltene:
- title: string
- meeting_date: string (YYYY-MM-DD, eller null)
- committee: string (eller null)
- document_type: string (innkalling/saksdokument/protokoll/vedlegg)

Dokument:
{preview}

Svar kun med JSON."""
    try:
        result = claude_client.complete(
            system="Du ekstraherer metadata fra norske kommunedokumenter. Svar kun med JSON.",
            user=prompt,
            max_tokens=256,
        )
        result = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(result)
    except Exception:
        return {"title": "Ukjent dokument", "meeting_date": None, "committee": None, "document_type": "saksdokument"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Kun PDF-filer er støttet")

    file_id = str(uuid.uuid4())[:8]
    safe_name = file.filename.replace("/", "_").replace("..", "_")
    tmp_path = f"{TMP_DIR}/{file_id}_{safe_name}"

    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        raw_text = extract_text(tmp_path)
        metadata = _extract_metadata(raw_text)

        # Upload to Supabase Storage
        sb = get_supabase()
        storage_path = f"{file_id}/{safe_name}"
        try:
            with open(tmp_path, "rb") as f:
                sb.storage.from_("pol-documents").upload(storage_path, f)
        except Exception:
            storage_path = None

        # Insert document record
        doc_data = {
            "title": metadata.get("title", safe_name),
            "meeting_date": metadata.get("meeting_date"),
            "committee": metadata.get("committee"),
            "document_type": metadata.get("document_type", "saksdokument"),
            "source": "upload",
            "raw_text": raw_text,
            "storage_path": storage_path,
        }
        result = sb.table("pol_documents").insert(doc_data).execute()
        doc = result.data[0]
        doc_id = doc["id"]

        # Store embeddings asynchronously (non-blocking best-effort)
        try:
            chunks = chunk_text(raw_text)
            if chunks:
                embeddings = embed_documents(chunks)
                chunk_rows = [
                    {"document_id": doc_id, "chunk_index": i, "chunk_text": c, "embedding": emb}
                    for i, (c, emb) in enumerate(zip(chunks, embeddings))
                ]
                # Insert in batches of 20
                for batch_start in range(0, len(chunk_rows), 20):
                    sb.table("pol_document_chunks").insert(chunk_rows[batch_start:batch_start + 20]).execute()
        except Exception:
            pass

        return doc

    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@router.get("")
def list_documents(
    committee: Optional[str] = None,
    document_type: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    sb = get_supabase()
    query = (
        sb.table("pol_documents")
        .select("id,title,meeting_date,committee,document_type,source,created_at")
        .order("meeting_date", desc=True, nullsfirst=False)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    if committee:
        query = query.ilike("committee", f"%{committee}%")
    if document_type:
        query = query.eq("document_type", document_type)

    result = query.execute()
    return result.data or []


@router.get("/search")
def search_documents(q: str = Query(..., min_length=2), top_k: int = 10):
    from services.embeddings import embed_query
    sb = get_supabase()
    try:
        q_emb = embed_query(q)
        result = sb.rpc("pol_search_documents", {
            "query_embedding": q_emb,
            "match_count": top_k,
        }).execute()
        return result.data or []
    except Exception:
        # Fallback to keyword search
        result = sb.table("pol_documents").select(
            "id,title,meeting_date,committee"
        ).ilike("title", f"%{q}%").limit(top_k).execute()
        return [{"document_id": r["id"], "title": r["title"],
                 "chunk_text": r["title"], "score": 0.5,
                 "meeting_date": r.get("meeting_date"),
                 "committee": r.get("committee")} for r in (result.data or [])]


@router.get("/committees/list")
def list_committees():
    sb = get_supabase()
    result = sb.table("pol_documents").select("committee").not_.is_("committee", "null").execute()
    seen = set()
    out = []
    for r in (result.data or []):
        c = r["committee"]
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return sorted(out)


@router.get("/{doc_id}")
def get_document(doc_id: str):
    sb = get_supabase()
    result = sb.table("pol_documents").select("*").eq("id", doc_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Dokument ikke funnet")
    return result.data


@router.delete("/{doc_id}")
def delete_document(doc_id: str):
    sb = get_supabase()
    # Try to delete from storage
    try:
        doc = sb.table("pol_documents").select("storage_path").eq("id", doc_id).single().execute()
        if doc.data and doc.data.get("storage_path"):
            sb.storage.from_("pol-documents").remove([doc.data["storage_path"]])
    except Exception:
        pass

    sb.table("pol_documents").delete().eq("id", doc_id).execute()
    return {"ok": True}
