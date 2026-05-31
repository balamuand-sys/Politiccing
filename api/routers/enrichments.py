from fastapi import APIRouter, HTTPException
from database import get_supabase
from models import EnrichmentRequest
from services import claude_client

router = APIRouter(prefix="/api/documents", tags=["enrichments"])

ENRICHMENT_CONFIGS = {
    "law": {
        "system": "Du er juridisk rådgiver for en norsk kommunepolitiker. Finn relevante lover og forskrifter. Skriv på norsk bokmål.",
        "user": "Finn relevante lover, forskrifter og paragrafhjemler for denne kommunale saken:\n\nTittel: {title}\nInnhold: {preview}\n\nList opp: lovnavn, paragrafnummer, og kort forklaring av relevans.",
    },
    "news": {
        "system": "Du er nyhetsanalytiker for en norsk kommunepolitiker. Finn relevante nyhetsartikler. Skriv på norsk bokmål.",
        "user": "Finn de 5 mest relevante norske nyhetsartiklene om:\n\nTittel: {title}\nKommune: {committee}\nInnhold: {preview}\n\nFor hver artikkel: tittel, nettsted, kort sammendrag, relevans.",
    },
    "municipal_comparison": {
        "system": "Du er kommunepolitisk analytiker. Fokuser på Høyre-styrte kommuner. Skriv på norsk bokmål.",
        "user": "Finn eksempler på hvordan andre norske kommuner har håndtert:\n\nTittel: {title}\nInnhold: {preview}\n\nFokuser på Høyre-styrte kommuner (Bærum, Asker, Stavanger, Bergen m.fl.) og vellykkede løsninger.",
    },
    "budget": {
        "system": "Du er økonomianalytiker for en norsk kommune. Skriv på norsk bokmål.",
        "user": "Finn relevante budsjett- og økonomidata for:\n\nTittel: {title}\nKommune: {committee}\nInnhold: {preview}\n\nInkluder kostnader i kontekst av kommunebudsjettet og sammenlignbare tall fra andre kommuner.",
    },
    "research": {
        "system": "Du er forskningsanalytiker for norske kommunepolitikere. Skriv på norsk bokmål.",
        "user": "Finn relevante forskningsrapporter og fagdokumentasjon for:\n\nTittel: {title}\nInnhold: {preview}\n\nSøk spesielt etter SSB-statistikk, NIBR-rapporter, NOU-utredninger, Menon-rapporter.",
    },
}


@router.post("/{doc_id}/enrich")
def enrich_document(doc_id: str, body: EnrichmentRequest):
    sb = get_supabase()
    result = sb.table("pol_documents").select("*").eq("id", doc_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Dokument ikke funnet")

    doc = result.data
    preview = (doc.get("raw_text") or "")[:3000]
    results = []

    for enrichment_type in body.types:
        config = ENRICHMENT_CONFIGS.get(enrichment_type)
        if not config:
            continue
        user = config["user"].format(
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
            row = sb.table("pol_enrichments").insert({
                "document_id": doc_id,
                "enrichment_type": enrichment_type,
                "content": content,
            }).execute().data[0]
            results.append(row)
        except Exception as e:
            results.append({"enrichment_type": enrichment_type, "error": str(e)})

    return results


@router.get("/{doc_id}/enrichments")
def get_enrichments(doc_id: str):
    sb = get_supabase()
    result = (
        sb.table("pol_enrichments")
        .select("*")
        .eq("document_id", doc_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
