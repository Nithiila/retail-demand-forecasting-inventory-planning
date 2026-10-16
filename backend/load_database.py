"""Load processed retail CSVs into PostgreSQL."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import psycopg

from .cleaning import clean_inventory, clean_products, clean_sales, clean_stores
from .database import database_url


def load_processed_data(processed_dir: str | Path = "data/processed", dsn: str | None = None) -> dict[str, int]:
    """Clean defensively, create the schema, and upsert processed CSV rows.

    Raw files are never read or changed. Duplicate keys are collapsed by the
    cleaning functions; invalid rows are dropped before insertion.
    """
    root = Path(processed_dir)
    names = ("products", "stores", "sales", "inventory")
    missing = [name for name in names if not (root / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"Missing processed CSV files: {', '.join(missing)}")
    frames = {
        "products": clean_products(pd.read_csv(root / "products.csv")),
        "stores": clean_stores(pd.read_csv(root / "stores.csv")),
        "sales": clean_sales(pd.read_csv(root / "sales.csv")),
        "inventory": clean_inventory(pd.read_csv(root / "inventory.csv")),
    }
    schema = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    with psycopg.connect(dsn or database_url()) as conn:
        conn.execute(schema.read_text(encoding="utf-8"))
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO products (product_id, product_name, category, unit_price) VALUES (%s,%s,%s,%s) ON CONFLICT (product_id) DO UPDATE SET product_name=EXCLUDED.product_name, category=EXCLUDED.category, unit_price=EXCLUDED.unit_price", frames["products"].itertuples(index=False, name=None))
            cur.executemany("INSERT INTO stores (store_id, store_name, city, region) VALUES (%s,%s,%s,%s) ON CONFLICT (store_id) DO UPDATE SET store_name=EXCLUDED.store_name, city=EXCLUDED.city, region=EXCLUDED.region", frames["stores"].itertuples(index=False, name=None))
            cur.executemany("INSERT INTO sales (sale_date, store_id, product_id, units_sold, unit_price, promotion) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (sale_date, store_id, product_id) DO UPDATE SET units_sold=EXCLUDED.units_sold, unit_price=EXCLUDED.unit_price, promotion=EXCLUDED.promotion", frames["sales"].rename(columns={"date": "sale_date"})[["sale_date", "store_id", "product_id", "units_sold", "unit_price", "promotion"]].itertuples(index=False, name=None))
            cur.executemany("INSERT INTO inventory (snapshot_date, store_id, product_id, stock_quantity, reorder_point, unit_cost) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (snapshot_date, store_id, product_id) DO UPDATE SET stock_quantity=EXCLUDED.stock_quantity, reorder_point=EXCLUDED.reorder_point, unit_cost=EXCLUDED.unit_cost", frames["inventory"].itertuples(index=False, name=None))
    return {name: len(frame) for name, frame in frames.items()}


if __name__ == "__main__":
    print(load_processed_data())
