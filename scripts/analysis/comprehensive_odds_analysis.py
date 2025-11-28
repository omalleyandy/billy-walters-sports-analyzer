#!/usr/bin/env python3
"""
Comprehensive odds analysis for NFL and NCAAF.

Dynamically determines current week and provides detailed analysis of:
- Edge detection across all games
- Market efficiency analysis
- Betting recommendations by tier
- Data quality assessment

Automatically adapts to current week in season.
"""

import json
import sys
from datetime import date
from pathlib import Path
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.season_calendar import get_nfl_week, get_ncaaf_week


def find_latest_edge_file(league: str, week: int | None) -> Path | None:
    """Find the most recent edge detection file for given league and week."""
    edge_dir = Path("output/edge_detection")

    if league == "nfl" and week:
        # Try specific week first, then generic
        pattern = f"nfl_edges_detected_week_{week}.jsonl"
        file_path = edge_dir / pattern
        if file_path.exists():
            return file_path
        # Fall back to generic
        pattern = "nfl_edges_detected_week_*.jsonl"
    elif league == "ncaaf" and week:
        # NCAAF uses JSON format, not JSONL
        pattern = f"ncaaf_edges_week_{week}.json"
        file_path = edge_dir / pattern
        if file_path.exists():
            return file_path

    return None


def load_nfl_edges(week: int | None) -> list[dict]:
    """Load NFL edges from most recent week data."""
    edges = []
    file_path = find_latest_edge_file("nfl", week)

    if not file_path or not file_path.exists():
        return edges

    try:
        with open(file_path) as f:
            for line in f:
                if line.strip():
                    edges.append(json.loads(line))
    except json.JSONDecodeError:
        pass

    return edges


def load_ncaaf_edges(week: int | None) -> dict:
    """Load NCAAF edges from JSON file."""
    file_path = find_latest_edge_file("ncaaf", week)

    if not file_path or not file_path.exists():
        return {"edges": [], "week": week}

    try:
        with open(file_path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"edges": [], "week": week}


def analyze_nfl_edges(edges: list[dict], week: int | None) -> dict:
    """Analyze NFL edges by strength tier."""
    strength_map = defaultdict(list)

    for edge in edges:
        strength = edge.get("edge_strength", "unknown")
        strength_map[strength].append(edge)

    stats = {}
    for strength in ["very_strong", "strong", "medium", "weak"]:
        edge_list = strength_map.get(strength, [])
        if edge_list:
            avg_edge = sum(e.get("edge_points", 0) for e in edge_list) / len(edge_list)
            avg_confidence = sum(e.get("confidence_score", 0) for e in edge_list) / len(
                edge_list
            )
            stats[strength] = {
                "count": len(edge_list),
                "avg_edge": avg_edge,
                "avg_confidence": avg_confidence,
                "edges": sorted(
                    edge_list, key=lambda x: x.get("edge_points", 0), reverse=True
                ),
            }

    return stats


def analyze_ncaaf_edges(data: dict) -> dict:
    """Analyze NCAAF edges by strength tier."""
    edges = data.get("edges", [])
    strength_map = defaultdict(list)

    for edge in edges:
        strength = edge.get("strength", "UNKNOWN")
        strength_map[strength].append(edge)

    stats = {}
    for strength in ["MAX BET", "STRONG", "MODERATE", "LEAN", "NO PLAY"]:
        edge_list = strength_map.get(strength, [])
        if edge_list:
            avg_edge = sum(e.get("edge", 0) for e in edge_list) / len(edge_list)
            stats[strength] = {
                "count": len(edge_list),
                "avg_edge": avg_edge,
                "edges": sorted(
                    edge_list, key=lambda x: x.get("edge", 0), reverse=True
                ),
            }

    return stats


