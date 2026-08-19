from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.friends import FriendRequestCreate, FriendResponse
from app.services.friend_service import (
    accept_friend_request,
    create_friend_request,
    delete_friend,
    get_my_friends,
    get_received_friend_requests,
    reject_friend_request,
)

router = APIRouter(
    prefix="/friends",
    tags=["friends"],
)


@router.post("/request", response_model=FriendResponse)
def request_friend(
    request: FriendRequestCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        return create_friend_request(
            db=db,
            requester_id=current_user_id,
            receiver_user_code=request.user_code,
        )
    except ValueError as exc:
        if str(exc) == "USER_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            ) from exc

        if str(exc) == "CANNOT_REQUEST_SELF":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신에게 친구 요청을 보낼 수 없습니다.",
            ) from exc

        if str(exc) == "FRIEND_REQUEST_ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 친구 요청 또는 친구 관계가 존재합니다.",
            ) from exc

        raise


@router.get("", response_model=list[FriendResponse])
def get_friends(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_my_friends(db, current_user_id)


@router.get("/requests", response_model=list[FriendResponse])
def get_friend_requests(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_received_friend_requests(db, current_user_id)


@router.patch("/{friend_id}/accept", response_model=FriendResponse)
def accept_request(
    friend_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    friend = accept_friend_request(db, current_user_id, friend_id)

    if friend is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="수락할 친구 요청을 찾을 수 없습니다.",
        )

    return friend


@router.patch("/{friend_id}/reject", response_model=FriendResponse)
def reject_request(
    friend_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    friend = reject_friend_request(db, current_user_id, friend_id)

    if friend is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="거절할 친구 요청을 찾을 수 없습니다.",
        )

    return friend


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    friend_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deleted = delete_friend(db, current_user_id, friend_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="친구 관계를 찾을 수 없습니다.",
        )