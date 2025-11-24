#!/usr/bin/env python3
"""
Setup NFL 2025 Database Schema
Applies nfl_extensions.sql schema to PostgreSQL sports_db
"""

import psycopg2
from pathlib import Path
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def read_sql_file(filepath: Path) -> str:
    """Read SQL file contents"""
    try:
        with open(filepath) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read SQL file: {e}")
        raise


def setup_schema(
    dbname: str = "sports_db",
    user: str = "postgres",
    password: str = "postgres",
    host: str = "localhost",
    port: int = 5432,
) -> bool:
    """Apply NFL schema to database"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        logger.info("[OK] Connected to PostgreSQL")

        # Read SQL file
        sql_file = Path(__file__).parent.parent.parent / "database" / "nfl_extensions.sql"
        sql_content = read_sql_file(sql_file)

        # Execute schema
        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        logger.info("[OK] Schema applied successfully")

        # Verify tables created
        cursor.execute(
            """
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE 'nfl_%'
            """
        )
        tables = cursor.fetchall()
        logger.info(f"[OK] Created tables: {[t[0] for t in tables]}")

        # Verify views created
        cursor.execute(
            """
            SELECT viewname FROM pg_views
            WHERE schemaname = 'public'
            AND viewname LIKE 'nfl_%'
            """
        )
        views = cursor.fetchall()
        logger.info(f"[OK] Created views: {[v[0] for v in views]}")

        cursor.close()
        conn.close()
        logger.info("[OK] Disconnected from PostgreSQL")
        return True

    except psycopg2.Error as e:
        logger.error(f"PostgreSQL error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Setup NFL 2025 database schema"
    )
    parser.add_argument(
        "--dbname",
        default="sports_db",
        help="Database name (default: sports_db)",
    )
    parser.add_argument(
        "--user",
        default="postgres",
        help="PostgreSQL user (default: postgres)",
    )
    parser.add_argument(
        "--password",
        default="postgres",
        help="PostgreSQL password",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Database host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5432,
        help="Database port (default: 5432)",
    )

    args = parser.parse_args()

    success = setup_schema(
        dbname=args.dbname,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port,
    )

    if success:
        logger.info("[OK] Setup complete!")
        exit(0)
    else:
        logger.error("[ERROR] Setup failed!")
        exit(1)
