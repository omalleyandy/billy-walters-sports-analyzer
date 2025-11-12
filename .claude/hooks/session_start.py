#!/usr/bin/env python3
"""
Session Start Hook
Runs at the beginning of each Claude Code session.
Shows git status, data freshness, and opportunities.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_git_status() -> dict:
    """Get git repository status."""
    import subprocess

    try:
        # Check if ahead/behind
        result = subprocess.run(
            ["git", "status", "-sb"],
            capture_output=True,
            text=True,
            timeout=5
        )

        status_line = result.stdout.split('\n')[0]

        # Parse ahead/behind
        ahead = 0
        behind = 0
        if 'ahead' in status_line:
            ahead = int(status_line.split('ahead ')[1].split(']')[0].split(',')[0])
        if 'behind' in status_line:
            behind = int(status_line.split('behind ')[1].split(']')[0])

        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5
        )

        uncommitted = len([l for l in result.stdout.split('\n') if l.strip()])

        return {
            "ahead": ahead,
            "behind": behind,
            "uncommitted": uncommitted,
            "clean": uncommitted == 0 and ahead == 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "ahead": 0,
            "behind": 0,
            "uncommitted": 0,
            "clean": True
        }


def get_nfl_week() -> int:
    """Get current NFL week."""
    try:
        project_root = get_project_root()
        sys.path.insert(0, str(project_root / "src"))

        from walters_analyzer.season_calendar import get_nfl_week

        week = get_nfl_week()
        return week if week else 0
    except Exception:
        return 0


def check_data_freshness() -> dict:
    """Check freshness of key data files."""
    project_root = get_project_root()
    current_week = get_nfl_week()

    files_to_check = {
        "power_ratings": project_root / "data" / "current" / "nfl_power_ratings_2025.json",
        "odds": project_root / "output" / "overtime_nfl_walters_*.json",
        "injuries": project_root / "data" / "current" / f"nfl_injuries_week_{current_week}.json",
        "schedule": project_root / "data" / "current" / f"nfl_week_{current_week}_games.json",
    }

    freshness = {}

    for key, path in files_to_check.items():
        if '*' in str(path):
            # Handle glob patterns
            matches = list(path.parent.glob(path.name))
            if matches:
                latest = max(matches, key=lambda f: f.stat().st_mtime)
                age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
                freshness[key] = {
                    "exists": True,
                    "age_hours": age_hours,
                    "status": "FRESH" if age_hours < 12 else "OK" if age_hours < 24 else "STALE"
                }
            else:
                freshness[key] = {"exists": False, "status": "MISSING"}
        else:
            if path.exists():
                age_hours = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
                freshness[key] = {
                    "exists": True,
                    "age_hours": age_hours,
                    "status": "FRESH" if age_hours < 12 else "OK" if age_hours < 24 else "STALE"
                }
            else:
                freshness[key] = {"exists": False, "status": "MISSING"}

    return freshness


def check_edges() -> dict:
    """Check if edges have been detected."""
    project_root = get_project_root()
    edges_file = project_root / "output" / "edge_detection" / "nfl_edges_detected.jsonl"

    if not edges_file.exists():
        return {"count": 0, "strong": 0, "moderate": 0}

    strong = 0
    moderate = 0

    try:
        with open(edges_file, 'r') as f:
            for line in f:
                if line.strip():
                    edge = json.loads(line)
                    edge_value = edge.get('edge_points', 0)
                    if edge_value >= 4:
                        strong += 1
                    elif edge_value >= 2:
                        moderate += 1

        return {"count": strong + moderate, "strong": strong, "moderate": moderate}
    except Exception:
        return {"count": 0, "strong": 0, "moderate": 0}


def get_game_count() -> int:
    """Get number of games for current week."""
    current_week = get_nfl_week()
    project_root = get_project_root()
    schedule_file = project_root / "data" / "current" / f"nfl_week_{current_week}_games.json"

    if not schedule_file.exists():
        return 0

    try:
        with open(schedule_file, 'r') as f:
            data = json.load(f)
            return len(data.get('games', []))
    except Exception:
        return 0


def main():
    """Main session start routine."""
    print("=" * 70)
    print("BILLY WALTERS SESSION START")
    print("=" * 70)
    print()

    # Git status
    git = get_git_status()
    if "error" in git:
        print(f"Git: [ERROR] {git['error']}")
    else:
        if git["clean"]:
            print("Git: [OK] Clean working tree, synced with origin")
        else:
            parts = []
            if git["ahead"] > 0:
                parts.append(f"{git['ahead']} commits ahead")
            if git["behind"] > 0:
                parts.append(f"{git['behind']} commits behind")
            if git["uncommitted"] > 0:
                parts.append(f"{git['uncommitted']} uncommitted files")

            status = ", ".join(parts)
            print(f"Git: [WARNING] {status}")

            if git["behind"] > 0:
                print("     -> Run: git pull origin main --rebase")
            if git["uncommitted"] > 0:
                print("     -> Uncommitted changes present")
    print()

    # NFL Week
    current_week = get_nfl_week()
    if current_week > 0:
        print(f"Week: NFL 2025 Week {current_week}")
    else:
        print("Week: Offseason or Playoffs")
    print()

    # Data freshness
    print("Data Status:")
    freshness = check_data_freshness()

    for key, info in freshness.items():
        key_display = key.replace('_', ' ').title()

        if not info["exists"]:
            print(f"  [X] {key_display}: MISSING")
        else:
            age_hours = info["age_hours"]
            status = info["status"]

            if status == "FRESH":
                print(f"  [OK] {key_display}: {age_hours:.1f}h old (FRESH)")
            elif status == "OK":
                print(f"  [OK] {key_display}: {age_hours:.1f}h old")
            else:
                print(f"  [!] {key_display}: {age_hours:.1f}h old (STALE)")

    # Check if any critical data is stale
    critical_stale = any(
        freshness.get(k, {}).get("status") in ["STALE", "MISSING"]
        for k in ["odds", "power_ratings"]
    )

    print()

    # Opportunities
    game_count = get_game_count()
    edges = check_edges()

    print("Opportunities:")
    if game_count > 0:
        print(f"  -> {game_count} NFL games this week")

    if critical_stale:
        print("  -> Run /collect-all-data to refresh critical data")

    if edges["count"] > 0:
        edge_str = []
        if edges["strong"] > 0:
            edge_str.append(f"{edges['strong']} STRONG")
        if edges["moderate"] > 0:
            edge_str.append(f"{edges['moderate']} MOD")
        print(f"  -> {' + '.join(edge_str)} edges detected")
        print("  -> Run /betting-card to review picks")
    else:
        if not critical_stale and game_count > 0:
            print("  -> Run /edge-detector to find value")
        elif game_count == 0:
            print("  -> No games scheduled (check schedule)")

    print()
    print("Ready for analysis, partner! [OK]")
    print()


if __name__ == "__main__":
    main()
