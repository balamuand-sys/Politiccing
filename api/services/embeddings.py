import os
from typing import List

VOYAGE_MODEL = "voyage-multilingual-2"
EMBEDDING_DIM = 1024
CHUNK_SIZE = 500   # words
CHUNK_OVERLAP = 50  # words


def _client():
    import voyageai
    return voyageai.Client(api_key=os.environ.get("VOYAGE_API_KEY", ""))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += chunk_size - overlap
    return chunks


def embed_documents(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    client = _client()
    # Voyage AI accepts up to 128 texts per call
    all_embeddings = []
    batch_size = 64
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = client.embed(batch, model=VOYAGE_MODEL, input_type="document")
        all_embeddings.extend(result.embeddings)
    return all_embeddings


def embed_query(query: str) -> List[float]:
    client = _client()
    result = client.embed([query], model=VOYAGE_MODEL, input_type="query")
    return result.embeddings[0]
