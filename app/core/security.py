from datetime import datetime, timedelta, timezone
import jwt
import hashlib
import secrets

from app.core.config import settings

# 사용자 ID를 사용하여 JWT 생성 (encode)
def create_access_token(subject: str) -> str :
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": subject,
        "exp": expire
    }

    token = jwt.encode(
        payload, 
        settings.jwt_secret,
        algorithm = settings.jwt_algorithm
    )

    return token

# JWT를 사용해서 사용자 ID 확인 (decode)
def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms = [settings.jwt_algorithm]
    )

    return payload

def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def get_refresh_token_expire_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )