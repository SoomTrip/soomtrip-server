from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.schemas.preferences import PreferenceSaveRequest

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"]
)

@router.post("")
def save_preferences(
    request: PreferenceSaveRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    return {
        "user_id": current_user_id,
        "scores": request.scores
    }