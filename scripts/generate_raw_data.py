"""Generate deterministic raw retail data with seed 42.

The checked-in sample is intentionally small and follows the same schema and
ID conventions. Run this script to create a longer 52-week training history.
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
RNG = np.random.default_rng(SEED)
ROOT = Path(__file__).resolve().parents[1] / "data" / "raw"

products = pd.DataFrame([
    ["P001", "Classic T-Shirt", "Apparel", 19.99],
    ["P002", "Running Shoes", "Footwear", 79.99],
    ["P003", "Wireless Headphones", "Electronics", 59.99],
    ["P004", "Insulated Bottle", "Home & Outdoor", 24.99],
], columns=["product_id", "product_name", "category", "unit_price"])
stores = pd.DataFrame([["S001", "New York Central", "New York", "Northeast"], ["S002", "Austin Downtown", "Austin", "South"]], columns=["store_id", "store_name", "city", "region"])
dates = pd.date_range("2023-01-01", periods=52, freq="W-SUN")
rows = []
for date in dates:
    for store in stores.store_id:
        for product in products.itertuples():
            promo = int(RNG.random() < 0.25)
            units = max(0, int(RNG.normal({"P001": 25, "P002": 10, "P003": 15, "P004": 20}[product.product_id] * (1.25 if promo else 1), 3)))
            rows.append([date.date(), store, product.product_id, units, product.unit_price, promo])
sales = pd.DataFrame(rows, columns=["date", "store_id", "product_id", "units_sold", "unit_price", "promotion"])
inventory = sales.groupby(["store_id", "product_id"], as_index=False).tail(1)[["store_id", "product_id"]].copy()
inventory.insert(0, "snapshot_date", dates[-1].date())
inventory["stock_quantity"] = RNG.integers(20, 120, len(inventory))
inventory["reorder_point"] = RNG.integers(10, 35, len(inventory))
inventory["unit_cost"] = inventory.product_id.map({"P001": 10.0, "P002": 42.0, "P003": 31.0, "P004": 13.0})
ROOT.mkdir(parents=True, exist_ok=True)
products.to_csv(ROOT / "products.csv", index=False)
stores.to_csv(ROOT / "stores.csv", index=False)
sales.to_csv(ROOT / "sales.csv", index=False)
inventory.to_csv(ROOT / "inventory.csv", index=False)
