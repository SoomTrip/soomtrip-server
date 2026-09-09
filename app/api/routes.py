from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from app.api.deps import get_current_user_id

from app.db.session import get_db
from app.schemas.routes import (
    RouteOptimizeRequest,
    RouteOptimizeResponse,
    RouteSaveRequest,
    RouteSaveResponse,
    SavedRouteResponse,
)
from app.services.route_service import (
    create_optimized_route,
    get_saved_route_by_region,
    save_route_entries,
)

router = APIRouter(
    prefix="/route",
    tags=["route"],
)


@router.post("/optimize", response_model=RouteOptimizeResponse)
def optimize_route_endpoint(
    request: RouteOptimizeRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not request.selected_spots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected spots are required.",
        )

    route = create_optimized_route(
        db=db,
        user_id=current_user_id,
        request=request,
    )

    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved region not found.",
        )

    return route

@router.post("/save", response_model=RouteSaveResponse)
def save_route(
    request: RouteSaveRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):

    try:
        entries = save_route_entries(
            db=db,
            user_id=current_user_id,
            request=request,
        )
    except ValueError as exc:
        if str(exc) == "INVALID_SAVED_REGION_SPOT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="저장된 여행지에 포함되지 않은 관광지가 있습니다.",
            ) from exc

        raise

    if entries is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 여행지를 찾을 수 없습니다.",
        )

    return {
        "saved_region_id": request.saved_region_id,
        "entries": entries,
    }

@router.get("/saved-region/{saved_region_id}", response_model=SavedRouteResponse)
def get_saved_route(
    saved_region_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    saved_route = get_saved_route_by_region(
        db=db,
        user_id=current_user_id,
        saved_region_id=saved_region_id,
    )

    if saved_route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 여행지를 찾을 수 없습니다.",
        )

    return saved_route