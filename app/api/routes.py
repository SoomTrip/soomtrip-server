from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user_id
from app.schemas.routes import RouteOptimizeRequest, RouteOptimizeResponse
from app.services.route_service import create_optimized_route


router = APIRouter(
    prefix="/route",
    tags=["route"],
)


@router.post("/optimize", response_model=RouteOptimizeResponse)
def optimize_route_endpoint(
    request: RouteOptimizeRequest,
    current_user_id: int = Depends(get_current_user_id),
):
    if not request.selected_spots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected spots are required.",
        )

    if request.mobility_choice not in ["car", "walk_transit"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mobility_choice must be car or walk_transit.",
        )

    return create_optimized_route(request)