import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

"""
HTTPBearer는 Authorization: Bearer ... 헤더를 읽어서 HTTPAuthorizationCredentials로 넘겨주는 보안 도구
헤더 없으면 기본적으로 인증 오류 반환
"""
bearer_scheme = HTTPBearer()

def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
        ) -> int:
    
    token = credentials.credentials # 순수 토큰만 가져옴

    try:
        payload = decode_access_token(token)
        """
        {
            "sub": "123456789",
            "exp": ...
        }
        정상 토큰이면 위와 같은 거 반환
        """
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 토큰입니다."
            )

        return int(user_id)

    # exp가 지난 토큰 검증
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료된 인증 토큰입니다."
        ) from exc

    # 토큰 자체가 이상한 거 검증
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다."
        ) from exc

