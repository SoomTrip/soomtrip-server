from fastapi import FastAPI
from app.api.health import router as health_router

from app.api.auth import router as auth_router

from app.core.config import settings
from app.api.users import router as users_router
from app.api.saved_regions import router as saved_regions_router
from app.api.friends import router as friends_router
from app.api.recommendations import router as recommendations_router
from app.api.diary_entries import router as diary_entries_router

from app.api.preferences import router as preferences_router
from app.api.uploads import router as uploads_router
from app.api.routes import router as routes_router
from app.api.stamps import router as stamps_router

app = FastAPI()


@app.get("/")
def root():
    return {"message": "SoomTrip Server",
            "environment":settings.app_env}


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(preferences_router)
app.include_router(users_router)
app.include_router(saved_regions_router)
app.include_router(friends_router)
app.include_router(recommendations_router)
app.include_router(diary_entries_router)
app.include_router(uploads_router)
app.include_router(routes_router)
app.include_router(stamps_router)