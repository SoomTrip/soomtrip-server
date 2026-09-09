import httpx
from sqlalchemy.orm import Session

from datetime import datetime, timezone

from app.core.security import (
    create_refresh_token,
    get_refresh_token_expire_at,
    hash_refresh_token,
)
from app.db.models import RefreshToken, User

KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"


async def get_kakao_user(kakao_access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {kakao_access_token}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            KAKAO_USER_INFO_URL,
            headers=headers
        )

    response.raise_for_status()

    return response.json()


def get_or_create_user_by_kakao(
    db: Session,
    kakao_user: dict,
) -> User:
    kakao_id = str(kakao_user["id"])

    user = (
        db.query(User)
        .filter(User.kakao_id == kakao_id)
        .first()
    )

    if user is not None:
        return user

    properties = kakao_user.get("properties") or {}
    kakao_account = kakao_user.get("kakao_account") or {}
    profile = kakao_account.get("profile") or {}

    nickname = (
        properties.get("nickname")
        or profile.get("nickname")
        or f"user_{kakao_id}"
    )

    profile_image = (
        properties.get("profile_image")
        or profile.get("profile_image_url")
    )

    user = User(
        kakao_id=kakao_id,
        nickname=nickname,
        profile_image=profile_image,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def issue_refresh_token(
    db: Session,
    user_id: int,
) -> str:
    refresh_token = create_refresh_token()

    db_refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=get_refresh_token_expire_at(),
    )

    db.add(db_refresh_token)
    db.commit()

    return refresh_token


def get_valid_refresh_token(
    db: Session,
    refresh_token: str,
) -> RefreshToken | None:
    token_hash = hash_refresh_token(refresh_token)

    db_refresh_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if db_refresh_token is None:
        return None

    if db_refresh_token.revoked_at is not None:
        return None

    expires_at = db_refresh_token.expires_at
    now = datetime.now(timezone.utc)

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        return None

    return db_refresh_token


def revoke_refresh_token(
    db: Session,
    refresh_token: str,
) -> bool:
    db_refresh_token = get_valid_refresh_token(
        db=db,
        refresh_token=refresh_token,
    )

    if db_refresh_token is None:
        return False

    db_refresh_token.revoked_at = datetime.now(timezone.utc)
    db.commit()

    return True

