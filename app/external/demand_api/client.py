import os
import random
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SEC = 0.5
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

DEMAND_API_KEY = os.getenv("TOUR_API_KEY")  # 관광공사 API는 보통 같은 인증키 공용
DEMAND_BASE_URL = "https://apis.data.go.kr/B551011/AreaTarDemDsService"

# "타권역 방문자 비중" 지표 코드 (Swagger에서 확인한 값)
TAR_SJRN_DS_IX_CD = "2101"


def get_recent_base_ym() -> str:
    """
    가장 최근 확정 통계월(YYYYMM)을 계산.
    보통 통계는 1~2개월 지연되어 제공되므로, 안전하게 2개월 전으로 설정.
    """
    target = datetime.now() - timedelta(days=60)
    return target.strftime("%Y%m")


def get_stay_intensity(area_cd: str, signgu_cd: str, base_ym: str = None) -> float | None:
    """
    지역별 관광 체류 강도(1박 방문자수 관련 지표) 조회.
    area_cd: 통계청 광역코드 (예: "11")
    signgu_cd: 통계청 시군구코드 (예: "11500")
    반환값: 조회 실패 시 None, 성공 시 float 값
    """
    if not area_cd or not signgu_cd:
        return None

    params = {
        "serviceKey": DEMAND_API_KEY,
        "numOfRows": 1,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "SoomTrip",
        "baseYm": base_ym or get_recent_base_ym(),
        "areaCd": area_cd,
        "signguCd": signgu_cd,
        "tarSjrnDsIxCd": TAR_SJRN_DS_IX_CD,
        "_type": "json",
    }

    response = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(f"{DEMAND_BASE_URL}/areaTarSjrnDsList", params=params, timeout=5)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            # 일일 한도를 다 쓴 경우(Remaining=0)는 재시도해도 소용없으므로 바로 포기한다.
            quota_exhausted = (
                exc.response is not None
                and exc.response.headers.get("X-RateLimit-Remaining") == "0"
            )
            retryable = (
                status_code is None or status_code in RETRYABLE_STATUS_CODES
            ) and not quota_exhausted
            if retryable and attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SEC * (2 ** (attempt - 1)) + random.uniform(0, 0.3))
                continue
            print(
                "[DemandAPI HTTP error] "
                f"area_cd={area_cd} signgu_cd={signgu_cd} "
                f"status={status_code} error_type={type(exc).__name__} attempts={attempt}",
                flush=True,
            )
            return None  # 실패 시 조용히 None 반환 (전체 추천 흐름을 막지 않기 위함)

    try:
        data = response.json()
        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "0000":
            return None

        items = data["response"]["body"].get("items", {})
        if not isinstance(items, dict):
            return None

        item = items.get("item", [])
        if isinstance(item, list):
            item = item[0] if item else None
        if not item:
            return None

        return float(item.get("tarSjrnDsIxVal", 0))
    except (KeyError, ValueError, TypeError):
        return None