import os
import requests
from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

NAVER_DIRECTIONS_URL = "https://maps.apigw.ntruss.com/map-direction/v1/driving"

def _coord_key(spot: dict) -> tuple:
    return (round(spot["longitude"], 5), round(spot["latitude"], 5))


def get_driving_route_info(route: list[dict]) -> dict:
    """
    네이버 Directions API로 자동차 기준 실제 도로 경로의
    전체 거리/시간과, 구간별(스팟 간) 거리/시간을 함께 구한다.
    """
    if len(route) < 2:
        return {"distance_km": 0, "duration_minutes": 0, "segments": []}

    # 좌표가 인접해서 겹치는 지점(같은 건물의 다른 스팟, 중복 선택 등)이 있으면
    # 네이버 API가 요청 자체를 오류로 거부하므로, 요청 전에 하나로 합친다.
    unique_indices = [0]
    for i in range(1, len(route)):
        if _coord_key(route[i]) != _coord_key(route[unique_indices[-1]]):
            unique_indices.append(i)
    unique_route = [route[i] for i in unique_indices]

    if len(unique_route) < 2:
        # 선택된 모든 스팟이 같은 좌표인 극단적인 경우
        zero_segments = [
            {
                "from": route[i].get("name", f"지점{i+1}"),
                "to": route[i + 1].get("name", f"지점{i+2}"),
                "distance_km": 0,
                "duration_minutes": 0,
            }
            for i in range(len(route) - 1)
        ]
        return {"distance_km": 0, "duration_minutes": 0, "segments": zero_segments}

    start = f"{unique_route[0]['longitude']},{unique_route[0]['latitude']}"
    goal = f"{unique_route[-1]['longitude']},{unique_route[-1]['latitude']}"
    waypoints_list = unique_route[1:-1]

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
        print("[Naver request params]", params)
        print("[Naver status]", response.status_code)
        print("[Naver body]", response.text[:1000])
        response.raise_for_status()
        
        data = response.json()
        summary = data["route"]["trafast"][0]["summary"]

        unique_segments = []

        if waypoints_list:
            # 경유지가 있는 경우: waypoints 각 항목 + goal이 구간별 정보를 담고 있음
            segment_points = summary.get("waypoints", []) + [summary["goal"]]
            for i, point in enumerate(segment_points):
                if "distance" not in point or "duration" not in point:
                    continue
                unique_segments.append({
                    "distance_km": round(point["distance"] / 1000, 1),
                    "duration_minutes": round(point["duration"] / 1000 / 60),
                })
        else:
            # 경유지가 없는 경우(출발-도착 2개뿐): summary 최상위 값이 곧 유일한 구간
            unique_segments.append({
                "distance_km": round(summary["distance"] / 1000, 1),
                "duration_minutes": round(summary["duration"] / 1000 / 60),
            })

        # 합쳤던 중복 좌표 구간을 복원해 원래 스팟 개수(len(route)-1)에 맞는
        # 세그먼트 목록을 만든다. 중복 구간은 거리/시간이 0.
        segments = []
        seg_ptr = 0
        for i in range(len(route) - 1):
            from_name = route[i].get("name", f"지점{i+1}")
            to_name = route[i + 1].get("name", f"지점{i+2}")
            if _coord_key(route[i]) == _coord_key(route[i + 1]):
                segments.append({
                    "from": from_name,
                    "to": to_name,
                    "distance_km": 0,
                    "duration_minutes": 0,
                })
            else:
                useg = unique_segments[seg_ptr] if seg_ptr < len(unique_segments) else {"distance_km": None, "duration_minutes": None}
                seg_ptr += 1
                segments.append({
                    "from": from_name,
                    "to": to_name,
                    "distance_km": useg["distance_km"],
                    "duration_minutes": useg["duration_minutes"],
                })

        return {
            "distance_km": round(summary["distance"] / 1000, 1),
            "duration_minutes": round(summary["duration"] / 1000 / 60),
            "segments": segments,
        }
    except Exception as e:
        print(f"[get_driving_route_info] 네이버 경로 API 호출 실패: {e}")
        return {"distance_km": None, "duration_minutes": None, "segments": []}