import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from database import get_supabase
from models import ContentGenerateRequest
from services import claude_client
from services.context_builder import build_context, get_political_context, get_style_examples

router = APIRouter(prefix="/documents", tags=["content"])


def _length_words(content_type: str, length: int) -> tuple[int, str]:
    if content_type == "tale":
        words = int(250 + (2500 - 250) * (length - 1) / 99)
        if length <= 20:   desc = "et kort 2-minutters innlegg"
        elif length <= 50: desc = f"et innlegg på ca. {words} ord (5-8 minutter)"
        elif length <= 80: desc = f"en tale på ca. {words} ord (10-15 minutter)"
        else:              desc = f"en grundig tale på ca. {words} ord (20 minutter)"
    else:
        words = int(150 + (800 - 150) * (length - 1) / 99)
        desc = f"et leserinnlegg på ca. {words} ord"
    return words, desc


def _sentiment_instruction(sentiment: int) -> str:
    if sentiment <= 20:
        return "Tonen skal være svært saklig: referer til tall, statistikk og eksperter. Nøkterne konklusjoner."
    if sentiment <= 40:
        return "Tonen skal være saklig med litt personlighet: fakta i sentrum, noen personlige observasjoner."
    if sentiment <= 60:
        return "Tonen skal være balansert: mix av fakta og verdier, konstruktiv og løsningsorientert."
    if sentiment <= 80:
        return "Tonen skal være engasjert: verdier og prinsipper i fokus, personlige historier og fremtidsvisjon."
    return "Tonen skal være svært engasjert og appellerende: Høyre-verdier (frihet, ansvar, fellesskap, valgfrihet), inspirerende historier, klare politiske standpunkter."


@router.post("/{doc_id}/generate")
def generate_content(doc_id: str, body: ContentGenerateRequest):
    sb = get_supabase()
    result = sb.table("pol_documents").select("*").eq("id", doc_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Dokument ikke funnet")

    doc = result.data
    content_type = body.content_type.value
    _, length_desc = _length_words(content_type, body.length_setting)
    sentiment_instr = _sentiment_instruction(body.sentiment_setting)

    context = build_context(
        (doc.get("title") or "") + " " + (doc.get("raw_text") or "")[:500],
        exclude_document_id=doc_id,
    )
    political = get_political_context()
    style_examples = get_style_examples(content_type)

    # Fetch enrichments
    enr_result = (
        sb.table("pol_enrichments")
        .select("enrichment_type,content")
        .eq("document_id", doc_id)
        .order("created_at", desc=True)
        .execute()
    )
    enrichment_text = ""
    for e in (enr_result.data or []):
        enrichment_text += f"\n### {e['enrichment_type'].upper()}:\n{(e.get('content') or '')[:1000]}\n"

    system = f"""Du er en dyktig norsk Høyre-politiker i en kommune som skriver {'taler' if content_type == 'tale' else 'leserinnlegg'}.

VIKTIGE REGLER:
- Skriv ALLTID i jeg-form, fra politikerens perspektiv
- Skriv på norsk bokmål
- Representerer Høyre sine verdier: frihet, ansvar, fellesskap, valgfrihet, privat initiativ
- Vær konkret og spesifikk, referer til faktiske tall og navn

"""
    if style_examples: system += style_examples + "\n\n"
    if political:      system += political + "\n\n"
    if context:        system += context + "\n\n"

    user = f"""Skriv {length_desc} om følgende sak.

{sentiment_instr}

SAKEN:
Tittel: {doc['title']}
Dato: {doc.get('meeting_date') or 'ukjent'}
Utvalg: {doc.get('committee') or 'ukjent'}

Dokumentinnhold:
{(doc.get('raw_text') or '')[:8000]}
{'## Berikelser:' + enrichment_text if enrichment_text else ''}

Skriv {'talen' if content_type == 'tale' else 'leserinnlegget'} nå:"""

    accumulated = []

    def generate():
        for chunk in claude_client.stream_text(system, user, max_tokens=3000):
            accumulated.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        full_text = "".join(accumulated)
        content_id = None
        try:
            sb2 = get_supabase()
            row = sb2.table("pol_generated_content").insert({
                "document_id": doc_id,
                "content_type": content_type,
                "content_text": full_text,
                "length_setting": body.length_setting,
                "sentiment_setting": body.sentiment_setting,
            }).execute().data[0]
            content_id = row["id"]
        except Exception:
            pass
        yield f"data: {json.dumps({'done': True, 'content_id': content_id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{doc_id}/content")
def get_content(doc_id: str, content_type: str = None):
    sb = get_supabase()
    query = (
        sb.table("pol_generated_content")
        .select("*")
        .eq("document_id", doc_id)
        .order("created_at", desc=True)
    )
    if content_type:
        query = query.eq("content_type", content_type)
    return query.execute().data or []


@router.post("/content/{content_id}/save-as-example")
def save_as_example(content_id: str):
    sb = get_supabase()
    row = sb.table("pol_generated_content").select("*").eq("id", content_id).single().execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Innhold ikke funnet")
    result = sb.table("pol_style_memory").insert({
        "content_type": row.data["content_type"],
        "example_text": row.data["content_text"],
    }).execute()
    return {"ok": True, "style_memory_id": result.data[0]["id"]}
