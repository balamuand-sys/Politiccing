from pathlib import Path
from fastapi import APIRouter, HTTPException
from models import SettingsUpdate, Settings
from services import claude_client

router = APIRouter(prefix="/settings", tags=["settings"])

ENV_PATH = Path.home() / "politikerapp" / ".env"
ENV_KEYS = ["ANTHROPIC_API_KEY", "PORTAL_URL", "USER_NAME", "PARTY"]


def _read_env() -> dict:
    result = {}
    if not ENV_PATH.exists():
        return result
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def _write_env(data: dict):
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for key, value in data.items():
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n")


@router.get("", response_model=dict)
def get_settings():
    env = _read_env()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    # Mask API key for display
    if api_key and len(api_key) > 8:
        masked = api_key[:4] + "..." + api_key[-4:]
    else:
        masked = "ikke satt" if not api_key else api_key
    return {
        "api_key_set": bool(api_key),
        "api_key_masked": masked,
        "portal_url": env.get("PORTAL_URL", ""),
        "user_name": env.get("USER_NAME", ""),
        "party": env.get("PARTY", "Høyre"),
    }


@router.post("")
def update_settings(body: SettingsUpdate):
    env = _read_env()

    if body.api_key is not None:
        env["ANTHROPIC_API_KEY"] = body.api_key
    if body.portal_url is not None:
        env["PORTAL_URL"] = body.portal_url
    if body.user_name is not None:
        env["USER_NAME"] = body.user_name
    if body.party is not None:
        env["PARTY"] = body.party

    _write_env(env)
    return {"ok": True}


@router.post("/test-api")
def test_api_connection():
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
            raise HTTPException(status_code=400, detail="Ugyldig API-nøkkel. Sjekk innstillingene.")
        elif "rate" in error_msg.lower():
            raise HTTPException(status_code=429, detail="For mange forespørsler. Prøv igjen om litt.")
        else:
            raise HTTPException(status_code=500, detail=f"API-feil: {error_msg}")
