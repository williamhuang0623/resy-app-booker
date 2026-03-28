"""
Security helpers: password hashing, JWT, and Fernet encryption.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

# ── Password hashing (bcrypt) ─────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── Fernet symmetric encryption ───────────────────────────────────────────────

def _fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt(value: str) -> str:
    """Encrypt a plaintext string and return a URL-safe base64 token."""
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a Fernet token back to plaintext. Raises InvalidToken on failure."""
    return _fernet().decrypt(token.encode()).decode()


def safe_decrypt(token: Optional[str]) -> Optional[str]:
    """Decrypt, returning None if the token is missing or invalid."""
    if not token:
        return None
    try:
        return decrypt(token)
    except (InvalidToken, Exception):
        return None


# ── JWT ───────────────────────────────────────────────────────────────────────

ACCESS_TOKEN_EXPIRE_DAYS = 30
ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT. Returns the payload dict.
    Raises JWTError on invalid / expired tokens.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
