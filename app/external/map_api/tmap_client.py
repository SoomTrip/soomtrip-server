import os
import requests
from dotenv import load_dotenv
from app.external.map_api.naver_client import get_driving_route_info

load_dotenv()

TMAP_APP_KEY = os.getenv("TMAP_APP_KEY")

TMAP_PEDESTRIAN_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"


def get_walking_route_info(route: list[dict]) -> dict:
    """
    티맵 보행자 경로 API로 도보 기준 실제 경로의 거리(km)와 소요시간(분)을 구한다.
    구간별로 순차 호출하며, 각 구간의 정보도 함께 반환한다.
    도보 경로가 없는 구간(NoSegment 등)은 네이버 자동차 경로로 대체 계산한다.
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
                "mobility_used": "walk_transit",
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
            response.raise_for_status()
            data = response.json()
            properties = data["features"][0]["properties"]

            segment_distance = properties.get("totalDistance", 0)
            segment_duration = properties.get("totalTime", 0)

            total_distance_m += segment_distance
            total_duration_s += segment_duration

            segments.append({
                "from": start.get("name", f"지점{i+1}"),
                "to": end.get("name", f"지점{i+2}"),
                "distance_km": round(segment_distance / 1000, 1),
                "duration_minutes": round(segment_duration / 60),
                "mobility_used": "walk_transit",
            })
        except Exception as e:
            print(f"[get_walking_route_info] 티맵 도보 경로 실패 (구간 {i}), 네이버로 대체 시도: {e}")

            # ⭐ 도보 실패 시 네이버(자차)로 대체
            try:
                fallback_result = get_driving_route_info([start, end])
                if fallback_result["distance_km"] is not None:
                    total_distance_m += fallback_result["distance_km"] * 1000
                    total_duration_s += fallback_result["duration_minutes"] * 60
                    segments.append({
                        "from": start.get("name", f"지점{i+1}"),
                        "to": end.get("name", f"지점{i+2}"),
                        "distance_km": fallback_result["distance_km"],
                        "duration_minutes": fallback_result["duration_minutes"],
                        "mobility_used": "car",
                    })
                    continue
            except Exception as fallback_error:
                print(f"[get_walking_route_info] 네이버 대체도 실패: {fallback_error}")

            segments.append({
                "from": start.get("name", f"지점{i+1}"),
                "to": end.get("name", f"지점{i+2}"),
                "distance_km": None,
                "duration_minutes": None,
                "mobility_used": None,
            })

    return {
        "distance_km": round(total_distance_m / 1000, 1),
        "duration_minutes": round(total_duration_s / 60),
        "segments": segments,
    }