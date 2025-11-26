#!/usr/bin/env python3
"""
Comprehensive database data inventory and backfill roadmap.

Shows what data we have, what's missing, and outlines the plan
for comprehensive backfill from Week 1 to current week.
"""

import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection


def analyze_data(db):
    """Analyze all database data."""
    # Games
    result = db.execute_query("""
        SELECT season, week, league, COUNT(*) as count
        FROM games
        GROUP BY season, week, league
        ORDER BY league, week
    """)

    print("\n" + "=" * 70)
    print("GAMES DATA")
    print("=" * 70)

    games_by_league = {}
    for row in result:
        league = row["league"]
        if league not in games_by_league:
            games_by_league[league] = {}
        games_by_league[league][row["week"]] = row["count"]

    for league in ["NFL", "NCAAF"]:
        if league in games_by_league:
            weeks = sorted(games_by_league[league].keys())
            total = sum(games_by_league[league].values())
            print(f"\n{league}: {total} games across {len(weeks)} weeks")
            for week in weeks:
                count = games_by_league[league][week]
                print(f"  Week {week:2d}: {count:2d} games")
        else:
            print(f"\n{league}: No games loaded")

    # Power Ratings
    result = db.execute_query("""
        SELECT season, week, league, source, COUNT(*) as count
        FROM power_ratings
        GROUP BY season, week, league, source
        ORDER BY league, week, source
    """)

    print("\n" + "=" * 70)
    print("POWER RATINGS DATA")
    print("=" * 70)

    ratings_by_league = {}
    for row in result:
        league = row["league"]
        week = row["week"]
        source = row["source"]

        if league not in ratings_by_league:
            ratings_by_league[league] = {}
        if week not in ratings_by_league[league]:
            ratings_by_league[league][week] = {}

        ratings_by_league[league][week][source] = row["count"]

    for league in ["NFL", "NCAAF"]:
        if league in ratings_by_league:
            weeks = sorted(ratings_by_league[league].keys())
            total = sum(sum(ratings_by_league[league][w].values()) for w in weeks)
            print(f"\n{league}: {total} ratings across {len(weeks)} weeks")
            for week in weeks:
                sources = ratings_by_league[league][week]
                src_total = sum(sources.values())
                print(f"  Week {week:2d}: {src_total:3d} teams")
                for source, count in sorted(sources.items()):
                    print(f"    - {source}: {count} teams")
        else:
            print(f"\n{league}: No power ratings loaded")

    # Odds
    result = db.execute_query("""
        SELECT COUNT(*) as count FROM odds
    """)
    odds_count = result[0]["count"]

    result = db.execute_query("""
        SELECT sportsbook, COUNT(*) as count
        FROM odds
        GROUP BY sportsbook
        ORDER BY count DESC
    """)

    print("\n" + "=" * 70)
    print("ODDS DATA")
    print("=" * 70)
    print(f"\nTotal odds records: {odds_count}")

    if odds_count > 0:
        print("\nOdds by sportsbook:")
        for row in result:
            print(f"  - {row['sportsbook']}: {row['count']} records")
    else:
        print("No odds records loaded yet")


