import pandas as pd

from backend.pipeline import generate_forecasts, validate_forecasts


def weekly_data():
    return pd.DataFrame({"week_start": pd.date_range("2024-01-01", periods=10, freq="7D").tolist() * 2, "store_id": ["S1"] * 10 + ["S2"] * 10, "product_id": ["P1"] * 20, "category": ["A"] * 20, "units_sold": list(range(10, 20)) * 2, "average_price": [10.0] * 20, "promotion_rate": [0.0] * 20})


def test_pipeline_generates_four_future_rows_per_pair(tmp_path):
    settings = tmp_path / "settings.yaml"
    settings.write_text("forecast:\n  horizon_weeks: 4\nmodel_selection:\n  selected_model: moving_average\n")
    result = generate_forecasts(weekly_data(), settings)
    assert len(result) == 8
    assert result.forecast_date.min() > pd.Timestamp("2024-03-04")
    assert result.prediction.notna().all()


def test_forecast_validation_rejects_wrong_counts():
    bad = pd.DataFrame(columns=["forecast_date", "store_id", "product_id", "prediction", "model"])
    try:
        validate_forecasts(bad, expected_pairs=1, horizon=4, last_history_date=pd.Timestamp("2024-01-01"))
    except ValueError as exc:
        assert "missing" in str(exc).lower() or "count" in str(exc).lower()
    else:
        raise AssertionError("invalid forecast output was accepted")
