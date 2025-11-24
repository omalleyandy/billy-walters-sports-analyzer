#!/usr/bin/env python3
"""
NFL Injury Report with Billy Walters Point Impact Analysis
Analyzes injury data and calculates betting impact
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Billy Walters Position Values (points impact when player is OUT)
POSITION_VALUES = {
    # Offense
    "QB": {"elite": 9.0, "starter": 6.0, "backup": 3.0},
    "RB": {"elite": 4.0, "starter": 2.5, "backup": 1.0},
    "WR": {"elite": 3.0, "starter": 2.0, "backup": 0.5},
    "TE": {"elite": 2.0, "starter": 1.5, "backup": 0.5},
    "LT": {"elite": 2.0, "starter": 1.5, "backup": 0.8},
    "RT": {"elite": 1.8, "starter": 1.5, "backup": 0.8},
    "LG": {"elite": 1.5, "starter": 1.2, "backup": 0.6},
    "RG": {"elite": 1.5, "starter": 1.2, "backup": 0.6},
    "C": {"elite": 1.8, "starter": 1.5, "backup": 0.7},
    "OL": {"elite": 1.5, "starter": 1.2, "backup": 0.7},  # Generic OL
    # Defense
    "DE": {"elite": 2.5, "starter": 1.5, "backup": 0.8},
    "DT": {"elite": 2.0, "starter": 1.2, "backup": 0.6},
    "LB": {"elite": 1.8, "starter": 1.2, "backup": 0.5},
    "MLB": {"elite": 2.0, "starter": 1.5, "backup": 0.6},
    "CB": {"elite": 2.0, "starter": 1.3, "backup": 0.6},
    "S": {"elite": 1.5, "starter": 1.0, "backup": 0.4},
    "FS": {"elite": 1.5, "starter": 1.0, "backup": 0.4},
    "SS": {"elite": 1.5, "starter": 1.0, "backup": 0.4},
    # Special Teams
    "K": {"elite": 1.0, "starter": 0.5, "backup": 0.3},
    "P": {"elite": 0.5, "starter": 0.3, "backup": 0.1},
}

# Status impact multipliers
STATUS_MULTIPLIERS = {
    "Out": 1.0,  # 100% impact
    "Doubtful": 0.85,  # 85% impact
    "Questionable": 0.15,  # 15% impact (most play)
    "Probable": 0.05,  # 5% impact
    "": 0.0,  # Unknown status
}


def get_position_impact(position: str, status: str, is_elite: bool = False) -> float:
    """
    Calculate point impact for an injured player

    Args:
        position: Player position
        status: Injury status (Out, Doubtful, Questionable, Probable)
        is_elite: Whether player is elite at their position

    Returns:
        Point impact value
    """
    # Normalize position
    pos = position.upper()

    # Get base value
    if pos in POSITION_VALUES:
        values = POSITION_VALUES[pos]
        if is_elite:
            base_value = values["elite"]
        else:
            base_value = values["starter"]
    else:
        # Default for unknown positions
        base_value = 0.5

    # Apply status multiplier
    multiplier = STATUS_MULTIPLIERS.get(status, 0.0)

    return round(base_value * multiplier, 2)


def classify_injury_severity(total_impact: float) -> tuple[str, str]:
    """
    Classify team injury severity

    Returns:
        (severity_level, description)
    """
    if total_impact >= 8.0:
        return "CRITICAL", "Major impact on team performance"
    elif total_impact >= 5.0:
        return "MAJOR", "Significant impact on spread/total"
    elif total_impact >= 2.0:
        return "MODERATE", "Noticeable impact, adjust expectations"
    elif total_impact >= 0.5:
        return "MINOR", "Minimal impact on betting lines"
    else:
        return "NEGLIGIBLE", "No material impact"


def analyze_injuries(injury_file: Path):
    """Analyze injury data with Billy Walters methodology"""

    print("=" * 80)
    print("NFL INJURY REPORT - BILLY WALTERS ANALYSIS")
    print("=" * 80)

    # Load injury data
    with open(injury_file, "r") as f:
        data = json.load(f)

    week = data.get("week", "Unknown")
    updated = data.get("updated", "Unknown")
    injuries = data.get("injuries", [])

    print(f"\nWeek: {week}")
    print(f"Last Updated: {updated}")
    print(f"Total Injuries Tracked: {len(injuries)}")
    print()

    # Group injuries by team
    teams = defaultdict(list)
    for injury in injuries:
        team = injury.get("team", "Unknown")
        teams[team].append(injury)

    # Analyze each team
    team_impacts = []

    for team in sorted(teams.keys()):
        team_injuries = teams[team]

        # Calculate total impact
        total_impact = 0.0
        out_players = []
        doubtful_players = []
        questionable_players = []

        for injury in team_injuries:
            status = injury.get("game_status", injury.get("injury_status", ""))
            position = injury.get("position", "")
            player = injury.get("player_name", "Unknown")

            # Simple elite detection (would need roster data for accuracy)
            is_elite = False  # Placeholder

            impact = get_position_impact(position, status, is_elite)
            total_impact += impact

            # Categorize by status
            if status == "Out":
                out_players.append((player, position, impact))
            elif status == "Doubtful":
                doubtful_players.append((player, position, impact))
            elif status == "Questionable":
                questionable_players.append((player, position, impact))

        severity, description = classify_injury_severity(total_impact)

        team_impacts.append(
            {
                "team": team,
                "total_impact": total_impact,
                "severity": severity,
                "description": description,
                "out_count": len(out_players),
                "doubtful_count": len(doubtful_players),
                "questionable_count": len(questionable_players),
                "out_players": out_players,
                "doubtful_players": doubtful_players,
                "questionable_players": questionable_players,
            }
        )

    # Sort by total impact
    team_impacts.sort(key=lambda x: x["total_impact"], reverse=True)

    # Display results
    print("=" * 80)
    print("TEAMS BY INJURY IMPACT (Highest to Lowest)")
    print("=" * 80)
    print()

    for team_data in team_impacts:
        team = team_data["team"]
        impact = team_data["total_impact"]
        severity = team_data["severity"]
        description = team_data["description"]
        out_count = team_data["out_count"]
        doubtful_count = team_data["doubtful_count"]
        questionable_count = team_data["questionable_count"]

        # Only show teams with meaningful injuries
        if impact < 0.3:
            continue

        print(f"{team:25s} | Impact: {impact:4.1f} pts | {severity:12s}")
        print(f"  Status: {description}")
        print(
            f"  Injuries: {out_count} OUT, {doubtful_count} Doubtful, {questionable_count} Questionable"
        )

        # Show OUT players
        if team_data["out_players"]:
            print("  OUT:")
            for player, pos, val in team_data["out_players"]:
                print(f"    - {player:30s} ({pos:3s}) [-{val:.1f} pts]")

        # Show DOUBTFUL players
        if team_data["doubtful_players"]:
            print("  DOUBTFUL:")
            for player, pos, val in team_data["doubtful_players"]:
                print(f"    - {player:30s} ({pos:3s}) [-{val:.1f} pts]")

        # Show significant QUESTIONABLE players
        sig_questionable = [p for p in team_data["questionable_players"] if p[2] > 0.2]
        if sig_questionable:
            print("  QUESTIONABLE (Key Players):")
            for player, pos, val in sig_questionable[:5]:  # Top 5 only
                print(f"    - {player:30s} ({pos:3s}) [-{val:.1f} pts]")

        print()

    # Summary statistics
    print("=" * 80)
    print("INJURY IMPACT SUMMARY")
    print("=" * 80)
    print()

    critical_teams = [t for t in team_impacts if t["severity"] == "CRITICAL"]
    major_teams = [t for t in team_impacts if t["severity"] == "MAJOR"]
    moderate_teams = [t for t in team_impacts if t["severity"] == "MODERATE"]

    print(f"CRITICAL Impact: {len(critical_teams)} teams (8.0+ points)")
    if critical_teams:
        for t in critical_teams:
            print(f"  - {t['team']:25s} {t['total_impact']:4.1f} pts")

    print(f"\nMAJOR Impact: {len(major_teams)} teams (5.0-7.9 points)")
    if major_teams:
        for t in major_teams:
            print(f"  - {t['team']:25s} {t['total_impact']:4.1f} pts")

    print(f"\nMODERATE Impact: {len(moderate_teams)} teams (2.0-4.9 points)")
    if moderate_teams:
        for t in moderate_teams[:5]:  # Top 5
            print(f"  - {t['team']:25s} {t['total_impact']:4.1f} pts")

    total_out = sum(t["out_count"] for t in team_impacts)
    total_doubtful = sum(t["doubtful_count"] for t in team_impacts)
    total_questionable = sum(t["questionable_count"] for t in team_impacts)

    print(f"\nLeague Totals:")
    print(f"  OUT: {total_out} players")
    print(f"  DOUBTFUL: {total_doubtful} players")
    print(f"  QUESTIONABLE: {total_questionable} players")

    print()
    print("=" * 80)
    print("BETTING RECOMMENDATIONS")
    print("=" * 80)
    print()

    print("Use injury impacts to adjust spreads/totals:")
    print("  - CRITICAL (8+ pts): Bet against injured team or UNDER")
    print("  - MAJOR (5-8 pts): Significant line value, fade injured team")
    print("  - MODERATE (2-5 pts): Minor adjustment, factor into analysis")
    print()
    print("Key Positions to Monitor:")
    print("  - QB OUT: 6-9 point swing (check backup quality)")
    print("  - Multiple OL OUT: 2-4 points (pass protection issues)")
    print("  - Elite pass rusher OUT: 2-3 points (QB gets more time)")
    print("  - Shutdown CB OUT: 1-2 points (WRs get better matchups)")
    print()

    return team_impacts


def main():
    """Main entry point"""
    injury_file = Path("output/injuries/nfl_official_injuries_week_12.json")

    if not injury_file.exists():
        print(f"[ERROR] Injury file not found: {injury_file}")
        print("Run data collection first: /collect-all-data")
        return 1

    analyze_injuries(injury_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