def print_header(title: str) -> None:
    """Print section header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)


def print_nfl_analysis(week: int | None, edges: list[dict]) -> None:
    """Print NFL analysis."""
    print_header(f"NFL WEEK {week} ANALYSIS" if week else "NFL ANALYSIS (WEEK UNKNOWN)")

    if not edges:
        print("\nNo edge data available")
        print("Recommendation: Run fresh data collection for complete Week analysis")
        return

    stats = analyze_nfl_edges(edges, week)

    print(f"\nTotal Games Analyzed: {len(edges)}")
    print("\nEDGE STRENGTH DISTRIBUTION:")
    for strength in ["very_strong", "strong", "medium", "weak"]:
        info = stats.get(strength)
        if info:
            print(
                f"  {strength.upper():15} {info['count']:2} games (avg edge: {info['avg_edge']:.2f}pts)"
            )

    # Print top edges
    very_strong = stats.get("very_strong", {}).get("edges", [])
    if very_strong:
        print("\n" + "-" * 80)
        print("TOP VERY STRONG EDGES")
        print("-" * 80)
        for i, edge in enumerate(very_strong[:5], 1):
            print(f"\n{i}. {edge['matchup']}")
            print(f"   Pick: {edge['recommended_bet'].upper()}")
            print(
                f"   Edge: {edge['edge_points']:.2f}pts | Confidence: {edge['confidence_score']:.1f}%"
            )
            print(
                f"   Market: {edge['market_spread']:+.1f} | Total: {edge['market_total']}"
            )
            print(f"   Game Time: {edge['game_time']}")


def print_ncaaf_analysis(week: int | None, data: dict) -> None:
    """Print NCAAF analysis."""
    print_header(
        f"NCAAF WEEK {week} ANALYSIS" if week else "NCAAF ANALYSIS (WEEK UNKNOWN)"
    )

    edges = data.get("edges", [])
    if not edges:
        print("\nNo edge data available")
        return

    stats = analyze_ncaaf_edges(data)

    print(f"\nTotal Games Analyzed: {data.get('total_games', len(edges))}")
    print(f"Teams Matched: {data.get('matched_teams', 'Unknown')}")

    print("\nEDGE STRENGTH DISTRIBUTION:")
    total_games = 0
    for strength in ["MAX BET", "STRONG", "MODERATE", "LEAN", "NO PLAY"]:
        info = stats.get(strength)
        if info:
            print(
                f"  {strength:12} {info['count']:3} games (avg edge: {info['avg_edge']:.1f}pts)"
            )
            total_games += info["count"]

    # Print top edges
    max_bet = stats.get("MAX BET", {}).get("edges", [])
    if max_bet:
        print("\n" + "-" * 80)
        print("TOP MAX BET OPPORTUNITIES")
        print("-" * 80)
        for i, edge in enumerate(max_bet[:5], 1):
            print(f"\n{i}. {edge['matchup']}")
            print(
                f"   Pick: {edge['pick_team']} ({edge['pick_side'].upper()}) @ {edge['pick_spread']}"
            )
            print(f"   Edge: {edge['edge']:.1f}pts | Strength: {edge['strength']}")
            print(f"   Game Time: {edge['game_time']}")
            print(
                f"   Power: {edge['away_team']} {edge['away_power']:+.1f} vs {edge['home_team']} {edge['home_power']:+.1f}"
            )


def print_summary(nfl_week: int | None, ncaaf_week: int | None) -> None:
    """Print overall summary."""
    print_header("SUMMARY & RECOMMENDATIONS")

    today = date.today()
    print(f"\nAnalysis Date: {today.strftime('%A, %B %d, %Y')}")
    print(f"NFL Week: {nfl_week if nfl_week else 'Not in regular season'}")
    print(f"NCAAF Week: {ncaaf_week if ncaaf_week else 'Not in regular season'}")

    print("\n" + "-" * 80)
    print("NEXT STEPS")
    print("-" * 80)
    print("\n1. Review all MAX BET edges (7+ point advantage)")
    print("2. Check current market odds vs our model predictions")
    print("3. Monitor Action Network for sharp money confirmation")
    print("4. Track closing line value (CLV) for accuracy")
    print("5. Execute picks with Kelly criterion bankroll management")

    print("\nKey Principle: Follow the money, not the tickets!")
    print("(Billy Walters - Professional Gambler)")


def main() -> None:
    """Run comprehensive odds analysis."""
    # Determine current week
    nfl_week = get_nfl_week()
    ncaaf_week = get_ncaaf_week()

    # Load edge data
    nfl_edges = load_nfl_edges(nfl_week)
    ncaaf_data = load_ncaaf_edges(ncaaf_week)

    # Print analysis
    print_nfl_analysis(nfl_week, nfl_edges)
    print_ncaaf_analysis(ncaaf_week, ncaaf_data)
    print_summary(nfl_week, ncaaf_week)

    print("\n" + "=" * 80)
    print("END OF ANALYSIS".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
