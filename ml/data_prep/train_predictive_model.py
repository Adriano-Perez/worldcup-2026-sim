"""Train model that ACTUALLY differentiates teams."""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from xgboost import XGBClassifier

print("Loading...")
df = pd.read_parquet('data/processed/train_fixed.parquet')
test = pd.read_parquet('data/processed/test_fixed.parquet')
df = pd.concat([df, test], ignore_index=True)

# Only major tournaments since 2000
major = ['FIFA World Cup','FIFA World Cup qualification','UEFA Euro','UEFA Euro qualification',
         'Copa América','African Cup of Nations','AFC Asian Cup','Gold Cup',
         'UEFA Nations League','CONCACAF Nations League','Confederations Cup','Oceania Nations Cup','Friendly']
df = df[df['tournament'].isin(major)]
df['year'] = pd.to_datetime(df['date']).dt.year
df = df[df['year'] >= 2000]
print(f"Matches since 2000: {len(df)}")

# Target
df['target'] = 0
df.loc[df['home_score'] == df['away_score'], 'target'] = 1
df.loc[df['home_score'] > df['away_score'], 'target'] = 2

# SIMPLE features that work for ANY team
df['pts_gap'] = df['home_fifa_points'].fillna(1500) - df['away_fifa_points'].fillna(1500)
df['rank_gap'] = df['away_fifa_rank'].fillna(100) - df['home_fifa_rank'].fillna(100)
df['form_gap'] = (df['home_last_wins'].fillna(2) - df['away_last_wins'].fillna(2)) / 5
df['gf_gap'] = (df['home_last_goals_for'].fillna(1.5) - df['away_last_goals_for'].fillna(1.5)) / 5
df['ga_gap'] = (df['away_last_goals_against'].fillna(1.5) - df['home_last_goals_against'].fillna(1.5)) / 5
df['elo_gap'] = df['home_key_player_elo'].fillna(50) - df['away_key_player_elo'].fillna(50)
df['streak_gap'] = df['home_win_streak'].fillna(0) - df['away_win_streak'].fillna(0)

features = ['neutral', 'pts_gap', 'rank_gap', 'form_gap', 'gf_gap', 'ga_gap', 'elo_gap', 'streak_gap']

df = df.dropna(subset=features + ['target'])
print(f"After dropna: {len(df)}")
print(f"Target: Away={((df['target']==0).mean()*100):.0f}% Draw={((df['target']==1).mean()*100):.0f}% Home={((df['target']==2).mean()*100):.0f}%")

# Train/val by time
train = df[df['year'] < 2020]
val = df[df['year'] >= 2020]
X_train, y_train = train[features], train['target']
X_val, y_val = val[features], val['target']

# Simple weights
w_map = {'FIFA World Cup': 10, 'FIFA World Cup qualification': 6, 'UEFA Euro': 8, 'Copa América': 8,
         'African Cup of Nations': 6, 'AFC Asian Cup': 5, 'Gold Cup': 5, 'UEFA Nations League': 4,
         'Confederations Cup': 7, 'Friendly': 1}
train_weights = train['tournament'].map(w_map).fillna(2).values

# Balance classes
from sklearn.utils.class_weight import compute_class_weight
cw = compute_class_weight('balanced', classes=np.array([0,1,2]), y=y_train)
sw = train_weights * np.array([cw[y] for y in y_train])

model = XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05,
                      objective='multi:softprob', num_class=3, random_state=42)
model.fit(X_train, y_train, sample_weight=sw, verbose=False)

# Eval
y_pred = model.predict(X_val)
acc = (y_pred == y_val).mean()
print(f"\nVal accuracy: {acc:.3f}")
for i, label in enumerate(['Away', 'Draw', 'Home']):
    mask = y_val == i
    if mask.sum() > 0:
        print(f"  {label}: {((y_pred[mask]==i).mean()*100):.0f}%")

# Test with REAL FIFA data
rankings = pd.read_csv('data/fifa_rankings_2026.csv')
pts = dict(zip(rankings['team'], rankings['fifa_points']))
ranks = dict(zip(rankings['team'], rankings['fifa_rank']))

print("\nTest predictions:")
for home, away in [('Paraguay','Australia'),('Paraguay','Turkey'),('Argentina','Brazil'),
                   ('Brazil','Haiti'),('USA','Paraguay'),('Germany','Curacao')]:
    row = pd.DataFrame([{f: 0 for f in features}])
    row['neutral'] = 1
    row['pts_gap'] = pts.get(home,1500) - pts.get(away,1500)
    row['rank_gap'] = ranks.get(away,100) - ranks.get(home,100)
    p = model.predict_proba(row[features])[0]
    winner = home if p[2] > max(p[0],p[1]) else (away if p[0] > max(p[1],p[2]) else 'DRAW')
    print(f"  {home} vs {away}: H={p[2]:.2f} D={p[1]:.2f} A={p[0]:.2f} → {winner}")

model._feature_names_list = features
joblib.dump(model, Path('ml') / 'worldcup_model.pkl')
print("\nSaved!")
