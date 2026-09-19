import os
import random
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOUR_API_KEY = os.getenv("TOUR_API_KEY")
BASE_URL = "https://apis.data.go.kr/B551011/KorService2"

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SEC = 0.5
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class TourApiError(Exception):
    """TourAPI 호출 중 발생한 에러"""
    pass


def _request(endpoint: str, params: dict) -> dict:
    default_params = {
        "serviceKey": TOUR_API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "SoomTrip",
        "_type": "json",
    }
    full_params = {**default_params, **params}

    response = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                f"{BASE_URL}/{endpoint}",
                params=full_params,
                timeout=5,
            )
            response.raise_for_status()
            break

        except requests.exceptions.RequestException as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else None
            )
            response_body = (
                exc.response.text[:500]
                if exc.response is not None
                else None
            )

            # 응답 자체가 없는 경우(타임아웃/연결 오류)와 429·5xx만 재시도한다.
            # 일일 한도를 다 쓴 경우(Remaining=0)는 재시도해도 소용없으므로 제외한다.
            quota_exhausted = (
                exc.response is not None
                and exc.response.headers.get("X-RateLimit-Remaining") == "0"
            )
            retryable = (
                status_code is None or status_code in RETRYABLE_STATUS_CODES
            ) and not quota_exhausted
            if retryable and attempt < MAX_ATTEMPTS:
                delay = RETRY_BACKOFF_SEC * (2 ** (attempt - 1)) + random.uniform(0, 0.3)
                print(
                    "[TourAPI retry] "
                    f"endpoint={endpoint} "
                    f"attempt={attempt}/{MAX_ATTEMPTS} "
                    f"status={status_code} "
                    f"error_type={type(exc).__name__} "
                    f"wait={delay:.2f}s",
                    flush=True,
                )
                time.sleep(delay)
                continue

            print(
                "[TourAPI HTTP error] "
                f"endpoint={endpoint} "
                f"status={status_code} "
                f"error_type={type(exc).__name__} "
                f"attempts={attempt} "
                f"body={response_body}",
                flush=True,
            )

            raise TourApiError("TourAPI 요청 실패") from exc

    data = response.json()

    header = data.get("response", {}).get("header", {})
    result_code = header.get("resultCode")

    if result_code != "0000":
        print(
            "[TourAPI response error] "
            f"endpoint={endpoint} "
            f"result_code={result_code} "
            f"result_message={header.get('resultMsg')}",
            flush=True,
        )

        raise TourApiError(
            f"TourAPI 에러 [{result_code}]: {header.get('resultMsg')}"
        )

    return data["response"]["body"]


def get_area_based_list(
    area_code: str = None,
    sigungu_code: str = None,
    content_type_id: str = None,
    cat1: str = None,
    cat2: str = None,
    cat3: str = None,
    page_no: int = 1,
    num_of_rows: int = 20,
) -> list[dict]:
    params = {
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "arrange": "O",
    }
    if area_code:
        params["areaCode"] = area_code
    if sigungu_code:
        params["sigunguCode"] = sigungu_code
    if content_type_id:
        params["contentTypeId"] = content_type_id
    if cat1:
        params["cat1"] = cat1
    if cat2:
        params["cat2"] = cat2
    if cat3:
        params["cat3"] = cat3

    body = _request("areaBasedList2", params)
    items_container = body.get("items", {})

    # 결과가 없을 때 빈 문자열("")이나 None으로 오는 경우 방어
    if not isinstance(items_container, dict):
        return []

    items = items_container.get("item", [])

    if isinstance(items, dict):
        items = [items]

    return items


def get_location_based_list(
    map_x: float,
    map_y: float,
    radius: int = 3000,
    content_type_id: str = None,
    page_no: int = 1,
    num_of_rows: int = 20,
) -> list[dict]:
    params = {
        "mapX": map_x,
        "mapY": map_y,
        "radius": radius,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "arrange": "E",
    }
    if content_type_id:
        params["contentTypeId"] = content_type_id

    body = _request("locationBasedList2", params)
    items_container = body.get("items", {})

    if not isinstance(items_container, dict):
        return []

    items = items_container.get("item", [])

    if isinstance(items, dict):
        items = [items]

    return items


def get_detail_common(content_id: str) -> dict:
    params = {
        "contentId": content_id,
        "defaultYN": "Y",
        "firstImageYN": "Y",
        "areacodeYN": "Y",
        "catcodeYN": "Y",
        "addrinfoYN": "Y",
        "mapinfoYN": "Y",
        "overviewYN": "Y",
    }
    body = _request("detailCommon2", params)
    items = body.get("items", {}).get("item", [])

    if isinstance(items, list):
        return items[0] if items else {}
    return items