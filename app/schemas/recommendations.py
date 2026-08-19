from pydantic import BaseModel


class RecommendationCreateRequest(BaseModel):
    preference_id: int