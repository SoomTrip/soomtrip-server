from fastapi import FastAPI
from app.api.health import router as health_router

from app.api.auth import router as auth_router

from app.core.config import settings
from app.api.users import router as users_router
from app.api.saved_regions import router as saved_regions_router
from app.api.friends import router as friends_router



from app.api.preferences import router as preferences_router
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