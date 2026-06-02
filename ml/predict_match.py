"""Predict a single international match using the saved model.

Example:
    python ml/predict_match.py --home-team Argentina --away-team Brazil --neutral true --stage group
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


MODEL_PATH = Path("ml") / "worldcup_model.pkl"
CLASS_NAMES = {0: "away_win", 1: "draw", 2: "home_win"}
SIMULATION_COUNT = 100_000


def outcome_labels(home_team: str, away_team: str, neutral: bool) -> dict[int, str]:
    if neutral:
        return {0: f"{away_team} win", 1: "draw", 2: f"{home_team} win"}
    return {0: "away win", 1: "draw", 2: "home win"}


def score_labels(home_team: str, away_team: str, neutral: bool) -> tuple[str, str]:
    if neutral:
        return home_team, away_team
    return "home", "away"


def run_monte_carlo(probabilities: dict[int, float], home_team: str, away_team: str, neutral: bool) -> tuple[dict[str, int], dict[tuple[int, int], int]]:
    outcome_keys = np.array([0, 1, 2])
    outcome_probs = np.array([probabilities.get(0, 0.0), probabilities.get(1, 0.0), probabilities.get(2, 0.0)], dtype=float)
    if outcome_probs.sum() <= 0:
        outcome_probs = np.array([1 / 3, 1 / 3, 1 / 3], dtype=float)
    else:
        outcome_probs = outcome_probs / outcome_probs.sum()

    winner_counts = {home_team if neutral else "home": 0, away_team if neutral else "away": 0, "draw": 0}
    score_counts: dict[tuple[int, int], int] = {}

    for outcome in np.random.choice(outcome_keys, size=SIMULATION_COUNT, p=outcome_probs):
        if outcome == 1:
            home_goals = int(np.random.poisson(1.25))
            away_goals = home_goals
            winner_counts["draw"] += 1
        elif outcome == 2:
            home_goals = int(np.random.poisson(1.95))
            away_goals = int(np.random.poisson(0.85))
            if home_goals <= away_goals:
                home_goals = away_goals + 1
            winner_counts[home_team if neutral else "home"] += 1
        else:
            home_goals = int(np.random.poisson(0.85))
            away_goals = int(np.random.poisson(1.95))
            if away_goals <= home_goals:
                away_goals = home_goals + 1
            winner_counts[away_team if neutral else "away"] += 1

        score = (home_goals, away_goals)
        score_counts[score] = score_counts.get(score, 0) + 1

    return winner_counts, score_counts


def knockout_profile(probabilities: dict[int, float]) -> tuple[np.ndarray, float, float]:
    home_prob = max(float(probabilities.get(2, 0.0)), 0.0)
    draw_prob = max(float(probabilities.get(1, 0.0)), 0.0)
    away_prob = max(float(probabilities.get(0, 0.0)), 0.0)

    total = home_prob + draw_prob + away_prob
    if total <= 0:
        home_prob = draw_prob = away_prob = 1.0 / 3.0
    else:
        home_prob /= total
        draw_prob /= total
        away_prob /= total

    strength_total = home_prob + away_prob
    if strength_total <= 0:
        closeness = 1.0
    else:
        closeness = 1.0 - abs(home_prob - away_prob) / strength_total
    closeness = float(np.clip(closeness, 0.0, 1.0))

    # Close knockout games should feel tighter and draw-prone.
    draw_boost = 0.18 * closeness
    draw_prob += draw_boost
    home_prob = max(home_prob * (1.0 - 0.5 * draw_boost), 1e-6)
    away_prob = max(away_prob * (1.0 - 0.5 * draw_boost), 1e-6)

    outcome_probs = np.array([away_prob, draw_prob, home_prob], dtype=float)
    outcome_probs = outcome_probs / outcome_probs.sum()

    if closeness >= 0.75:
        home_mean = 1.05
        away_mean = 1.05
    elif closeness >= 0.45:
        edge = float(np.clip((home_prob - away_prob) * 1.4, -0.25, 0.25))
        home_mean = 1.15 + edge
        away_mean = 1.15 - edge
    else:
        edge = float(np.clip((home_prob - away_prob) * 1.8, -0.45, 0.45))
        home_mean = 1.35 + edge
        away_mean = 0.85 - edge

    home_mean = max(home_mean, 0.55)
    away_mean = max(away_mean, 0.55)
    return outcome_probs, home_mean, away_mean


def resolve_knockout_draw(probabilities: dict[int, float]) -> str:
    home_prob = probabilities.get(2, 0.0)
    away_prob = probabilities.get(0, 0.0)
    total = home_prob + away_prob
    if total <= 0:
        return "home"
    return "home" if np.random.random() < (home_prob / total) else "away"


def apply_history_adjustments(probabilities: dict[int, float], sample_row: pd.Series) -> dict[int, float]:
    """Adjust knockout probabilities using team tournament-history features.

    This down-weights teams that historically underperform in knockouts/finals
    (low `knockout_win_rate_last_10_matches` or very long `years_since_last_major_win`).
    Returns a new probability mapping for classes {0: away, 1: draw, 2: home}.
    """
    probs = probabilities.copy()
    home_rate = float(sample_row.get("home_knockout_win_rate_last_10_matches", 0.5) or 0.5)
    away_rate = float(sample_row.get("away_knockout_win_rate_last_10_matches", 0.5) or 0.5)
    home_years = float(sample_row.get("home_years_since_last_major_win", 999.0) or 999.0)
    away_years = float(sample_row.get("away_years_since_last_major_win", 999.0) or 999.0)

    # Base home/away probabilities from model
    home_p = max(float(probs.get(2, 0.0)), 0.0)
    draw_p = max(float(probs.get(1, 0.0)), 0.0)
    away_p = max(float(probs.get(0, 0.0)), 0.0)

    # Relative knockout experience adjustment (scale in [-0.2, 0.2])
    rate_delta = np.clip(home_rate - away_rate, -1.0, 1.0)
    experience_adj = 0.20 * rate_delta

    # Years-since-last-win penalty: more years -> slight pressure penalty
    years_delta = (away_years - home_years) / 50.0  # normalized roughly to [-~2,2]
    years_adj = np.clip(0.06 * years_delta, -0.06, 0.06)

    home_factor = 1.0 + experience_adj + years_adj
    away_factor = 1.0 - experience_adj - years_adj

    # Keep factors reasonable
    home_factor = float(np.clip(home_factor, 0.7, 1.3))
    away_factor = float(np.clip(away_factor, 0.7, 1.3))

    home_p *= home_factor
    away_p *= away_factor

    # If both teams have very low knockout rate, increase draw probability slightly
    if (home_rate < 0.4) and (away_rate < 0.4):
        draw_p += 0.06

    total = home_p + draw_p + away_p
    if total <= 0:
        return {0: 1 / 3, 1: 1 / 3, 2: 1 / 3}

    home_p /= total
    draw_p /= total
    away_p /= total

    return {0: away_p, 1: draw_p, 2: home_p}


def run_knockout_monte_carlo(
    probabilities: dict[int, float], home_team: str, away_team: str, neutral: bool
) -> tuple[dict[str, int], dict[tuple[int, int], int]]:
    outcome_keys = np.array([0, 1, 2])
    outcome_probs, home_mean_base, away_mean_base = knockout_profile(probabilities)

    winner_counts = {home_team if neutral else "home": 0, away_team if neutral else "away": 0}
    score_counts: dict[tuple[int, int], int] = {}

    for outcome in np.random.choice(outcome_keys, size=SIMULATION_COUNT, p=outcome_probs):
        if outcome == 1:
            home_goals = int(np.random.poisson(home_mean_base))
            away_goals = int(np.random.poisson(away_mean_base))
            if home_goals == away_goals:
                tiebreak_winner = resolve_knockout_draw(probabilities)
                if tiebreak_winner == "home":
                    home_goals = away_goals + 1
                    winner_counts[home_team if neutral else "home"] += 1
                else:
                    away_goals = home_goals + 1
                    winner_counts[away_team if neutral else "away"] += 1
            elif home_goals > away_goals:
                winner_counts[home_team if neutral else "home"] += 1
            else:
                winner_counts[away_team if neutral else "away"] += 1
        elif outcome == 2:
            home_goals = int(np.random.poisson(1.80))
            away_goals = int(np.random.poisson(0.80))
            if home_goals <= away_goals:
                home_goals = away_goals + 1
            winner_counts[home_team if neutral else "home"] += 1
        else:
            home_goals = int(np.random.poisson(0.80))
            away_goals = int(np.random.poisson(1.80))
            if away_goals <= home_goals:
                away_goals = home_goals + 1
            winner_counts[away_team if neutral else "away"] += 1

        score = (home_goals, away_goals)
        score_counts[score] = score_counts.get(score, 0) + 1

    return winner_counts, score_counts


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
    else:
        df["year"] = 2023

    if "neutral" in df.columns:
        if df["neutral"].dtype == bool:
            df["neutral"] = df["neutral"].astype(bool)
        else:
            df["neutral"] = df["neutral"].map({"true": True, "false": False, "TRUE": True, "FALSE": False}).fillna(df["neutral"]).astype(bool)
    else:
        df["neutral"] = False

    df["is_home"] = ~df["neutral"]

    key_players_df = pd.read_csv("./data/key_players.csv")
    key_players = dict(zip(key_players_df["team"], key_players_df["player"]))
    for team, player in key_players.items():
        col = f"{player}_played"
        df[col] = (((df.get("home_team") == team) | (df.get("away_team") == team))).astype(int)

    return df


def swap_home_away_features(df: pd.DataFrame) -> pd.DataFrame:
    swapped = df.copy()

    home_cols = [col for col in swapped.columns if col.startswith("home_")]
    away_cols = [col for col in swapped.columns if col.startswith("away_")]

    for home_col in home_cols:
        away_col = "away_" + home_col[len("home_"):]
        if away_col in swapped.columns:
            home_values = swapped[home_col].copy()
            swapped[home_col] = swapped[away_col]
            swapped[away_col] = home_values

    return swapped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home-team", required=True)
    parser.add_argument("--away-team", required=True)
    parser.add_argument("--neutral", default="true", help="true/false")
    parser.add_argument("--stage", default="group", choices=["group", "knockout"], help="group or knockout")
    parser.add_argument("--date", default="2023-01-01", help="Optional date used to derive year")
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        raise SystemExit(f"Missing model file: {MODEL_PATH}. Run ml/train_predictive_model.py first.")

    model = joblib.load(MODEL_PATH)

    # Try to load actual match data from test/train sets (with team features)
    sample = None
    train_pq = Path("data") / "processed" / "train_with_features.parquet"
    test_pq = Path("data") / "processed" / "test_with_features.parquet"
    
    if train_pq.exists() or test_pq.exists():
        dfs = []
        if train_pq.exists():
            dfs.append(pd.read_parquet(train_pq))
        if test_pq.exists():
            dfs.append(pd.read_parquet(test_pq))
        if dfs:
            all_matches = pd.concat(dfs, ignore_index=False)
            # Find a match with these teams
            matching = all_matches[
                (all_matches["home_team"] == args.home_team) & 
                (all_matches["away_team"] == args.away_team)
            ]
            if len(matching) > 0:
                sample = matching.iloc[[0]].copy()

    # Fallback to synthetic sample if no real match found
    if sample is None:
        sample = pd.DataFrame(
            [
                {
                    "home_team": args.home_team,
                    "away_team": args.away_team,
                    "neutral": args.neutral,
                    "date": args.date,
                }
            ]
        )
        sample = add_features(sample)

    feature_names = list(getattr(model, "_feature_names_list", []))
    if not feature_names:
        raise SystemExit("Saved model does not expose feature names; retrain with the current training script.")

    for feature in feature_names:
        if feature not in sample.columns:
            sample[feature] = 0

    sample_X = sample[feature_names].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy()
    proba = model.predict_proba(sample_X)[0]

    if bool(sample["neutral"].iloc[0]):
        swapped_sample = sample.copy()
        if "home_team" in swapped_sample.columns and "away_team" in swapped_sample.columns:
            home_team_swapped = swapped_sample["home_team"].copy()
            swapped_sample["home_team"] = swapped_sample["away_team"]
            swapped_sample["away_team"] = home_team_swapped
        swapped_sample = swap_home_away_features(swapped_sample)
        for feature in feature_names:
            if feature not in swapped_sample.columns:
                swapped_sample[feature] = 0
        swapped_X = swapped_sample[feature_names].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy()
        swapped_proba = model.predict_proba(swapped_X)[0]
        proba = (proba + swapped_proba) / 2.0

    pred = int(model.classes_[int(np.argmax(proba))])
    class_to_proba = {int(cls): float(prob) for cls, prob in zip(model.classes_, proba)}
    labels = outcome_labels(args.home_team, args.away_team, bool(sample['neutral'].iloc[0]))
    if args.stage == "knockout":
        winner_counts, score_counts = run_knockout_monte_carlo(class_to_proba, args.home_team, args.away_team, bool(sample['neutral'].iloc[0]))
        likely_winner = max(winner_counts.items(), key=lambda item: item[1])[0]
    else:
        winner_counts, score_counts = run_monte_carlo(class_to_proba, args.home_team, args.away_team, bool(sample['neutral'].iloc[0]))
        likely_winner = max(winner_counts.items(), key=lambda item: item[1])[0]
    likely_score = max(score_counts.items(), key=lambda item: item[1])[0]
    score_home_name, score_away_name = score_labels(args.home_team, args.away_team, bool(sample['neutral'].iloc[0]))

    print(f"Match: {args.home_team} vs {args.away_team}")
    print(f"Neutral: {bool(sample['neutral'].iloc[0])}")
    print(f"Stage: {args.stage}")
    print(f"ML prediction: {labels.get(pred, CLASS_NAMES.get(pred, pred))}")
    print(f"Prob {labels.get(0, 'away win')}: {class_to_proba.get(0, 0.0):.3f}")
    print(f"Prob {labels.get(1, 'draw')}: {class_to_proba.get(1, 0.0):.3f}")
    print(f"Prob {labels.get(2, 'home win')}: {class_to_proba.get(2, 0.0):.3f}")
    if args.stage == "knockout":
        print(f"Monte Carlo real prediction: {likely_winner}")
        print(f"ML score: {score_home_name} {likely_score[0]} - {likely_score[1]} {score_away_name}")
    else:
        print(f"Monte Carlo winner: {likely_winner}")
        print(f"Most likely score after {SIMULATION_COUNT:,} sims: {score_home_name} {likely_score[0]} - {likely_score[1]} {score_away_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
