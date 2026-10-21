"""Build forecasting features from processed weekly demand."""

from pathlib import Path

import pandas as pd

from backend.features import add_demand_features


ROOT = Path(__file__).resolve().parents[1]


def build_features(input_path: str | Path = ROOT / "data" / "processed" / "weekly_demand.csv", output_path: str | Path = ROOT / "data" / "processed" / "weekly_demand_features.csv") -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features = add_demand_features(pd.read_csv(input_path))
    features.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    print(build_features())
