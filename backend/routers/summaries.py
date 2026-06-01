import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from database import get_connection
from models import SummaryCreate
from services import claude_client
from services.context_builder import build_context, get_political_context

router = APIRouter(prefix="/documents", tags=["summaries"])


def _length_to_instruction(length: int) -> str:
    if length <= 20:
        return "3-5 korte kulepunkter, maksimalt 150 ord totalt"
    elif length <= 40:
        return "et kort sammendrag med 5-8 kulepunkter, ca. 200-300 ord"
    elif length <= 60:
        return "et middels detaljert sammendrag med de viktigste punktene, ca. 400-500 ord"
    elif length <= 80:
        return "et detaljert sammendrag med alle vesentlige punkt, ca. 600-800 ord"
    else:
        return "en grundig analyse med alle detaljer, bakgrunn, konsekvenser og politiske implikasjoner, ca. 1000-1500 ord"


def _build_summary_system(doc: dict, context: str, political: str) -> str:
    system = """Du er en politisk rådgiver for en Høyre-politiker i en norsk kommune.
Du analyserer kommunale saksdokumenter og lager presise, politisk relevante sammendrag.
Skriv alltid på norsk bokmål.

Oppsummeringen skal alltid inneholde:
1. **Hva saken gjelder** – kort og tydelig
2. **Kommunens anbefaling/innstilling** – hva administrasjonen foreslår
3. **Økonomikonsekvenser** – hvis relevant (beløp, budsjettpost)
4. **Politiske implikasjoner for Høyre** – hva betyr dette for Høyre-politikk?

"""
    if political:
        system += political + "\n\n"
    if context:
        system += context + "\n\n"
    return system


@router.post("/{doc_id}/summarize")
def summarize_document(doc_id: int, body: SummaryCreate):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")

        doc = dict(doc)
        length_instruction = _length_to_instruction(body.length_setting)

        context = build_context(doc.get("title", "") + " " + (doc.get("raw_text", "")[:500]),
                                conn, exclude_document_id=doc_id)
        political = get_political_context(conn)
        system = _build_summary_system(doc, context, political)

        user = f"""Lag et sammendrag av følgende kommunale saksdokument.
Format: {length_instruction}

Dokument: {doc['title']}
{doc.get('raw_text', '')[:12000]}"""

        accumulated = []

        def generate():
            for chunk in claude_client.stream_text(system, user, max_tokens=2048):
                accumulated.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            full_text = "".join(accumulated)
            try:
                cur2 = conn.cursor()
                cur2.execute(
                    "INSERT INTO summaries (document_id, summary_text, length_setting) VALUES (?,?,?)",
                    (doc_id, full_text, body.length_setting),
                )
                conn.commit()
            except Exception:
                pass
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/summaries")
def get_summaries(doc_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM summaries WHERE document_id = ? ORDER BY created_at DESC",
            (doc_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
