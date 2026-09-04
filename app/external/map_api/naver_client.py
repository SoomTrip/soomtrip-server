import os
import requests
from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

NAVER_DIRECTIONS_URL = "https://maps.apigw.ntruss.com/map-direction/v1/driving"

def get_driving_route_info(route: list[dict]) -> dict:
    """
    네이버 Directions API로 자동차 기준 실제 도로 경로의
    전체 거리/시간과, 구간별(스팟 간) 거리/시간을 함께 구한다.
    """
    if len(route) < 2:
        return {"distance_km": 0, "duration_minutes": 0, "segments": []}

    start = f"{route[0]['longitude']},{route[0]['latitude']}"
    goal = f"{route[-1]['longitude']},{route[-1]['latitude']}"
    waypoints_list = route[1:-1]

    waypoints = "|".join(
        f"{w['longitude']},{w['latitude']}" for w in waypoints_list
    )

    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET,
    }

    params = {
        "start": start,
        "goal": goal,
        "option": "trafast",
    }
    if waypoints:
        params["waypoints"] = waypoints

    try:
        response = requests.get(NAVER_DIRECTIONS_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        summary = data["route"]["trafast"][0]["summary"]

        segments = []

        if waypoints_list:
            # 경유지가 있는 경우: waypoints 각 항목 + goal이 구간별 정보를 담고 있음
            segment_points = summary.get("waypoints", []) + [summary["goal"]]
            for i, point in enumerate(segment_points):
                if "distance" not in point or "duration" not in point:
                    continue
                segments.append({
                    "from": route[i].get("name", f"지점{i+1}"),
                    "to": route[i + 1].get("name", f"지점{i+2}"),
                    "distance_km": round(point["distance"] / 1000, 1),
                    "duration_minutes": round(point["duration"] / 1000 / 60),
                })
        else:
            # 경유지가 없는 경우(출발-도착 2개뿐): summary 최상위 값이 곧 유일한 구간
            segments.append({
                "from": route[0].get("name", "지점1"),
                "to": route[1].get("name", "지점2"),
                "distance_km": round(summary["distance"] / 1000, 1),
                "duration_minutes": round(summary["duration"] / 1000 / 60),
            })

        return {
            "distance_km": round(summary["distance"] / 1000, 1),
            "duration_minutes": round(summary["duration"] / 1000 / 60),
            "segments": segments,
        }
    except Exception as e:
        print(f"[get_driving_route_info] 네이버 경로 API 호출 실패: {e}")
        return {"distance_km": None, "duration_minutes": None, "segments": []}