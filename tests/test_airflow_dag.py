import pytest

pytest.importorskip("airflow")

from airflow.models import DagBag


def test_retail_dag_imports_and_dependencies():
    bag = DagBag(dag_folder="airflow", include_examples=False)
    assert not bag.import_errors
    dag = bag.get_dag("retail_demand_forecasting")
    assert dag is not None
    assert dag.task_ids == ["validate_raw_data", "clean_datasets", "generate_weekly_forecasts", "calculate_inventory_plan"]
    assert dag.get_task("clean_datasets").upstream_task_ids == {"validate_raw_data"}
    assert dag.get_task("generate_weekly_forecasts").upstream_task_ids == {"clean_datasets"}
    assert dag.get_task("calculate_inventory_plan").upstream_task_ids == {"generate_weekly_forecasts"}
