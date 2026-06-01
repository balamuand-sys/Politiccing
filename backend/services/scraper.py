import asyncio
import os
import json
from pathlib import Path
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path.home() / "politikerapp" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# In-memory session state (single user, local app)
_sessions: dict = {}


async def start_browser_session(portal_url: str, session_id: str) -> str:
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    if portal_url:
        await page.goto(portal_url)

    _sessions[session_id] = {
        "playwright": pw,
        "browser": browser,
        "context": context,
        "page": page,
        "status": "waiting_for_login",
        "progress": [],
        "done": False,
        "error": None,
    }
    return session_id


async def signal_login_complete(session_id: str):
    if session_id not in _sessions:
        raise ValueError(f"Session {session_id} not found")
    _sessions[session_id]["status"] = "scraping"


async def scrape_documents(session_id: str, portal_url: str) -> AsyncGenerator[dict, None]:
    session = _sessions.get(session_id)
    if not session:
        yield {"type": "error", "message": "Sesjon ikke funnet"}
        return

    # Wait for login signal
    for _ in range(600):  # max 10 minutes wait
        if session["status"] == "scraping":
            break
        await asyncio.sleep(1)
    else:
        yield {"type": "error", "message": "Tidsavbrudd under innlogging"}
        return

    try:
        context = session["context"]
        page = session["page"]

        yield {"type": "status", "message": "Navigerer til møteliste..."}

        # Navigate to meetings list
        await page.wait_for_load_state("networkidle", timeout=30000)

        # Find meeting links - ACOS portal structure varies, attempt common patterns
        meeting_links = await page.query_selector_all("a[href*='meeting'], a[href*='mote'], a[href*='Mote']")
        total_meetings = len(meeting_links)

        if total_meetings == 0:
            # Try finding by table rows
            meeting_links = await page.query_selector_all("table tr td a")
            total_meetings = len(meeting_links)

        yield {"type": "status", "message": f"Fant {total_meetings} møter", "total": total_meetings}

        downloaded = 0
        for i, link in enumerate(meeting_links):
            try:
                href = await link.get_attribute("href")
                text = await link.inner_text()

                yield {
                    "type": "progress",
                    "message": f"Behandler møte: {text.strip()[:60]}",
                    "current": i + 1,
                    "total": total_meetings,
                }

                # Navigate to meeting page
                meeting_page = await context.new_page()
                if href.startswith("http"):
                    await meeting_page.goto(href, timeout=30000)
                else:
                    base = portal_url.rstrip("/")
                    await meeting_page.goto(f"{base}/{href.lstrip('/')}", timeout=30000)

                await meeting_page.wait_for_load_state("networkidle", timeout=20000)

                # Find PDF links
                pdf_links = await meeting_page.query_selector_all("a[href$='.pdf'], a[href*='pdf']")

                for pdf_link in pdf_links:
                    pdf_href = await pdf_link.get_attribute("href")
                    pdf_name = await pdf_link.inner_text()
                    if not pdf_href:
                        continue

                    if not pdf_href.startswith("http"):
                        base = portal_url.rstrip("/")
                        pdf_href = f"{base}/{pdf_href.lstrip('/')}"

                    # Download PDF
                    try:
                        async with context.expect_download(timeout=30000) as download_info:
                            await meeting_page.evaluate(f"window.open('{pdf_href}', '_blank')")
                        download = await download_info.value
                        save_path = UPLOAD_DIR / f"scrape_{session_id}_{downloaded}_{download.suggested_filename}"
                        await download.save_as(str(save_path))
                        downloaded += 1

                        yield {
                            "type": "file_downloaded",
                            "file_path": str(save_path),
                            "file_name": pdf_name.strip() or download.suggested_filename,
                            "meeting": text.strip(),
                        }
                    except Exception as e:
                        logger.warning(f"Could not download {pdf_href}: {e}")

                await meeting_page.close()

            except Exception as e:
                logger.warning(f"Error processing meeting {i}: {e}")
                continue

        yield {
            "type": "done",
            "message": f"Ferdig! Lastet ned {downloaded} dokumenter",
            "downloaded": downloaded,
        }

    except Exception as e:
        yield {"type": "error", "message": f"Feil under skraping: {str(e)}"}
    finally:
        session["done"] = True
        try:
            await session["browser"].close()
            await session["playwright"].stop()
        except Exception:
            pass


def get_session(session_id: str) -> dict:
    return _sessions.get(session_id)


def cleanup_session(session_id: str):
    _sessions.pop(session_id, None)
