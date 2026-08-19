"""Predict a single international match using the saved model."""
from __future__ import annotations
import argparse
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path("ml") / "worldcup_model.pkl"
CLASS_NAMES = {0: "away_win", 1: "draw", 2: "home_win"}
SIMULATION_COUNT = 100_000

def outcome_labels(home_team, away_team, neutral):
    if neutral:
        return {0: f"{away_team} win", 1: "draw", 2: f"{home_team} win"}
    return {0: "away win", 1: "draw", 2: "home win"}

def score_labels(home_team, away_team, neutral):
    return (home_team, away_team) if neutral else ("home", "away")

def run_monte_carlo(probabilities, home_team, away_team, neutral):
    outcome_keys = np.array([0, 1, 2])
    outcome_probs = np.array([probabilities.get(0,0), probabilities.get(1,0), probabilities.get(2,0)])
    if outcome_probs.sum() <= 0:
        outcome_probs = np.array([1/3, 1/3, 1/3])
    else:
        outcome_probs = outcome_probs / outcome_probs.sum()
    winner_counts = {home_team if neutral else "home": 0, away_team if neutral else "away": 0, "draw": 0}
    score_counts = {}
    hwp = outcome_probs[2]
    awp = outcome_probs[0]
    for _ in range(SIMULATION_COUNT):
        outcome = int(np.random.choice(outcome_keys, p=outcome_probs))
        if outcome == 1:
            dg = np.random.choice([0,1,1,2,2,3], p=[0.15,0.35,0.25,0.15,0.07,0.03])
            winner_counts["draw"] += 1
            score = (dg, dg)
        elif outcome == 2:
            if hwp > 0.75: scores = [(1,0,12),(2,0,18),(2,1,15),(3,0,20),(3,1,15),(3,2,5),(4,0,8),(4,1,5),(5,0,2)]
            elif hwp > 0.60: scores = [(1,0,18),(2,0,15),(2,1,25),(3,0,10),(3,1,15),(3,2,8),(2,0,5),(4,1,4)]
            else: scores = [(1,0,22),(2,0,10),(2,1,30),(3,1,12),(3,2,12),(1,0,8),(4,2,6)]
            choices = [(hg,ag) for hg,ag,_ in scores]
            weights = [w for _,_,w in scores]
            idx = np.random.choice(len(choices), p=np.array(weights)/sum(weights))
            hg, ag = choices[idx]
            if hg <= ag: hg = ag + 1
            winner_counts[home_team if neutral else "home"] += 1
            score = (hg, ag)
        else:
            if awp > 0.75: scores = [(0,1,12),(0,2,18),(1,2,15),(0,3,20),(1,3,15),(2,3,5),(0,4,8),(1,4,5),(0,5,2)]
            elif awp > 0.60: scores = [(0,1,18),(0,2,15),(1,2,25),(0,3,10),(1,3,15),(2,3,8),(0,2,5),(1,4,4)]
            else: scores = [(0,1,22),(0,2,10),(1,2,30),(1,3,12),(2,3,12),(0,1,8),(2,4,6)]
            choices = [(hg,ag) for hg,ag,_ in scores]
            weights = [w for _,_,w in scores]
            idx = np.random.choice(len(choices), p=np.array(weights)/sum(weights))
            hg, ag = choices[idx]
            if ag <= hg: ag = hg + 1
            winner_counts[away_team if neutral else "away"] += 1
            score = (hg, ag)
        score_counts[score] = score_counts.get(score, 0) + 1
    return winner_counts, score_counts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home-team", required=True)
    parser.add_argument("--away-team", required=True)
    parser.add_argument("--neutral", default="true")
    parser.add_argument("--stage", default="group")
    parser.add_argument("--date", default="2023-01-01")
    parser.add_argument("--round-num", type=int, default=2)
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        raise SystemExit(f"Missing model: {MODEL_PATH}")

    if args.stage == 'knockout':
        ko_path = Path('ml') / 'worldcup_model_knockout.pkl'
        model = joblib.load(ko_path if ko_path.exists() else MODEL_PATH)
    else:
        model = joblib.load(MODEL_PATH)
    features = list(getattr(model, "_feature_names_list", []))
    if not features:
        raise SystemExit("Model missing feature names")

    sample = pd.DataFrame([{f: 0 for f in features}])
    sample["venue"] = 1
    if "both_defensive" in features:
        sample["both_defensive"] = 0
    try:
        rankings = pd.read_csv("data/fifa_rankings_2026.csv")
        pts = dict(zip(rankings["team"], rankings["fifa_points"]))
        ranks = dict(zip(rankings["team"], rankings["fifa_rank"]))
        sample["pts_gap"] = pts.get(args.home_team, 1500) - pts.get(args.away_team, 1500)
        sample["rank_gap"] = ranks.get(args.away_team, 100) - ranks.get(args.home_team, 100)
    except: pass
    try:
        sv = pd.read_csv("data/squad_values.csv")
        sv_dict = dict(zip(sv["team"], sv["squad_market_value_eur"]))
        sample["mv_gap"] = np.log1p(sv_dict.get(args.home_team, 50e6)) - np.log1p(sv_dict.get(args.away_team, 50e6))
    except: pass
    for f in features:
        if f not in sample.columns:
            sample[f] = 0

    X = sample[features].fillna(0).to_numpy()
    proba = model.predict_proba(X)[0]

    # Neutral knockout: average home/away perspectives
    if args.stage == "knockout":
        swapped = sample.copy()
        for col in ["pts_gap", "rank_gap", "mv_gap", "xg_diff", "form_gap", "ko_exp_gap"]:
            if col in swapped.columns:
                swapped[col] = -swapped[col]
        X2 = swapped[features].fillna(0).to_numpy()
        proba = (proba + model.predict_proba(X2)[0]) / 2.0

    class_to_proba = {int(cls): float(prob) for cls, prob in zip(model.classes_, proba)}

    # General head-to-head: recent competitive results between these teams
    if args.stage == "knockout":
        try:
            games = pd.read_csv("data/games.csv", parse_dates=["date"])
            mask = ((games["home_club_name"] == args.home_team) & (games["away_club_name"] == args.away_team)) |                    ((games["home_club_name"] == args.away_team) & (games["away_club_name"] == args.home_team))
            h2h = games.loc[mask].sort_values("date", ascending=False).head(5)
            
            if len(h2h) > 0:
                home_wins = 0
                away_wins = 0
                for _, m in h2h.iterrows():
                    comp = str(m.get("competition_type", "")).lower()
                    if "friendly" in comp:
                        continue
                    hg = int(m.get("home_club_goals", 0))
                    ag = int(m.get("away_club_goals", 0))
                    if m["home_club_name"] == args.home_team:
                        if hg > ag: home_wins += 1
                        elif ag > hg: away_wins += 1
                    else:
                        if ag > hg: home_wins += 1
                        elif hg > ag: away_wins += 1
                
                if home_wins > away_wins:
                    class_to_proba[2] *= 1.3
                    class_to_proba[0] *= 0.7
                elif away_wins > home_wins:
                    class_to_proba[0] *= 1.3
                    class_to_proba[2] *= 0.7
                
                total = sum(class_to_proba.values())
                class_to_proba = {k: v/total for k,v in class_to_proba.items()}
        except:
            pass

    # Knockout: FIFA points boost for stronger teams
    if args.stage == 'knockout':
        try:
            rankings = pd.read_csv('data/fifa_rankings_2026.csv')
            pts = dict(zip(rankings['team'], rankings['fifa_points']))
            home_pts = pts.get(args.home_team, 1500)
            away_pts = pts.get(args.away_team, 1500)
            gap = abs(home_pts - away_pts)
            if gap > 20:
                if home_pts > away_pts:
                    class_to_proba[2] *= 1.5
                    class_to_proba[0] *= 0.6
                else:
                    class_to_proba[0] *= 1.5
                    class_to_proba[2] *= 0.6
                total = sum(class_to_proba.values())
                class_to_proba = {k: v/total for k,v in class_to_proba.items()}
        except: pass

    # FIFA adjustments - light touch
    try:
        rankings = pd.read_csv("data/fifa_rankings_2026.csv")
        pts = dict(zip(rankings["team"], rankings["fifa_points"]))
        gap = abs(pts.get(args.home_team,1500) - pts.get(args.away_team,1500))
        
        if gap > 250:
            # Mismatch: favorite wins more
            if pts.get(args.home_team,1500) > pts.get(args.away_team,1500):
                class_to_proba[2] *= 1.3
                class_to_proba[0] *= 0.7
            else:
                class_to_proba[0] *= 1.3
                class_to_proba[2] *= 0.7
        elif gap < 80:
            # Close match: natural draw from ML, small boost
            class_to_proba[1] *= 1.25
            class_to_proba[0] *= 0.875
            class_to_proba[2] *= 0.875
        
        total = sum(class_to_proba.values())
        class_to_proba = {k: v/total for k,v in class_to_proba.items()}
    except: pass
    
    labels = outcome_labels(args.home_team, args.away_team, True)

    winner_counts, score_counts = run_monte_carlo(class_to_proba, args.home_team, args.away_team, True)
    if args.stage == 'knockout':
        # No draws in knockout - pick home or away based on win counts
        home_wins = winner_counts.get(args.home_team, 0)
        away_wins = winner_counts.get(args.away_team, 0)
        likely_winner = args.home_team if home_wins >= away_wins else args.away_team
    elif class_to_proba.get(1, 0) >= 0.30:
        likely_winner = "draw"
    else:
        likely_winner = max(winner_counts.items(), key=lambda x: x[1])[0]

    if likely_winner == "draw":
        scores = {k:v for k,v in score_counts.items() if k[0]==k[1]}
        likely_score = max(scores.items(), key=lambda x: x[1])[0] if scores else (1,1)
    elif likely_winner == args.home_team:
        scores = {k:v for k,v in score_counts.items() if k[0]>k[1]}
        likely_score = max(scores.items(), key=lambda x: x[1])[0] if scores else (2,1)
    else:
        scores = {k:v for k,v in score_counts.items() if k[1]>k[0]}
        likely_score = max(scores.items(), key=lambda x: x[1])[0] if scores else (1,2)

    sh, sa = score_labels(args.home_team, args.away_team, True)

    print(f"Match: {args.home_team} vs {args.away_team}")
    print(f"Neutral: True")
    print(f"Stage: {args.stage}")
    print(f"Prob {labels.get(0, 'away win')}: {class_to_proba.get(0, 0.0):.3f}")
    print(f"Prob {labels.get(1, 'draw')}: {class_to_proba.get(1, 0.0):.3f}")
    print(f"Prob {labels.get(2, 'home win')}: {class_to_proba.get(2, 0.0):.3f}")
    print(f"Monte Carlo winner: {likely_winner}")
    print(f"Most likely score after {SIMULATION_COUNT:,} sims: {sh} {likely_score[0]} - {likely_score[1]} {sa}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())