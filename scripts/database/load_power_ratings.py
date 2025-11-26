#!/usr/bin/env python3
"""
Load NCAAF Power Ratings into PostgreSQL
Source: data/current/massey_ratings_ncaaf.json
"""

import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from datetime import datetime
import argparse


def load_power_ratings(
    system: str = "massey_composite", week: int = 13, season: int = 2025
):
    """Load power ratings into ncaaf_power_ratings table"""
    print(
        f"[INFO] Loading NCAAF power ratings ({system}) for Week {week}, Season {season}..."
    )

    # Database connection
    try:
        conn = psycopg2.connect(
            dbname="sports_db",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432",
        )
        cur = conn.cursor()
        print("[OK] Connected to PostgreSQL")
    except psycopg2.Error as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

    # Load ratings file
    try:
        ratings_file = (
            Path(__file__).parent.parent.parent
            / "data"
            / "current"
            / "massey_ratings_ncaaf.json"
        )
        with open(ratings_file) as f:
            ratings_data = json.load(f)

        # Check if it's a list or dict
        if isinstance(ratings_data, list):
            teams_ratings = ratings_data
        else:
            teams_ratings = ratings_data.get("teams", ratings_data.get("ratings", []))

        print(f"[OK] Loaded {len(teams_ratings)} team ratings from file")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {ratings_file}")
        conn.close()
        return False
    except Exception as e:
        print(f"[ERROR] Failed to load ratings file: {e}")
        conn.close()
        return False

    # Prepare data for insertion
    rows = []
    rating_date = datetime.now().date()

    # Handle different data formats
    for item in teams_ratings:
        if isinstance(item, dict):
            # Try to extract team_id and rating
            team_id = item.get("team_id") or item.get("id")
            rating_value = item.get("rating") or item.get("rating_value")

            if team_id and rating_value is not None:
                row = (
                    team_id,
                    system,
                    float(rating_value),
                    rating_date,
                    week,
                    season,
                )
                rows.append(row)

    print(f"[INFO] Prepared {len(rows)} power rating records for insertion")

    if len(rows) == 0:
        print("[WARNING] No valid ratings found in data file")
        conn.close()
        return False

    # Insert ratings
    try:
        sql = """
            INSERT INTO ncaaf_power_ratings (
                team_id, rating_system, rating_value, rating_date, week, season_year
            ) VALUES %s
            ON CONFLICT (team_id, rating_system, week, season_year) DO UPDATE SET
                rating_value = EXCLUDED.rating_value,
                rating_date = EXCLUDED.rating_date
        """
        execute_values(cur, sql, rows, template=None)
        conn.commit()
        print(f"[OK] Inserted {len(rows)} power rating records")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] Failed to insert ratings: {e}")
        print(f"[DEBUG] Sample row: {rows[0] if rows else 'No rows'}")
        conn.close()
        return False

    # Verify insertion
    try:
        cur.execute(
            "SELECT COUNT(*) FROM ncaaf_power_ratings WHERE rating_system = %s",
            (system,),
        )
        count = cur.fetchone()[0]
        print(f"[OK] Verified: {count} rating records in database")
    except psycopg2.Error as e:
        print(f"[WARNING] Could not verify: {e}")

    cur.close()
    conn.close()
    print("[OK] Power ratings loading complete!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load NCAAF power ratings")
    parser.add_argument(
        "--system",
        type=str,
        default="massey_composite",
        help="Rating system name (default: massey_composite)",
    )
    parser.add_argument(
        "--week", type=int, default=13, help="Week number (default: 13)"
    )
    parser.add_argument(
        "--season", type=int, default=2025, help="Season year (default: 2025)"
    )

    args = parser.parse_args()
    success = load_power_ratings(args.system, args.week, args.season)
    exit(0 if success else 1)
