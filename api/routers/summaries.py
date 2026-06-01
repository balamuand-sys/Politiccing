import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from database import get_supabase
from models import SummaryCreate
from services import claude_client
from services.context_builder import build_context, get_political_context

router = APIRouter(prefix="/documents", tags=["summaries"])


def _length_to_instruction(length: int) -> str:
    if length <= 20:   return "3-5 korte kulepunkter, maks 150 ord"
    if length <= 40:   return "kort sammendrag med 5-8 kulepunkter, ca. 250 ord"
    if length <= 60:   return "middels detaljert sammendrag, ca. 400-500 ord"
    if length <= 80:   return "detaljert sammendrag med alle vesentlige punkt, ca. 700 ord"
    return "grundig analyse med all detaljer, bakgrunn og implikasjoner, ca. 1200 ord"


@router.post("/{doc_id}/summarize")
def summarize_document(doc_id: str, body: SummaryCreate):
    sb = get_supabase()
    result = sb.table("pol_documents").select("*").eq("id", doc_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Dokument ikke funnet")

    doc = result.data
    length_instruction = _length_to_instruction(body.length_setting)
    context = build_context(
        (doc.get("title") or "") + " " + (doc.get("raw_text") or "")[:500],
        exclude_document_id=doc_id,
    )
    political = get_political_context()

    system = """Du er en politisk rådgiver for en Høyre-politiker i en norsk kommune.
Analyser kommunale saksdokumenter og lag presise, politisk relevante sammendrag.
Skriv alltid på norsk bokmål.

Oppsummeringen skal alltid inneholde:
1. **Hva saken gjelder**
2. **Kommunens anbefaling/innstilling**
3. **Økonomikonsekvenser** (hvis relevant)
4. **Politiske implikasjoner for Høyre**

"""
    if political:
        system += political + "\n\n"
    if context:
        system += context + "\n\n"

    user = f"""Lag et sammendrag av følgende kommunale saksdokument.
Format: {length_instruction}

Dokument: {doc['title']}
{(doc.get('raw_text') or '')[:12000]}"""

    accumulated = []

    def generate():
        for chunk in claude_client.stream_text(system, user, max_tokens=2048):
            accumulated.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        full_text = "".join(accumulated)
        try:
            sb2 = get_supabase()
            sb2.table("pol_summaries").insert({
                "document_id": doc_id,
                "summary_text": full_text,
                "length_setting": body.length_setting,
            }).execute()
        except Exception:
            pass
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{doc_id}/summaries")
def get_summaries(doc_id: str):
    sb = get_supabase()
    result = (
        sb.table("pol_summaries")
        .select("*")
        .eq("document_id", doc_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
