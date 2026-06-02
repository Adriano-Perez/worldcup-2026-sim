"""
Integrate club training data (player profiles, market values, injuries) into national team features.
This creates team-level aggregates (avg market value, injury count, player pool size) to enrich match predictions.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Paths
PLAYER_PROFILES = "data/raw/training data/player_profiles.csv"
PLAYER_MARKET_VALUE = "data/raw/training data/player_market_value.csv"
PLAYER_INJURIES = "data/raw/training data/player_injuries.csv"
TRAIN_PARQUET = "data/processed/train.parquet"
TEST_PARQUET = "data/processed/test.parquet"
OUTPUT_TRAIN = "data/processed/train_with_features.parquet"
OUTPUT_TEST = "data/processed/test_with_features.parquet"

print("Loading player profiles...")
profiles = pd.read_csv(PLAYER_PROFILES)
print(f"  Loaded {len(profiles)} player records")

print("\nLoading player market values...")
market_values = pd.read_csv(PLAYER_MARKET_VALUE)
# Convert date column (it's a string, not unix timestamp despite column name)
market_values['date'] = pd.to_datetime(market_values['date_unix'])
print(f"  Loaded {len(market_values)} market value records")

print("\nLoading player injuries...")
injuries = pd.read_csv(PLAYER_INJURIES)
print(f"  Loaded {len(injuries)} injury records")

# Group player profiles by citizenship to get player count per country
print("\nAggregating player data by country...")
country_profiles = profiles.groupby('citizenship').agg({
    'player_id': 'count',  # player count per country
    'height': 'mean',  # avg height
    'foot': lambda x: (x == 'right').sum() / len(x),  # % right-footed
}).reset_index()
country_profiles.columns = ['country', 'player_count', 'avg_height', 'pct_right_footed']

# Get latest market values per player (most recent value)
print("\nProcessing market values (latest per player)...")
latest_values = market_values.sort_values('date').groupby('player_id').tail(1)

# Merge with profiles to get country for each player
player_values = latest_values.merge(profiles[['player_id', 'citizenship']], on='player_id', how='left')
player_values = player_values.dropna(subset=['citizenship'])

# Aggregate by country
country_market_values = player_values.groupby('citizenship').agg({
    'value': ['mean', 'median', 'sum', 'count']
}).reset_index()
country_market_values.columns = ['country', 'avg_market_value', 'median_market_value', 'total_market_value', 'valued_players']

# Get injury data by country
print("\nProcessing injury data...")
# Merge injuries with profiles to get country
injuries_with_country = injuries.merge(profiles[['player_id', 'citizenship']], on='player_id', how='left')
injuries_with_country = injuries_with_country.dropna(subset=['citizenship'])

# Only count recent injuries (last 2 seasons: 2024/25, 2025/26)
recent_seasons = ['24/25', '25/26', '2024/25', '2025/26']
recent_injuries = injuries_with_country[injuries_with_country['season_name'].isin(recent_seasons)]

country_injuries = recent_injuries.groupby('citizenship').agg({
    'player_id': 'nunique',  # unique injured players
    'days_missed': 'sum',    # total days missed
    'games_missed': 'sum',   # total games missed
}).reset_index()
country_injuries.columns = ['country', 'recent_injured_players', 'total_days_missed', 'total_games_missed']

# Merge all country-level features
print("\nMerging country-level features...")
team_features = country_profiles.merge(country_market_values, on='country', how='left')
team_features = team_features.merge(country_injuries, on='country', how='left')

# Fill NaN values for countries without injury/market data
team_features = team_features.fillna(0)

print("\nTeam features summary:")
print(team_features.head(10))

# Load match data
print("\n" + "="*60)
print("Loading match data and adding features...")

def add_team_features(match_df, team_features):
    """Add home and away team features to match data."""
    # Rename columns for home team
    home_features = team_features.rename(columns={col: f'home_{col}' if col != 'country' else col for col in team_features.columns})
    home_features = home_features.rename(columns={'country': 'home_team'})
    
    # Rename columns for away team
    away_features = team_features.rename(columns={col: f'away_{col}' if col != 'country' else col for col in team_features.columns})
    away_features = away_features.rename(columns={'country': 'away_team'})
    
    # Merge with match data
    match_with_features = match_df.merge(home_features, on='home_team', how='left')
    match_with_features = match_with_features.merge(away_features, on='away_team', how='left')
    
    return match_with_features

# Process training data
print("\nProcessing training data...")
train_df = pd.read_parquet(TRAIN_PARQUET)
print(f"  Original: {len(train_df)} rows")
train_with_features = add_team_features(train_df, team_features)
train_with_features.to_parquet(OUTPUT_TRAIN)
print(f"  Saved to {OUTPUT_TRAIN}")
print(f"  Added columns: {[c for c in train_with_features.columns if 'home_' in c or 'away_' in c]}")

# Process test data
print("\nProcessing test data...")
test_df = pd.read_parquet(TEST_PARQUET)
print(f"  Original: {len(test_df)} rows")
test_with_features = add_team_features(test_df, team_features)
test_with_features.to_parquet(OUTPUT_TEST)
print(f"  Saved to {OUTPUT_TEST}")

print("\n" + "="*60)
print("Integration complete!")
print(f"Train features shape: {train_with_features.shape}")
print(f"Test features shape: {test_with_features.shape}")
print(f"New feature columns: {len([c for c in train_with_features.columns if 'home_' in c or 'away_' in c])}")
