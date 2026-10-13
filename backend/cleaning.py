"""Reusable cleaning helpers for raw retail CSV datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


def clean_missing(df: pd.DataFrame, required: Iterable[str]) -> pd.DataFrame:
    """Remove rows missing required fields and return a copied frame."""
    required = list(required)
    return df.dropna(subset=required).drop_duplicates().reset_index(drop=True).copy()


def coerce_dates(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Parse date columns and remove rows whose dates cannot be parsed."""
    result = df.copy()
    for column in columns:
        result[column] = pd.to_datetime(result[column], errors="coerce")
    return result.dropna(subset=list(columns)).reset_index(drop=True)


def coerce_numeric(df: pd.DataFrame, columns: Iterable[str], non_negative: Iterable[str] = ()) -> pd.DataFrame:
    """Convert numeric columns and remove non-numeric or invalid quantities."""
    result = df.copy()
    for column in columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    non_negative = list(non_negative)
    result = result.dropna(subset=list(columns))
    if non_negative:
        result = result[(result[non_negative] >= 0).all(axis=1)]
    return result.reset_index(drop=True)


def normalize_categories(df: pd.DataFrame, mappings: Mapping[str, Mapping[str, str]]) -> pd.DataFrame:
    """Normalize categorical values using per-column replacement mappings."""
    result = df.copy()
    for column, mapping in mappings.items():
        result[column] = result[column].astype("string").str.strip().replace(mapping)
    return result


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    result = clean_missing(df, ["date", "store_id", "product_id", "units_sold", "unit_price"])
    result = coerce_dates(result, ["date"])
    result = coerce_numeric(result, ["units_sold", "unit_price"], ["units_sold"])
    return result[result["unit_price"] > 0].reset_index(drop=True)


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    result = clean_missing(df, ["product_id", "product_name", "category", "unit_price"])
    result = coerce_numeric(result, ["unit_price"])
    result = normalize_categories(result, {"category": {"Home and Outdoor": "Home & Outdoor"}})
    return result[result["unit_price"] > 0].drop_duplicates("product_id").reset_index(drop=True)


def clean_stores(df: pd.DataFrame) -> pd.DataFrame:
    result = clean_missing(df, ["store_id", "store_name", "city", "region"])
    result = normalize_categories(result, {"region": {"northeast": "Northeast", "south": "South"}})
    return result.drop_duplicates("store_id").reset_index(drop=True)


def clean_inventory(df: pd.DataFrame) -> pd.DataFrame:
    result = clean_missing(df, ["snapshot_date", "store_id", "product_id", "stock_quantity", "reorder_point"])
    result = coerce_dates(result, ["snapshot_date"])
    result = coerce_numeric(result, ["stock_quantity", "reorder_point", "unit_cost"], ["stock_quantity", "reorder_point"])
    return result.reset_index(drop=True)


def clean_raw_datasets(raw_dir: str | Path, processed_dir: str | Path) -> dict[str, Path]:
    """Clean all raw datasets and write separate processed CSV files."""
    raw_dir, processed_dir = Path(raw_dir), Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    cleaners = {"sales": clean_sales, "products": clean_products, "stores": clean_stores, "inventory": clean_inventory}
    outputs: dict[str, Path] = {}
    for name, cleaner in cleaners.items():
        output = processed_dir / f"{name}.csv"
        cleaner(pd.read_csv(raw_dir / f"{name}.csv")).to_csv(output, index=False)
        outputs[name] = output
    return outputs
