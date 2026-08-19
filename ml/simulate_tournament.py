"""Run full 2026 World Cup simulation: Group Stage + Knockout Stage."""
import subprocess
import sys
from pathlib import Path

def run_script(script_name):
    """Run script and stream output in real-time."""
    print(f"\n{'='*75}")
    print(f"Running: {script_name}")
    print(f"{'='*75}\n")
    
    result = subprocess.run(
        [sys.executable, str(Path("ml") / script_name)],
        timeout=600
    )
    
    if result.returncode != 0:
        print(f"ERROR: {script_name} failed")
    return result.returncode

def show_third_place_table():
    """Display the third place teams table."""
    print(f"\n{'='*75}")
    print("THIRD PLACE TEAMS TABLE")
    print(f"{'='*75}")
    
    import json
    with open('data/output/group_standings.json') as f:
        standings = json.load(f)
    
    third_place_teams = []
    for group_id, teams in standings.items():
        for team in teams:
            if team['status'] == 'third':
                third_place_teams.append({**team, 'group': group_id})
    
    third_place_sorted = sorted(
        third_place_teams,
        key=lambda t: (t.get('pts', 0), t.get('gd', 0), t.get('gf', 0), t.get('team', '')),
        reverse=True,
    )
    
    print(f"\n  {'Rank':<6} {'Team':<25} {'Group':<7} {'Pts':<5} {'GD':<5} {'GF':<5} {'Status':<12}")
    print(f"  {'-'*70}")
    for i, team in enumerate(third_place_sorted, 1):
        status = "ADVANCES" if i <= 8 else "ELIMINATED"
        print(f"  {i:<6} {team['team']:<25} {team['group']:<7} {team['pts']:<5} {team['gd']:<5} {team['gf']:<5} {status:<12}")

def main():
    print("=" * 75)
    print("2026 FIFA WORLD CUP - FULL TOURNAMENT SIMULATION")
    print("=" * 75)
    
    # Step 1: Group Stage
    print("\nSTEP 1: GROUP STAGE")
    run_script("predict_group_stage.py")
    
    # Step 2: Third Place Table
    show_third_place_table()
    
    # Step 3: Knockout Stage
    print("\nSTEP 2: KNOCKOUT STAGE")
    run_script("generate_knockout.py")
    
    print("\n" + "=" * 75)
    print("TOURNAMENT SIMULATION COMPLETE")
    print("=" * 75)

if __name__ == "__main__":
    main()
