import json
from pathlib import Path
import pandas as pd

from backend.forecasting import evaluate_holt_winters_sample

ROOT = Path(__file__).resolve().parents[1]


def run(input_path=ROOT / "data" / "processed" / "weekly_demand.csv", output_dir=ROOT / "outputs" / "forecasting", validation_weeks=8, top_n=20):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics, predictions, report = evaluate_holt_winters_sample(pd.read_csv(input_path), validation_weeks, top_n)
    metrics.to_csv(output_dir / "holt_winters_comparison_metrics.csv", index=False)
    predictions.to_csv(output_dir / "holt_winters_comparison_predictions.csv", index=False)
    (output_dir / "holt_winters_sampling_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(run().to_string(index=False))
