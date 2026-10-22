import numpy as np
import pandas as pd

from backend.forecasting import chronological_split, evaluate_baselines, moving_average_forecast, naive_forecast, seasonal_naive_forecast


def test_forecast_calculations():
    history = pd.Series([1, 2, 3, 4])
    assert naive_forecast(history, 2).tolist() == [4.0, 4.0]
    assert moving_average_forecast(history, 2, 2).tolist() == [3.5, 3.5]
    assert seasonal_naive_forecast(history, 3, 2).tolist() == [3.0, 4.0, 3.0]


def test_chronological_split_has_shared_last_weeks():
    data = pd.DataFrame({"week_start": pd.date_range("2024-01-01", periods=10, freq="7D"), "store_id": "S1", "product_id": "P1", "units_sold": range(10)})
    train, validation = chronological_split(data, 3)
    assert train.week_start.max() < validation.week_start.min()
    assert len(validation) == 3


def test_metrics_are_computed_on_same_validation_rows():
    data = pd.DataFrame({"week_start": pd.date_range("2024-01-01", periods=12, freq="7D"), "store_id": "S1", "product_id": "P1", "units_sold": range(12)})
    metrics, predictions = evaluate_baselines(data, validation_weeks=4, moving_window=2, season_length=4)
    assert set(metrics.model) == {"naive", "moving_average", "seasonal_naive"}
    assert (metrics.mae >= 0).all() and (metrics.rmse >= metrics.mae).all()
    assert predictions.groupby("model").size().nunique() == 1
