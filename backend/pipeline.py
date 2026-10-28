"""End-to-end preparation, feature generation, and weekly forecast pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from .features import add_demand_features
from .forecasting import holt_winters_forecast, moving_average_forecast, naive_forecast, seasonal_naive_forecast


def load_settings(path: str | Path = "config/settings.yaml") -> dict:
    with Path(path).open(encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def validate_forecasts(forecasts: pd.DataFrame, expected_pairs: int, horizon: int, last_history_date: pd.Timestamp) -> None:
    required = {"forecast_date", "store_id", "product_id", "prediction", "model"}
    missing = required - set(forecasts.columns)
    if missing:
        raise ValueError(f"Forecast output is missing columns: {sorted(missing)}")
    if forecasts[list(required)].isna().any().any():
        raise ValueError("Forecast output contains missing required values")
    if (forecasts.prediction < 0).any():
        raise ValueError("Forecast predictions must be non-negative")
    dates = pd.to_datetime(forecasts.forecast_date)
    if dates.min() <= last_history_date or dates.nunique() != horizon:
        raise ValueError("Forecast dates must be future dates spanning the configured horizon")
    if len(forecasts) != expected_pairs * horizon:
        raise ValueError("Unexpected forecast prediction count")


def generate_forecasts(weekly: pd.DataFrame, settings_path: str | Path = "config/settings.yaml") -> pd.DataFrame:
    settings = load_settings(settings_path)
    horizon = int(settings.get("forecast", {}).get("horizon_weeks", 4))
    model_name = settings.get("model_selection", {}).get("selected_model", "moving_average")
    if model_name == "random_forest":
        raise ValueError("Random Forest requires a separately trained artifact and recursive feature generation")
    frame = add_demand_features(weekly)
    frame["week_start"] = pd.to_datetime(frame["week_start"])
    last_date = frame.week_start.max()
    rows = []
    for (store_id, product_id), group in frame.groupby(["store_id", "product_id"]):
        history = group.sort_values("week_start").units_sold
        if model_name == "naive":
            values = naive_forecast(history, horizon)
        elif model_name == "moving_average":
            values = moving_average_forecast(history, horizon, 4)
        elif model_name == "seasonal_naive":
            values = seasonal_naive_forecast(history, horizon, 52)
        elif model_name == "holt_winters":
            values = holt_winters_forecast(history, horizon, 52)
        else:
            raise ValueError(f"Unsupported selected model: {model_name}")
        for date, prediction in zip(pd.date_range(last_date + pd.Timedelta(days=7), periods=horizon, freq="7D"), values):
            rows.append({"forecast_date": date, "store_id": store_id, "product_id": product_id, "prediction": float(max(0, prediction)), "model": model_name})
    forecasts = pd.DataFrame(rows)
    validate_forecasts(forecasts, frame[["store_id", "product_id"]].drop_duplicates().shape[0], horizon, last_date)
    return forecasts


def run_pipeline(weekly_path: str | Path = "data/processed/weekly_demand.csv", output_path: str | Path = "outputs/forecasting/weekly_forecasts.csv", settings_path: str | Path = "config/settings.yaml") -> Path:
    forecasts = generate_forecasts(pd.read_csv(weekly_path), settings_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(output, index=False)
    return output
