#!/usr/bin/env python3
"""
Load NCAAF Team Master Data into PostgreSQL
Source: ESPN API client data
"""

import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path


def load_teams():
    """Load all NCAAF teams into ncaaf_teams table"""
    print("[INFO] Starting team master data load...")

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

    # Load ESPN teams mapping
    try:
        espn_teams_file = (
            Path(__file__).parent.parent.parent / "data" / "current" / "espn_teams.json"
        )
        with open(espn_teams_file) as f:
            espn_data = json.load(f)
        espn_teams = espn_data.get("ncaaf", {})
        print(f"[OK] Loaded {len(espn_teams)} teams from ESPN mapping")
    except Exception as e:
        print(f"[ERROR] Failed to load ESPN teams: {e}")
        conn.close()
        return False

    # Load team abbreviation mappings
    try:
        mappings_file = (
            Path(__file__).parent.parent.parent
            / "src"
            / "data"
            / "ncaaf_team_mappings.json"
        )
        with open(mappings_file) as f:
            mappings = json.load(f).get("mappings", {})
        print(f"[OK] Loaded {len(mappings)} team abbreviation mappings")
    except Exception as e:
        print(f"[WARNING] Could not load team mappings: {e}")
        mappings = {}

    # Prepare data for insertion
    teams_data = []
    for team_id, team_name in espn_teams.items():
        # Clean team name for lookup
        clean_name = team_name.replace(" NCAA", "").replace(" (ESPN)", "")
        abbrev = mappings.get(clean_name, "")

        # Try to get conference (simple heuristic - can be enhanced)
        conference = None  # ESPN API doesn't provide in this endpoint

        teams_data.append((team_id, team_name, abbrev, conference))

    print(f"[INFO] Prepared {len(teams_data)} teams for insertion")

    # Insert teams
    try:
        sql = """
            INSERT INTO ncaaf_teams (team_id, team_name, team_abbreviation, conference)
            VALUES %s
            ON CONFLICT (team_id) DO UPDATE SET
                team_name = EXCLUDED.team_name,
                team_abbreviation = EXCLUDED.team_abbreviation
        """
        execute_values(cur, sql, teams_data, template=None)
        conn.commit()
        print(f"[OK] Inserted {len(teams_data)} teams into ncaaf_teams")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"[ERROR] Failed to insert teams: {e}")
        conn.close()
        return False

    # Verify insertion
    try:
        cur.execute("SELECT COUNT(*) FROM ncaaf_teams")
        count = cur.fetchone()[0]
        print(f"[OK] Verified: {count} teams in database")
    except psycopg2.Error as e:
        print(f"[WARNING] Could not verify: {e}")

    cur.close()
    conn.close()
    print("[OK] Team loading complete!")
    return True


if __name__ == "__main__":
    success = load_teams()
    exit(0 if success else 1)
