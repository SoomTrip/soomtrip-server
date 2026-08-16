from math import radians, sin, cos, sqrt, atan2


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표 간 거리를 km 단위로 계산 (하버사인 공식)"""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c