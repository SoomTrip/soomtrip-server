from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_current_user_id
from app.schemas.uploads import ImageUploadResponse
from app.services.upload_service import upload_diary_image_to_supabase


router = APIRouter(
    prefix="/uploads",
    tags=["uploads"],
)


@router.post("/diary-image", response_model=ImageUploadResponse)
def upload_diary_image(
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        image_path = upload_diary_image_to_supabase(
            file=file,
            user_id=current_user_id,
        )
    except ValueError as e:
        if str(e) == "INVALID_IMAGE_TYPE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only jpeg, png, webp images are allowed.",
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed.",
        )

    return ImageUploadResponse(image_url=image_path)