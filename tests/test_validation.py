import pandas as pd

from backend.validation import validate_dataframes


def valid_frames():
    products = pd.DataFrame({"product_id": ["P1"], "unit_price": [10.0]})
    stores = pd.DataFrame({"store_id": ["S1"]})
    sales = pd.DataFrame({"date": ["2024-01-07"], "store_id": ["S1"], "product_id": ["P1"], "units_sold": [3], "unit_price": [10.0], "promotion": [0]})
    inventory = pd.DataFrame({"snapshot_date": ["2024-01-07"], "store_id": ["S1"], "product_id": ["P1"], "stock_quantity": [20], "reorder_point": [5]})
    return sales, products, stores, inventory


def test_valid_data_returns_clear_success_report():
    report = validate_dataframes(*valid_frames())
    assert report["valid"] is True
    assert report["issues"] == []


def test_missing_values_and_invalid_quantities_are_reported():
    sales, products, stores, inventory = valid_frames()
    sales.loc[0, "units_sold"] = -1
    sales.loc[0, "date"] = None
    report = validate_dataframes(sales, products, stores, inventory)
    codes = {issue["code"] for issue in report["issues"]}
    assert {"missing_values", "invalid_dates", "invalid_quantities"} <= codes


def test_duplicate_keys_and_inconsistent_ids_are_reported():
    sales, products, stores, inventory = valid_frames()
    sales.loc[0, "store_id"] = "UNKNOWN"
    products.loc[1] = ["P1", 11.0]
    report = validate_dataframes(sales, products, stores, inventory)
    codes = {issue["code"] for issue in report["issues"]}
    assert "duplicate_keys" in codes
    assert "inconsistent_ids" in codes
