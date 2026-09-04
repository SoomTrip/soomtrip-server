# SoomTrip Server

SoomTrip 백엔드 서버입니다.

SoomTrip은 사용자의 취향 월드컵 결과를 기반으로 국내 여행지를 추천하고, 사용자가 마음에 드는 추천 결과를 저장할 수 있는 서비스입니다.

이 서버는 인증, 사용자 정보, 취향 결과 저장, 추천 생성, 저장 여행지, 친구 기능을 담당합니다.

## 기술 스택

- Python
- FastAPI
- PostgreSQL / Supabase
- SQLAlchemy
- Pydantic
- pydantic-settings
- PyJWT
- httpx

## 프로젝트 구조

```text
soomtrip-server/
  app/
    api/              # FastAPI 라우터
    core/             # 설정, 보안, 공통 인프라
    db/               # DB 세션 및 SQLAlchemy 모델
    external/         # 외부 API 클라이언트
    recommendation/   # 추천 엔진 및 추천 관련 로직
    schemas/          # Pydantic 요청/응답 스키마
    services/         # 비즈니스 로직
    main.py           # FastAPI 앱 진입점
  requirements.txt
  README.md
  AGENTS.md
```

## 개발 환경 설정

가상환경 생성:

```powershell
python -m venv .venv
```

가상환경 실행:

```powershell
.\.venv\Scripts\Activate.ps1
```

패키지 설치:

```powershell
pip install -r requirements.txt
```

## 환경 변수

프로젝트 루트에 `.env` 파일을 생성합니다.

실제 비밀값이 들어간 `.env` 파일은 절대 Git에 올리지 않습니다.

```env
APP_ENV=development

DATABASE_URL=

JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=

TOUR_API_KEY=
MAP_API_KEY=
AI_API_KEY=

NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

TMAP_APP_KEY=
```

## 서버 실행

```powershell
fastapi dev app/main.py
```

또는:

```powershell
uvicorn app.main:app --reload
```

서버 주소:

```text
http://127.0.0.1:8000
```

Swagger 문서:

```text
http://127.0.0.1:8000/docs
```

## 기본 확인

루트 확인:

```text
GET /
```

헬스 체크:

```text
GET /health
```

문법 검사:

```powershell
python -m compileall app
```

## 인증 흐름

Flutter 앱에서 카카오 로그인을 수행한 뒤, 카카오 access token을 백엔드로 전달합니다.

```text
POST /auth/kakao
```

백엔드 처리 흐름:

1. 카카오 access token을 검증합니다.
2. 카카오 사용자 id를 기준으로 `users` 테이블에서 사용자를 조회합니다.
3. 사용자가 없으면 새로 생성합니다.
4. SoomTrip JWT를 발급합니다.
5. JWT의 `sub`에는 카카오 id가 아니라 DB의 `users.id`를 넣습니다.

중요:

```text
JWT sub = users.id
JWT sub != Kakao user id
```

인증이 필요한 API는 아래 헤더를 사용합니다.

```text
Authorization: Bearer <SOOMTRIP_JWT>
```

## 주요 프론트 호출 흐름

```text
1. POST /auth/kakao
2. POST /preferences
3. POST /recommendations
4. 추천 결과와 주변 관광지를 화면에 표시
5. 사용자가 저장 버튼을 누르면 POST /saved-regions
6. 저장 목록 화면에서는 GET /saved-regions 사용
```

## 주요 API

### 인증

```text
POST /auth/kakao
GET /auth/verify
```

`POST /auth/kakao`는 카카오 access token을 검증하고 SoomTrip JWT를 발급합니다.

`GET /auth/verify`는 현재 JWT가 유효한지 확인하고 현재 사용자 id를 반환합니다.

### 취향

```text
POST /preferences
GET /preferences/me
DELETE /preferences/{preference_id}
```

`POST /preferences`는 취향 월드컵 결과 하나를 저장합니다.

요청 예시:

