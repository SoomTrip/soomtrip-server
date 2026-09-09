import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMAP_APP_KEY = os.getenv("TMAP_APP_KEY")

TMAP_PEDESTRIAN_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"


def get_walking_route_info(route: list[dict]) -> dict:
    """
    티맵 보행자 경로 API로 도보 기준 실제 경로의 거리(km)와 소요시간(분)을 구한다.
    구간별로 순차 호출하며, 각 구간의 정보도 함께 반환한다.
    """
    if len(route) < 2:
        return {"distance_km": 0, "duration_minutes": 0, "segments": []}

    total_distance_m = 0
    total_duration_s = 0
    segments = []

    headers = {
        "accept": "application/json",
        "appKey": TMAP_APP_KEY,
        "content-type": "application/json",
    }

    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]

        if (round(start["longitude"], 5), round(start["latitude"], 5)) == (
            round(end["longitude"], 5), round(end["latitude"], 5)
        ):
            # 좌표가 겹치는 구간(같은 건물의 다른 스팟 등)은 API 호출 없이 0으로 처리
            segments.append({
                "from": start.get("name", f"지점{i+1}"),
                "to": end.get("name", f"지점{i+2}"),
                "distance_km": 0,
                "duration_minutes": 0,
            })
            continue

        payload = {
            "startX": str(start["longitude"]),
            "startY": str(start["latitude"]),
            "endX": str(end["longitude"]),
            "endY": str(end["latitude"]),
            "reqCoordType": "WGS84GEO",
            "resCoordType": "WGS84GEO",
            "startName": "출발",
            "endName": "도착",
        }

        try:
            response = requests.post(TMAP_PEDESTRIAN_URL, json=payload, headers=headers, timeout=10)
            print("[Tmap payload]", payload)
            print("[Tmap status]", response.status_code)
            print("[Tmap body]", response.text[:1000])
            response.raise_for_status()
            data = response.json()
            properties = data["features"][0]["properties"]

            segment_distance = properties.get("totalDistance", 0)
            segment_duration = properties.get("totalTime", 0)

            total_distance_m += segment_distance
            total_duration_s += segment_duration

            # ⭐ 구간별 정보 저장
            segments.append({
                "from": start.get("name", f"지점{i+1}"),
                "to": end.get("name", f"지점{i+2}"),
                "distance_km": round(segment_distance / 1000, 1),
                "duration_minutes": round(segment_duration / 60),
            })
        except Exception as e:
            print(f"[get_walking_route_info] 티맵 도보 경로 API 호출 실패 (구간 {i}): {e}")
            segments.append({
                "from": start.get("name", f"지점{i+1}"),
                "to": end.get("name", f"지점{i+2}"),
                "distance_km": None,
                "duration_minutes": None,
            })
            continue

    return {
        "distance_km": round(total_distance_m / 1000, 1),
        "duration_minutes": round(total_duration_s / 60),
        "segments": segments,
    }