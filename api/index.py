import sys
import os

# Ensure the api/ directory is on sys.path for Vercel serverless
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import ensure_storage_bucket
from routers import documents, summaries, enrichments, content, memory, settings

app = FastAPI(
    title="Politikerapp API",
    description="AI-assistent for kommunepolitikere",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure Supabase storage bucket exists (idempotent)
try:
    ensure_storage_bucket()
except Exception:
    pass

app.include_router(documents.router)
app.include_router(summaries.router)
app.include_router(enrichments.router)
app.include_router(content.router)
app.include_router(memory.router)
app.include_router(settings.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Politikerapp v2"}
