#!/usr/bin/env python3
"""
Load NCAAF Game Schedules into PostgreSQL
Source: output/unified/ncaaf_schedule.json
"""

import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from datetime import datetime
import argparse


def parse_game_date(date_str):
    """Parse date string to datetime"""
    if not date_str:
        return None

    for fmt in ["%Y-%m-%dT%H:%M%z", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str.replace("Z", "+0000"), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def load_schedules(season: int = 2025):
    """Load game schedules into ncaaf_schedules table"""
    print(f"[INFO] Loading NCAAF schedules for Season {season}...")

    # Database connection
    try:
        conn = psycopg2.connect(
            dbname="sports_db",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        print("[OK] Connected to PostgreSQL")
    except psycopg2.Error as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

    # Load schedules file
    try:
        schedule_file = (
            Path(__file__).parent.parent.parent / "output" / "unified" /
            "ncaaf_schedule.json"
        )
        with open(schedule_file) as f:
            content = f.read()

        # Handle JSONL format (one JSON per line)
        games = []
        if content.strip().startswith("["):
            # Standard JSON array
            games = json.loads(content)
        else:
            # JSONL format
            for line in content.strip().split("\n"):
                if line.strip():
                    games.append(json.loads(line))

        print(f"[OK] Loaded {len(games)} games from schedule file")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {schedule_file}")
        conn.close()
        return False
    except Exception as e:
        print(f"[ERROR] Failed to load schedule file: {e}")
        conn.close()
        return False

    # Prepare data for insertion
    rows = []
    for game in games:
        game_id = game.get("game_id") or game.get("id")
        if not game_id:
            continue

        home_team_id = game.get("home_team_id")
        away_team_id = game.get("away_team_id")

        if not home_team_id or not away_team_id:
            continue

        game_date = parse_game_date(game.get("game_date") or game.get("date"))
        week = game.get("week")
        status = game.get("status", "Scheduled")
        home_score = game.get("home_score")
        away_score = game.get("away_score")
        location = game.get("location") or game.get("venue")

        row = (
            game_id,
            home_team_id,
            away_team_id,
            game_date,
            week,
            season,
            status,
            home_score,
            away_score,
            location,
        )
        rows.append(row)

    print(f"[INFO] Prepared {len(rows)} schedule records for insertion")

    if len(rows) == 0:
        print("[WARNING] No valid games found in schedule file")
        conn.close()
        return False

    # Insert schedules
    try:
        sql = """
            INSERT INTO ncaaf_schedules (
                game_id, home_team_id, away_team_id, game_date, week,
                season_year, status, home_score, away_score, location
            ) VALUES %s
            ON CONFLICT (game_id) DO UPDATE SET
                status = EXCLUDED.status,
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score
        """
        execute_values(cur, sql, rows, template=None)
        conn.commit()
        print(f"[OK] Inserted {len(rows)} schedule records")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] Failed to insert schedules: {e}")
        print(f"[DEBUG] Sample row: {rows[0] if rows else 'No rows'}")
        conn.close()
        return False

    # Verify insertion
    try:
        cur.execute(
            "SELECT COUNT(*) FROM ncaaf_schedules WHERE season_year = %s",
            (season,)
        )
        count = cur.fetchone()[0]
        print(f"[OK] Verified: {count} game records in database")
    except psycopg2.Error as e:
        print(f"[WARNING] Could not verify: {e}")

    cur.close()
    conn.close()
    print("[OK] Schedule loading complete!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load NCAAF game schedules")
    parser.add_argument("--season", type=int, default=2025, help="Season year (default: 2025)")

    args = parser.parse_args()
    success = load_schedules(args.season)
    exit(0 if success else 1)
