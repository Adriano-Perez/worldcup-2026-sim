"""
Train a predictive model for World Cup matches using only features available before the match.
Add your own features (player info, trends, elevation, etc.) as you go!
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import joblib
from pathlib import Path
DATA_DIR = Path("data") / "processed"
CLASS_NAMES = {0: "away_win", 1: "draw", 2: "home_win"}


def outcome_labels(home_team: str, away_team: str, neutral: bool) -> dict[int, str]:
    if neutral:
        return {0: f"{away_team} win", 1: "draw", 2: f"{home_team} win"}
    return {0: "away win", 1: "draw", 2: "home win"}


# 1. Load cleaned match data (prefer train/test splits if present)
train_pq = DATA_DIR / "train_with_features.parquet"
test_pq = DATA_DIR / "test_with_features.parquet"

# Fallback to non-enriched versions if enriched versions don't exist
if not train_pq.exists() or not test_pq.exists():
    train_pq = DATA_DIR / "train.parquet"
    test_pq = DATA_DIR / "test.parquet"

if train_pq.exists() and test_pq.exists():
    train_df = pd.read_parquet(train_pq)
    test_df = pd.read_parquet(test_pq)
else:
    print("train/test parquet not found, falling back to matches.parquet and an 80/20 split")
    matches = pd.read_parquet("data/processed/matches.parquet")
    train_df, test_df = train_test_split(matches, test_size=0.2, random_state=42)


# Utility to add features used by this simple model
def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # ensure date column is datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
    else:
        df["year"] = 0

    # (removed random_factor to avoid leakage/randomness in features)

    # neutral/is_home heuristic
    host_teams = ["Mexico", "Canada", "USA"]

    def is_true_home(row):
        return (
            (row.get("home_team") in host_teams)
            and (row.get("country") == row.get("home_team"))
            and (row.get("tournament") == "FIFA World Cup")
        )

    if "neutral" in df.columns:
        # assume neutral already boolean-like; coerce
        df["neutral"] = df["neutral"].map({"TRUE": True, "FALSE": False}).fillna(df["neutral"]).astype(bool)
    else:
        df["neutral"] = ~df.apply(is_true_home, axis=1)

    df["is_home"] = ~df["neutral"]

    # Load key players and add indicator columns
    key_players_df = pd.read_csv("./data/key_players.csv")
    key_players = dict(zip(key_players_df["team"], key_players_df["player"]))
    for team, player in key_players.items():
        col = f"{player}_played"
        df[col] = (((df.get("home_team") == team) | (df.get("away_team") == team))).astype(int)

    return df


train_df = add_features(train_df)
test_df = add_features(test_df)

# Build feature list: use only features that exist in the parquets
# (Avoid _played columns since they're not persisted to parquet)
base_features = ["neutral", "is_home", "year"]

# Add team-level features that actually exist (from integrate_club_features.py and add_player_elo.py)
team_features = [c for c in train_df.columns if (c.startswith("home_") or c.startswith("away_")) 
                 and c not in ["home_team", "away_team", "home_score", "away_score"]]

# Only use features that exist in both train and test
all_features = [f for f in base_features + team_features if f in train_df.columns and f in test_df.columns]

X_train = train_df[all_features].fillna(0)
X_test = test_df[all_features].fillna(0)

# Ensure all features are numeric
X_train = X_train.apply(pd.to_numeric, errors='coerce').fillna(0)
X_test = X_test.apply(pd.to_numeric, errors='coerce').fillna(0)

# 3-class target: 0 = away win, 1 = draw, 2 = home win
def make_target(df: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.select(
            [df["home_score"] > df["away_score"], df["home_score"] == df["away_score"]],
            [2, 1],
            default=0,
        ).astype(int),
        index=df.index
    )

y_train = make_target(train_df)
y_test = make_target(test_df)

# Train model with balanced class weights to better predict upsets
model = RandomForestClassifier(class_weight='balanced', random_state=42, n_estimators=200)
model.fit(X_train.to_numpy(dtype=np.float64), y_train.to_numpy(dtype=np.int64))

# Store feature names as a custom attribute
model._feature_names_list = all_features  # type: ignore

# Evaluate
acc = model.score(X_test.to_numpy(), y_test.to_numpy())  # type: ignore
print("Test Accuracy:", acc)
print("Class mapping:", CLASS_NAMES)

# Save model
OUT_MODEL = Path("ml") / "worldcup_model.pkl"
OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, OUT_MODEL)
print(f"Saved model -> {OUT_MODEL}")

# Predict a single match from the test set (first row)
sample = test_df.iloc[[0]]
sample_X = sample[all_features].apply(pd.to_numeric, errors="coerce").fillna(0)
pred = model.predict(sample_X.to_numpy())[0]  # type: ignore
pred_proba = model.predict_proba(sample_X.to_numpy())[0]  # type: ignore
actual = int(np.select(
    [sample["home_score"].iloc[0] > sample["away_score"].iloc[0], sample["home_score"].iloc[0] == sample["away_score"].iloc[0]],
    [2, 1],
    default=0,
))

print("\nSingle-match prediction (first test row):")
date_val = sample['date'].iloc[0] if 'date' in sample.columns else None
labels = outcome_labels(str(sample['home_team'].iloc[0]), str(sample['away_team'].iloc[0]), bool(sample['neutral'].iloc[0]))
print(f"{sample['home_team'].iloc[0]} vs {sample['away_team'].iloc[0]} on {date_val}")
print(f"Actual: {labels.get(actual, CLASS_NAMES.get(actual, actual))}")
print(f"Predicted: {labels.get(int(pred), CLASS_NAMES.get(int(pred), pred))}")
print(
    f"Prob {labels.get(0, 'away win')}: {pred_proba[list(model.classes_).index(0)]:.3f}, "
    f"prob {labels.get(1, 'draw')}: {pred_proba[list(model.classes_).index(1)]:.3f}, "
    f"prob {labels.get(2, 'home win')}: {pred_proba[list(model.classes_).index(2)]:.3f}"
)

print("\nFeature importances:")
importances = model.feature_importances_
for name, importance in sorted(zip(all_features, importances), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{name}: {importance:.4f}")