```json
{
  "ocean_score": 42,
  "nature_score": 0,
  "theme_choice": "ocean",
  "walk_transit_score": 0,
  "car_score": 35,
  "mobility_choice": "car",
  "solo_score": 50,
  "group_score": 0,
  "companion_choice": "solo",
  "rest_score": 27,
  "dynamic_score": 0,
  "activity_choice": "rest",
  "outdoor_score": 40,
  "indoor_score": 0,
  "indoor_choice": false
}
```

응답에는 저장된 취향 결과의 `id`가 포함됩니다.

이 `id`는 추천 요청 시 `preference_id`로 사용합니다.

### 추천

```text
POST /recommendations
```

추천 결과는 자동으로 DB에 저장하지 않습니다.

선택한 취향 결과를 기반으로 추천 엔진을 실행하고, 추천 여행지와 주변 관광지를 바로 반환합니다.

요청 예시:

```json
{
  "preference_id": 12
}
```

응답 형태 예시:

```json
{
  "candidates": [
    {
      "content_id": "12345",
      "name": "경포해변",
      "address": "강원 강릉시 ...",
      "latitude": 37.1,
      "longitude": 127.1,
      "image_url": "https://...",
      "cat1": "A01",
      "score": 46.12,
      "nearby_count": 34,
      "nearby_spots": [
        {
          "content_id": "67890",
          "name": "오죽헌",
          "address": "강원 강릉시 ...",
          "latitude": 37.2,
          "longitude": 127.2,
          "image_url": "https://...",
          "cat1": "A02"
        }
      ]
    }
  ]
}
```

### 저장 여행지

```text
POST /saved-regions
GET /saved-regions
GET /saved-regions/{saved_region_id}
DELETE /saved-regions/{saved_region_id}
```

추천 결과는 사용자가 직접 저장 버튼을 눌렀을 때만 저장됩니다.

요청 예시:

```json
{
  "region_name": "경포해변",
  "score": 46,
  "spots": [
    {
      "content_id": "12345",
      "name": "경포해변",
      "is_anchor": true
    },
    {
      "content_id": "67890",
      "name": "오죽헌",
      "is_anchor": false
    }
  ]
}
```

`is_anchor = true`는 추천의 중심 여행지를 의미합니다.

`is_anchor = false`는 함께 보여줄 주변 관광지를 의미합니다.

### 사용자

```text
GET /users/me
PATCH /users/me
```

`GET /users/me`는 현재 로그인한 사용자의 프로필과 `user_code`를 반환합니다.

`user_code`는 친구 요청에 사용됩니다.

### 친구

```text
POST /friends/request
GET /friends
GET /friends/requests
PATCH /friends/{friend_id}/accept
PATCH /friends/{friend_id}/reject
DELETE /friends/{friend_id}
```

친구 정책:

- `PENDING`: 이미 대기 중인 요청이 있으면 중복 요청을 막습니다.
- `ACCEPTED`: 이미 친구이면 중복 요청을 막습니다.
- `REJECTED`: 거절된 요청은 나중에 다시 요청할 수 있도록 처리할 수 있습니다.
- `DELETE /friends/{friend_id}`는 친구 삭제 또는 요청 취소에 사용할 수 있습니다.

## 개발 규칙

- API 라우터는 얇게 유지합니다.
- 비즈니스 로직은 `app/services/`에 둡니다.
- 요청/응답 형식은 `app/schemas/`에 둡니다.
- DB 연결 구조나 모델 구조를 중복으로 만들지 않습니다.
- 팀원이 담당하는 DB 모델은 협의 없이 변경하지 않습니다.
- 추천 알고리즘을 API 코드 안에 중복 구현하지 않습니다.
- 추천 생성은 `app.recommendation.engine.get_recommendations()`를 진입점으로 사용합니다.

## 보안 주의사항

아래 값은 절대 커밋하지 않습니다.

- `.env`
- DB 비밀번호
- JWT secret
- Kakao secret
- Tour API key
- Map API key
- AI API key
- Supabase service role key
