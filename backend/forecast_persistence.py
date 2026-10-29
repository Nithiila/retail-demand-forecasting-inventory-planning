"""PostgreSQL persistence for generated weekly forecasts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import psycopg

from .database import database_url


def save_forecasts(forecasts: pd.DataFrame, dsn: str | None = None, schema_path: str | Path = "sql/schema.sql") -> int:
    required = {"forecast_date", "store_id", "product_id", "prediction", "model"}
    missing = required - set(forecasts.columns)
    if missing:
        raise ValueError(f"Missing forecast columns: {sorted(missing)}")
    rows = [(row.forecast_date, row.store_id, row.product_id, float(row.prediction), row.model, json.dumps({"source": "forecast_pipeline"})) for row in forecasts.itertuples()]
    sql = """INSERT INTO forecasts (target_week, store_id, product_id, predicted_demand, model_name, metadata)
             VALUES (%s, %s, %s, %s, %s, %s::jsonb)
             ON CONFLICT (product_id, store_id, target_week, model_name)
             DO UPDATE SET predicted_demand=EXCLUDED.predicted_demand, generated_at=NOW(), metadata=EXCLUDED.metadata"""
    with psycopg.connect(dsn or database_url()) as conn:
        conn.execute(Path(schema_path).read_text(encoding="utf-8"))
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
    return len(rows)
