"""Generate knockout bracket from group stage results."""
import json
from pathlib import Path

with open('data/output/group_standings.json') as f:
    standings = json.load(f)

winners = {}
runners_up = {}
third_place = []

for group_id, teams in standings.items():
    for team in teams:
        if team['status'] == 'top2' and team['rank'] == 1:
            winners[group_id] = team['team']
        elif team['status'] == 'top2' and team['rank'] == 2:
            runners_up[group_id] = team['team']
        elif team['status'] == 'third':
            third_place.append({**team, 'group': group_id})

third_place.sort(key=lambda x: (x['pts'], x['gd'], x['gf']), reverse=True)
best_thirds = third_place[:8]

r32 = [
    {'match': 1, 'home': winners.get('A', 'TBD'), 'away': best_thirds[0]['team'] if len(best_thirds) > 0 else 'TBD'},
    {'match': 2, 'home': runners_up.get('C', 'TBD'), 'away': runners_up.get('D', 'TBD')},
    {'match': 3, 'home': winners.get('B', 'TBD'), 'away': best_thirds[1]['team'] if len(best_thirds) > 1 else 'TBD'},
    {'match': 4, 'home': winners.get('F', 'TBD'), 'away': runners_up.get('E', 'TBD')},
    {'match': 5, 'home': winners.get('C', 'TBD'), 'away': best_thirds[2]['team'] if len(best_thirds) > 2 else 'TBD'},
    {'match': 6, 'home': winners.get('E', 'TBD'), 'away': runners_up.get('F', 'TBD')},
    {'match': 7, 'home': winners.get('D', 'TBD'), 'away': best_thirds[3]['team'] if len(best_thirds) > 3 else 'TBD'},
    {'match': 8, 'home': winners.get('G', 'TBD'), 'away': runners_up.get('H', 'TBD')},
    {'match': 9, 'home': winners.get('H', 'TBD'), 'away': best_thirds[4]['team'] if len(best_thirds) > 4 else 'TBD'},
    {'match': 10, 'home': runners_up.get('A', 'TBD'), 'away': runners_up.get('B', 'TBD')},
    {'match': 11, 'home': winners.get('I', 'TBD'), 'away': best_thirds[5]['team'] if len(best_thirds) > 5 else 'TBD'},
    {'match': 12, 'home': winners.get('K', 'TBD'), 'away': runners_up.get('J', 'TBD')},
    {'match': 13, 'home': winners.get('J', 'TBD'), 'away': best_thirds[6]['team'] if len(best_thirds) > 6 else 'TBD'},
    {'match': 14, 'home': winners.get('L', 'TBD'), 'away': runners_up.get('K', 'TBD')},
    {'match': 15, 'home': runners_up.get('I', 'TBD'), 'away': best_thirds[7]['team'] if len(best_thirds) > 7 else 'TBD'},
    {'match': 16, 'home': runners_up.get('G', 'TBD'), 'away': runners_up.get('L', 'TBD')},
]

print("=" * 50)
print("KNOCKOUT BRACKET - ROUND OF 32")
print("=" * 50)
for m in r32:
    print(f"  M{m['match']:2d}: {m['home']} vs {m['away']}")

knockout = {
    'round_of_32': r32,
    'round_of_16': [{'match': i, 'home': 'TBD', 'away': 'TBD'} for i in range(1, 9)],
    'quarter_finals': [{'match': i, 'home': 'TBD', 'away': 'TBD'} for i in range(1, 5)],
    'semi_finals': [{'match': 1, 'home': 'TBD', 'away': 'TBD'}, {'match': 2, 'home': 'TBD', 'away': 'TBD'}],
    'final': {'home': 'TBD', 'away': 'TBD'},
}

Path('data/output').mkdir(parents=True, exist_ok=True)
with open('data/output/knockout_bracket.json', 'w') as f:
    json.dump(knockout, f, indent=2)
print("\nSaved to data/output/knockout_bracket.json")
