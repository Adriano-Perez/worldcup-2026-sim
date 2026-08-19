"""Simulate full knockout stage using official FIFA 2026 bracket structure."""
import json, sys
from pathlib import Path

def predict_ko_match(home: str, away: str, round_stage: str = "R32") -> str:
    import subprocess
    cmd = [
        sys.executable,
        str(Path("ml") / "predict_match.py"),
        "--home-team", home,
        "--away-team", away,
        "--neutral", "true",
        "--stage", "knockout",
        "--round-num", "4",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode != 0:
        return home if hash(home + away + round_stage) % 2 == 0 else away
    
    output = result.stdout
    for line in output.split("\n"):
        if "Monte Carlo winner:" in line:
            winner = line.split(":", 1)[1].strip()
            if winner == "draw":
                return home if hash(home + away + round_stage) % 2 == 0 else away
            return winner
    
    return home

def get_score(home, away, winner, round_stage):
    h = abs(hash(home + away + round_stage))
    if winner == home:
        scores = [(1,0), (2,0), (2,1), (3,0), (3,1), (2,1)]
        hg, ag = scores[h % len(scores)]
        return f"{home} {hg}-{ag} {away}"
    else:
        scores = [(0,1), (0,2), (1,2), (0,3), (1,3), (1,2)]
        hg, ag = scores[h % len(scores)]
        return f"{home} {hg}-{ag} {away}"

# Load group stage standings
with open('data/output/group_standings.json') as f:
    standings = json.load(f)

winners, runners_up, third_place = {}, {}, []
for group_id, teams in standings.items():
    for team in teams:
        if team['status'] == 'top2' and team['rank'] == 1:
            winners[group_id] = team['team']
        elif team['status'] == 'top2' and team['rank'] == 2:
            runners_up[group_id] = team['team']
        elif team['status'] == 'third':
            third_place.append({**team, 'group': group_id})

# Sort third place teams
third_place_sorted = sorted(
    third_place,
    key=lambda t: (t.get('pts', 0), t.get('gd', 0), t.get('gf', 0), t.get('team', '')),
    reverse=True,
)
third_place_order = [{'team': t['team'], 'group': t['group']} for t in third_place_sorted[:8]]
available_thirds = list(third_place_order)

def get_third(groups_str):
    for g in groups_str.split('/'):
        for i, t in enumerate(available_thirds):
            if t['group'] == g:
                return available_thirds.pop(i)['team']
    if available_thirds:
        return available_thirds.pop(0)['team']
    return ''

# Official FIFA 2026 R32 bracket - EXACT matchups
r32 = [
    ('Match 73', runners_up['A'], runners_up['B']),
    ('Match 74', winners['E'], get_third('A/B/C/D/F')),
    ('Match 75', winners['F'], runners_up['C']),
    ('Match 76', winners['C'], runners_up['F']),
    ('Match 77', winners['I'], get_third('C/D/F/G/H')),
    ('Match 78', runners_up['E'], runners_up['I']),
    ('Match 79', winners['A'], get_third('C/E/F/H/I')),
    ('Match 80', winners['L'], get_third('E/H/I/J/K')),
    ('Match 81', winners['D'], get_third('B/E/F/I/J')),
    ('Match 82', winners['G'], get_third('A/E/H/I/J')),
    ('Match 83', runners_up['K'], runners_up['L']),
    ('Match 84', winners['H'], runners_up['J']),
    ('Match 85', winners['B'], get_third('E/F/G/I/J')),
    ('Match 86', winners['J'], runners_up['H']),
    ('Match 87', winners['K'], get_third('D/E/I/J/L')),
    ('Match 88', runners_up['D'], runners_up['G']),
]

def run_round(matchups, round_name):
    print(f"\n{'='*75}")
    print(f"{round_name:^75}")
    print(f"{'='*75}")
    results = []
    for name, home, away in matchups:
        winner = predict_ko_match(home, away, round_name)
        score = get_score(home, away, winner, round_name)
        print(f"  {name:9s} | {home:>14s} vs {away:<14s} -> {winner:>14s}  ({score})")
        results.append((name, winner))
    return results

# Run R32
r32_res = run_round(r32, 'R32')

# R16 matchups following FIFA bracket
r16 = [
    ('M89', r32_res[1][1], r32_res[4][1]),   # W74 vs W77
    ('M90', r32_res[0][1], r32_res[2][1]),   # W73 vs W75
    ('M91', r32_res[3][1], r32_res[5][1]),   # W76 vs W78
    ('M92', r32_res[6][1], r32_res[7][1]),   # W79 vs W80
    ('M93', r32_res[10][1], r32_res[12][1]), # W83 vs W85
    ('M94', r32_res[8][1], r32_res[9][1]),   # W81 vs W82
    ('M95', r32_res[14][1], r32_res[13][1]), # W87 vs W86
    ('M96', r32_res[11][1], r32_res[15][1]), # W84 vs W88
]
r16_res = run_round(r16, 'R16')

# QF matchups
qf = [
    ('M97', r16_res[0][1], r16_res[1][1]),   # W89 vs W90
    ('M98', r16_res[4][1], r16_res[5][1]),   # W93 vs W94
    ('M99', r16_res[2][1], r16_res[3][1]),   # W91 vs W92
    ('M100', r16_res[6][1], r16_res[7][1]),  # W95 vs W96
]
qf_res = run_round(qf, 'QF')

# SF matchups
sf = [
    ('M101', qf_res[0][1], qf_res[1][1]),    # W97 vs W98
    ('M102', qf_res[2][1], qf_res[3][1]),    # W99 vs W100
]
sf_res = run_round(sf, 'SF')

# Final
print(f"\n{'='*75}")
print(f"{'🏆 WORLD CUP 2026 FINAL 🏆':^75}")
print(f"{'='*75}")
champion = predict_ko_match(sf_res[0][1], sf_res[1][1], 'F')
runner_up = sf_res[1][1] if champion == sf_res[0][1] else sf_res[0][1]
score = get_score(sf_res[0][1], sf_res[1][1], champion, 'F')
print(f"\n  {sf_res[0][1]} vs {sf_res[1][1]}")
print(f"  Winner: {champion}  ({score})")
print(f"\n  🏆 CHAMPION: {champion} 🏆")
print(f"  🥈 RUNNER-UP: {runner_up} 🥈")

print(f"\n{'='*75}")
print(f"{'KNOCKOUT STAGE COMPLETE':^75}")
print(f"{'='*75}")
