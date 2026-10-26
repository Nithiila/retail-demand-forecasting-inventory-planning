"""Leakage-safe Random Forest demand model and evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .features import add_demand_features
from .forecasting import chronological_split


def build_pipeline(random_state: int = 42) -> Pipeline:
    numeric = ["lag_1", "lag_2", "rolling_mean_4", "rolling_std_4", "rolling_mean_8", "rolling_std_8", "history_count", "week_of_year", "month", "quarter", "week_sin", "week_cos", "price_change", "promotion_rate", "promotion_flag", "average_price"]
    categorical = ["store_id", "product_id", "category"]
    prep = ColumnTransformer([( "numeric", SimpleImputer(strategy="median"), numeric), ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical)], remainder="drop")
    model = RandomForestRegressor(random_state=random_state, n_jobs=-1)
    return Pipeline([("preprocess", prep), ("model", model)])


def train_random_forest(data: pd.DataFrame, validation_weeks: int = 8, top_n: int = 20, random_state: int = 42, artifact_dir: str | Path = "models/random_forest") -> tuple[pd.DataFrame, dict]:
    engineered = add_demand_features(data)
    train, validation = chronological_split(engineered, validation_weeks)
    top = train.groupby(["store_id", "product_id"], as_index=False).units_sold.sum().nlargest(top_n, "units_sold")[["store_id", "product_id"]]
    train = train.merge(top, on=["store_id", "product_id"])
    validation = validation.merge(top, on=["store_id", "product_id"])
    feature_names = ["lag_1", "lag_2", "rolling_mean_4", "rolling_std_4", "rolling_mean_8", "rolling_std_8", "history_count", "week_of_year", "month", "quarter", "week_sin", "week_cos", "price_change", "promotion_rate", "promotion_flag", "average_price", "store_id", "product_id", "category"]
    X_train, y_train = train[feature_names], train.units_sold
    splitter = TimeSeriesSplit(n_splits=min(3, max(2, len(X_train) // 10)))
    search = GridSearchCV(build_pipeline(random_state), {"model__n_estimators": [100], "model__min_samples_leaf": [1, 3]}, scoring="neg_root_mean_squared_error", cv=splitter, n_jobs=-1)
    search.fit(X_train, y_train)
    predictions = search.predict(validation[feature_names])
    metrics = {"mae": float(mean_absolute_error(validation.units_sold, predictions)), "rmse": float(np.sqrt(mean_squared_error(validation.units_sold, predictions))), "validation_rows": int(len(validation))}
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(search.best_estimator_, artifact_dir / "random_forest.joblib")
    transformed = search.best_estimator_.named_steps["preprocess"].get_feature_names_out()
    importance = pd.DataFrame({"feature": transformed, "importance": search.best_estimator_.named_steps["model"].feature_importances_}).sort_values("importance", ascending=False)
    importance.to_csv(artifact_dir / "feature_importances.csv", index=False)
    metadata = {"model": "RandomForestRegressor", "features": feature_names, "training_start": str(train.week_start.min().date()), "training_end": str(train.week_start.max().date()), "validation_start": str(validation.week_start.min().date()), "validation_end": str(validation.week_start.max().date()), "validation_weeks": validation_weeks, "requested_top_series": top_n, "evaluated_series": int(len(top)), "best_params": search.best_params_, "metrics": metrics, "limitation": "The model is evaluated on top-volume product-store series selected using training data."}
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    scored = validation[["week_start", "store_id", "product_id", "units_sold"]].copy()
    scored["prediction"] = predictions
    return scored, metadata
