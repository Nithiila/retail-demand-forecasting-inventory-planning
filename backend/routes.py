
import pandas as pd
import psycopg
from fastapi import APIRouter, HTTPException

from .forecast_persistence import save_forecasts
from .schemas import ForecastBatch

router = APIRouter(prefix="/api/v1")


@router.post("/forecasts", status_code=201)
def persist_forecasts(payload: ForecastBatch) -> dict[str, int]:
    """Validate and persist a forecast batch using the database upsert."""
    try:
        rows = [item.model_dump() for item in payload.forecasts]
        return {"saved": save_forecasts(pd.DataFrame(rows))}
    except (psycopg.Error, OSError) as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
