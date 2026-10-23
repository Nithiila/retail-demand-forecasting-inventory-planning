import numpy as np
import pandas as pd

from backend.forecasting import evaluate_holt_winters_sample, holt_winters_forecast


def test_holt_winters_forecast_has_requested_horizon_and_nonnegative_values():
    forecast = holt_winters_forecast(pd.Series(np.arange(20, dtype=float)), 5, seasonal_periods=4)
    assert len(forecast) == 5
    assert np.all(forecast >= 0)


def test_holt_winters_uses_same_validation_window_as_baselines():
    data = pd.DataFrame({"week_start": pd.date_range("2024-01-01", periods=20, freq="7D"), "store_id": "S1", "product_id": "P1", "units_sold": np.arange(20) + 10})
    metrics, predictions, report = evaluate_holt_winters_sample(data, validation_weeks=8, top_n=20, season_length=4)
    assert set(metrics.model) == {"naive", "moving_average", "seasonal_naive", "holt_winters"}
    assert predictions.week_start.nunique() == 8
    assert report["evaluated_series"] == 1
