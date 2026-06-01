import asyncio
import json
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import get_connection
from services import scraper as scraper_service
from services.pdf_parser import extract_text, get_preview
from services import claude_client
from services.embeddings import chunk_text, store_embeddings

router = APIRouter(prefix="/scraping", tags=["scraping"])


class StartScrapeRequest(BaseModel):
    portal_url: str


@router.post("/start")
async def start_scrape(body: StartScrapeRequest):
    session_id = str(uuid.uuid4())[:8]
    await scraper_service.start_browser_session(body.portal_url, session_id)
    return {"session_id": session_id, "status": "waiting_for_login"}


@router.post("/continue/{session_id}")
async def continue_scrape(session_id: str):
    session = scraper_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesjon ikke funnet")
    await scraper_service.signal_login_complete(session_id)
    return {"ok": True, "status": "scraping"}


@router.get("/stream/{session_id}")
async def stream_scraping_progress(session_id: str):
    session = scraper_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesjon ikke funnet")

    portal_url = ""

    async def generate():
        conn = get_connection()
        try:
            async for event in scraper_service.scrape_documents(session_id, portal_url):
                yield f"data: {json.dumps(event)}\n\n"

                if event.get("type") == "file_downloaded":
                    file_path = event.get("file_path")
                    file_name = event.get("file_name", "Ukjent dokument")
                    meeting = event.get("meeting", "")

                    try:
                        raw_text = extract_text(file_path)
                        preview = get_preview(raw_text, 3000)

                        # Extract metadata with Claude
                        meta_prompt = f"""Ekstraher metadata fra dette dokumentet. Returner JSON med feltene:
title, meeting_date (YYYY-MM-DD eller null), committee, document_type (innkalling/saksdokument/protokoll/vedlegg)

Dokument (første del):
{preview}

Svar kun med JSON."""

                        try:
                            meta_str = claude_client.complete(
                                system="Ekstraher metadata fra norske kommunedokumenter. Svar kun med JSON.",
                                user=meta_prompt,
                                max_tokens=256,
                            )
                            import json as json_module
                            meta_str = meta_str.strip()
                            if meta_str.startswith("```"):
                                meta_str = meta_str.split("```")[1]
                                if meta_str.startswith("json"):
                                    meta_str = meta_str[4:]
                            metadata = json_module.loads(meta_str)
                        except Exception:
                            metadata = {
                                "title": file_name,
                                "meeting_date": None,
                                "committee": meeting,
                                "document_type": "saksdokument",
                            }

                        cur = conn.cursor()
                        cur.execute(
                            """INSERT INTO documents (title, meeting_date, committee, document_type, source, raw_text, file_path)
                               VALUES (?,?,?,?,?,?,?)""",
                            (
                                metadata.get("title", file_name),
                                metadata.get("meeting_date"),
                                metadata.get("committee", meeting),
                                metadata.get("document_type", "saksdokument"),
                                "scrape",
                                raw_text,
                                file_path,
                            ),
                        )
                        doc_id = cur.lastrowid
                        conn.commit()

                        try:
                            chunks = chunk_text(raw_text)
                            store_embeddings(doc_id, chunks, conn)
                        except Exception:
                            pass

                        yield f"data: {json.dumps({'type': 'saved', 'doc_id': doc_id, 'title': metadata.get('title', file_name)})}\n\n"

                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'error', 'message': f'Feil ved lagring: {str(e)}'})}\n\n"

        finally:
            conn.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/session/{session_id}")
def get_session_status(session_id: str):
    session = scraper_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesjon ikke funnet")
    return {
        "session_id": session_id,
        "status": session.get("status"),
        "done": session.get("done"),
    }
