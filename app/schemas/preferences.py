from pydantic import BaseModel

class PreferenceScore(BaseModel):
    tag: str
    score: float

class PreferenceSaveRequest(BaseModel):
    scores: list[PreferenceScore]