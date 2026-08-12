from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "SoomTrip Server"}


@app.get("/health")
def health_check():
    return {"status": "ok"}