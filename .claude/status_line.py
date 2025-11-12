#!/usr/bin/env python3
"""
Status line script for Billy Walters Sports Analyzer.
Displays current NFL week, data freshness, and edge count.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_current_nfl_week() -> int:
    """Get current NFL week from season calendar."""
    try:
        # Import season calendar module
        project_root = get_project_root()
        sys.path.insert(0, str(project_root / "src"))

        from walters_analyzer.season_calendar import get_current_week

        week = get_current_week()
        return week if week else 0
    except Exception:
        # Fallback: estimate based on date (season starts ~Sep 5)
        now = datetime.now()
        if now.month < 9 or (now.month == 9 and now.day < 5):
            return 0  # Preseason/offseason
        elif now.month >= 9:
            # Rough week calculation
            season_start = datetime(now.year, 9, 5)
            days_since_start = (now - season_start).days
            return min(days_since_start // 7 + 1, 18)
        return 0


def get_latest_odds_file() -> tuple[str, int]:
    """Get latest odds file timestamp and age in minutes."""
    try:
        project_root = get_project_root()
        output_dir = project_root / "output"

        # Find latest walters format odds file
        odds_files = list(output_dir.glob("overtime_nfl_walters_*.json"))

        if not odds_files:
            return "No odds", 999999

        latest_file = max(odds_files, key=lambda f: f.stat().st_mtime)
        file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
        age_minutes = int((datetime.now() - file_time).total_seconds() / 60)

        # Format age
        if age_minutes < 60:
            age_str = f"{age_minutes}m ago"
        elif age_minutes < 1440:  # Less than 24 hours
            age_str = f"{age_minutes // 60}h ago"
        else:
            age_str = f"{age_minutes // 1440}d ago"

        return age_str, age_minutes
    except Exception:
        return "Unknown", 999999


def get_edge_count() -> tuple[int, int]:
    """Get count of detected edges (strong and moderate+)."""
    try:
        project_root = get_project_root()
        edges_file = project_root / "output" / "edge_detection" / "nfl_edges_detected.jsonl"

        if not edges_file.exists():
            return 0, 0

        strong_count = 0
        moderate_count = 0

        with open(edges_file, 'r') as f:
            for line in f:
                if line.strip():
                    edge = json.loads(line)
                    edge_value = edge.get('edge_points', 0)

                    if edge_value >= 4:  # Strong edge
                        strong_count += 1
                    elif edge_value >= 2:  # Moderate edge
                        moderate_count += 1

        return strong_count, moderate_count
    except Exception:
        return 0, 0


def get_freshness_indicator(age_minutes: int) -> str:
    """Get freshness indicator emoji/symbol."""
    if age_minutes < 60:
        return "[FRESH]"  # Fresh data
    elif age_minutes < 360:  # 6 hours
        return "[OK]"  # Acceptable
    elif age_minutes < 1440:  # 24 hours
        return "[STALE]"  # Getting old
    else:
        return "[OLD]"  # Too old


def main():
    """Generate status line output."""
    try:
        # Get all status components
        current_week = get_current_nfl_week()
        odds_age_str, odds_age_minutes = get_latest_odds_file()
        strong_edges, moderate_edges = get_edge_count()
        freshness = get_freshness_indicator(odds_age_minutes)

        # Build status line
        parts = [
            "Billy Walters",
            f"Week {current_week}" if current_week > 0 else "Offseason",
        ]

        # Add odds freshness
        parts.append(f"Odds: {odds_age_str} {freshness}")

        # Add edge counts if any exist
        if strong_edges > 0 or moderate_edges > 0:
            edge_str = []
            if strong_edges > 0:
                edge_str.append(f"{strong_edges} STRONG")
            if moderate_edges > 0:
                edge_str.append(f"{moderate_edges} MOD")
            parts.append(f"Edges: {' + '.join(edge_str)}")

        # Print status line
        print(" | ".join(parts))

    except Exception as e:
        # Fallback status line
        print(f"Billy Walters Sports Analyzer [Error: {str(e)[:20]}]")


if __name__ == "__main__":
    main()
