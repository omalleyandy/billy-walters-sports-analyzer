#!/usr/bin/env python3
"""Check current database state."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db import get_db_connection

db = get_db_connection()

# Check what data currently exists
print("=" * 70)
print("CURRENT DATABASE STATE")
print("=" * 70)

# Games
result = db.execute_query("SELECT COUNT(*) as count FROM games")
print(f"\nGames: {result[0]['count']}")

result = db.execute_query("""
    SELECT season, week, league, COUNT(*) as count
    FROM games
    GROUP BY season, week, league
    ORDER BY league, week
""")
print("Games by week:")
for row in result:
    print(f"  {row['league']} Season {row['season']} Week {row['week']}: {row['count']} games")

# Power Ratings
result = db.execute_query("SELECT COUNT(*) as count FROM power_ratings")
print(f"\nPower Ratings: {result[0]['count']}")

result = db.execute_query("""
    SELECT season, week, COUNT(*) as count
    FROM power_ratings
    GROUP BY season, week
    ORDER BY week
""")
print("Power Ratings by week:")
for row in result:
    print(f"  Week {row['week']}: {row['count']} teams")

# Odds
result = db.execute_query("SELECT COUNT(*) as count FROM odds")
print(f"\nOdds Records: {result[0]['count']}")

# Check schema
print("\n" + "=" * 70)
print("SCHEMA ANALYSIS")
print("=" * 70)

# Power Ratings columns
result = db.execute_query("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'power_ratings'
    ORDER BY ordinal_position
""")
print("\nPower Ratings columns:")
for row in result:
    print(f"  - {row['column_name']}")

# Odds columns
result = db.execute_query("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'odds'
    ORDER BY ordinal_position
""")
print("\nOdds columns:")
for row in result:
    print(f"  - {row['column_name']}")

db.close_all_connections()
print("\n" + "=" * 70)
