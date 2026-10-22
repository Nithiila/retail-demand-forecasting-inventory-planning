
"""Simple weekly-demand baselines and comparable time-based evaluation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def naive_forecast(history: pd.Series, horizon: int) -> np.ndarray:
    if history.empty:
        raise ValueError("history must contain at least one observation")
    return np.repeat(float(history.iloc[-1]), horizon)


def moving_average_forecast(history: pd.Series, horizon: int, window: int = 4) -> np.ndarray:
    if history.empty or window < 1:
        raise ValueError("history must be non-empty and window must be positive")
    return np.repeat(float(history.iloc[-window:].mean()), horizon)


def seasonal_naive_forecast(history: pd.Series, horizon: int, season_length: int = 52) -> np.ndarray:
    if history.empty or season_length < 1:
        raise ValueError("history must be non-empty and season_length must be positive")
    if len(history) < season_length:
        return naive_forecast(history, horizon)
    season = history.iloc[-season_length:].to_numpy(dtype=float)
    return np.resize(season, horizon)


def chronological_split(data: pd.DataFrame, validation_weeks: int = 8) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split globally by week, keeping the same validation dates for all models."""
    if validation_weeks < 1:
        raise ValueError("validation_weeks must be positive")
    frame = data.copy()
    frame["week_start"] = pd.to_datetime(frame["week_start"])
    weeks = sorted(frame.week_start.dropna().unique())
    if len(weeks) <= validation_weeks:
        raise ValueError("not enough weeks for the requested validation window")
    cutoff = weeks[-validation_weeks]
    return frame[frame.week_start < cutoff].copy(), frame[frame.week_start >= cutoff].copy()


def evaluate_baselines(data: pd.DataFrame, validation_weeks: int = 8, moving_window: int = 4, season_length: int = 52) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate all baselines on one chronological validation window."""
    train, validation = chronological_split(data, validation_weeks)
    predictions: list[dict] = []
    for (store_id, product_id), valid_group in validation.groupby(["store_id", "product_id"]):
        history = train[(train.store_id == store_id) & (train.product_id == product_id)].sort_values("week_start").units_sold
        if history.empty:
            continue
        for name, values in (("naive", naive_forecast(history, len(valid_group))), ("moving_average", moving_average_forecast(history, len(valid_group), moving_window)), ("seasonal_naive", seasonal_naive_forecast(history, len(valid_group), season_length))):
            for row, prediction in zip(valid_group.sort_values("week_start").itertuples(), values):
                predictions.append({"model": name, "week_start": row.week_start, "store_id": store_id, "product_id": product_id, "actual": row.units_sold, "prediction": prediction})
    scored = pd.DataFrame(predictions)
    metrics = scored.groupby("model").apply(lambda x: pd.Series({"mae": np.mean(np.abs(x.actual - x.prediction)), "rmse": np.sqrt(np.mean((x.actual - x.prediction) ** 2)), "observations": len(x)}), include_groups=False).reset_index()
    return metrics, scored
