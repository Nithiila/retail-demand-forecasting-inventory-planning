import numpy as np
import pandas as pd

from backend.model_selection import score_predictions, select_model, wape


def test_wape_handles_zero_demand():
    assert wape([0, 0], [0, 0]) == 0
    assert np.isnan(wape([0, 0], [1, 0]))


def test_metrics_and_selection_are_comparable():
    scored = pd.DataFrame({"model": ["a", "a", "b", "b"], "actual": [10, 10, 10, 10], "prediction": [10, 10, 8, 8]})
    metrics = score_predictions(scored)
    assert {"mae", "rmse", "wape"} <= set(metrics.columns)
    assert select_model(metrics) == "a"
