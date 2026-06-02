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
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "data" / "raw" / "results.csv"
OUT = REPO_ROOT / "data" / "processed" / "matches.parquet"
TEAM_HISTORY_OUT = REPO_ROOT / "data" / "processed" / "team_tournament_history.parquet"
def compute_team_tournament_history(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-team historical features used to model high-pressure performance.

    Features produced:
      - team: team name
      - years_since_last_major_win: years since last final win (finals detected by stage containing 'final')
      - finals_appearances_last_20yrs: count of final appearances in last 20 years
      - knockout_win_rate_last_10_matches: win rate in the last 10 knockout matches
      - semifinal_appearances_last_20yrs: semifinals reached in last 20 years

    The function is intentionally conservative about missing data and uses textual
    matching on the `stage` column to detect finals/semis/knockouts so it works
    across the historical CSV formatting variations.
    """
    df = df.copy()
    # Ensure date column is datetime
    df["date"] = pd.to_datetime(df["date"])
    latest = df["date"].max()
    year_back_20 = latest - pd.DateOffset(years=20)

    # Ensure stage exists (some raw exports omit stage)
    if "stage" not in df.columns:
        df["stage"] = ""
    # Normalize stage text
    df["stage_norm"] = df["stage"].fillna("").str.lower()
    df["is_final"] = df["stage_norm"].str.contains("final")
    df["is_semi"] = df["stage_norm"].str.contains("semi")
    # Consider knockout as stage not containing 'group' and not empty
    df["is_knockout"] = (~df["stage_norm"].str.contains("group")) & (df["stage_norm"] != "")

    # determine winners (na when draw)
    def winner_row(r: pd.Series) -> str | None:
        if r["home_score"] > r["away_score"]:
            return r["home_team"]
        if r["away_score"] > r["home_score"]:
            return r["away_team"]
        return None

    df["winner"] = df.apply(winner_row, axis=1)

    teams = pd.unique(df[["home_team", "away_team"]].values.ravel("K"))
    rows: list[dict] = []

    for team in teams:
        team_mask_home = df["home_team"] == team
        team_mask_away = df["away_team"] == team
        team_mask = team_mask_home | team_mask_away

        # Finals and semis overall
        finals = df[team_mask & df["is_final"]]
        semis = df[team_mask & df["is_semi"]]

        # Finals in last 20 years
        finals_20 = finals[finals["date"] >= year_back_20]
        semis_20 = semis[semis["date"] >= year_back_20]

        # Last final win date
        final_wins = finals[finals["winner"] == team]
        if not final_wins.empty:
            last_win_date = final_wins["date"].max()
            years_since_last_major_win = (latest - last_win_date).days / 365.25
        else:
            years_since_last_major_win = np.nan

        # Last 20 years semifinal/final counts
        finals_appearances_last_20yrs = int(len(finals_20))
        semifinal_appearances_last_20yrs = int(len(semis_20))

        # Knockout win rate in last 10 knockout matches
        kn_mask = team_mask & df["is_knockout"]
        team_knockouts = df[kn_mask].sort_values(by=["date"], ascending=[False])
        last10 = team_knockouts.head(10)
        wins = (last10["winner"] == team).sum()
        total_considered = int(last10["winner"].notna().sum())
        knockout_win_rate_last_10_matches = float(wins) / total_considered if total_considered > 0 else np.nan

        rows.append({
            "team": team,
            "years_since_last_major_win": float(years_since_last_major_win) if not np.isnan(years_since_last_major_win) else np.nan,
            "finals_appearances_last_20yrs": finals_appearances_last_20yrs,
            "semifinal_appearances_last_20yrs": semifinal_appearances_last_20yrs,
            "knockout_win_rate_last_10_matches": knockout_win_rate_last_10_matches,
            "as_of_date": latest,
        })

    out = pd.DataFrame(rows)
    # Fill missing numeric values with sensible defaults
    out["years_since_last_major_win"] = out["years_since_last_major_win"].fillna(999.0)
    out["knockout_win_rate_last_10_matches"] = out["knockout_win_rate_last_10_matches"].fillna(0.5)

    return out


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
    # Also compute and write team-level tournament history features
    team_hist = compute_team_tournament_history(df)
    TEAM_HISTORY_OUT.parent.mkdir(parents=True, exist_ok=True)
    team_hist.to_parquet(TEAM_HISTORY_OUT, index=False)

    print(f"Wrote team history -> {TEAM_HISTORY_OUT}")

    print(f"Wrote {len(df):,} rows -> {OUT}")


if __name__ == "__main__":
    main()
