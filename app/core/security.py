from datetime import datetime, timedelta, timezone
import jwt
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