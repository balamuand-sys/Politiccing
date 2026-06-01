import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import ensure_storage_bucket
from routers import documents, summaries, enrichments, content, memory, settings

# Sub-app: routers use prefixes without /api (e.g. /documents, /memory)
api = FastAPI(
    title="Politikerapp API",
    description="AI-assistent for kommunepolitikere",
    version="2.0.0",
)

api.include_router(documents.router)
api.include_router(summaries.router)
api.include_router(enrichments.router)
api.include_router(content.router)
api.include_router(memory.router)
api.include_router(settings.router)


@api.get("/health")
def health():
    return {"status": "ok", "app": "Politikerapp v2"}


# Root app: Vercel serverless receives the full path (/api/...) and forwards here.
# Mounting api at /api means /api/documents/... routes to the /documents/ router.
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api", api)

try:
    ensure_storage_bucket()
except Exception:
    pass
