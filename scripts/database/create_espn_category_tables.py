#!/usr/bin/env python3
"""
Create ESPN category tables for component data storage.

Establishes separate tables for each ESPN data category:
- schedules: Game schedules with dates and venues
- injuries: Player injury reports
- team_stats: Offensive/defensive statistics
- scoreboards: Game scores and results
- standings: Team standings and records

This allows building custom power ratings from raw component data
instead of relying on Massey composite.
"""

import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection


def create_espn_schedules_table(conn, cursor):
    """Create table for ESPN game schedules."""
    print("\n[CREATE] ESPN Schedules table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS espn_schedules (
            schedule_id SERIAL PRIMARY KEY,

            -- Game identification
            game_id VARCHAR(50),
            season INT NOT NULL,
            week INT NOT NULL,
            league VARCHAR(10) NOT NULL,

            -- Teams
            home_team VARCHAR(100) NOT NULL,
            away_team VARCHAR(100) NOT NULL,

            -- Venue
            stadium VARCHAR(100),
            city VARCHAR(100),
            state VARCHAR(50),
            is_outdoor BOOLEAN,

            -- Schedule details
            game_date TIMESTAMP NOT NULL,
            day_of_week VARCHAR(10),
            is_neutral_site BOOLEAN DEFAULT FALSE,
            is_prime_time BOOLEAN,

            -- Data source
            data_source VARCHAR(100) DEFAULT 'espn',
            source_url VARCHAR(500),

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            -- Constraints
            UNIQUE(season, week, league, home_team, away_team)
        );
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_espn_schedules_game_date
        ON espn_schedules(game_date);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_espn_schedules_week
        ON espn_schedules(season, week, league);
    """)

    conn.commit()
    print("  [OK] ESPN Schedules table created")


def create_espn_injuries_table(conn, cursor):
    """Create table for ESPN injury reports."""
    print("\n[CREATE] ESPN Injuries table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS espn_injuries (
            injury_id SERIAL PRIMARY KEY,

            -- Game reference
            game_id VARCHAR(50),
            season INT NOT NULL,
            week INT NOT NULL,
            league VARCHAR(10) NOT NULL,

            -- Player info
            player_name VARCHAR(100) NOT NULL,
            position VARCHAR(20),
            jersey_number INT,

            -- Team
            team VARCHAR(100) NOT NULL,

            -- Injury details
            injury_type VARCHAR(100),
            status VARCHAR(50),
            -- ACTIVE, OUT, DOUBTFUL, QUESTIONABLE, PROBABLE,
            -- DAY_TO_DAY, LIKELY_OUT, WEEK_TO_WEEK

            severity VARCHAR(20),
            -- ELITE (starter, high impact), STARTER, BACKUP, RESERVE

            impact_estimate DECIMAL(4,2),
            -- Points we estimate this injury affects the spread

            return_week INT,  -- Expected return week

            -- Data source
            data_source VARCHAR(100) DEFAULT 'espn',
            source_url VARCHAR(500),

            -- Metadata
            report_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_espn_injuries_team_week
        ON espn_injuries(team, week);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_espn_injuries_status
        ON espn_injuries(status);
    """)

    conn.commit()
    print("  [OK] ESPN Injuries table created")


def create_espn_team_stats_table(conn, cursor):
    """Create table for ESPN team statistics."""
    print("\n[CREATE] ESPN Team Stats table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS espn_team_stats (
            stat_id SERIAL PRIMARY KEY,

            -- Team identification
            season INT NOT NULL,
            week INT NOT NULL,
            league VARCHAR(10) NOT NULL,
            team VARCHAR(100) NOT NULL,

            -- Offensive stats
            points_per_game DECIMAL(6,2),
            total_yards_per_game DECIMAL(8,2),
            passing_yards_per_game DECIMAL(8,2),
            rushing_yards_per_game DECIMAL(8,2),
            passes_completed DECIMAL(6,2),
            passes_attempted DECIMAL(6,2),
            completion_percentage DECIMAL(5,2),
            yards_per_attempt DECIMAL(5,2),
            touchdowns_passing INT,
            touchdowns_rushing INT,
            interceptions INT,
            fumbles INT,

            -- Defensive stats
            points_allowed_per_game DECIMAL(6,2),
            yards_allowed_per_game DECIMAL(8,2),
            passing_yards_allowed_per_game DECIMAL(8,2),
            rushing_yards_allowed_per_game DECIMAL(8,2),
            sacks INT,
            interceptions_gained INT,
            fumbles_recovered INT,

            -- Special efficiency metrics
            turnover_margin DECIMAL(5,2),
            third_down_percentage DECIMAL(5,2),
            fourth_down_percentage DECIMAL(5,2),
            red_zone_percentage DECIMAL(5,2),

            -- Data source
            data_source VARCHAR(100) DEFAULT 'espn',
            source_url VARCHAR(500),

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            -- Constraints
            UNIQUE(season, week, league, team)
        );
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_espn_team_stats_week
        ON espn_team_stats(season, week, league, team);
    """)

    conn.commit()
    print("  [OK] ESPN Team Stats table created")


def create_espn_scoreboards_table(conn, cursor):
    """Create table for ESPN game scores and results."""
    print("\n[CREATE] ESPN Scoreboards table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS espn_scoreboards (
            scoreboard_id SERIAL PRIMARY KEY,

            -- Game reference
            game_id VARCHAR(50),
            season INT NOT NULL,
            week INT NOT NULL,
            league VARCHAR(10) NOT NULL,

            -- Teams
            home_team VARCHAR(100) NOT NULL,
            away_team VARCHAR(100) NOT NULL,

            -- Score
            home_score INT,
            away_score INT,
            total_points INT,
            final_margin INT,

            -- Game status
            status VARCHAR(20),
            -- SCHEDULED, IN_PROGRESS, FINAL, POSTPONED, CANCELLED

            quarter INT,
            time_remaining VARCHAR(10),

            -- Data source
            data_source VARCHAR(100) DEFAULT 'espn',
            source_url VARCHAR(500),

            -- Metadata
            game_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_espn_scoreboards_game
        ON espn_scoreboards(game_id);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_espn_scoreboards_week
        ON espn_scoreboards(season, week, league);
    """)

    conn.commit()
    print("  [OK] ESPN Scoreboards table created")


