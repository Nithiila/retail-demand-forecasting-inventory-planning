"""Local Airflow orchestration for validation, cleaning, forecasting, and inventory planning."""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

from backend.cleaning import clean_raw_datasets
from backend.database import load_project_settings
from backend.inventory_planning import calculate_inventory_plan
from backend.pipeline import run_pipeline
from backend.validation import validate_raw_datasets

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUT = ROOT / "outputs" / "forecasting"


def failure_callback(context):
    task = context.get("task_instance")
    if task:
        task.log.error("Retail demand workflow failed: task=%s run=%s", task.task_id, context.get("run_id"))


def validate_task():
    report = validate_raw_datasets(RAW)
    print("Validation report:", report)
    if not report["valid"]:
        raise ValueError(f"Raw datasets failed validation: {report['issues']}")


def clean_task():
    outputs = clean_raw_datasets(RAW, PROCESSED)
    print("Cleaned datasets:", outputs)


def forecast_task():
    output = run_pipeline(PROCESSED / "weekly_demand.csv", OUTPUT / "weekly_forecasts.csv", ROOT / "config" / "settings.yaml")
    print("Forecast output:", output)


def inventory_task():
    settings = load_project_settings(ROOT / "config" / "settings.yaml")
    inventory = pd.read_csv(PROCESSED / "inventory.csv")
    forecasts = pd.read_csv(OUTPUT / "weekly_forecasts.csv")
    plan = calculate_inventory_plan(inventory, forecasts, float(settings.get("inventory", {}).get("service_level", 0.95)))
    output = OUTPUT / "inventory_plan.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    plan.to_csv(output, index=False)
    print("Inventory plan output:", output)


default_args = {"owner": "retail-demand", "retries": 2, "retry_delay": timedelta(minutes=2), "on_failure_callback": failure_callback}

with DAG(dag_id="retail_demand_forecasting", start_date=datetime(2024, 1, 1), schedule=None, catchup=False, default_args=default_args, tags=["retail", "forecasting"]) as dag:
    validate = PythonOperator(task_id="validate_raw_data", python_callable=validate_task)
    clean = PythonOperator(task_id="clean_datasets", python_callable=clean_task)
    forecast = PythonOperator(task_id="generate_weekly_forecasts", python_callable=forecast_task)
    inventory = PythonOperator(task_id="calculate_inventory_plan", python_callable=inventory_task)
    validate >> clean >> forecast >> inventory
