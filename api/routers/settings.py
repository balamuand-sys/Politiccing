import os
from fastapi import APIRouter, HTTPException
from database import get_supabase
from models import SettingsUpdate
from services import claude_client

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_setting(sb, key: str) -> str:
    result = sb.table("pol_settings").select("value").eq("key", key).single().execute()
    return (result.data or {}).get("value", "") or ""


def _set_setting(sb, key: str, value: str):
    sb.table("pol_settings").upsert({"key": key, "value": value}, on_conflict="key").execute()


@router.get("")
def get_settings():
    sb = get_supabase()
    api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
    voyage_set = bool(os.environ.get("VOYAGE_API_KEY"))
    return {
        "api_key_set": api_key_set,
        "voyage_key_set": voyage_set,
        "user_name": _get_setting(sb, "user_name"),
        "party": _get_setting(sb, "party") or "Høyre",
        "portal_url": _get_setting(sb, "portal_url"),
    }


@router.post("")
def update_settings(body: SettingsUpdate):
    sb = get_supabase()
    if body.user_name is not None:
        _set_setting(sb, "user_name", body.user_name)
    if body.party is not None:
        _set_setting(sb, "party", body.party)
    if body.portal_url is not None:
        _set_setting(sb, "portal_url", body.portal_url)
    return {"ok": True}


@router.post("/test-api")
def test_api_connection():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY er ikke satt i Vercel Environment Variables.")
    try:
        result = claude_client.complete(
            system="Du er en hjelpsom assistent.",
            user="Si 'OK' på norsk.",
            max_tokens=10,
        )
        return {"ok": True, "response": result}
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "authentication" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Ugyldig API-nøkkel.")
        raise HTTPException(status_code=500, detail=f"API-feil: {error_msg}")
