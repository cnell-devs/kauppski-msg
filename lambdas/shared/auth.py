import os
import json
import time
import urllib.request
from jose import jwt, JWTError

_jwks_cache = None
_jwks_fetched_at = 0
_JWKS_TTL = 3600  # re-fetch public keys at most once per hour


def _get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.time()
    if _jwks_cache is None or now - _jwks_fetched_at > _JWKS_TTL:
        url = os.environ["SUPABASE_URL"].rstrip("/") + "/auth/v1/.well-known/jwks.json"
        with urllib.request.urlopen(url, timeout=5) as resp:
            _jwks_cache = json.loads(resp.read())
        _jwks_fetched_at = now
    return _jwks_cache


def validate_token(token: str) -> str:
    """Validate a Supabase JWT via JWKS and return the user's UUID (sub claim)."""
    try:
        payload = jwt.decode(
            token,
            _get_jwks(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("No sub claim in token")
        return user_id
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")
