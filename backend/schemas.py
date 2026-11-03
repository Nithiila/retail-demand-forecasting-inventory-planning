from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ForecastInput(BaseModel):
    forecast_date: date
    store_id: str = Field(min_length=1, max_length=32)
    product_id: str = Field(min_length=1, max_length=32)
    prediction: float = Field(ge=0)
    model: str = Field(min_length=1, max_length=100)


class ForecastBatch(BaseModel):
    forecasts: list[ForecastInput] = Field(min_length=1)


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ErrorResponse(BaseModel):
    detail: str
