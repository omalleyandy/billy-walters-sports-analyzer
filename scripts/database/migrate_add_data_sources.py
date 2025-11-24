#!/usr/bin/env python3
"""
Migration: Add data source tracking to database.

Adds:
1. data_sources table to track all data sources
2. data_source column to games, power_ratings, odds tables
3. Support for historical snapshots (weekly data retention)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db import get_db_connection

def create_data_sources_table(conn, cursor):
    """Create data_sources reference table."""
    print("\n[MIGRATION] Creating data_sources table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_sources (
            source_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            source_type VARCHAR(50) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Insert common sources
    sources = [
        ('massey', 'ratings', 'Massey Ratings Composite Rankings'),
        ('espn', 'ratings', 'ESPN Team Statistics and Ratings'),
        ('nfl_com', 'schedule', 'Official NFL.com Schedule'),
        ('ncaa_com', 'schedule', 'Official NCAA.com Schedule'),
        ('action_network', 'odds', 'Action Network Public Betting Data'),
        ('covers', 'odds', 'Covers Sportsbook Consensus Odds'),
        ('vegas_insider', 'odds', 'Vegas Insider Consensus Lines'),
        ('overtime_ag', 'odds', 'Overtime.ag Betting Lines'),
        ('pinnacle', 'odds', 'Pinnacle Sportsbook Odds'),
    ]

    for source_name, source_type, description in sources:
        cursor.execute("""
            INSERT INTO data_sources (name, source_type, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING;
        """, (source_name, source_type, description))

    conn.commit()
    print("[OK] data_sources table created with 9 sources")


def add_data_source_to_games(conn, cursor):
    """Add data_source column to games table."""
    print("\n[MIGRATION] Adding data_source to games table...")

    try:
        cursor.execute("""
            ALTER TABLE games
            ADD COLUMN data_source VARCHAR(100) DEFAULT 'nfl_com';
        """)
        conn.commit()
        print("[OK] data_source column added to games")
    except Exception as e:
        if 'already exists' in str(e):
            print("[SKIP] data_source column already exists in games")
            conn.rollback()
        else:
            raise


def add_data_source_to_power_ratings(conn, cursor):
    """Update power_ratings to use data_sources table."""
    print("\n[MIGRATION] Verifying power_ratings has source column...")

    try:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'power_ratings' AND column_name = 'source';
        """)
        if cursor.fetchone():
            print("[OK] power_ratings already has source column")
        else:
            cursor.execute("""
                ALTER TABLE power_ratings
                ADD COLUMN source VARCHAR(100) DEFAULT 'massey';
            """)
            conn.commit()
            print("[OK] source column added to power_ratings")
    except Exception as e:
        print(f"[WARNING] {str(e)}")
        conn.rollback()


def add_data_source_to_odds(conn, cursor):
    """Update odds table - already has sportsbook, add data_collection_source."""
    print("\n[MIGRATION] Adding data_collection_source to odds table...")

    try:
        cursor.execute("""
            ALTER TABLE odds
            ADD COLUMN data_collection_source VARCHAR(100) DEFAULT 'overtime_ag';
        """)
        conn.commit()
        print("[OK] data_collection_source column added to odds")
    except Exception as e:
        if 'already exists' in str(e):
            print("[SKIP] data_collection_source column already exists in odds")
            conn.rollback()
        else:
            raise


def create_power_ratings_history_table(conn, cursor):
    """Create table to track power ratings history for audit/rollback."""
    print("\n[MIGRATION] Creating power_ratings_history table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS power_ratings_history (
            history_id SERIAL PRIMARY KEY,

            -- Original rating ID
            original_id INT,

            -- Rating snapshot
            season INT NOT NULL,
            week INT NOT NULL,
            league VARCHAR(10) NOT NULL,
            team VARCHAR(100) NOT NULL,
            rating DECIMAL(6,2) NOT NULL,
            source VARCHAR(100) NOT NULL,

            -- Snapshot metadata
            snapshot_date TIMESTAMP NOT NULL,
            action VARCHAR(20),  -- 'INSERT', 'UPDATE', 'DELETE'

            -- Audit trail
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Create index for fast lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pr_history_season_week
        ON power_ratings_history(season, week, team);
    """)

    conn.commit()
    print("[OK] power_ratings_history table created")


def create_odds_history_table(conn, cursor):
    """Create table to track odds snapshots for line movement analysis."""
    print("\n[MIGRATION] Creating odds_history table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS odds_history (
            history_id SERIAL PRIMARY KEY,

            -- Original odds ID
            original_id INT,

            -- Game reference
            game_id VARCHAR(50) NOT NULL,

            -- Odds snapshot
            sportsbook VARCHAR(50) NOT NULL,
            home_spread DECIMAL(4,1),
            total DECIMAL(4,1),
            home_moneyline INT,

            -- Line movement
            previous_home_spread DECIMAL(4,1),
            previous_total DECIMAL(4,1),
            spread_movement DECIMAL(4,1),
            total_movement DECIMAL(4,1),

            -- Snapshot metadata
            snapshot_date TIMESTAMP NOT NULL,
            data_collection_source VARCHAR(100),

            -- Audit trail
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_odds_history_game_date
        ON odds_history(game_id, snapshot_date);
    """)

    conn.commit()
    print("[OK] odds_history table created")


def main():
    """Run all migrations."""
    db = get_db_connection()

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        print("=" * 70)
        print("MIGRATION: ADD DATA SOURCE TRACKING")
        print("=" * 70)

        create_data_sources_table(conn, cursor)
        add_data_source_to_games(conn, cursor)
        add_data_source_to_power_ratings(conn, cursor)
        add_data_source_to_odds(conn, cursor)
        create_power_ratings_history_table(conn, cursor)
        create_odds_history_table(conn, cursor)

        print("\n" + "=" * 70)
        print("[OK] ALL MIGRATIONS COMPLETED SUCCESSFULLY")
        print("=" * 70)

        cursor.close()

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close_all_connections()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
