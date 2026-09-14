from uuid import uuid4

import httpx
from fastapi import UploadFile

from app.core.config import settings


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

DEFAULT_PROFILE_IMAGE_KEYS = {
    "profile1",
    "profile2",
    "profile3",
    "profile4",
    "profile5",
}


def upload_diary_image_to_supabase(
    file: UploadFile,
    user_id: int,
) -> str:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("INVALID_IMAGE_TYPE")

    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL_NOT_SET")

    if not settings.supabase_service_role_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY_NOT_SET")

    bucket = settings.supabase_storage_bucket
    extension = ALLOWED_IMAGE_TYPES[file.content_type]
    file_path = f"diary/{user_id}/{uuid4()}{extension}"

    upload_url = (
        f"{settings.supabase_url}/storage/v1/object/"
        f"{bucket}/{file_path}"
    )

    file_bytes = file.file.read()

    response = httpx.post(
        upload_url,
        headers={
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
            "Content-Type": file.content_type,
            "x-upsert": "false",
        },
        content=file_bytes,
        timeout=30,
    )

    if response.status_code >= 400:
        raise ValueError("IMAGE_UPLOAD_FAILED")

    return file_path

def upload_profile_image_to_supabase(
    file: UploadFile,
    user_id: int,
) -> str:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("INVALID_IMAGE_TYPE")

    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL_NOT_SET")

    if not settings.supabase_service_role_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY_NOT_SET")

    bucket = settings.supabase_storage_bucket
    extension = ALLOWED_IMAGE_TYPES[file.content_type]
    file_path = f"profile/{user_id}/{uuid4()}{extension}"

    upload_url = (
        f"{settings.supabase_url}/storage/v1/object/"
        f"{bucket}/{file_path}"
    )

    file_bytes = file.file.read()

    response = httpx.post(
        upload_url,
        headers={
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
            "Content-Type": file.content_type,
            "x-upsert": "false",
        },
        content=file_bytes,
        timeout=30,
    )

    if response.status_code >= 400:
        raise ValueError("IMAGE_UPLOAD_FAILED")

    return file_path

def create_profile_image_signed_url(
    image_path: str | None,
    expires_in: int = 3600,
) -> str | None:
    if image_path is None:
        return None

    if image_path in DEFAULT_PROFILE_IMAGE_KEYS:
        return None

    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path

    if not image_path.startswith("profile/"):
        return None

    try:
        return create_diary_image_signed_url(image_path, expires_in)
    except ValueError:
        return None

def is_allowed_profile_image_path(
    image_path: str | None,
    user_id: int,
) -> bool:
    if image_path is None:
        return True

    if image_path in DEFAULT_PROFILE_IMAGE_KEYS:
        return True

    if image_path.startswith(f"profile/{user_id}/"):
        return True

    if image_path.startswith("http://") or image_path.startswith("https://"):
        return True

    return False

def create_diary_image_signed_url(
    image_path: str | None,
    expires_in: int = 3600,
) -> str | None:
    if image_path is None:
        return None

    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path

    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL_NOT_SET")

    if not settings.supabase_service_role_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY_NOT_SET")

    bucket = settings.supabase_storage_bucket

    sign_url = (
        f"{settings.supabase_url}/storage/v1/object/sign/"
        f"{bucket}/{image_path}"
    )

    response = httpx.post(
        sign_url,
        headers={
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
        },
        json={"expiresIn": expires_in},
        timeout=30,
    )

    if response.status_code >= 400:
        raise ValueError("IMAGE_SIGNED_URL_FAILED")

    signed_url = response.json().get("signedURL")

    if signed_url is None:
        raise ValueError("IMAGE_SIGNED_URL_FAILED")

    if signed_url.startswith("http"):
        return signed_url

    return f"{settings.supabase_url}/storage/v1{signed_url}"

def delete_diary_images_from_supabase(
    image_paths: list[str],
) -> None:
    if not image_paths:
        return

    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL_NOT_SET")

    if not settings.supabase_service_role_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY_NOT_SET")

    bucket = settings.supabase_storage_bucket

    delete_url = (
        f"{settings.supabase_url}/storage/v1/object/"
        f"{bucket}"
    )

    response = httpx.request(
        "DELETE",
        delete_url,
        headers={
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
            "Content-Type": "application/json",
        },
        json={
            "prefixes": image_paths,
        },
        timeout=30,
    )

    if response.status_code >= 400:
        raise ValueError("IMAGE_DELETE_FAILED")

def is_uploaded_image_path(
    image_path: str | None,
    prefix: str,
    user_id: int,
) -> bool:
    if image_path is None:
        return True

    return image_path.startswith(f"{prefix}/{user_id}/")