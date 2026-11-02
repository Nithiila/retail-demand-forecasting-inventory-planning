"""Inventory risk classification and actionable reorder recommendations."""

from __future__ import annotations

import pandas as pd


def classify_inventory_risk(plan: pd.DataFrame, forecasts: pd.DataFrame, settings: dict | None = None) -> pd.DataFrame:
    """Classify stockout, low-cover, normal, and excess inventory.

    Coverage is on-hand stock divided by average forecast demand per week.
    Thresholds come from ``inventory.risk`` in settings and are expressed in
    weeks of coverage. Stock at or below zero is always a stockout.
    """
    settings = settings or {}
    risk = settings.get("inventory", {}).get("risk", {})
    critical = float(risk.get("critical_coverage_weeks", 0.5))
    warning = float(risk.get("warning_coverage_weeks", 1.0))
    excess = float(risk.get("excess_coverage_weeks", 8.0))
    if not critical < warning < excess:
        raise ValueError("Risk coverage thresholds must satisfy critical < warning < excess")
    required = {"store_id", "product_id", "stock_quantity", "reorder_point", "recommended_order_quantity"}
    if missing := required - set(plan.columns):
        raise ValueError(f"Missing plan columns: {sorted(missing)}")
    fc = forecasts.groupby(["store_id", "product_id"], as_index=False).prediction.mean().rename(columns={"prediction": "average_weekly_demand"})
    result = plan.merge(fc, on=["store_id", "product_id"], how="left")
    result["average_weekly_demand"] = result.average_weekly_demand.fillna(0).clip(lower=0)
    result["coverage_weeks"] = result.apply(lambda row: float("inf") if row.average_weekly_demand == 0 and row.stock_quantity > 0 else (0.0 if row.average_weekly_demand == 0 else row.stock_quantity / row.average_weekly_demand), axis=1)
    def classify(row):
        if row.stock_quantity <= 0 or row.coverage_weeks == 0:
            return "stockout"
        if row.coverage_weeks < critical:
            return "critical"
        if row.coverage_weeks < warning:
            return "warning"
        if row.coverage_weeks > excess:
            return "excess"
        return "normal"
    result["risk_level"] = result.apply(classify, axis=1)
    result["recommended_order_quantity"] = result.apply(lambda row: max(row.recommended_order_quantity, row.reorder_point - row.stock_quantity) if row.risk_level in {"stockout", "critical", "warning"} else 0.0, axis=1)
    result["recommendation"] = result.apply(lambda row: {"stockout": "Expedite replenishment immediately", "critical": "Place replenishment order now", "warning": "Review and place replenishment order", "excess": "Pause replenishment and consider markdown or transfer", "normal": "Monitor; no action required"}[row.risk_level], axis=1)
    result["risk_thresholds"] = f"critical<{critical}w; warning<{warning}w; excess>{excess}w"
    return result
