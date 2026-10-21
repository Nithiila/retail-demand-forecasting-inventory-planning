import pandas as pd

from backend.features import add_demand_features


def sample():
    return pd.DataFrame({
        "week_start": pd.date_range("2024-01-01", periods=4, freq="7D"),
        "store_id": ["S1"] * 4, "product_id": ["P1"] * 4,
        "units_sold": [10, 20, 30, 40], "average_price": [10, 10, 11, 11],
        "promotion_rate": [0, 1, 0, 0],
    })


def test_lags_and_rolling_values_use_history_only():
    result = add_demand_features(sample(), windows=(2,))
    assert pd.isna(result.loc[0, "lag_1"])
    assert result.loc[1, "lag_1"] == 10
    assert result.loc[3, "rolling_mean_2"] == 25


def test_missing_history_is_explicit_and_not_imputed_from_future():
    result = add_demand_features(sample(), windows=(2,))
    assert pd.isna(result.loc[0, "rolling_std_2"])
    assert result.loc[0, "history_count"] == 0
    assert result.loc[1, "history_count"] == 1


def test_future_target_change_cannot_change_prior_features():
    original = add_demand_features(sample(), windows=(2,))
    changed = sample()
    changed.loc[3, "units_sold"] = 9999
    modified = add_demand_features(changed, windows=(2,))
    cols = ["lag_1", "lag_2", "rolling_mean_2", "rolling_std_2", "history_count"]
    pd.testing.assert_frame_equal(original.loc[:2, cols], modified.loc[:2, cols])
