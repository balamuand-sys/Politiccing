import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from database import get_connection
from models import ContentGenerateRequest
from services import claude_client
from services.context_builder import build_context, get_political_context, get_style_examples

router = APIRouter(prefix="/documents", tags=["content"])


def _length_words(content_type: str, length: int) -> tuple[int, str]:
    if content_type == "tale":
        min_words, max_words = 250, 2500
        words = int(min_words + (max_words - min_words) * (length - 1) / 99)
        if length <= 20:
            desc = "et kort 2-minutters innlegg"
        elif length <= 50:
            desc = f"et innlegg på ca. {words} ord (5-8 minutter)"
        elif length <= 80:
            desc = f"en tale på ca. {words} ord (10-15 minutter)"
        else:
            desc = f"en grundig tale på ca. {words} ord (20 minutter)"
    else:  # leserinnlegg
        min_words, max_words = 150, 800
        words = int(min_words + (max_words - min_words) * (length - 1) / 99)
        desc = f"et leserinnlegg på ca. {words} ord"
    return words, desc


def _sentiment_instruction(sentiment: int) -> str:
    if sentiment <= 20:
        return """Tonen skal være svært saklig og faktabasert:
- Referer til tall, statistikk og ekspertuttalelser
- Nøkterne konklusjoner uten følelsesladet språk
- Presist og akademisk"""
    elif sentiment <= 40:
        return """Tonen skal være saklig med litt personlighet:
- Fakta og tall i sentrum
- Noen personlige observasjoner
- Konkrete eksempler"""
    elif sentiment <= 60:
        return """Tonen skal være balansert mellom saklig og engasjert:
- Mix av fakta og verdier
- Personlige perspektiver
- Konstruktiv og løsningsorientert"""
    elif sentiment <= 80:
        return """Tonen skal være engasjert og appellerende:
- Verdier og prinsipper i fokus
- Personlige historier og eksempler
- Fremtidsvisjon for kommunen"""
    else:
        return """Tonen skal være svært engasjert og appellerende:
- Sterke Høyre-verdier: frihet, ansvar, fellesskap, valgfrihet
- Inspirerende historier og fremtidsvisjon
- Klare politiske standpunkter
- Appellerende og motiverende språk"""


def _build_content_system(content_type: str, doc: dict, context: str, political: str, style_examples: str) -> str:
    system = f"""Du er en dyktig norsk Høyre-politiker i en kommune som skriver {'taler' if content_type == 'tale' else 'leserinnlegg'}.

VIKTIGE REGLER:
- Skriv ALLTID i jeg-form, fra politikerens perspektiv
- Skriv på norsk bokmål
- Representerer Høyre sine verdier: frihet, ansvar, fellesskap, valgfrihet, privat initiativ
- Aldri bruk klisjeer som "det er viktig at" eller "vi må"
- Vær konkret og spesifikk, referer til faktiske tall og navn fra dokumentet

"""
    if style_examples:
        system += style_examples + "\n\n"
    if political:
        system += political + "\n\n"
    if context:
        system += context + "\n\n"
    return system


@router.post("/{doc_id}/generate")
def generate_content(doc_id: int, body: ContentGenerateRequest):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")

        doc = dict(doc)
        content_type = body.content_type.value

        words, length_desc = _length_words(content_type, body.length_setting)
        sentiment_instr = _sentiment_instruction(body.sentiment_setting)

        context = build_context(
            doc.get("title", "") + " " + (doc.get("raw_text", "")[:500]),
            conn,
            exclude_document_id=doc_id,
        )
        political = get_political_context(conn)
        style_examples = get_style_examples(conn, content_type)

        # Fetch enrichments for this doc
        cur.execute(
            "SELECT enrichment_type, content FROM enrichments WHERE document_id = ? ORDER BY created_at DESC",
            (doc_id,),
        )
        enrichments = cur.fetchall()
        enrichment_text = ""
        if enrichments:
            enrichment_text = "\n## Berikelser og bakgrunnsinformasjon:\n"
            for e in enrichments:
                enrichment_text += f"\n### {e['enrichment_type'].upper()}:\n{e['content'][:1000]}\n"

        system = _build_content_system(content_type, doc, context, political, style_examples)

        user = f"""Skriv {length_desc} om følgende sak fra kommunestyret.

{sentiment_instr}

SAKEN:
Tittel: {doc['title']}
Dato: {doc.get('meeting_date', 'ukjent')}
Utvalg: {doc.get('committee', 'ukjent')}

Dokumentinnhold:
{doc.get('raw_text', '')[:8000]}
{enrichment_text}

Skriv {'talen' if content_type == 'tale' else 'leserinnlegget'} nå:"""

        accumulated = []

        def generate():
            for chunk in claude_client.stream_text(system, user, max_tokens=3000):
                accumulated.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            full_text = "".join(accumulated)
            try:
                cur2 = conn.cursor()
                cur2.execute(
                    """INSERT INTO generated_content
                       (document_id, content_type, content_text, length_setting, sentiment_setting)
                       VALUES (?,?,?,?,?)""",
                    (doc_id, content_type, full_text, body.length_setting, body.sentiment_setting),
                )
                conn.commit()
                content_id = cur2.lastrowid
                yield f"data: {json.dumps({'done': True, 'content_id': content_id})}\n\n"
            except Exception:
                yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/content")
def get_content(doc_id: int, content_type: str = None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = "SELECT * FROM generated_content WHERE document_id = ?"
        params = [doc_id]
        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)
        query += " ORDER BY created_at DESC"
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post("/content/{content_id}/save-as-example")
def save_as_example(content_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM generated_content WHERE id = ?", (content_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Innhold ikke funnet")

        cur.execute(
            "INSERT INTO style_memory (content_type, example_text) VALUES (?,?)",
            (row["content_type"], row["content_text"]),
        )
        conn.commit()
        return {"ok": True, "style_memory_id": cur.lastrowid}
    finally:
        conn.close()
