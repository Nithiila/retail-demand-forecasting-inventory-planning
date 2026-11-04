
import pandas as pd
import psycopg
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from .database import database_url
from .forecast_persistence import save_forecasts
from .schemas import ForecastBatch

router = APIRouter(prefix="/api/v1")


def pagination(page: int = 1, limit: int = 50) -> tuple[int, int]:
    if page < 1 or limit < 1 or limit > 200:
        raise ValueError("page must be >= 1 and limit must be between 1 and 200")
    return (page - 1) * limit, limit


def _list(table: str, columns: str, where: str = "", params: list = None, page: int = 1, limit: int = 50):
    offset, limit = pagination(page, limit)
    with psycopg.connect(database_url(), row_factory=dict_row) as conn:
        return conn.execute(f"SELECT {columns} FROM {table} {where} ORDER BY 1 LIMIT %s OFFSET %s", (params or []) + [limit, offset]).fetchall()


@router.get("/products")
def products(product_id: str | None = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
    where, params = ("WHERE product_id=%s", [product_id]) if product_id else ("", [])
    try:
        rows = _list("products", "product_id, product_name, category, unit_price", where, params, page, limit)
        if product_id and not rows:
            raise HTTPException(404, "Unknown product ID")
        return {"items": rows, "page": page, "limit": limit}
    except psycopg.Error as exc:
        raise HTTPException(503, "Database unavailable") from exc


@router.get("/stores")
def stores(store_id: str | None = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
    where, params = ("WHERE store_id=%s", [store_id]) if store_id else ("", [])
    try:
        rows = _list("stores", "store_id, store_name, city, region", where, params, page, limit)
        if store_id and not rows:
            raise HTTPException(404, "Unknown store ID")
        return {"items": rows, "page": page, "limit": limit}
    except psycopg.Error as exc:
        raise HTTPException(503, "Database unavailable") from exc


@router.get("/forecasts")
def forecasts(product_id: str | None = None, store_id: str | None = None, date_from: date | None = None, date_to: date | None = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "date_from must be on or before date_to")
    clauses, params = [], []
    if product_id: clauses += ["product_id=%s"]; params += [product_id]
    if store_id: clauses += ["store_id=%s"]; params += [store_id]
    if date_from: clauses += ["target_week >= %s"]; params += [date_from]
    if date_to: clauses += ["target_week <= %s"]; params += [date_to]
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    try:
        with psycopg.connect(database_url(), row_factory=dict_row) as conn:
            for table, column, value, label in (("products", "product_id", product_id, "product"), ("stores", "store_id", store_id, "store")):
                if value and not conn.execute(f"SELECT 1 FROM {table} WHERE {column}=%s", (value,)).fetchone():
                    raise HTTPException(404, f"Unknown {label} ID")
        rows = _list("forecasts", "product_id, store_id, target_week, predicted_demand, model_name, metadata", where, params, page, limit)
        return {"items": rows, "page": page, "limit": limit}
    except psycopg.Error as exc:
        raise HTTPException(503, "Database unavailable") from exc


@router.post("/forecasts", status_code=201)
def persist_forecasts(payload: ForecastBatch) -> dict[str, int]:
    """Validate and persist a forecast batch using the database upsert."""
    try:
        rows = [item.model_dump() for item in payload.forecasts]
        return {"saved": save_forecasts(pd.DataFrame(rows))}
    except (psycopg.Error, OSError) as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
