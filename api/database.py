import os
from supabase import create_client, Client


def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def ensure_storage_bucket():
    try:
        sb = get_supabase()
        sb.storage.create_bucket("pol-documents", options={"public": False})
    except Exception:
        pass  # Bucket already exists
