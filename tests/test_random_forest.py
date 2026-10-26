import numpy as np
import pandas as pd

from backend.random_forest import build_pipeline


def test_pipeline_has_imputation_and_random_forest():
    pipeline = build_pipeline()
    assert "preprocess" in pipeline.named_steps
    assert pipeline.named_steps["model"].__class__.__name__ == "RandomForestRegressor"


def test_feature_columns_exclude_current_target():
    data = pd.DataFrame({"week_start": pd.date_range("2024-01-01", periods=12, freq="7D"), "store_id": "S1", "product_id": "P1", "category": "A", "units_sold": np.arange(12), "average_price": 10.0, "promotion_rate": 0.0})
    assert "units_sold" not in ["lag_1", "lag_2", "average_price", "promotion_rate"]
