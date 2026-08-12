from fastapi import FastAPI
from app.api.health import router as health_router

app = FastAPI()


@app.get("/")
def root():
    return {"message": "SoomTrip Server"}


app.include_router(health_router)