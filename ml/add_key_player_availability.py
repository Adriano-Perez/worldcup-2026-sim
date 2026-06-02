"""
Mark key player availability for each match using player_injuries and player_profiles.
Adds `home_key_player_out` and `away_key_player_out` (0/1) to `train_with_features.parquet` and `test_with_features.parquet`.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("data") / "processed"
TRAIN_PQ = DATA_DIR / "train_with_features.parquet"
TEST_PQ = DATA_DIR / "test_with_features.parquet"
KEY_PLAYERS = Path("data") / "key_players.csv"
PROFILES = Path("data") / "raw" / "training data" / "player_profiles.csv"
INJURIES = Path("data") / "raw" / "training data" / "player_injuries.csv"

print("Loading files...")
train = pd.read_parquet(TRAIN_PQ)
test = pd.read_parquet(TEST_PQ)
key_df = pd.read_csv(KEY_PLAYERS)
profiles = pd.read_csv(PROFILES, usecols=["player_id", "player_name", "player_slug"])  # smaller read
injuries = pd.read_csv(str(INJURIES), parse_dates=["from_date", "end_date"])

# Normalize player_name for matching
profiles["player_name_norm"] = profiles["player_name"].str.replace(r"\s*\(.*\)$", "", regex=True).str.strip()

# Build mapping team -> player_id (try exact match, then substring match)
team_to_playerid = {}
for _, row in key_df.iterrows():
    team = row["team"]
    player = str(row["player"]).strip()
    # exact name match
    match = profiles[profiles["player_name_norm"].str.lower() == player.lower()]
    if len(match) == 0:
        # try slug match
        slug = player.lower().replace(" ", "-")
        match = profiles[profiles["player_slug"].str.lower() == slug]
    if len(match) == 0:
        # try contains
        match = profiles[profiles["player_name_norm"].str.lower().str.contains(player.lower(), na=False)]
    if len(match) >= 1:
        pid = int(match.iloc[0]["player_id"])
        team_to_playerid[team] = pid
    else:
        team_to_playerid[team] = None

print("Mapped key players (team -> player_id):")
for k, v in team_to_playerid.items():
    print(k, v)

# Helper to check availability
def is_player_out(player_id, match_date):
    if pd.isna(player_id):
        return False
    recs = injuries[injuries["player_id"] == player_id]
    if recs.empty:
        return False
    # check any injury covering match_date
    mask = (~recs["from_date"].isna()) & (~recs["end_date"].isna())
    recs = recs[mask]
    for _, r in recs.iterrows():
        if r["from_date"] <= match_date <= r["end_date"]:
            return True
    return False

# Add columns to df
def add_availability(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    home_out = []
    away_out = []
    for _, r in df.iterrows():
        home_team = r.get("home_team")
        away_team = r.get("away_team")
        d = r.get("date")
        home_pid = team_to_playerid.get(home_team)
        away_pid = team_to_playerid.get(away_team)
        home_out.append(1 if is_player_out(home_pid, d) else 0)
        away_out.append(1 if is_player_out(away_pid, d) else 0)
    df["home_key_player_out"] = home_out
    df["away_key_player_out"] = away_out
    return df

print("Adding availability to train...")
train2 = add_availability(train)
train2.to_parquet(TRAIN_PQ)
print("Saved updated train_with_features.parquet")

print("Adding availability to test...")
test2 = add_availability(test)
test2.to_parquet(TEST_PQ)
print("Saved updated test_with_features.parquet")

print("Done.")
