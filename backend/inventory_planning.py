"""Inventory planning calculations aligned to weekly demand forecasts."""

from __future__ import annotations

from statistics import NormalDist

import pandas as pd


def lead_time_weeks(lead_time_days: float) -> int:
    """Convert days to whole coverage weeks, rounding up conservatively."""
    if pd.isna(lead_time_days) or lead_time_days < 0:
        raise ValueError("lead_time_days is required and must be non-negative")
    return int((float(lead_time_days) + 6) // 7)


def calculate_inventory_plan(inventory: pd.DataFrame, forecasts: pd.DataFrame, service_level: float = 0.95) -> pd.DataFrame:
    """Calculate lead-time demand, safety stock, reorder point, and order quantity.

    Missing/negative lead times are rejected. Negative stock is treated as zero
    (a stockout) and retained in ``original_stock_quantity`` for auditability.
    Zero demand yields zero lead-time demand and safety stock.
    """
    required_inventory = {"store_id", "product_id", "stock_quantity", "lead_time_days"}
    required_forecast = {"store_id", "product_id", "forecast_date", "prediction"}
    if missing := required_inventory - set(inventory.columns):
        raise ValueError(f"Missing inventory columns: {sorted(missing)}")
    if missing := required_forecast - set(forecasts.columns):
        raise ValueError(f"Missing forecast columns: {sorted(missing)}")
    if not 0 < service_level < 1:
        raise ValueError("service_level must be between 0 and 1")
    inv = inventory.copy()
    inv["lead_time_weeks"] = inv.lead_time_days.map(lead_time_weeks)
    inv["original_stock_quantity"] = inv.stock_quantity
    inv["stock_quantity"] = pd.to_numeric(inv.stock_quantity, errors="raise").clip(lower=0)
    fc = forecasts.copy()
    fc["forecast_date"] = pd.to_datetime(fc.forecast_date)
    z = NormalDist().inv_cdf(service_level)
    rows = []
    for row in inv.itertuples():
        series = fc[(fc.store_id == row.store_id) & (fc.product_id == row.product_id)].sort_values("forecast_date").prediction.astype(float)
        weeks = int(row.lead_time_weeks)
        demand = series.head(weeks)
        lead_demand = float(demand.sum())
        safety = float(max(0, z * demand.std(ddof=0) * (weeks ** 0.5))) if weeks and not demand.empty else 0.0
        reorder = lead_demand + safety
        rows.append({"store_id": row.store_id, "product_id": row.product_id, "lead_time_days": row.lead_time_days, "lead_time_weeks": weeks, "original_stock_quantity": row.original_stock_quantity, "stock_quantity": float(row.stock_quantity), "lead_time_demand": lead_demand, "safety_stock": safety, "reorder_point": reorder, "recommended_order_quantity": max(0.0, reorder - float(row.stock_quantity)), "service_level": service_level})
    return pd.DataFrame(rows)
