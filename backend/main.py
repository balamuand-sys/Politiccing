import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
LOG_DIR = Path.home() / "politikerapp" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

from database import init_db
from routers import documents, summaries, enrichments, content, memory, scraping, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logging.getLogger(__name__).info("Database initialized")
    yield


app = FastAPI(
    title="Politikerapp API",
    description="Lokal AI-assistent for kommunepolitikere",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(summaries.router, prefix="/api")
app.include_router(enrichments.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(scraping.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Politikerapp"}
