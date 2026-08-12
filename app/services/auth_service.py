import httpx

# 사용자 정보 조회를 위한 카카오 API url
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

'''
코드가 하는 일
프론트가 보내준 카카오 토큰이
abc123...이면 
headers = {
    "Authorization": "Bearer abc123..."
} 를 만들어서 카카오에 요청한다
카카오가 토큰을 정상적으로 인정하면 사용자 데이터 반환
{
  "id": 123456789, <- 이건 카카오 서비스 사용자 ID
  "connected_at": "...",
  "properties": {},
  "kakao_account": {}
}
카카오 서비스 사용자 id를 이용하여 DB 조회를 하여 기존회원인지 아닌지 판단
'''