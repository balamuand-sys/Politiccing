from .embeddings import embed_query
from database import get_supabase

MAX_CONTEXT_TOKENS = 8000
AVG_CHARS_PER_TOKEN = 4


def build_context(query: str, exclude_document_id: str = None) -> str:
    if not query.strip():
        return ""
    try:
        q_emb = embed_query(query)
        sb = get_supabase()
        result = sb.rpc("pol_search_documents", {
            "query_embedding": q_emb,
            "match_count": 20,
            "exclude_doc_id": str(exclude_document_id) if exclude_document_id else None,
        }).execute()

        rows = result.data or []
        max_chars = MAX_CONTEXT_TOKENS * AVG_CHARS_PER_TOKEN
        sections = []
        used = 0
        for row in rows:
            header = f"[{row['title']} — {row.get('meeting_date') or 'ukjent dato'} — {row.get('committee') or ''}]\n"
            section = header + row["chunk_text"] + "\n\n"
            if used + len(section) > max_chars:
                break
            sections.append(section)
            used += len(section)

        if not sections:
            return ""
        return "## Relevante tidligere saker:\n\n" + "".join(sections)
    except Exception:
        return ""


def get_political_context() -> str:
    try:
        sb = get_supabase()
        result = sb.table("pol_political_context").select("topic,stance,notes").order("created_at", desc=True).execute()
        rows = result.data or []
        if not rows:
            return ""
        lines = ["## Politiske standpunkter (Høyre):"]
        for row in rows:
            line = f"- **{row['topic']}**: {row['stance']}"
            if row.get("notes"):
                line += f" ({row['notes']})"
            lines.append(line)
        return "\n".join(lines)
    except Exception:
        return ""


def get_style_examples(content_type: str, max_examples: int = 3) -> str:
    try:
        sb = get_supabase()
        result = (
            sb.table("pol_style_memory")
            .select("example_text")
            .eq("content_type", content_type)
            .order("created_at", desc=True)
            .limit(max_examples)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return ""
        lines = [f"## Eksempler på din skrivestil ({content_type}):"]
        for i, row in enumerate(rows, 1):
            lines.append(f"\n### Eksempel {i}:\n{row['example_text'][:1500]}")
        return "\n".join(lines)
    except Exception:
        return ""
