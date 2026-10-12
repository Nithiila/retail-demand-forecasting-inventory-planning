"""Validation utilities for the raw Day 3 CSV datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


DATASETS = ("sales", "products", "stores", "inventory")


def _issue(code: str, message: str, rows: int = 0) -> dict[str, Any]:
    return {"code": code, "message": message, "rows": rows}


def validate_dataframes(
    sales: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
    inventory: pd.DataFrame,
) -> dict[str, Any]:
    """Validate the four related raw datasets without changing their contents.

    Returns a serializable report with ``valid`` and detailed ``issues`` fields.
    """
    issues: list[dict[str, Any]] = []
    required = {
        "sales": {"date", "store_id", "product_id", "units_sold", "unit_price", "promotion"},
        "products": {"product_id", "unit_price"},
        "stores": {"store_id"},
        "inventory": {"snapshot_date", "store_id", "product_id", "stock_quantity", "reorder_point"},
    }
    frames = {"sales": sales, "products": products, "stores": stores, "inventory": inventory}

    for name, frame in frames.items():
        missing_columns = sorted(required[name] - set(frame.columns))
        if missing_columns:
            issues.append(_issue("missing_columns", f"{name}: missing {missing_columns}"))
            continue
        null_rows = int(frame[list(required[name])].isna().any(axis=1).sum())
        if null_rows:
            issues.append(_issue("missing_values", f"{name}: required fields contain missing values", null_rows))
        duplicate_rows = int(frame.duplicated().sum())
        if duplicate_rows:
            issues.append(_issue("duplicate_rows", f"{name}: duplicate rows found", duplicate_rows))

    for name, column in (("sales", "date"), ("inventory", "snapshot_date")):
        if column in frames[name]:
            invalid = int(pd.to_datetime(frames[name][column], errors="coerce").isna().sum())
            if invalid:
                issues.append(_issue("invalid_dates", f"{name}.{column}: invalid dates found", invalid))

    for name, column in (("sales", "units_sold"), ("inventory", "stock_quantity"), ("inventory", "reorder_point")):
        if column in frames[name]:
            values = pd.to_numeric(frames[name][column], errors="coerce")
            invalid = int(values.isna().sum() + (values < 0).sum())
            if invalid:
                issues.append(_issue("invalid_quantities", f"{name}.{column}: quantities must be numeric and non-negative", invalid))

    if "unit_price" in sales:
        prices = pd.to_numeric(sales.unit_price, errors="coerce")
        invalid = int(prices.isna().sum() + (prices <= 0).sum())
        if invalid:
            issues.append(_issue("invalid_prices", "sales.unit_price: prices must be positive", invalid))

    for name, keys in (("products", ["product_id"]), ("stores", ["store_id"]), ("inventory", ["snapshot_date", "store_id", "product_id"]), ("sales", ["date", "store_id", "product_id"])):
        if all(key in frames[name] for key in keys):
            duplicates = int(frames[name].duplicated(keys).sum())
            if duplicates:
                issues.append(_issue("duplicate_keys", f"{name}: duplicate key combinations {keys}", duplicates))

    if "store_id" in sales and "store_id" in stores:
        unknown = sorted(set(sales.store_id.dropna()) - set(stores.store_id.dropna()))
        if unknown:
            issues.append(_issue("inconsistent_ids", f"sales.store_id: unknown IDs {unknown}", len(unknown)))
    if "product_id" in sales and "product_id" in products:
        unknown = sorted(set(sales.product_id.dropna()) - set(products.product_id.dropna()))
        if unknown:
            issues.append(_issue("inconsistent_ids", f"sales.product_id: unknown IDs {unknown}", len(unknown)))
    if "store_id" in inventory and "store_id" in stores:
        unknown = sorted(set(inventory.store_id.dropna()) - set(stores.store_id.dropna()))
        if unknown:
            issues.append(_issue("inconsistent_ids", f"inventory.store_id: unknown IDs {unknown}", len(unknown)))
    if "product_id" in inventory and "product_id" in products:
        unknown = sorted(set(inventory.product_id.dropna()) - set(products.product_id.dropna()))
        if unknown:
            issues.append(_issue("inconsistent_ids", f"inventory.product_id: unknown IDs {unknown}", len(unknown)))

    return {"valid": not issues, "issues": issues, "datasets": {name: int(frame.shape[0]) for name, frame in frames.items()}}


def validate_raw_datasets(data_dir: str | Path) -> dict[str, Any]:
    """Load and validate ``sales.csv``, ``products.csv``, ``stores.csv``, and ``inventory.csv``."""
    root = Path(data_dir)
    paths = {name: root / f"{name}.csv" for name in DATASETS}
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        return {"valid": False, "issues": [_issue("missing_files", f"Missing files: {missing}")], "datasets": {}}
    frames = {name: pd.read_csv(path) for name, path in paths.items()}
    return validate_dataframes(**frames)
