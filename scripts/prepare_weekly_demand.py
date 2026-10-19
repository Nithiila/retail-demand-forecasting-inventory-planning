"""Prepare clean weekly historical demand for forecasting."""

from pathlib import Path

import pandas as pd

from backend.cleaning import clean_products, clean_sales, clean_stores


ROOT = Path(__file__).resolve().parents[1]


def prepare_weekly_demand(raw_dir: str | Path = ROOT / "data" / "raw", processed_dir: str | Path = ROOT / "data" / "processed") -> Path:
    raw_dir, processed_dir = Path(raw_dir), Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    products = clean_products(pd.read_csv(raw_dir / "products.csv"))
    stores = clean_stores(pd.read_csv(raw_dir / "stores.csv"))
    sales = clean_sales(pd.read_csv(raw_dir / "sales.csv"))
    sales = sales.merge(products[["product_id", "category"]], on="product_id", validate="many_to_one")
    sales = sales.merge(stores[["store_id"]], on="store_id", validate="many_to_one")
    sales["week_start"] = sales["date"].dt.to_period("W-SUN").dt.start_time.dt.date
    weekly = sales.groupby(["week_start", "store_id", "product_id", "category"], as_index=False).agg(
        units_sold=("units_sold", "sum"),
        average_price=("unit_price", "mean"),
        promotion_rate=("promotion", "mean"),
    )
    weekly = weekly.sort_values(["store_id", "product_id", "week_start"]).reset_index(drop=True)
    output = processed_dir / "weekly_demand.csv"
    weekly.to_csv(output, index=False)
    return output


if __name__ == "__main__":
    print(prepare_weekly_demand())
