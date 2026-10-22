from pathlib import Path
import pandas as pd

from backend.forecasting import evaluate_baselines

ROOT = Path(__file__).resolve().parents[1]


def run(input_path=ROOT / "data" / "processed" / "weekly_demand.csv", output_dir=ROOT / "outputs" / "forecasting", validation_weeks=8):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics, predictions = evaluate_baselines(pd.read_csv(input_path), validation_weeks=validation_weeks)
    metrics.to_csv(output_dir / "baseline_metrics.csv", index=False)
    predictions.to_csv(output_dir / "baseline_predictions.csv", index=False)
    return metrics


if __name__ == "__main__":
    print(run().to_string(index=False))
