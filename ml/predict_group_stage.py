"""Predict all 2026 World Cup group stage matches and save results to CSV/JSON."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

GROUPS: dict[str, list[str]] = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

# Each group plays these matchups (home, away, round_num)
MATCHUPS = [
    (0, 1, 1),  # 1st vs 2nd - Round 1
    (2, 3, 1),  # 3rd vs 4th - Round 1
    (0, 2, 2),  # 1st vs 3rd - Round 2
    (1, 3, 2),  # 2nd vs 4th - Round 2
    (0, 3, 3),  # 1st vs 4th - Round 3
    (1, 2, 3),  # 2nd vs 3rd - Round 3
]


def predict_match(home: str, away: str, round_num: int, stage: str = "group") -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            "ml/predict_match.py",
            "--home-team", home,
            "--away-team", away,
            "--neutral", "true",
            "--stage", stage,
            "--round-num", str(round_num),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )

    output = result.stdout.strip()
    lines = output.split("\n")

    data: dict[str, Any] = {
        "home_team": home,
        "away_team": away,
        "raw_output": output,
    }

    for line in lines:
        line = line.strip()
        if line.startswith("ML prediction:"):
            data["ml_prediction"] = line.split(":", 1)[1].strip()
        elif "Prob" in line and ":" in line:
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    prob_val = float(parts[1].strip())
                    if "away" in line.lower() or away in line:
                        data["prob_away_win"] = prob_val
                    elif "draw" in line.lower():
                        data["prob_draw"] = prob_val
                    elif "home" in line.lower() or home in line:
                        data["prob_home_win"] = prob_val
            except (ValueError, IndexError):
                pass
        elif line.startswith("Monte Carlo winner:") or line.startswith("Monte Carlo real prediction:"):
            data["monte_carlo_winner"] = line.split(":", 1)[1].strip()
        elif line.startswith("Most likely") or line.startswith("ML score:"):
            score_part = line.split(":", 1)[1].strip()
            data["most_likely_score"] = score_part
            try:
                parts = score_part.split("-")
                if len(parts) == 2:
                    data["predicted_home_goals"] = int(parts[0].strip().split()[-1])
                    data["predicted_away_goals"] = int(parts[1].strip().split()[0])
            except (ValueError, IndexError):
                data["predicted_home_goals"] = None
                data["predicted_away_goals"] = None

    prob_home = data.get("prob_home_win", 0)
    prob_draw = data.get("prob_draw", 0)
    prob_away = data.get("prob_away_win", 0)

    if prob_home >= prob_draw and prob_home >= prob_away:
        data["predicted_winner"] = home
    elif prob_away >= prob_draw and prob_away >= prob_home:
        data["predicted_winner"] = away
    else:
        data["predicted_winner"] = "draw"

    return data


def calculate_standings(group_id: str, teams: list[str], match_results: list[dict]) -> list[dict]:
    standings = {team: {"team": team, "mp": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0} for team in teams}

    for match in match_results:
        home = match["home_team"]
        away = match["away_team"]
        home_goals = match.get("predicted_home_goals")
        away_goals = match.get("predicted_away_goals")

        if home_goals is None or away_goals is None:
            continue

        standings[home]["mp"] += 1
        standings[away]["mp"] += 1
        standings[home]["gf"] += home_goals
        standings[home]["ga"] += away_goals
        standings[away]["gf"] += away_goals
        standings[away]["ga"] += home_goals

        if home_goals > away_goals:
            standings[home]["w"] += 1
            standings[away]["l"] += 1
            standings[home]["pts"] += 3
        elif away_goals > home_goals:
            standings[away]["w"] += 1
            standings[home]["l"] += 1
            standings[away]["pts"] += 3
        else:
            standings[home]["d"] += 1
            standings[away]["d"] += 1
            standings[home]["pts"] += 1
            standings[away]["pts"] += 1

    for team in teams:
        standings[team]["gd"] = standings[team]["gf"] - standings[team]["ga"]

    sorted_standings = sorted(
        standings.values(),
        key=lambda x: (x["pts"], x["gd"], x["gf"], x["team"]),
        reverse=True,
    )

    for i, team in enumerate(sorted_standings):
        team["rank"] = i + 1
        if i < 2:
            team["status"] = "top2"
        elif i == 2:
            team["status"] = "third"
        else:
            team["status"] = "out"

    return sorted_standings


def main():
    print("=" * 60)
    print("2026 WORLD CUP - GROUP STAGE PREDICTIONS")
    print("=" * 60)

    all_matches: list[dict] = []
    all_standings: dict[str, list[dict]] = {}

    for group_id, teams in GROUPS.items():
        print(f"\n{'=' * 40}")
        print(f"GROUP {group_id}")
        print(f"{'=' * 40}")

        group_matches: list[dict] = []

        for home_idx, away_idx, round_num in MATCHUPS:
            home = teams[home_idx]
            away = teams[away_idx]
            print(f"\n  {home} vs {away}")

            try:
                result = predict_match(home, away, round_num, "group")
                result["group"] = group_id
                result["round_num"] = round_num
                group_matches.append(result)
                all_matches.append(result)

                winner = result.get("predicted_winner", "?")
                score = result.get("most_likely_score", "?")
                ph = result.get("prob_home_win", "?")
                pd = result.get("prob_draw", "?")
                pa = result.get("prob_away_win", "?")
                print(f"    Winner: {winner}")
                print(f"    Score: {score}")
                print(f"    Probs - Home: {ph}, Draw: {pd}, Away: {pa}")
            except Exception as e:
                print(f"    ERROR: {e}")

        standings = calculate_standings(group_id, teams, group_matches)
        all_standings[group_id] = standings

        print(f"\n  GROUP {group_id} STANDINGS:")
        print(f"  {'Rank':<6} {'Team':<25} {'MP':<4} {'W':<4} {'D':<4} {'L':<4} {'GF':<4} {'GA':<4} {'GD':<5} {'Pts':<4}")
        print(f"  {'-' * 65}")
        for team in standings:
            print(f"  {team['rank']:<6} {team['team']:<25} {team['mp']:<4} {team['w']:<4} {team['d']:<4} {team['l']:<4} {team['gf']:<4} {team['ga']:<4} {team['gd']:<5} {team['pts']:<4}")

    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "group_stage_predictions.json", "w") as f:
        json.dump(all_matches, f, indent=2, default=str)

    with open(output_dir / "group_standings.json", "w") as f:
        json.dump(all_standings, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"Results saved to data/output/")
    print(f"  - group_stage_predictions.json")
    print(f"  - group_standings.json")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
