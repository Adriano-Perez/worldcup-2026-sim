"""Integrate per-team tournament history into existing match feature parquet files.

This script reads `data/processed/team_tournament_history.parquet` and merges
the team-level features into `data/processed/train_with_features.parquet` and
`data/processed/test_with_features.parquet` as `home_*` and `away_*` columns.

Run from repo root:
  python ml/integrate_team_history.py
"""
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PROC = REPO_ROOT / "data" / "processed"
TEAM_HISTORY = PROC / "team_tournament_history.parquet"
TRAIN_F = PROC / "train_with_features.parquet"
TEST_F = PROC / "test_with_features.parquet"


def integrate_one(src: Path, out: Path, team_hist: pd.DataFrame) -> None:
    df = pd.read_parquet(src)

    # Prepare home and away history tables
    home_hist = team_hist.add_prefix("home_").rename(columns={"home_team": "home_team"})
    away_hist = team_hist.add_prefix("away_").rename(columns={"away_team": "away_team"})

    # Merge
    out_df = df.merge(home_hist, on="home_team", how="left")
    out_df = out_df.merge(away_hist, on="away_team", how="left")

    # Fill sensible defaults where missing
    if "home_knockout_win_rate_last_10_matches" in out_df.columns:
        out_df["home_knockout_win_rate_last_10_matches"] = out_df["home_knockout_win_rate_last_10_matches"].fillna(0.5)
    if "away_knockout_win_rate_last_10_matches" in out_df.columns:
        out_df["away_knockout_win_rate_last_10_matches"] = out_df["away_knockout_win_rate_last_10_matches"].fillna(0.5)

    out_df.to_parquet(out, index=False)
    print(f"Updated {out} ({len(out_df)} rows)")


def main() -> None:
    if not TEAM_HISTORY.exists():
        raise SystemExit(f"Missing team history: {TEAM_HISTORY}")
    team_hist = pd.read_parquet(TEAM_HISTORY)

    if TRAIN_F.exists():
        integrate_one(TRAIN_F, TRAIN_F, team_hist)
    else:
        print(f"Skipping missing {TRAIN_F}")

    if TEST_F.exists():
        integrate_one(TEST_F, TEST_F, team_hist)
    else:
        print(f"Skipping missing {TEST_F}")


if __name__ == "__main__":
    main()
