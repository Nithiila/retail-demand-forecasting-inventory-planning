from pathlib import Path
import pandas as pd
from backend.random_forest import train_random_forest

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    scored, metadata = train_random_forest(pd.read_csv(ROOT / "data/processed/weekly_demand.csv"), validation_weeks=8, top_n=20, artifact_dir=ROOT / "models/random_forest")
    print(metadata["metrics"])
