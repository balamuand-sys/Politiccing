import json
from fastapi import APIRouter, HTTPException

from database import get_connection
from models import EnrichmentRequest
from services import claude_client

router = APIRouter(prefix="/documents", tags=["enrichments"])

ENRICHMENT_PROMPTS = {
    "law": {
        "query_prefix": "lovdata lovhjemmel paragraf",
        "system": """Du er en juridisk rådgiver som hjelper norske kommunepolitikere.
Finn relevante lover, forskrifter og paragrafer som er aktuelle for saken.
Fokuser på hjemler som er direkte nevnt eller implisitt relevant.
Skriv på norsk bokmål. Strukturer svaret tydelig med paragrafnummer og kort forklaring.""",
        "user_template": """Finn relevante lover og forskrifter for denne kommunale saken:

Tittel: {title}
Innhold: {preview}

List opp relevante lovhjemler med: paragrafnummer, lovnavn, kort forklaring av relevans.
Søk spesielt etter Plan- og bygningsloven, Kommuneloven, Opplæringsloven, og andre relevante lover.""",
    },
    "news": {
        "query_prefix": "norske nyheter",
        "system": """Du er en nyhetsanalytiker for en norsk kommunepolitiker.
Finn og oppsummer relevante nyhetsartikler om saken.
Skriv på norsk bokmål.""",
        "user_template": """Finn de 5 mest relevante norske nyhetsartiklene om denne kommunale saken:

Tittel: {title}
Kommune: {committee}
Innhold: {preview}

For hver artikkel, oppgi:
- Tittel og nettsted
- Kort sammendrag (2-3 setninger)
- Relevans for saken""",
    },
    "municipal_comparison": {
        "query_prefix": "andre kommuner vedtak Høyre",
        "system": """Du er en kommunepolitisk analytiker.
Finn hvordan andre norske kommuner, særlig Høyre-styrte kommuner, har håndtert tilsvarende saker.
Skriv på norsk bokmål.""",
        "user_template": """Finn eksempler på hvordan andre norske kommuner har håndtert denne typen sak:

Tittel: {title}
Innhold: {preview}

Fokuser spesielt på:
- Høyre-styrte kommuner (Bærum, Asker, Stavanger, Bergen m.fl.)
- Vellykkede løsninger og erfaringer
- Sammenlignbare vedtak""",
    },
    "budget": {
        "query_prefix": "kommunebudsjett økonomi",
        "system": """Du er en økonomianalytiker for en norsk kommune.
Finn relevante budsjett- og økonomidata.
Skriv på norsk bokmål.""",
        "user_template": """Finn relevante budsjett- og økonomidata for denne kommunale saken:

Tittel: {title}
Kommune: {committee}
Innhold: {preview}

Inkluder:
- Kostnader nevnt i dokumentet i kontekst av kommunebudsjettet
- Sammenlignbare poster fra andre kommuner
- Historiske tall hvis tilgjengelig""",
    },
    "research": {
        "query_prefix": "SSB NIBR NOU forskning rapport",
        "system": """Du er en forskningsanalytiker som hjelper norske kommunepolitikere.
Finn relevante forskningsrapporter, NOU-er, SSB-statistikk og fagrapporter.
Skriv på norsk bokmål.""",
        "user_template": """Finn relevante forskningsrapporter og faglig dokumentasjon for denne kommunale saken:

Tittel: {title}
Innhold: {preview}

Søk spesielt etter:
- SSB-statistikk og -rapporter
- NIBR-rapporter
- NOU-utredninger
- Menon-rapporter
- Kommunenes Sentralforbund (KS) publikasjoner""",
    },
}


@router.post("/{doc_id}/enrich")
def enrich_document(doc_id: int, body: EnrichmentRequest):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Dokument ikke funnet")

        doc = dict(doc)
        results = []

        for enrichment_type in body.types:
            config = ENRICHMENT_PROMPTS.get(enrichment_type)
            if not config:
                continue

            preview = (doc.get("raw_text") or "")[:3000]
            user = config["user_template"].format(
                title=doc.get("title", ""),
                committee=doc.get("committee", ""),
                preview=preview,
            )

            try:
                content = claude_client.complete(
                    system=config["system"],
                    user=user,
                    tools=[claude_client.WEB_SEARCH_TOOL],
                    max_tokens=2048,
                )

                cur.execute(
                    """INSERT INTO enrichments (document_id, enrichment_type, content)
                       VALUES (?,?,?)""",
                    (doc_id, enrichment_type, content),
                )
                conn.commit()
                enrichment_id = cur.lastrowid

                results.append({
                    "id": enrichment_id,
                    "document_id": doc_id,
                    "enrichment_type": enrichment_type,
                    "content": content,
                })

            except Exception as e:
                results.append({
                    "enrichment_type": enrichment_type,
                    "error": f"Feil ved berikelse: {str(e)}",
                })

        return results
    finally:
        conn.close()


@router.get("/{doc_id}/enrichments")
def get_enrichments(doc_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM enrichments WHERE document_id = ? ORDER BY created_at DESC",
            (doc_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
