#!/usr/bin/env python3
"""
Session End Hook
Runs at the end of each Claude Code session.
Shows uncommitted changes, pending tasks, and next steps.
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
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5
        )

        lines = [l for l in result.stdout.split('\n') if l.strip()]

        # Parse file status
        modified = []
        untracked = []
        staged = []

        for line in lines:
            if not line.strip():
                continue

            status = line[:2]
            filepath = line[3:]

            if status == '??':
                untracked.append(filepath)
            elif status[0] in ['M', 'A', 'D', 'R']:
                staged.append(filepath)
            elif status[1] in ['M', 'D']:
                modified.append(filepath)

        return {
            "clean": len(lines) == 0,
            "modified": modified,
            "untracked": untracked,
            "staged": staged,
            "total": len(lines)
        }
    except Exception as e:
        return {
            "error": str(e),
            "clean": True,
            "modified": [],
            "untracked": [],
            "staged": [],
            "total": 0
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


def check_data_staleness() -> list:
    """Check which data is stale and needs updating."""
    project_root = get_project_root()
    current_week = get_nfl_week()

    files_to_check = {
        "Odds": project_root / "output" / "overtime_nfl_walters_*.json",
        "Injuries": project_root / "data" / "current" / f"nfl_injuries_week_{current_week}.json",
        "Weather": project_root / "data" / "current" / f"nfl_weather_week_{current_week}.json",
    }

    stale_items = []

    for key, path in files_to_check.items():
        if '*' in str(path):
            # Handle glob patterns
            matches = list(path.parent.glob(path.name))
            if matches:
                latest = max(matches, key=lambda f: f.stat().st_mtime)
                age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
                if age_hours > 24:
                    stale_items.append(f"{key} ({age_hours:.0f}h old)")
            else:
                stale_items.append(f"{key} (missing)")
        else:
            if path.exists():
                age_hours = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
                if age_hours > 24:
                    stale_items.append(f"{key} ({age_hours:.0f}h old)")
            else:
                stale_items.append(f"{key} (missing)")

    return stale_items


def get_clv_status() -> dict:
    """Check CLV tracking status."""
    project_root = get_project_root()
    current_week = get_nfl_week()

    # Check if CLV has been tracked this week
    bets_file = project_root / "data" / "bets" / "active_bets.json"

    if not bets_file.exists():
        return {"tracked": False, "bets": 0}

    try:
        with open(bets_file, 'r') as f:
            data = json.load(f)
            week_bets = [b for b in data if b.get('week') == current_week]
            return {"tracked": len(week_bets) > 0, "bets": len(week_bets)}
    except Exception:
        return {"tracked": False, "bets": 0}


def suggest_commit_message(git_status: dict) -> str:
    """Suggest a commit message based on changed files."""
    files = git_status["modified"] + git_status["untracked"] + git_status["staged"]

    # Analyze file patterns
    has_data = any('data/' in f or 'output/' in f for f in files)
    has_scripts = any('scripts/' in f for f in files)
    has_src = any('src/' in f for f in files)
    has_docs = any('.md' in f or 'docs/' in f for f in files)
    has_settings = any('.claude/' in f or 'settings' in f for f in files)

    # Suggest commit message
    if has_settings:
        return 'feat(claude): update settings and hooks'
    elif has_data and not (has_scripts or has_src):
        current_week = get_nfl_week()
        return f'data: update week {current_week} data collection'
    elif has_scripts and not has_src:
        return 'feat(scripts): add/update analysis scripts'
    elif has_src:
        return 'feat(analyzer): update core analysis logic'
    elif has_docs:
        return 'docs: update documentation'
    else:
        return 'chore: miscellaneous updates'


def main():
    """Main session end routine."""
    print()
    print("=" * 70)
    print("BILLY WALTERS SESSION END")
    print("=" * 70)
    print()

    # Git status
    git = get_git_status()

    if "error" in git:
        print(f"Git: [ERROR] {git['error']}")
        print()
    elif git["clean"]:
        print("Git: [OK] All changes committed and pushed")
        print()
    else:
        print(f"Git: [WARNING] {git['total']} uncommitted files")
        print()

        # Show file categories
        if git["staged"]:
            print(f"  Staged ({len(git['staged'])}):")
            for f in git["staged"][:5]:
                print(f"    + {f}")
            if len(git["staged"]) > 5:
                print(f"    ... and {len(git['staged']) - 5} more")

        if git["modified"]:
            print(f"  Modified ({len(git['modified'])}):")
            for f in git["modified"][:5]:
                print(f"    M {f}")
            if len(git["modified"]) > 5:
                print(f"    ... and {len(git['modified']) - 5} more")

        if git["untracked"]:
            print(f"  Untracked ({len(git['untracked'])}):")
            for f in git["untracked"][:5]:
                print(f"    ? {f}")
            if len(git["untracked"]) > 5:
                print(f"    ... and {len(git['untracked']) - 5} more")

        print()

        # Suggest commit command
        suggested_msg = suggest_commit_message(git)
        print("  Suggested commit:")
        print(f'    git add . && git commit -m "{suggested_msg}"')
        print()

    # Pending Tasks
    print("Pending Tasks:")

    pending = []

    # Check edges
    edges = check_edges()
    if edges["count"] > 0:
        edge_str = []
        if edges["strong"] > 0:
            edge_str.append(f"{edges['strong']} STRONG")
        if edges["moderate"] > 0:
            edge_str.append(f"{edges['moderate']} MOD")
        pending.append(f"Review {' + '.join(edge_str)} edges (/betting-card)")

    # Check CLV
    clv = get_clv_status()
    if edges["count"] > 0 and not clv["tracked"]:
        pending.append("Track CLV for detected edges (/clv-tracker)")

    # Check stale data
    stale = check_data_staleness()
    if stale:
        pending.append(f"Refresh stale data: {', '.join(stale)}")

    if pending:
        for task in pending:
            print(f"  -> {task}")
    else:
        print("  [OK] No pending tasks")

    print()

    # Next Session Priorities
    print("Next Session:")

    current_week = get_nfl_week()
    day_of_week = datetime.now().strftime("%A")

    priorities = []

    # Day-specific priorities
    if day_of_week in ["Tuesday", "Wednesday"]:
        priorities.append("1. Run /collect-all-data (optimal days for line collection)")
        priorities.append("2. Run /edge-detector after data collection")
        priorities.append("3. Review /betting-card for week's opportunities")
    elif day_of_week == "Thursday":
        priorities.append("1. Refresh odds before TNF (/scrape-overtime)")
        priorities.append("2. Update weather/injuries for Thursday game")
        priorities.append("3. Re-run /edge-detector with fresh data")
    elif day_of_week in ["Friday", "Saturday"]:
        priorities.append("1. Final injury report check (/injury-report nfl)")
        priorities.append("2. Update game-day weather forecasts (/weather)")
        priorities.append("3. Final edge detection before Sunday")
    elif day_of_week == "Sunday":
        priorities.append("1. Monitor live games (optional)")
        priorities.append("2. Track bet results")
    elif day_of_week == "Monday":
        priorities.append("1. Update CLV for completed bets (/clv-tracker)")
        priorities.append("2. Review week's performance")
        priorities.append("3. Document lessons learned if applicable")

    # Add general priorities
    if edges["count"] > 0:
        priorities.insert(0, f"-> Review {edges['count']} detected edges")

    if stale:
        priorities.insert(0, "-> Refresh stale data before analysis")

    if priorities:
        for priority in priorities[:5]:  # Show max 5 priorities
            print(f"  {priority}")
    else:
        print("  [OK] No specific priorities")

    print()
    print("See you next time, partner! [OK]")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
