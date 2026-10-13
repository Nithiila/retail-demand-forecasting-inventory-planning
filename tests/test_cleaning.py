import pandas as pd

from backend.cleaning import clean_inventory, clean_sales, normalize_categories


def test_sales_cleaning_drops_missing_invalid_and_duplicate_records():
    frame = pd.DataFrame({
        "date": ["2024-01-01", "bad-date", "2024-01-01", None],
        "store_id": ["S1", "S1", "S1", "S1"],
        "product_id": ["P1", "P1", "P1", "P1"],
        "units_sold": [2, "bad", 2, 1],
        "unit_price": [10, 10, 10, 10],
    })
    cleaned = clean_sales(frame)
    assert len(cleaned) == 1
    assert cleaned.loc[0, "units_sold"] == 2
    assert pd.api.types.is_datetime64_any_dtype(cleaned["date"])


def test_inventory_cleaning_removes_negative_quantities():
    frame = pd.DataFrame({
        "snapshot_date": ["2024-01-01", "2024-01-01"], "store_id": ["S1", "S1"],
        "product_id": ["P1", "P2"], "stock_quantity": [10, -1],
        "reorder_point": [3, 2], "unit_cost": [5, 5],
    })
    cleaned = clean_inventory(frame)
    assert cleaned["product_id"].tolist() == ["P1"]


def test_category_normalization_strips_and_maps_values():
    frame = pd.DataFrame({"region": [" northeast ", "south"]})
    cleaned = normalize_categories(frame, {"region": {"northeast": "Northeast", "south": "South"}})
    assert cleaned["region"].tolist() == ["Northeast", "South"]
