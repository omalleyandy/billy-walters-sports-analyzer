#!/usr/bin/env python3
"""
Load NCAAF Team Statistics into PostgreSQL
Source: data/current/ncaaf_team_stats_week_X.json
"""

import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
import argparse


def load_team_stats(week: int, season: int):
    """Load team statistics for given week into ncaaf_team_stats table"""
    print(f"[INFO] Loading NCAAF stats for Week {week}, Season {season}...")

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

    # Load stats file
    try:
        stats_file = (
            Path(__file__).parent.parent.parent
            / "data"
            / "current"
            / f"ncaaf_team_stats_week_{week}.json"
        )
        with open(stats_file) as f:
            stats_data = json.load(f)

        teams = stats_data.get("teams", [])
        print(f"[OK] Loaded {len(teams)} teams from stats file")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {stats_file}")
        conn.close()
        return False
    except Exception as e:
        print(f"[ERROR] Failed to load stats file: {e}")
        conn.close()
        return False

    # Prepare data for insertion
    rows = []
    for team in teams:
        row = (
            team.get("team_id"),
            week,
            season,
            team.get("points_per_game"),
            team.get("total_points"),
            team.get("passing_yards_per_game"),
            team.get("rushing_yards_per_game"),
            team.get("total_yards_per_game"),
            team.get("points_allowed_per_game"),
            team.get("passing_yards_allowed_per_game"),
            team.get("rushing_yards_allowed_per_game"),
            team.get("total_yards_allowed_per_game"),
            team.get("turnover_margin"),
            team.get("third_down_pct"),
            team.get("takeaways"),
            team.get("giveaways"),
            team.get("games_played"),
        )
        rows.append(row)

    print(f"[INFO] Prepared {len(rows)} statistics records for insertion")

    # Insert stats
    try:
        sql = """
            INSERT INTO ncaaf_team_stats (
                team_id, week, season_year,
                points_per_game, total_points,
                passing_yards_per_game, rushing_yards_per_game, total_yards_per_game,
                points_allowed_per_game, passing_yards_allowed_per_game,
                rushing_yards_allowed_per_game, total_yards_allowed_per_game,
                turnover_margin, third_down_pct, takeaways, giveaways, games_played
            ) VALUES %s
            ON CONFLICT (team_id, week, season_year) DO UPDATE SET
                points_per_game = EXCLUDED.points_per_game,
                total_points = EXCLUDED.total_points,
                passing_yards_per_game = EXCLUDED.passing_yards_per_game,
                rushing_yards_per_game = EXCLUDED.rushing_yards_per_game,
                total_yards_per_game = EXCLUDED.total_yards_per_game,
                points_allowed_per_game = EXCLUDED.points_allowed_per_game,
                passing_yards_allowed_per_game = EXCLUDED.passing_yards_allowed_per_game,
                rushing_yards_allowed_per_game = EXCLUDED.rushing_yards_allowed_per_game,
                total_yards_allowed_per_game = EXCLUDED.total_yards_allowed_per_game,
                turnover_margin = EXCLUDED.turnover_margin,
                third_down_pct = EXCLUDED.third_down_pct,
                takeaways = EXCLUDED.takeaways,
                giveaways = EXCLUDED.giveaways,
                games_played = EXCLUDED.games_played
        """
        execute_values(cur, sql, rows, template=None)
        conn.commit()
        print(f"[OK] Inserted {len(rows)} statistics records")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] Failed to insert stats: {e}")
        conn.close()
        return False

    # Verify insertion
    try:
        cur.execute(
            "SELECT COUNT(*) FROM ncaaf_team_stats WHERE week = %s AND season_year = %s",
            (week, season),
        )
        count = cur.fetchone()[0]
        print(f"[OK] Verified: {count} stat records in database for Week {week}")
    except psycopg2.Error as e:
        print(f"[WARNING] Could not verify: {e}")

    cur.close()
    conn.close()
    print("[OK] Statistics loading complete!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load NCAAF team statistics")
    parser.add_argument(
        "--week", type=int, default=13, help="Week number (default: 13)"
    )
    parser.add_argument(
        "--season", type=int, default=2025, help="Season year (default: 2025)"
    )

    args = parser.parse_args()
    success = load_team_stats(args.week, args.season)
    exit(0 if success else 1)
