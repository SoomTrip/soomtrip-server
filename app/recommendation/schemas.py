from pydantic import BaseModel
from typing import Optional


class PreferenceInput(BaseModel):
    theme_weights: dict[str, float]
    budget_level: int = 2
    transport: Optional[str] = None
    activity_intensity: int = 3
    pet_friendly: bool = False
    travel_companion: Optional[str] = None
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


class RecommendationResult(BaseModel):
    """엔진이 반환하는 최종 결과"""
    candidates: list[AnchorSpotCandidate]