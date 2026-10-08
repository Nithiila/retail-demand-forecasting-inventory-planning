from fastapi import FastAPI

from .database import settings

app = FastAPI(title="Retail Demand Forecasting API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
