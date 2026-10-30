import pandas as pd
import pytest

from backend.inventory_planning import calculate_inventory_plan, lead_time_weeks


def frames(stock=10, lead=10, demand=None):
    inventory = pd.DataFrame([{ "store_id": "S1", "product_id": "P1", "stock_quantity": stock, "lead_time_days": lead }])
    forecasts = pd.DataFrame({"store_id": ["S1"] * 4, "product_id": ["P1"] * 4, "forecast_date": pd.date_range("2024-02-01", periods=4, freq="7D"), "prediction": demand or [10, 10, 10, 10]})
    return inventory, forecasts


def test_lead_time_rounds_up_to_forecast_weeks():
    assert lead_time_weeks(0) == 0
    assert lead_time_weeks(1) == 1
    assert lead_time_weeks(8) == 2


def test_normal_plan_calculates_demand_safety_and_order_quantity():
    inventory, forecasts = frames(stock=5, lead=8)
    result = calculate_inventory_plan(inventory, forecasts, service_level=0.95).iloc[0]
    assert result.lead_time_demand == 20
    assert result.safety_stock >= 0
    assert result.recommended_order_quantity > 0


def test_zero_demand_and_negative_stock_rules():
    inventory, forecasts = frames(stock=-3, lead=0, demand=[0, 0, 0, 0])
    result = calculate_inventory_plan(inventory, forecasts).iloc[0]
    assert result.stock_quantity == 0
    assert result.lead_time_demand == 0
    assert result.safety_stock == 0
    assert result.recommended_order_quantity == 0


def test_missing_or_negative_lead_time_is_rejected():
    inventory, forecasts = frames(lead=-1)
    with pytest.raises(ValueError):
        calculate_inventory_plan(inventory, forecasts)
