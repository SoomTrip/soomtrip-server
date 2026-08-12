import httpx

from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import KakaoLoginRequest, LoginResponse
from app.services.auth_service import get_kakao_user
from app.core.security import create_access_token

router = APIRouter(
    prefix="/auth", # 이 파일 안의 모든 API 앞에 자동으로 /auth가 붙음
    tags = ["auth"] #Swagger /docs에서 API를 auth 그룹으로 묶어서 보여주기 위한 거
)

@router.post("/kakao", response_model=LoginResponse) # 실제 주소는 POST /auth/kakao가 됨
async def kakao_login(request: KakaoLoginRequest): #request: KakaoLoginRequest로 요청 데이터 형식 검사
    try:
        # 실제 카카오 통신은 services/auth_service.py에서 카카오에 토큰 확인
        kakao_user = await get_kakao_user(
            request.kakao_access_token
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "유효하지 않은 카카오 엑세스 토큰입니다."
        )from exc

    soomtrip_access_token = create_access_token(
        str(kakao_user["id"])
    )
    return {
        "access_token": soomtrip_access_token,
        "token_type": "bearer"
    }