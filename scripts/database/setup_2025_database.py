#!/usr/bin/env python3
"""
Setup 2025 NCAAF Historical Database
Creates sports_db database and schema
"""

import psycopg2
from psycopg2 import sql
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database(password: str = "Omarley@2025") -> bool:
    """Create sports_db database"""
    try:
        # Connect to default postgres database to create sports_db
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password=password,
            host="localhost",
            port=5432,
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'sports_db';"
        )
        if cursor.fetchone():
            logger.info("[OK] Database sports_db already exists")
            cursor.close()
            conn.close()
            return True

        # Create database
        cursor.execute("CREATE DATABASE sports_db;")
        logger.info("[OK] Created database sports_db")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False


def create_schema(password: str = "Omarley@2025") -> bool:
    """Create ncaaf_team_stats table"""
    try:
        conn = psycopg2.connect(
            dbname="sports_db",
            user="postgres",
            password=password,
            host="localhost",
            port=5432,
        )
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'ncaaf_team_stats';"
        )
        if cursor.fetchone():
            logger.info("[OK] Table ncaaf_team_stats already exists")
            cursor.close()
            conn.close()
            return True

        # Create table
        create_table_sql = """
        CREATE TABLE ncaaf_team_stats (
            id SERIAL PRIMARY KEY,
            team_id VARCHAR(10) NOT NULL,
            team_name VARCHAR(255) NOT NULL,
            week INTEGER NOT NULL,
            season_year INTEGER NOT NULL,
            games_played FLOAT,
            points_per_game FLOAT,
            total_points FLOAT,
            passing_yards_per_game FLOAT,
            rushing_yards_per_game FLOAT,
            total_yards_per_game FLOAT,
            points_allowed_per_game FLOAT,
            passing_yards_allowed_per_game FLOAT,
            rushing_yards_allowed_per_game FLOAT,
            total_yards_allowed_per_game FLOAT,
            turnover_margin FLOAT,
            third_down_pct FLOAT,
            takeaways INTEGER,
            giveaways INTEGER,
            UNIQUE(team_id, week, season_year)
        );
        """

        cursor.execute(create_table_sql)
        conn.commit()
        logger.info("[OK] Created table ncaaf_team_stats")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Failed to create schema: {e}")
        return False


if __name__ == "__main__":
    import sys

    password = sys.argv[1] if len(sys.argv) > 1 else "Omarley@2025"

    logger.info("Setting up 2025 NCAAF Historical Database...")
    if create_database(password) and create_schema(password):
        logger.info("[OK] Database setup complete!")
        sys.exit(0)
    else:
        logger.error("[ERROR] Database setup failed")
        sys.exit(1)
