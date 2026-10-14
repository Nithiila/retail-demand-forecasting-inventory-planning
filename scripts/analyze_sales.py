"""Prepare and analyze weekly retail sales without modifying raw datasets."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUTPUT = Path(__file__).resolve().parents[1] / "outputs" / "analysis"
REQUIRED = ("sales.csv", "products.csv", "stores.csv", "inventory.csv")


def generate_synthetic_raw(raw: Path = RAW, seed: int = SEED) -> None:
    """Generate 52 weeks of consistent data only when a required file is absent."""
    rng = np.random.default_rng(seed)
    raw.mkdir(parents=True, exist_ok=True)
    products = pd.DataFrame([
        ["P001", "Classic T-Shirt", "Apparel", 19.99],
        ["P002", "Running Shoes", "Footwear", 79.99],
        ["P003", "Wireless Headphones", "Electronics", 59.99],
        ["P004", "Insulated Bottle", "Home & Outdoor", 24.99],
    ], columns=["product_id", "product_name", "category", "unit_price"])
    stores = pd.DataFrame([["S001", "New York Central", "New York", "Northeast"], ["S002", "Austin Downtown", "Austin", "South"]], columns=["store_id", "store_name", "city", "region"])
    dates = pd.date_range("2023-01-01", periods=52, freq="W-SUN")
    base = {"P001": 25, "P002": 10, "P003": 15, "P004": 20}
    rows = []
    for date in dates:
        seasonal = 1 + 0.18 * np.sin(2 * np.pi * date.isocalendar().week / 52)
        for store in stores.store_id:
            for product in products.itertuples():
                promotion = int(rng.random() < 0.25)
                units = max(0, int(rng.normal(base[product.product_id] * seasonal * (1.25 if promotion else 1), 3)))
                rows.append([date.date(), store, product.product_id, units, product.unit_price, promotion])
    sales = pd.DataFrame(rows, columns=["date", "store_id", "product_id", "units_sold", "unit_price", "promotion"])
    inventory = sales.groupby(["store_id", "product_id"], as_index=False).tail(1)[["store_id", "product_id"]].copy()
    inventory.insert(0, "snapshot_date", dates[-1].date())
    inventory["stock_quantity"] = rng.integers(20, 120, len(inventory))
    inventory["reorder_point"] = rng.integers(10, 35, len(inventory))
    inventory["unit_cost"] = inventory.product_id.map({"P001": 10.0, "P002": 42.0, "P003": 31.0, "P004": 13.0})
    for name, frame in {"products": products, "stores": stores, "sales": sales, "inventory": inventory}.items():
        frame.to_csv(raw / f"{name}.csv", index=False)


def ensure_raw_data(raw: Path = RAW) -> bool:
    """Return whether files were generated; preserve an already complete raw set."""
    missing = [name for name in REQUIRED if not (raw / name).exists()]
    if missing:
        generate_synthetic_raw(raw)
        return True
    return False


def analyze(raw: Path = RAW, output: Path = OUTPUT) -> dict[str, pd.DataFrame | dict]:
    output.mkdir(parents=True, exist_ok=True)
    sales = pd.read_csv(raw / "sales.csv", parse_dates=["date"])
    products = pd.read_csv(raw / "products.csv")
    stores = pd.read_csv(raw / "stores.csv")
    sales = sales.merge(products[["product_id", "product_name", "category"]], on="product_id", validate="many_to_one")
    sales = sales.merge(stores[["store_id", "store_name"]], on="store_id", validate="many_to_one")
    sales["revenue"] = sales["units_sold"] * sales["unit_price"]
    sales["week"] = sales["date"].dt.to_period("W-SUN").dt.start_time
    weekly = sales.groupby(["week", "product_id", "product_name", "store_id", "store_name", "category"], as_index=False).agg(units_sold=("units_sold", "sum"), revenue=("revenue", "sum"), avg_price=("unit_price", "mean"), promotion_rate=("promotion", "mean"))
    category = weekly.groupby(["week", "category"], as_index=False).agg(units_sold=("units_sold", "sum"), revenue=("revenue", "sum"))
    promo = sales.groupby("promotion", as_index=False).agg(avg_units=("units_sold", "mean"), avg_revenue=("revenue", "mean"), avg_price=("unit_price", "mean"), records=("units_sold", "size"))
    price = sales.groupby("product_id", as_index=False).agg(avg_price=("unit_price", "mean"), avg_units=("units_sold", "mean"), price_std=("unit_price", "std"))
    anomaly = weekly.copy()
    anomaly["z_score"] = anomaly.groupby(["product_id", "store_id"])["units_sold"].transform(lambda x: (x - x.mean()) / x.std(ddof=0).replace(0, np.nan) if hasattr(x.std(ddof=0), "replace") else (x - x.mean()) / (x.std(ddof=0) or np.nan))
    anomaly = anomaly[anomaly["z_score"].abs() >= 2].copy()
    seasonality = weekly.groupby(weekly.week.dt.isocalendar().week.astype(int), as_index=False).agg(units_sold=("units_sold", "sum"), revenue=("revenue", "sum"))
    findings = {"weeks": int(weekly.week.nunique()), "records": int(len(sales)), "promotion_lift_units": float(promo.loc[promo.promotion == 1, "avg_units"].iloc[0] / promo.loc[promo.promotion == 0, "avg_units"].iloc[0] - 1) if set(promo.promotion) >= {0, 1} else None, "anomaly_count": int(len(anomaly))}
    weekly.to_csv(output / "weekly_sales_by_product_store_category.csv", index=False)
    category.to_csv(output / "weekly_sales_by_category.csv", index=False)
    promo.to_csv(output / "promotion_analysis.csv", index=False)
    price.to_csv(output / "pricing_analysis.csv", index=False)
    seasonality.to_csv(output / "seasonality_by_week.csv", index=False)
    anomaly.to_csv(output / "unusual_sales_patterns.csv", index=False)
    (output / "findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    (output / "README.md").write_text("# Sales analysis outputs\n\nWeekly product/store/category summaries, seasonality, promotion and pricing comparisons, and z-score unusual-pattern results are generated by `scripts/analyze_sales.py`. Raw files are read-only inputs.\n", encoding="utf-8")
    return {"weekly": weekly, "category": category, "promotion": promo, "pricing": price, "seasonality": seasonality, "anomalies": anomaly, "findings": findings}


if __name__ == "__main__":
    generated = ensure_raw_data()
    result = analyze()
    print(json.dumps({"generated_raw": generated, **result["findings"]}, indent=2))
