from fastapi import APIRouter, HTTPException, Query
from typing import List

from database import get_connection
from models import StyleMemoryCreate, PoliticalContextCreate
from services import claude_client
from services.embeddings import semantic_search

router = APIRouter(prefix="/memory", tags=["memory"])


# --- Style Memory ---

@router.get("/style")
def list_style_memory(content_type: str = None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        if content_type:
            cur.execute(
                "SELECT * FROM style_memory WHERE content_type = ? ORDER BY created_at DESC",
                (content_type,),
            )
        else:
            cur.execute("SELECT * FROM style_memory ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post("/style")
def add_style_example(body: StyleMemoryCreate):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO style_memory (content_type, example_text) VALUES (?,?)",
            (body.content_type.value, body.example_text),
        )
        conn.commit()
        cur.execute("SELECT * FROM style_memory WHERE id = ?", (cur.lastrowid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.delete("/style/{style_id}")
def delete_style_example(style_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM style_memory WHERE id = ?", (style_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Eksempel ikke funnet")
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@router.post("/style/analyze")
def analyze_style():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT content_type, example_text FROM style_memory ORDER BY created_at DESC LIMIT 10")
        rows = cur.fetchall()

        if not rows:
            raise HTTPException(status_code=400, detail="Ingen stileksempler lagret ennå")

        examples_text = "\n\n---\n\n".join(
            [f"TYPE: {r['content_type']}\n\n{r['example_text']}" for r in rows]
        )

        result = claude_client.complete(
            system="""Du er en skrivestilanalytiker. Analyser teksteksempler og beskriv forfatterens skrivestil.
Skriv på norsk bokmål. Vær konkret og spesifikk.""",
            user=f"""Analyser disse tekstene og beskriv skrivestilen på en kortfattet og nyttig måte:

{examples_text[:8000]}

Beskriv:
1. Setningsstruktur og lengde
2. Ordvalg og register
3. Argumentasjonsteknikk
4. Personlighet og tone
5. Særtrekk og mønstre som går igjen""",
            max_tokens=1024,
        )

        return {"analysis": result}
    finally:
        conn.close()


# --- Political Context ---

@router.get("/political-context")
def list_political_context():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM political_context ORDER BY topic")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post("/political-context")
def add_political_context(body: PoliticalContextCreate):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO political_context (topic, stance, notes) VALUES (?,?,?)",
            (body.topic, body.stance, body.notes),
        )
        conn.commit()
        cur.execute("SELECT * FROM political_context WHERE id = ?", (cur.lastrowid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.put("/political-context/{context_id}")
def update_political_context(context_id: int, body: PoliticalContextCreate):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE political_context SET topic=?, stance=?, notes=? WHERE id=?",
            (body.topic, body.stance, body.notes, context_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Standpunkt ikke funnet")
        conn.commit()
        cur.execute("SELECT * FROM political_context WHERE id = ?", (context_id,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.delete("/political-context/{context_id}")
def delete_political_context(context_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM political_context WHERE id = ?", (context_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Standpunkt ikke funnet")
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# --- Cross-document semantic search ---

@router.get("/search")
def search_across_documents(q: str = Query(..., min_length=2), top_k: int = 15):
    conn = get_connection()
    try:
        results = semantic_search(q, conn, top_k=top_k)
        return results
    finally:
        conn.close()
