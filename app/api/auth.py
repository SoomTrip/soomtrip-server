import httpx

from fastapi import APIRouter, Depends,  HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    KakaoLoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.services.auth_service import (
    get_kakao_user,
    get_or_create_user_by_kakao,
    get_valid_refresh_token,
    issue_refresh_token,
    revoke_refresh_token,
)
from app.core.security import create_access_token
from app.api.deps import get_current_user_id

router = APIRouter(
    prefix="/auth", # 이 파일 안의 모든 API 앞에 자동으로 /auth가 붙음
    tags = ["auth"] #Swagger /docs에서 API를 auth 그룹으로 묶어서 보여주기 위한 거
)

@router.post("/kakao", response_model=LoginResponse)
async def kakao_login(
    request: KakaoLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        kakao_user = await get_kakao_user(
            request.kakao_access_token
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 카카오 액세스 토큰입니다.",
        ) from exc

    user = get_or_create_user_by_kakao(
        db=db,
        kakao_user=kakao_user,
    )

    soomtrip_access_token = create_access_token(
        str(user.id)
    )

    soomtrip_refresh_token = issue_refresh_token(
        db=db,
        user_id=user.id,
    )

    return {
        "access_token": soomtrip_access_token,
        "refresh_token": soomtrip_refresh_token,
        "token_type": "bearer",
    }


@router.get("/verify")
def verify_token(
    current_user_id: int = Depends(get_current_user_id),
):
    return {
        "user_id": current_user_id,
    }

@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    db_refresh_token = get_valid_refresh_token(
        db=db,
        refresh_token=request.refresh_token,
    )

    if db_refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 refresh token입니다.",
        )

    access_token = create_access_token(str(db_refresh_token.user_id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
):
    revoke_refresh_token(
        db=db,
        refresh_token=request.refresh_token,
    )

    return {
        "message": "로그아웃되었습니다.",
    }