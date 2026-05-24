import sqlite3
from .embeddings import semantic_search

MAX_CONTEXT_TOKENS = 8000
AVG_CHARS_PER_TOKEN = 4


def build_context(query: str, conn: sqlite3.Connection, exclude_document_id: int = None) -> str:
    results = semantic_search(query, conn, top_k=20)

    if exclude_document_id:
        results = [r for r in results if r["document_id"] != exclude_document_id]

    max_chars = MAX_CONTEXT_TOKENS * AVG_CHARS_PER_TOKEN
    sections = []
    used_chars = 0

    for r in results:
        header = f"[{r['title']} — {r.get('meeting_date', 'ukjent dato')} — {r.get('committee', '')}]\n"
        body = r["chunk_text"]
        section = header + body + "\n\n"
        if used_chars + len(section) > max_chars:
            break
        sections.append(section)
        used_chars += len(section)

    if not sections:
        return ""

    return "## Relevante tidligere saker fra databasen:\n\n" + "".join(sections)


def get_political_context(conn: sqlite3.Connection) -> str:
    cur = conn.cursor()
    cur.execute("SELECT topic, stance, notes FROM political_context ORDER BY created_at DESC")
    rows = cur.fetchall()
    if not rows:
        return ""
    lines = ["## Politiske standpunkter (Høyre):"]
    for row in rows:
        line = f"- **{row['topic']}**: {row['stance']}"
        if row["notes"]:
            line += f" ({row['notes']})"
        lines.append(line)
    return "\n".join(lines)


def get_style_examples(conn: sqlite3.Connection, content_type: str, max_examples: int = 3) -> str:
    cur = conn.cursor()
    cur.execute(
        "SELECT example_text FROM style_memory WHERE content_type = ? ORDER BY created_at DESC LIMIT ?",
        (content_type, max_examples),
    )
    rows = cur.fetchall()
    if not rows:
        return ""
    lines = [f"## Eksempler på din skrivestil ({content_type}):"]
    for i, row in enumerate(rows, 1):
        lines.append(f"\n### Eksempel {i}:\n{row['example_text'][:1500]}")
    return "\n".join(lines)
