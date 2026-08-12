from fastapi import FastAPI
from app.api.health import router as health_router

from app.api.auth import router as auth_router

from app.core.config import settings


app = FastAPI()


@app.get("/")
def root():
    return {"message": "SoomTrip Server",
            "environment":settings.app_env}


app.include_router(health_router)
app.include_router(auth_router)