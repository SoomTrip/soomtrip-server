import httpx
from sqlalchemy.orm import Session

from app.db.models import User

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

