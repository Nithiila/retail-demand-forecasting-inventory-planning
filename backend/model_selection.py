"""Common scoring and model-selection helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def wape(actual, predicted) -> float:
    """Weighted absolute percentage error; returns 0 for an all-zero perfect series."""
    actual, predicted = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    denominator = np.abs(actual).sum()
    numerator = np.abs(actual - predicted).sum()
    if denominator == 0:
        return 0.0 if numerator == 0 else float("nan")
    return float(numerator / denominator)


def score_predictions(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model, frame in scored.groupby("model"):
        rows.append({"model": model, "mae": float(np.mean(np.abs(frame.actual - frame.prediction))), "rmse": float(np.sqrt(np.mean((frame.actual - frame.prediction) ** 2))), "wape": wape(frame.actual, frame.prediction), "observations": len(frame)})
    return pd.DataFrame(rows).sort_values(["rmse", "wape"], na_position="last").reset_index(drop=True)


def select_model(metrics: pd.DataFrame) -> str:
    """Select the lowest-RMSE model, breaking ties with WAPE then MAE."""
    if metrics.empty:
        raise ValueError("metrics must not be empty")
    return metrics.sort_values(["rmse", "wape", "mae"], na_position="last").iloc[0].model
