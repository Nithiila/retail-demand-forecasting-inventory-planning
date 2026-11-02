import pandas as pd
import pytest

from backend.inventory_risk import classify_inventory_risk


def data(stock, reorder=20, demand=10):
    plan = pd.DataFrame([{ "store_id": "S1", "product_id": "P1", "stock_quantity": stock, "reorder_point": reorder, "recommended_order_quantity": max(0, reorder-stock) }])
    fc = pd.DataFrame({"store_id": ["S1"] * 4, "product_id": ["P1"] * 4, "prediction": [demand] * 4})
    return plan, fc


def test_stockout_is_critical_and_actionable():
    plan, fc = data(0)
    result = classify_inventory_risk(plan, fc).iloc[0]
    assert result.risk_level == "stockout"
    assert result.recommended_order_quantity == 20


def test_excess_inventory_recommends_pause():
    plan, fc = data(100, reorder=20, demand=5)
    result = classify_inventory_risk(plan, fc).iloc[0]
    assert result.risk_level == "excess"
    assert result.recommended_order_quantity == 0
    assert "Pause" in result.recommendation


def test_normal_inventory_requires_no_action():
    plan, fc = data(30, reorder=20, demand=10)
    result = classify_inventory_risk(plan, fc).iloc[0]
    assert result.risk_level == "normal"
    assert result.recommended_order_quantity == 0


def test_invalid_thresholds_are_rejected():
    plan, fc = data(10)
    with pytest.raises(ValueError):
        classify_inventory_risk(plan, fc, {"inventory": {"risk": {"critical_coverage_weeks": 2, "warning_coverage_weeks": 1, "excess_coverage_weeks": 3}}})