def print_backfill_roadmap():
    """Print comprehensive backfill roadmap."""
    print("\n" + "=" * 70)
    print("DATA BACKFILL ROADMAP")
    print("=" * 70)

    print("""
CURRENT STATUS (2025-11-23):
  NFL: Week 12 (current)
  NCAAF: Week 13 (current)

CURRENT DATABASE STATE:
  [OK] 16 NFL games (Week 1 only)
  [OK] 32 NFL power ratings (Week 12 via Massey)
  [OK] 136 NCAAF power ratings (Week 12 via Massey)
  [MISSING] 0 odds records loaded
  [MISSING] No historical data (Week 1-11 for NFL, Week 1-12 for NCAAF)

PHASE 1: MASSEY POWER RATINGS (WEEKS 1-CURRENT)
  Status: IN PROGRESS (Week 12 loaded)
  What we have:
    - Massey JSON files for historical weeks in output/massey/
    - 32 NFL teams (Week 12)
    - 136 NCAAF teams (Week 12)
  What's needed:
    - Parse all historical Massey files (Week 1-11 for NFL, Week 1-12 for NCAAF)
    - Load into power_ratings table with source='massey'
    - Maintain weekly snapshots (not overwrites)
  Expected result: ~352 NFL ratings (32 teams × 11 weeks) + ~1,632 NCAAF
  Effort: Medium (~2 hours for parsing + loading)

PHASE 2: ESPN TEAM STATISTICS (WEEKS 1-CURRENT)
  Status: NOT STARTED
  Data source: ESPN API (free, public)
  What we need:
    - Team offensive/defensive stats by week
    - Points per game, yards per game, etc.
    - Injury data
    - Team records and standings
  Expected result: Enriched power ratings with team stats
  Effort: Medium (~2-3 hours)

PHASE 3: GAME SCHEDULES (WEEKS 1-CURRENT)
  Status: STARTED (16 games for Week 1 only)
  Data sources:
    - ESPN API (comprehensive)
    - NFL.com (official)
    - NCAA.com (official)
  What we need:
    - All 287 NFL games (32 teams × 17 weeks average / 2)
    - All 756 NCAAF games (130+ teams × 13 weeks / 2)
  Expected result: Complete game schedule with dates
  Effort: Low (~1 hour to fetch via APIs)

PHASE 4: ODDS DATA (WEEKS 1-CURRENT)
  Status: NOT STARTED
  Data sources:
    - Overtime.ag API (has historical data via API)
    - Action Network (public betting percentages)
    - Vegas Insider (historical lines)
    - Covers (consensus lines)
  What we need:
    - Opening spreads, totals, moneylines
    - Line movements throughout the week
    - Closing lines
    - Public betting percentages
  Expected result: ~287 NFL + ~756 NCAAF odds records per week
  Effort: High (~8-10 hours due to data complexity)

PHASE 5: INJURY DATA (WEEKS 1-CURRENT)
  Status: NOT STARTED
  Data sources:
    - ESPN injury reports
    - NFL.com official injuries
    - Team websites
  What we need:
    - Player injuries by week
    - Severity/impact classification
    - Return timeline
  Expected result: Historical injury records with impact analysis
  Effort: High (~10-15 hours due to manual verification)

IMPLEMENTATION STRATEGY:
  [OK] 1. Keep database structure with data_source tracking (DONE)
  [OK] 2. Create historical snapshot tables (DONE)
  [NEXT] 3. Load all historical Massey ratings (THIS WEEK)
  [NEXT] 4. Load ESPN schedule and stats (THIS WEEK)
  [NEXT] 5. Load Overtime.ag odds via API (NEXT WEEK)
  [NEXT] 6. Add injury data via ESPN scrapers (NEXT WEEK)
  [NEXT] 7. Verify data quality and completeness (NEXT WEEK)

PRAGMATIC APPROACH:
  Rather than perfect historical data, we'll:
  1. Get current week fully populated (schedules + odds)
  2. Add historical Massey ratings (available locally)
  3. Add ESPN stats where available via API
  4. Use for forward-looking analysis starting immediately

ESTIMATED TIMELINE:
  - Core data (Massey + schedules): 2-3 days
  - Odds data: 3-5 days
  - Injury data: 5-7 days
  - Total: ~2 weeks for comprehensive historical backfill

NEXT IMMEDIATE STEPS:
  1. Load all historical Massey JSON files
  2. Fetch ESPN schedule for all weeks
  3. Get Overtime.ag odds for recent weeks
  4. Begin using database for edge detection analysis
""")

    print("=" * 70)


def main():
    """Run complete inventory."""
    print("=" * 70)
    print("DATABASE DATA INVENTORY & BACKFILL ROADMAP")
    print("=" * 70)

    db = get_db_connection()
    try:
        analyze_data(db)
        print_backfill_roadmap()
    finally:
        db.close_all_connections()

    print("\nTo run backfill:")
    print("  python scripts/database/backfill_nfl_ncaaf_data.py")
    print("\nFor data summary:")
    print("  python scripts/utilities/data_inventory.py")


if __name__ == "__main__":
    main()
