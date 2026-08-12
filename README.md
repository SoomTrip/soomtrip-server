# SoomTrip Server

숨트립(SoomTrip) 서비스의 백엔드 서버입니다.

## 기술 스택

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy

## 개발 환경 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd soomtrip-server
```

### 2. Python 가상환경 생성

Windows PowerShell 기준:

```powershell
python -m venv .venv
```

가상환경 활성화:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 패키지 설치

```powershell
pip install -r requirements.txt
```

### 4. 서버 실행

```powershell
fastapi dev app/main.py
```

정상적으로 실행되면 아래 주소에서 서버를 확인할 수 있습니다.

```text
http://127.0.0.1:8000
```

응답 예시:

```json
{
  "message": "SoomTrip Server"
}
```

### 5. 서버 상태 확인

```text
http://127.0.0.1:8000/health
```

응답:

```json
{
  "status": "ok"
}
```

### 6. API 문서 확인

FastAPI에서 자동 생성되는 Swagger 문서는 아래 주소에서 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

## 환경변수

API Key, DB 비밀번호 등의 민감한 정보는 `.env` 파일에서 관리합니다.

`.env` 파일은 GitHub에 업로드하지 않습니다.

필요한 환경변수는 `.env.example`을 참고합니다.

```env
APP_ENV=development

DATABASE_URL=
JWT_SECRET=

KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=

TOUR_API_KEY=
MAP_API_KEY=
AI_API_KEY=
```

## 프로젝트 구조

```text
soomtrip-server/
├── app/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── schemas/
│   ├── core/
│   ├── db/
│   ├── external/
│   └── recommendation/
│
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 협업 시 주의사항

* `.venv/`는 GitHub에 업로드하지 않습니다.
* `.env`는 GitHub에 업로드하지 않습니다.
* 새로운 패키지를 설치한 경우 `requirements.txt`를 갱신합니다.

```powershell
pip freeze > requirements.txt
```
