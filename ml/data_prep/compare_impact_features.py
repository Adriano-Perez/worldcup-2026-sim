"""Train and compare models with and without injury-impact features.

This script assumes `data/processed/train_with_features.parquet` and
`data/processed/test_with_features.parquet` already exist.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


DATA_DIR = Path("data") / "processed"
TRAIN_PQ = DATA_DIR / "train_with_features.parquet"
TEST_PQ = DATA_DIR / "test_with_features.parquet"

IMPACT_COLUMNS = [
    "home_attack_impact",
    "home_defense_impact",
    "home_mid_impact",
    "away_attack_impact",
    "away_defense_impact",
    "away_mid_impact",
    "home_key_player_out",
    "away_key_player_out",
]


def outcome_target(df: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.select(
            [df["home_score"] > df["away_score"], df["home_score"] == df["away_score"]],
            [2, 1],
            default=0,
        ).astype(int),
        index=df.index,
    )


def build_features(df: pd.DataFrame, drop_impact: bool) -> tuple[pd.DataFrame, list[str]]:
    frame = df.copy()
    if "date" in frame.columns:
        frame["date"] = pd.to_datetime(frame["date"])
        frame["year"] = frame["date"].dt.year

    if "neutral" in frame.columns:
        frame["neutral"] = frame["neutral"].map({"TRUE": True, "FALSE": False}).fillna(frame["neutral"]).astype(bool)

    frame["is_home"] = ~frame["neutral"]

    base_features = ["neutral", "is_home", "year"]
    team_features = [
        column
        for column in frame.columns
        if (column.startswith("home_") or column.startswith("away_"))
        and column not in {"home_team", "away_team", "home_score", "away_score"}
    ]

    if drop_impact:
        team_features = [column for column in team_features if column not in IMPACT_COLUMNS]

    feature_names = [column for column in base_features + team_features if column in frame.columns]
    X = frame[feature_names].fillna(0).apply(pd.to_numeric, errors="coerce").fillna(0)
    return X, feature_names


def train_and_score(train_df: pd.DataFrame, test_df: pd.DataFrame, drop_impact: bool) -> tuple[float, RandomForestClassifier, list[str]]:
    X_train, feature_names = build_features(train_df, drop_impact=drop_impact)
    X_test, _ = build_features(test_df, drop_impact=drop_impact)
    y_train = outcome_target(train_df)
    y_test = outcome_target(test_df)

    model = RandomForestClassifier(class_weight="balanced", random_state=42, n_estimators=200)
    model.fit(X_train.to_numpy(dtype=np.float64), y_train.to_numpy(dtype=np.int64))
    accuracy = model.score(X_test.to_numpy(dtype=np.float64), y_test.to_numpy(dtype=np.int64))
    model._feature_names_list = feature_names  # type: ignore[attr-defined]
    return float(accuracy), model, feature_names


def print_top_features(model: RandomForestClassifier, feature_names: list[str], title: str) -> None:
    print(f"\n{title}")
    ranked = sorted(zip(feature_names, model.feature_importances_), key=lambda item: item[1], reverse=True)
    for name, importance in ranked[:10]:
        print(f"{name}: {importance:.4f}")


def injury_mask(df: pd.DataFrame) -> pd.Series:
    return df[IMPACT_COLUMNS].fillna(0).sum(axis=1) > 0


def score_subset(model: RandomForestClassifier, df: pd.DataFrame, feature_names: list[str], mask: pd.Series) -> float:
    if int(mask.sum()) == 0:
        return float("nan")
    subset = df.iloc[mask.to_numpy()].copy()
    X, _ = build_features(subset, drop_impact=False)
    X = X[feature_names].fillna(0).apply(pd.to_numeric, errors="coerce").fillna(0)
    y = outcome_target(subset)
    return float(model.score(X.to_numpy(dtype=np.float64), y.to_numpy(dtype=np.int64)))


def main() -> int:
    if not TRAIN_PQ.exists() or not TEST_PQ.exists():
        raise SystemExit("Missing processed parquet files. Run ml/add_key_player_availability.py first.")

    train_df = pd.read_parquet(TRAIN_PQ)
    test_df = pd.read_parquet(TEST_PQ)

    impact_accuracy, impact_model, impact_features = train_and_score(train_df, test_df, drop_impact=False)
    baseline_accuracy, baseline_model, baseline_features = train_and_score(train_df, test_df, drop_impact=True)

    injured = injury_mask(test_df)
    clean = ~injured
    impact_injured_accuracy = score_subset(impact_model, test_df, impact_features, injured)
    baseline_injured_accuracy = score_subset(baseline_model, test_df, baseline_features, injured)
    impact_clean_accuracy = score_subset(impact_model, test_df, impact_features, clean)
    baseline_clean_accuracy = score_subset(baseline_model, test_df, baseline_features, clean)

    print(f"Impact features accuracy:   {impact_accuracy:.4f}")
    print(f"Baseline accuracy:          {baseline_accuracy:.4f}")
    print(f"Delta:                     {impact_accuracy - baseline_accuracy:+.4f}")
    print(f"Injured rows:               {int(injured.sum())}")
    print(f"Clean rows:                 {int(clean.sum())}")
    print(f"Impact on injured rows:     {impact_injured_accuracy:.4f}")
    print(f"Baseline on injured rows:    {baseline_injured_accuracy:.4f}")
    print(f"Impact on clean rows:       {impact_clean_accuracy:.4f}")
    print(f"Baseline on clean rows:     {baseline_clean_accuracy:.4f}")

    print_top_features(impact_model, impact_features, "Top impact-model features")
    print_top_features(baseline_model, baseline_features, "Top baseline-model features")

    if impact_accuracy >= baseline_accuracy:
        print("\nRecommendation: keep the impact features in the main training pipeline.")
    else:
        print("\nRecommendation: impact features did not improve test accuracy on this split.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())