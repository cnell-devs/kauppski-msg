import os
import json
from jose import jwt, JWTError


def validate_token(token: str) -> str:
    """Validate a Supabase JWT and return the user's UUID (sub claim)."""
    secret = os.environ["SUPABASE_JWT_SECRET"]
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("No sub claim in token")
        return user_id
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")
