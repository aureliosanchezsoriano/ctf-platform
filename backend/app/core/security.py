from datetime import datetime, timedelta, timezone
from typing import Any
import hmac
import hashlib
import bcrypt
from jose import jwt
from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(subject: str, extra_claims: dict[str, Any] = {}) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        **extra_claims,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def generate_flag(user_id: str, challenge_id: str) -> str:
    """Generate a unique flag per user per challenge using HMAC-SHA256."""
    message = f"{user_id}:{challenge_id}".encode()
    secret = settings.flag_hmac_secret.encode()
    digest = hmac.new(secret, message, hashlib.sha256).hexdigest()[:24]
    return f"{settings.flag_prefix}{{{digest}}}"


def verify_flag(submitted: str, user_id: str, challenge_id: str) -> bool:
    """Constant-time flag comparison to prevent timing attacks."""
    expected = generate_flag(user_id, challenge_id)
    return hmac.compare_digest(submitted.strip(), expected)
