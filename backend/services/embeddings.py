import numpy as np
import sqlite3
from typing import List, Tuple
import re


CHUNK_SIZE = 500  # words
CHUNK_OVERLAP = 50  # words
EMBEDDING_DIM = 1024


def _get_model():
    from sentence_transformers import SentenceTransformer
    if not hasattr(_get_model, "_instance"):
        _get_model._instance = SentenceTransformer("intfloat/multilingual-e5-large")
    return _get_model._instance


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start += chunk_size - overlap
    return chunks


def embed_chunks(chunks: List[str]) -> np.ndarray:
    model = _get_model()
    # multilingual-e5 requires "query: " / "passage: " prefix
    prefixed = [f"passage: {c}" for c in chunks]
    embeddings = model.encode(prefixed, normalize_embeddings=True)
    return embeddings


def store_embeddings(document_id: int, chunks: List[str], conn: sqlite3.Connection):
    """Store chunks in document_chunks and their embeddings in document_embeddings."""
    embeddings = embed_chunks(chunks)
    cur = conn.cursor()

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        cur.execute(
            "INSERT INTO document_chunks (document_id, chunk_index, chunk_text) VALUES (?,?,?)",
            (document_id, i, chunk),
        )
        chunk_id = cur.lastrowid
        try:
            cur.execute(
                "INSERT INTO document_embeddings (chunk_id, embedding) VALUES (?,?)",
                (chunk_id, emb.tobytes()),
            )
        except Exception:
            pass

    conn.commit()


def semantic_search(
    query: str, conn: sqlite3.Connection, top_k: int = 10
) -> List[dict]:
    model = _get_model()
    q_emb = model.encode([f"query: {query}"], normalize_embeddings=True)[0]

    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT de.chunk_id, de.distance
            FROM document_embeddings de
            WHERE de.embedding MATCH ?
            ORDER BY de.distance
            LIMIT ?
            """,
            (q_emb.tobytes(), top_k),
        )
        rows = cur.fetchall()
    except Exception:
        # sqlite-vec not available — fall back to full-text keyword match
        words = query.lower().split()
        like_clauses = " OR ".join([f"LOWER(chunk_text) LIKE ?" for _ in words])
        params = [f"%{w}%" for w in words] + [top_k]
        cur.execute(
            f"SELECT id as chunk_id, 0.5 as distance FROM document_chunks WHERE {like_clauses} LIMIT ?",
            params,
        )
        rows = cur.fetchall()

    results = []
    for row in rows:
        chunk_id = row[0]
        distance = row[1]
        cur.execute(
            """SELECT dc.chunk_text, dc.document_id, d.title, d.meeting_date, d.committee
               FROM document_chunks dc
               JOIN documents d ON d.id = dc.document_id
               WHERE dc.id = ?""",
            (chunk_id,),
        )
        chunk_row = cur.fetchone()
        if chunk_row:
            results.append({
                "document_id": chunk_row["document_id"],
                "title": chunk_row["title"],
                "chunk_text": chunk_row["chunk_text"],
                "score": float(1 - distance),
                "meeting_date": chunk_row["meeting_date"],
                "committee": chunk_row["committee"],
            })

    return results
