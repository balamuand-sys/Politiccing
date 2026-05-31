from fastapi import APIRouter, HTTPException, Query
from database import get_supabase
from models import StyleMemoryCreate, PoliticalContextCreate
from services import claude_client
from services.embeddings import embed_query

router = APIRouter(prefix="/api/memory", tags=["memory"])


# ---- Style memory ----

@router.get("/style")
def list_style_memory(content_type: str = None):
    sb = get_supabase()
    query = sb.table("pol_style_memory").select("*").order("created_at", desc=True)
    if content_type:
        query = query.eq("content_type", content_type)
    return query.execute().data or []


@router.post("/style")
def add_style_example(body: StyleMemoryCreate):
    sb = get_supabase()
    result = sb.table("pol_style_memory").insert({
        "content_type": body.content_type.value,
        "example_text": body.example_text,
    }).execute()
    return result.data[0]


@router.delete("/style/{style_id}")
def delete_style_example(style_id: str):
    sb = get_supabase()
    sb.table("pol_style_memory").delete().eq("id", style_id).execute()
    return {"ok": True}


@router.post("/style/analyze")
def analyze_style():
    sb = get_supabase()
    result = sb.table("pol_style_memory").select("content_type,example_text").order("created_at", desc=True).limit(10).execute()
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=400, detail="Ingen stileksempler lagret ennå")

    examples_text = "\n\n---\n\n".join(
        [f"TYPE: {r['content_type']}\n\n{r['example_text']}" for r in rows]
    )
    analysis = claude_client.complete(
        system="Du er en skrivestilanalytiker. Analyser teksteksempler og beskriv forfatterens skrivestil. Skriv på norsk bokmål.",
        user=f"""Analyser disse tekstene og beskriv skrivestilen:

{examples_text[:8000]}

Beskriv: setningsstruktur, ordvalg, argumentasjonsteknikk, tone, og særtrekk.""",
        max_tokens=1024,
    )
    return {"analysis": analysis}


# ---- Political context ----

@router.get("/political-context")
def list_political_context():
    sb = get_supabase()
    return sb.table("pol_political_context").select("*").order("topic").execute().data or []


@router.post("/political-context")
def add_political_context(body: PoliticalContextCreate):
    sb = get_supabase()
    result = sb.table("pol_political_context").insert({
        "topic": body.topic,
        "stance": body.stance,
        "notes": body.notes,
    }).execute()
    return result.data[0]


@router.put("/political-context/{context_id}")
def update_political_context(context_id: str, body: PoliticalContextCreate):
    sb = get_supabase()
    result = sb.table("pol_political_context").update({
        "topic": body.topic,
        "stance": body.stance,
        "notes": body.notes,
    }).eq("id", context_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Standpunkt ikke funnet")
    return result.data[0]


@router.delete("/political-context/{context_id}")
def delete_political_context(context_id: str):
    sb = get_supabase()
    sb.table("pol_political_context").delete().eq("id", context_id).execute()
    return {"ok": True}


# ---- Cross-document search ----

@router.get("/search")
def search_across_documents(q: str = Query(..., min_length=2), top_k: int = 15):
    sb = get_supabase()
    try:
        q_emb = embed_query(q)
        result = sb.rpc("pol_search_documents", {
            "query_embedding": q_emb,
            "match_count": top_k,
        }).execute()
        return result.data or []
    except Exception:
        result = sb.table("pol_documents").select(
            "id,title,meeting_date,committee"
        ).ilike("title", f"%{q}%").limit(top_k).execute()
        return [{"document_id": r["id"], "title": r["title"],
                 "chunk_text": r["title"], "score": 0.5,
                 "meeting_date": r.get("meeting_date"),
                 "committee": r.get("committee")} for r in (result.data or [])]
