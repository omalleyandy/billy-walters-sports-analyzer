#!/usr/bin/env python3
"""
Validate NCAAF PostgreSQL Database Integrity
Checks for data quality, completeness, and consistency
"""

import psycopg2
from tabulate import tabulate
import sys


def validate_database():
    """Run comprehensive database validation"""
    print("\n" + "=" * 80)
    print("NCAAF PostgreSQL Database Validation")
    print("=" * 80 + "\n")

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
        print("[OK] Connected to PostgreSQL\n")
    except psycopg2.Error as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

    all_passed = True

    # =====================================================================
    # Check 1: Table Existence
    # =====================================================================
    print("CHECK 1: Table Existence")
    print("-" * 80)

    tables = [
        "ncaaf_teams",
        "ncaaf_team_stats",
        "ncaaf_power_ratings",
        "ncaaf_schedules",
        "ncaaf_team_injuries",
    ]

    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  [OK] {table:30} {count:>10} records")
        except psycopg2.Error:
            print(f"  [ERROR] {table:30} TABLE MISSING")
            all_passed = False

    print()

    # =====================================================================
    # Check 2: Teams Table Validation
    # =====================================================================
    print("CHECK 2: Teams Data Quality")
    print("-" * 80)

    try:
        # Total teams
        cur.execute("SELECT COUNT(*) FROM ncaaf_teams")
        total_teams = cur.fetchone()[0]
        print(f"  Total Teams: {total_teams}")

        # Check Boston College
        cur.execute(
            "SELECT team_id, team_name, team_abbreviation FROM ncaaf_teams WHERE team_id = '103'"
        )
        bc = cur.fetchone()
        if bc:
            print(
                f"  [OK] Boston College verified: ID={bc[0]}, Name={bc[1]}, Abbrev={bc[2]}"
            )
        else:
            print(f"  [WARNING] Boston College (ID 103) not found")
            all_passed = False

        # Check for NULL team names
        cur.execute("SELECT COUNT(*) FROM ncaaf_teams WHERE team_name IS NULL")
        null_names = cur.fetchone()[0]
        if null_names > 0:
            print(f"  [WARNING] {null_names} teams with NULL names")
            all_passed = False

        # Conference distribution
        cur.execute("""
            SELECT conference, COUNT(*) as count
            FROM ncaaf_teams
            WHERE conference IS NOT NULL
            GROUP BY conference
            ORDER BY count DESC
        """)
        print(f"\n  Conference Distribution:")
        for conf, count in cur.fetchall():
            print(f"    {conf:30} {count:>3} teams")

    except psycopg2.Error as e:
        print(f"  [ERROR] {e}")
        all_passed = False

    print()

    # =====================================================================
    # Check 3: Statistics Table Validation
    # =====================================================================
    print("CHECK 3: Statistics Data Quality")
    print("-" * 80)

    try:
        # Total stats records
        cur.execute("SELECT COUNT(*) FROM ncaaf_team_stats")
        total_stats = cur.fetchone()[0]
        print(f"  Total Stat Records: {total_stats}")

        # Stats by week
        cur.execute("""
            SELECT week, COUNT(*) as teams, season_year
            FROM ncaaf_team_stats
            GROUP BY week, season_year
            ORDER BY season_year DESC, week DESC
        """)
        print(f"\n  Statistics by Week:")
        results = cur.fetchall()
        if results:
            for week, count, season in results[:5]:
                print(f"    Week {week:2} (2025): {count:3} teams")

        # Check Boston College stats
        cur.execute("""
            SELECT week, points_per_game, points_allowed_per_game, turnover_margin
            FROM ncaaf_team_stats
            WHERE team_id = '103'
            ORDER BY week DESC
            LIMIT 1
        """)
        bc_stats = cur.fetchone()
        if bc_stats:
            print(
                f"\n  [OK] Boston College Week {bc_stats[0]}: PPG={bc_stats[1]}, PAPG={bc_stats[2]}, TO_Margin={bc_stats[3]}"
            )

        # Check for missing/NULL critical fields
        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN points_per_game IS NULL THEN 1 ELSE 0 END) as null_ppg,
                SUM(CASE WHEN points_allowed_per_game IS NULL THEN 1 ELSE 0 END) as null_papg,
                SUM(CASE WHEN turnover_margin IS NULL THEN 1 ELSE 0 END) as null_tm
            FROM ncaaf_team_stats
        """)
        total, null_ppg, null_papg, null_tm = cur.fetchone()
        if null_ppg > 0 or null_papg > 0 or null_tm > 0:
            print(f"  [WARNING] NULL values found:")
            print(f"    PPG: {null_ppg}/{total}")
            print(f"    PAPG: {null_papg}/{total}")
            print(f"    Turnover Margin: {null_tm}/{total}")
            if null_ppg > 10 or null_papg > 10:
                all_passed = False
        else:
            print(f"  [OK] No NULL values in critical fields")

    except psycopg2.Error as e:
        print(f"  [ERROR] {e}")
        all_passed = False

    print()

    # =====================================================================
    # Check 4: Power Ratings Validation
    # =====================================================================
    print("CHECK 4: Power Ratings Data Quality")
    print("-" * 80)

    try:
        cur.execute("SELECT COUNT(*) FROM ncaaf_power_ratings")
        total_ratings = cur.fetchone()[0]
        print(f"  Total Rating Records: {total_ratings}")

        # Rating systems present
        cur.execute("""
            SELECT rating_system, COUNT(*) as count
            FROM ncaaf_power_ratings
            GROUP BY rating_system
            ORDER BY count DESC
        """)
        print(f"\n  Rating Systems:")
        for system, count in cur.fetchall():
            print(f"    {system:40} {count:>4} ratings")

        # Check Boston College ratings
        cur.execute("""
            SELECT rating_system, rating_value
            FROM ncaaf_power_ratings
            WHERE team_id = '103'
            ORDER BY rating_system
        """)
        bc_ratings = cur.fetchall()
        if bc_ratings:
            print(f"\n  [OK] Boston College Power Ratings:")
            for system, value in bc_ratings[:3]:
                print(f"    {system:40} {value:.2f}")

    except psycopg2.Error as e:
        print(f"  [ERROR] {e}")
        all_passed = False

    print()

    # =====================================================================
    # Check 5: Foreign Key Validation
    # =====================================================================
    print("CHECK 5: Foreign Key Integrity")
    print("-" * 80)

    try:
        # Check orphaned stats
        cur.execute("""
            SELECT COUNT(*) FROM ncaaf_team_stats
            WHERE team_id NOT IN (SELECT team_id FROM ncaaf_teams)
        """)
        orphaned_stats = cur.fetchone()[0]
        if orphaned_stats > 0:
            print(f"  [WARNING] {orphaned_stats} orphaned stat records")
            all_passed = False
        else:
            print(f"  [OK] No orphaned stat records")

        # Check orphaned schedules
        cur.execute("""
            SELECT COUNT(*) FROM ncaaf_schedules
            WHERE home_team_id NOT IN (SELECT team_id FROM ncaaf_teams)
               OR away_team_id NOT IN (SELECT team_id FROM ncaaf_teams)
        """)
        orphaned_games = cur.fetchone()[0]
        if orphaned_games > 0:
            print(f"  [WARNING] {orphaned_games} games with missing team references")
            all_passed = False
        else:
            print(f"  [OK] All game teams reference valid team IDs")

    except psycopg2.Error as e:
        print(f"  [ERROR] {e}")
        all_passed = False

    print()

    # =====================================================================
    # Check 6: Schedule Validation
    # =====================================================================
    print("CHECK 6: Schedule Data Quality")
    print("-" * 80)

    try:
        cur.execute("SELECT COUNT(*) FROM ncaaf_schedules")
        total_games = cur.fetchone()[0]
        print(f"  Total Games: {total_games}")

        # Games by status
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM ncaaf_schedules
            GROUP BY status
            ORDER BY count DESC
        """)
        print(f"\n  Games by Status:")
        for status, count in cur.fetchall():
            print(f"    {status:30} {count:>5}")

    except psycopg2.Error as e:
        print(f"  [ERROR] {e}")
        all_passed = False

    print()

    # =====================================================================
    # Summary
    # =====================================================================
    print("=" * 80)
    if all_passed:
        print("[SUCCESS] ✅ Database validation passed!")
    else:
        print("[WARNING] ⚠️  Some validation checks failed - review above")
    print("=" * 80 + "\n")

    cur.close()
    conn.close()
    return all_passed


if __name__ == "__main__":
    success = validate_database()
    exit(0 if success else 1)
