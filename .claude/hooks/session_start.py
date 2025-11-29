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


def get_ncaaf_week() -> int:
    """Get current NCAAF week."""
    try:
        project_root = get_project_root()
        sys.path.insert(0, str(project_root / "src"))

        from walters_analyzer.season_calendar import get_ncaaf_week

        week = get_ncaaf_week()
        return week if week else 0
    except Exception:
        return 0


def check_data_freshness() -> dict:
    """Check freshness of key data files for NFL and NCAAF."""
    project_root = get_project_root()
    nfl_week = get_nfl_week()
    ncaaf_week = get_ncaaf_week()

    # Comprehensive data files check - organized by category
    files_to_check = {
        # NFL Core Data
        "nfl_power_ratings": project_root / "data" / "current" / "nfl_power_ratings.json",
        "nfl_odds": project_root / "output" / "overtime" / "nfl" / "pregame" / "nfl_odds_*.json",
        "nfl_schedule": project_root / "data" / "current" / f"nfl_week_{nfl_week}_games.json",
        "nfl_injuries": project_root / "data" / "current" / f"nfl_week_{nfl_week}_injuries.json",
        "nfl_weather": project_root / "data" / "current" / f"nfl_week_{nfl_week}_weather.json",
        "nfl_team_stats": project_root / "data" / "current" / f"nfl_team_stats_week_{nfl_week}.json",
        # NCAAF Core Data
        "ncaaf_power_ratings": project_root / "data" / "current" / "ncaaf_power_ratings.json",
        "ncaaf_odds": project_root / "output" / "overtime" / "ncaaf" / "pregame" / "ncaaf_odds_*.json",
        "ncaaf_schedule": project_root / "data" / "current" / f"ncaaf_week_{ncaaf_week}_games.json",
        "ncaaf_team_stats": project_root / "data" / "current" / f"ncaaf_team_stats_week_{ncaaf_week}.json",
        # Supplemental Sources
        "x_news": project_root / "output" / "x_news" / "integrated" / "x_news_*.json",
        "action_network_nfl": project_root / "output" / "action_network" / "nfl" / "games" / "odds_*.json",
        "espn_stats_nfl": project_root / "output" / "espn" / "stats" / "nfl" / "team_stats_nfl_*.json",
        "espn_stats_ncaaf": project_root / "output" / "espn" / "stats" / "ncaaf" / "team_stats_ncaaf_*.json",
    }

    freshness = {}

    for key, path in files_to_check.items():
        if '*' in str(path):
            # Handle glob patterns
            parent = path.parent
            if parent.exists():
                matches = list(parent.glob(path.name))
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
    """Check if edges have been detected for NFL and NCAAF."""
    project_root = get_project_root()
    current_week = get_nfl_week()

    # Check both NFL and NCAAF edge files
    edge_files = [
        project_root / "output" / "edge_detection" / f"nfl_edges_detected_week_{current_week}.jsonl",
        project_root / "output" / "edge_detection" / f"ncaaf_edges_detected_week_{current_week}.jsonl",
        # Fallback to non-week-specific files
        project_root / "output" / "edge_detection" / "nfl_edges_detected.jsonl",
        project_root / "output" / "edge_detection" / "ncaaf_edges_detected.jsonl",
    ]

    strong = 0
    moderate = 0
    nfl_edges = 0
    ncaaf_edges = 0

    for edges_file in edge_files:
        if not edges_file.exists():
            continue

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

                        # Track by league
                        if 'nfl' in str(edges_file).lower():
                            nfl_edges += 1
                        elif 'ncaaf' in str(edges_file).lower():
                            ncaaf_edges += 1
        except Exception:
            continue

    return {
        "count": strong + moderate,
        "strong": strong,
        "moderate": moderate,
        "nfl": nfl_edges,
        "ncaaf": ncaaf_edges
    }


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

    # Current Weeks
    nfl_week = get_nfl_week()
    ncaaf_week = get_ncaaf_week()
    print(f"Current Week: NFL Week {nfl_week} | NCAAF Week {ncaaf_week}")
    print()

    # Data freshness - organized by league
    freshness = check_data_freshness()

    # NFL Data Status
    print("NFL Data Status:")
    nfl_keys = [k for k in freshness.keys() if k.startswith("nfl_")]
    for key in nfl_keys:
        info = freshness[key]
        key_display = key.replace('nfl_', '').replace('_', ' ').title()
        _print_data_status(key_display, info)

    print()

    # NCAAF Data Status
    print("NCAAF Data Status:")
    ncaaf_keys = [k for k in freshness.keys() if k.startswith("ncaaf_")]
    for key in ncaaf_keys:
        info = freshness[key]
        key_display = key.replace('ncaaf_', '').replace('_', ' ').title()
        _print_data_status(key_display, info)

    print()

    # Supplemental Sources
    print("Supplemental Sources:")
    other_keys = [k for k in freshness.keys() if not k.startswith("nfl_") and not k.startswith("ncaaf_")]
    for key in other_keys:
        info = freshness[key]
        key_display = key.replace('_', ' ').title()
        _print_data_status(key_display, info)

    # Check for critical missing data
    nfl_missing = [k for k in nfl_keys if freshness.get(k, {}).get("status") == "MISSING"]
    ncaaf_missing = [k for k in ncaaf_keys if freshness.get(k, {}).get("status") == "MISSING"]

    critical_stale = any(
        freshness.get(k, {}).get("status") in ["STALE", "MISSING"]
        for k in ["nfl_odds", "nfl_power_ratings", "ncaaf_odds", "ncaaf_power_ratings"]
    )

    print()

    # Data Gaps Summary
    if nfl_missing or ncaaf_missing:
        print("Data Gaps:")
        if nfl_missing:
            missing_display = [k.replace('nfl_', '') for k in nfl_missing]
            print(f"  [!] NFL Week {nfl_week} missing: {', '.join(missing_display)}")
        if ncaaf_missing:
            missing_display = [k.replace('ncaaf_', '') for k in ncaaf_missing]
            print(f"  [!] NCAAF Week {ncaaf_week} missing: {', '.join(missing_display)}")
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

        league_str = []
        if edges.get("nfl", 0) > 0:
            league_str.append(f"NFL:{edges['nfl']}")
        if edges.get("ncaaf", 0) > 0:
            league_str.append(f"NCAAF:{edges['ncaaf']}")

        print(f"  -> {' + '.join(edge_str)} edges detected ({', '.join(league_str)})")
        print("  -> Run /betting-card to review picks")
    else:
        if not critical_stale and game_count > 0:
            print("  -> Run /edge-detector to find value")
        elif game_count == 0:
            print("  -> No games scheduled (check schedule)")

    print()
    print("Ready for analysis! [OK]")
    print()


def _print_data_status(key_display: str, info: dict) -> None:
    """Helper to print data status line."""
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


if __name__ == "__main__":
    main()
