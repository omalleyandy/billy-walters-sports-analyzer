#!/usr/bin/env python3
"""
Analyze Week 12 Edges - Find Betting Opportunities

This script performs edge detection on real Week 12 data:
1. Compares power ratings to market odds
2. Identifies edges (mismatches between your prediction and market)
3. Classifies edge strength (MAX/STRONG/MEDIUM/WEAK)
4. Outputs recommended bets with edge analysis
"""

import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection


def analyze_edges(db):
    """Run edge detection analysis on Week 12 games."""

    # Query: Find edges for Week 12
    query = """
    SELECT
        g.game_id,
        g.away_team,
        g.home_team,
        g.game_date,

        -- Power Ratings
        pr_away.rating as away_rating,
        pr_home.rating as home_rating,

        -- Your Predicted Spread (away perspective)
        ROUND(pr_away.rating - pr_home.rating - 3.5, 2) as predicted_spread,

        -- Market Spread (opening odds)
        o.home_spread as market_spread,

        -- Edge Calculation
        ROUND(
            ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread),
            2
        ) as edge_points,

        -- Edge Classification
        CASE
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 7 THEN 'MAX'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 4 THEN 'STRONG'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 2 THEN 'MEDIUM'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 1 THEN 'WEAK'
            ELSE 'NO_PLAY'
        END as edge_strength,

        -- Betting Direction
        CASE
            WHEN (pr_away.rating - pr_home.rating - 3.5) > o.home_spread THEN
                CONCAT(g.away_team, ' +', ABS(o.home_spread)::TEXT)
            WHEN (pr_away.rating - pr_home.rating - 3.5) < o.home_spread THEN
                CONCAT(g.home_team, ' -', ABS(o.home_spread)::TEXT)
            ELSE 'NO_EDGE'
        END as recommended_bet,

        -- Expected Win Rate (Billy Walters)
        CASE
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 7 THEN '77%'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 4 THEN '64%'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 2 THEN '58%'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 1 THEN '54%'
            ELSE 'N/A'
        END as expected_win_pct,

        -- Recommended Units (Kelly-based)
        CASE
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 7 THEN '5.0'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 4 THEN '3.0'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 2 THEN '2.0'
            WHEN ABS((pr_away.rating - pr_home.rating - 3.5) - o.home_spread) >= 1 THEN '1.0'
            ELSE '0.0'
        END as recommended_units

    FROM games g
    LEFT JOIN power_ratings pr_away ON
        g.season = pr_away.season AND
        g.week = pr_away.week AND
        g.league = pr_away.league AND
        g.away_team = pr_away.team AND
        pr_away.source = 'composite'
    LEFT JOIN power_ratings pr_home ON
        g.season = pr_home.season AND
        g.week = pr_home.week AND
        g.league = pr_home.league AND
        g.home_team = pr_home.team AND
        pr_home.source = 'composite'
    LEFT JOIN odds o ON
        g.game_id = o.game_id AND
        o.odds_type = 'opening'

    WHERE g.season = 2025 AND g.week = 12 AND g.league = 'NFL'
      AND pr_away.rating IS NOT NULL
      AND pr_home.rating IS NOT NULL
      AND o.home_spread IS NOT NULL

    ORDER BY edge_points DESC, g.game_date ASC;
    """

    results = db.execute_query(query)
    return results


def print_edge_report(edges):
    """Pretty print edge detection report."""

    print("\n" + "=" * 120)
    print("WEEK 12 EDGE DETECTION REPORT")
    print("=" * 120)

    if not edges:
        print("No edges found.")
        return

    # Summary stats
    total_games = len(edges)
    playable_games = len([e for e in edges if e["edge_strength"] != "NO_PLAY"])
    max_edges = len([e for e in edges if e["edge_strength"] == "MAX"])
    strong_edges = len([e for e in edges if e["edge_strength"] == "STRONG"])

    print(f"\nSummary:")
    print(f"  Total Games: {total_games}")
    print(f"  Playable Edges (>1pt): {playable_games}")
    print(f"  MAX Edges (7+pts): {max_edges}")
    print(f"  STRONG Edges (4-7pts): {strong_edges}")

    print("\n" + "-" * 120)
    print(
        f"{'Game':<20} {'Matchup':<30} {'Ratings':<15} {'Market':<10} {'Edge':<8} {'Category':<10} {'Bet':<20} {'Units':<8} {'Win%':<7}"
    )
    print("-" * 120)

    for edge in edges:
        if edge["edge_strength"] != "NO_PLAY":
            game_key = (
                f"{edge['away_team'][:3].upper()}@{edge['home_team'][:3].upper()}"
            )

            matchup = f"{edge['away_team'][:12]} @ {edge['home_team'][:12]}"

            ratings = f"{edge['away_rating']:.1f} vs {edge['home_rating']:.1f}"

            market = f"{edge['market_spread']:+.1f}" if edge["market_spread"] else "N/A"

            edge_str = f"{edge['edge_points']:.1f}"

            category = edge["edge_strength"]

            bet = (
                edge["recommended_bet"][:20]
                if edge["recommended_bet"] != "NO_EDGE"
                else "SKIP"
            )

            units = edge["recommended_units"]

            win_pct = edge["expected_win_pct"]

            print(
                f"{game_key:<20} {matchup:<30} {ratings:<15} {market:<10} "
                f"{edge_str:<8} {category:<10} {bet:<20} {units:<8} {win_pct:<7}"
            )

    print("-" * 120)

    print("\n" + "=" * 120)
    print("EDGE INTERPRETATION GUIDE")
    print("=" * 120)
    print("""
MAX EDGE (7+ points):
  - Your prediction is 7+ points different from market
  - Expected win rate: 77%
  - Kelly % (conservative): 5.0 units
  - Action: STRONG BET

STRONG EDGE (4-7 points):
  - Your prediction is 4-7 points different from market
  - Expected win rate: 64%
  - Kelly % (conservative): 3.0 units
  - Action: BET

MEDIUM EDGE (2-4 points):
  - Your prediction is 2-4 points different from market
  - Expected win rate: 58%
  - Kelly % (conservative): 2.0 units
  - Action: CONSIDER

WEAK EDGE (1-2 points):
  - Your prediction is 1-2 points different from market
  - Expected win rate: 54%
  - Kelly % (conservative): 1.0 unit
  - Action: PASS (unless size is right)

NO PLAY (<1 point):
  - Market matches your prediction (or very close)
  - No statistical edge
  - Action: DO NOT BET
    """)

    print("=" * 120)


def main():
    """Main function."""
    print("=" * 120)
    print("BILLY WALTERS WEEK 12 EDGE DETECTION")
    print("=" * 120)

    try:
        db = get_db_connection()
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        return False

    try:
        print("\n[1/2] Loading power ratings and odds...")
        edges = analyze_edges(db)

        print(f"[OK] Found {len(edges)} games to analyze")

        print("\n[2/2] Generating edge report...")
        print_edge_report(edges)

        return True

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        db.close_all_connections()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
