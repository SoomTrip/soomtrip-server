from pydantic import BaseModel
from typing import Optional


class PreferenceInput(BaseModel):
    theme_weights: dict[str, float]     # 엔진 계산용 (아래에서 15개 필드로부터 조립)
    mobility_choice: Optional[str] = None    # "walk_transit" 또는 "car"
    companion_choice: Optional[str] = None   # "solo" 또는 "group"
    activity_intensity: int = 3               # rest/dynamic 점수로부터 환산
    indoor_choice: Optional[bool] = None      # 실내(true)/야외(false)
    budget_level: int = 2
    area_code: str


class NearbySpot(BaseModel):
    """앵커스팟 주변의 추천 관광지 1개"""
    content_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    cat1: Optional[str] = None
    category_label: Optional[str] = None


class AnchorSpotCandidate(BaseModel):
    """여행지(앵커스팟) 후보 1개 + 그 주변 관광지 리스트"""
    content_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    cat1: Optional[str] = None
    score: float
    nearby_count: int
    nearby_spots: list[NearbySpot] = []
    one_line_review: Optional[str] = None


class RecommendationResult(BaseModel):
    """엔진이 반환하는 최종 결과"""
    candidates: list[AnchorSpotCandidate]


class RouteRequest(BaseModel):
    """동선 최적화 요청 - 프론트에서 선택한 관광지 리스트 + 여행 일수"""
    selected_spots: list[NearbySpot]
    num_days: int = 1   # 기본값 1(당일치기)


class RouteResponse(BaseModel):
    """동선 최적화 결과 - 날짜별로 정렬된 방문 순서"""
    route_by_day: dict[str, list[NearbySpot]]