def create_espn_standings_table(conn, cursor):
    """Create table for ESPN team standings."""
    print("\n[CREATE] ESPN Standings table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS espn_standings (
            standing_id SERIAL PRIMARY KEY,

            -- Team identification
            season INT NOT NULL,
            week INT NOT NULL,
            league VARCHAR(10) NOT NULL,
            team VARCHAR(100) NOT NULL,

            -- Conference/Division
            conference VARCHAR(50),
            division VARCHAR(50),

            -- Record
            wins INT,
            losses INT,
            ties INT,

            -- Winning percentage
            win_percentage DECIMAL(5,4),

            -- Home/Away split
            home_wins INT,
            home_losses INT,
            away_wins INT,
            away_losses INT,

            -- Streak
            streak_type VARCHAR(10),  -- W or L
            streak_count INT,

            -- Data source
            data_source VARCHAR(100) DEFAULT 'espn',
            source_url VARCHAR(500),

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            -- Constraints
            UNIQUE(season, week, league, team)
        );
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_espn_standings_week
        ON espn_standings(season, week, league);
    """)

    conn.commit()
    print("  [OK] ESPN Standings table created")


def create_massey_reference_table(conn, cursor):
    """Create table for Massey ratings as reference/fallback."""
    print("\n[CREATE] Massey Reference table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS massey_ratings (
            massey_id SERIAL PRIMARY KEY,

            -- Team identification
            season INT NOT NULL,
            week INT NOT NULL,
            league VARCHAR(10) NOT NULL,
            team VARCHAR(100) NOT NULL,

            -- Rankings (Massey provides multiple ranking systems)
            ranking INT,
            rating DECIMAL(6,2),

            -- Components
            offense_rating DECIMAL(6,2),
            defense_rating DECIMAL(6,2),
            sos_rating DECIMAL(6,2),

            -- Record
            wins INT,
            losses INT,
            ties INT,

            -- Data source
            data_source VARCHAR(100) DEFAULT 'massey',
            source_url VARCHAR(500),

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            -- Constraints
            UNIQUE(season, week, league, team)
        );
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_massey_ratings_week
        ON massey_ratings(season, week, league);
    """)

    conn.commit()
    print("  [OK] Massey Reference table created")


def main():
    """Run all table creations."""
    db = get_db_connection()

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        print("=" * 70)
        print("CREATE ESPN CATEGORY TABLES")
        print("=" * 70)

        create_espn_schedules_table(conn, cursor)
        create_espn_injuries_table(conn, cursor)
        create_espn_team_stats_table(conn, cursor)
        create_espn_scoreboards_table(conn, cursor)
        create_espn_standings_table(conn, cursor)
        create_massey_reference_table(conn, cursor)

        print("\n" + "=" * 70)
        print("[OK] ALL ESPN CATEGORY TABLES CREATED")
        print("=" * 70)
        print("\nNew tables:")
        print("  - espn_schedules (game schedules and venues)")
        print("  - espn_injuries (player injury reports)")
        print("  - espn_team_stats (team statistics)")
        print("  - espn_scoreboards (game scores and results)")
        print("  - espn_standings (team standings)")
        print("  - massey_ratings (reference/fallback)")
        print("\nYour custom power ratings will be built from:")
        print("  - espn_team_stats (offensive/defensive efficiency)")
        print("  - espn_injuries (injury impact)")
        print("  - espn_standings (team health/momentum)")
        print("  - Custom formula in power_ratings table")

        cursor.close()
        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to create tables: {str(e)}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close_all_connections()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
