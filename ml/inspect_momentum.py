"""Analyze group stage momentum trends and calculate Mexico's Quinto Partido handicap."""
import json
from pathlib import Path

DATA_PATH = Path('data/output/group_standings.json')

if not DATA_PATH.exists():
    print("Error: data/output/group_standings.json not found. Run your group stage simulation first!")
    exit()

with open(DATA_PATH) as f:
    standings = json.load(f)

print("=" * 70)
print(f"{'GROUP STAGE MOMENTUM & TRENDS ANALYSIS':^70}")
print("=" * 70)

perfect_teams = []
qualified_teams = []

for group_id, teams in standings.items():
    for team in teams:
        # Track 9-point teams (3 wins)
        if team.get('pts', 0) == 9:
            perfect_teams.append((team['team'], group_id))
        if team.get('status') in ['top2', 'third'] and team.get('rank', 4) <= 3:
            qualified_teams.append(team)

# 1. 9-Point Giants
print("\n🔥 9-POINT PERFECT MOMENTUM TEAMS:")
if perfect_teams:
    for team, group in perfect_teams:
        print(f"  • {team} (Group {group}) - Swept the group stage. Highly favored for deep run.")
else:
    print("  • None! A completely chaotic group stage with zero clean sweeps.")

# 2. Mexico Check
mexico_status = next((t for t in qualified_teams if t['team'] == 'Mexico'), None)
print("\n🇲🇽 MEXICO 'QUINTO PARTIDO' CRUNCH:")
if mexico_status:
    print(f"  • Status: Qualified from Group {mexico_status.get('group', 'Unknown')} with {mexico_status.get('pts', 0)} points.")
    print("  • Mathematical Breakdown for Round of 16:")
    
    # Showcase how the 20% penalty alters base probabilities against different tiers
    scenarios = [
        ("Vs Heavyweight (e.g., France/Brazil)", 0.45, 0.55),
        ("Vs Balanced Tier (e.g., USA/Colombia)", 0.50, 0.50),
        ("Vs Underdog Tier (e.g., Ecuador/Japan)", 0.60, 0.40)
    ]
    
    print(f"    {'Matchup Scenario':<35} | {'Original Odds':<15} | {'With 20% Curse Penalty':<20}")
    print("    " + "-" * 75)
    for label, base_mex, base_opp in scenarios:
        # Simulate how the curse scales down Mexico's probability
        raw_mex_p = base_mex * 0.80
        raw_opp_p = base_opp
        total = raw_mex_p + raw_opp_p
        
        final_mex_p = raw_mex_p / total
        final_opp_p = raw_opp_p / total
        
        print(f"    {label:<35} | {base_mex:>.1%} vs {base_opp:>.1%} | {final_mex_p:>.1%} vs {final_opp_p:>.1%}")
else:
    print("  • Mexico did not advance past the group stage! The curse struck early.")

print("=" * 70)
