"""Leakage-safe weekly demand feature engineering."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_demand_features(weekly: pd.DataFrame, windows: tuple[int, ...] = (4, 8)) -> pd.DataFrame:
    """Add features to weekly demand data without using future target values.

    The target is ``units_sold``. Every lag and rolling statistic is shifted by
    one period, so a row's features depend only on observations before that row.
    """
    required = {"week_start", "store_id", "product_id", "units_sold"}
    missing = required - set(weekly.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    result = weekly.copy()
    result["week_start"] = pd.to_datetime(result["week_start"])
    result = result.sort_values(["store_id", "product_id", "week_start"]).reset_index(drop=True)
    grouped = result.groupby(["store_id", "product_id"], sort=False)
    group = grouped["units_sold"]
    result["lag_1"] = group.shift(1)
    result["lag_2"] = group.shift(2)
    for window in windows:
        result[f"rolling_mean_{window}"] = grouped["units_sold"].transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
        result[f"rolling_std_{window}"] = grouped["units_sold"].transform(lambda x: x.shift(1).rolling(window, min_periods=2).std(ddof=0))
    result["history_count"] = group.apply(lambda x: x.shift(1).notna().cumsum()).reset_index(level=[0, 1], drop=True)
    result["week_of_year"] = result.week_start.dt.isocalendar().week.astype(int)
    result["month"] = result.week_start.dt.month
    result["quarter"] = result.week_start.dt.quarter
    result["week_sin"] = np.sin(2 * np.pi * result.week_of_year / 52)
    result["week_cos"] = np.cos(2 * np.pi * result.week_of_year / 52)
    if "average_price" in result:
        result["price_change"] = result.groupby(["store_id", "product_id"])["average_price"].pct_change()
    if "promotion_rate" in result:
        result["promotion_flag"] = (result["promotion_rate"].fillna(0) > 0).astype(int)
    if "list_price" in result and "average_price" in result:
        result["discount_rate"] = ((result["list_price"] - result["average_price"]) / result["list_price"].replace(0, np.nan)).clip(lower=0)
    return result
