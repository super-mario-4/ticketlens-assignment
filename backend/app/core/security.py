import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import Settings

_ALGORITHM = "HS256"
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    encoded = (base64.b64encode(value).decode() for value in (salt, _derive(password, salt)))
    return "scrypt$" + "$".join(encoded)


def verify_password(password: str, stored: str) -> bool:
    """False for anything that is not a real hash."""
    parts = stored.split("$")
    if len(parts) != 3 or parts[0] != "scrypt":
        return False
    salt, expected = (base64.b64decode(value) for value in parts[1:])
    return hmac.compare_digest(_derive(password, salt), expected)


def create_token(user_id: uuid.UUID, settings: Settings) -> str:
    claims = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm=_ALGORITHM)


def read_token(token: str, settings: Settings) -> uuid.UUID | None:
    """None for an invalid or expired token."""
    try:
        claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=[_ALGORITHM])
        return uuid.UUID(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
