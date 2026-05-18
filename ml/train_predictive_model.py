"""
Train a predictive model for World Cup matches using only features available before the match.
Add your own features (player info, trends, elevation, etc.) as you go!
"""


import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import numpy as np


# 1. Load cleaned match data
matches = pd.read_parquet("data/processed/matches.parquet")


# 2. Add new features
matches["random_factor"] = np.random.rand(len(matches))
matches["year"] = matches["date"].dt.year

# Set 'neutral' to False for true home games for Mexico, Canada, USA in group stage World Cup matches, True otherwise
host_teams = ["Mexico", "Canada", "USA"]
def is_true_home(row):
    return (
        (row["home_team"] in host_teams)
        and (row["country"] == row["home_team"])
        and (row["tournament"] == "FIFA World Cup")
        # Optionally, add a check for group stage if you have that info
    )
matches["neutral"] = ~matches.apply(is_true_home, axis=1)
matches["is_home"] = ~matches["neutral"]

# Load key players
key_players_df = pd.read_csv("./data/key_players.csv")
key_players = dict(zip(key_players_df["team"], key_players_df["player"]))

# Add a column for each key player
for team, player in key_players.items():
    matches[f"{player}_played"] = ((matches["home_team"] == team) | (matches["away_team"] == team)).astype(int)

# Build feature set
player_cols = [f"{player}_played" for player in key_players.values()]
X = matches[player_cols + ["neutral", "random_factor", "is_home", "year"]]  # Add/remove features as you wish


y = (matches["home_score"] > matches["away_score"]).astype(int)  # 1 if home win, 0 otherwise

# 4. Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)


# 6. Evaluate
print("Accuracy:", model.score(X_test, y_test))

# 7. Show feature importances
importances = model.feature_importances_
feature_names = X.columns
feat_imp = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
print("\nFeature importances:")
for name, importance in feat_imp:
    print(f"{name}: {importance:.4f}")

# 7. TODO: Save your model for later use (optional)
# import joblib
# joblib.dump(model, "../ml/worldcup_model.pkl")
