import json
from pathlib import Path
import pandas as pd

from backend.forecasting import evaluate_holt_winters_sample
from backend.model_selection import score_predictions, select_model
from backend.random_forest import train_random_forest

ROOT = Path(__file__).resolve().parents[1]


def run(input_path=ROOT / "data/processed/weekly_demand.csv", output_dir=ROOT / "outputs/forecasting", validation_weeks=8, top_n=20):
    data = pd.read_csv(input_path)
    metrics, predictions, report = evaluate_holt_winters_sample(data, validation_weeks, top_n)
    rf_scored, rf_report = train_random_forest(data, validation_weeks, top_n, artifact_dir=ROOT / "models/random_forest")
    rf_scored = rf_scored.rename(columns={"units_sold": "actual"})
    rf_scored["model"] = "random_forest"
    predictions = pd.concat([predictions, rf_scored[["model", "week_start", "store_id", "product_id", "actual", "prediction"]]], ignore_index=True)
    scored = score_predictions(predictions)
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    scored.to_csv(output_dir / "model_comparison_metrics.csv", index=False)
    predictions.to_csv(output_dir / "model_comparison_predictions.csv", index=False)
    report.update({"selected_model": select_model(scored), "evaluation_series": int(predictions[["store_id", "product_id"]].drop_duplicates().shape[0]), "random_forest": rf_report})
    (output_dir / "model_selection.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return scored, report


if __name__ == "__main__":
    print(run()[0].to_string(index=False))
