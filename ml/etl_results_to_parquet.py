"""
Read martj42 `data/raw/results.csv` and write a cleaned `data/processed/matches.parquet`.

Run from repo root:
  python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
  pip install -r requirements.txt
  python ml/etl_results_to_parquet.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "data" / "raw" / "results.csv"
OUT = REPO_ROOT / "data" / "processed" / "matches.parquet"


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"Missing input file: {RAW}")

    df = pd.read_csv(RAW, parse_dates=["date"])

    # Drop rows without a recorded score (keeps training labels valid)
    df = df.dropna(subset=["home_score", "away_score"])

    # Normalize dtypes
    df["home_score"] = df["home_score"].astype("int64")
    df["away_score"] = df["away_score"].astype("int64")
    df["neutral"] = df["neutral"].map({"TRUE": True, "FALSE": False}).astype("bool")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)

    print(f"Wrote {len(df):,} rows -> {OUT}")


if __name__ == "__main__":
    main()
