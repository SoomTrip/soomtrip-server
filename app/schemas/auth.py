from pydantic import BaseModel


# KakaoLoginRequest.kakao_access_token 카카오가 발급한 Access Token
class KakaoLoginRequest(BaseModel):
    kakao_access_token: str

# LoginResponse.access_token 우리 서버가 발급하는 JWT
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"