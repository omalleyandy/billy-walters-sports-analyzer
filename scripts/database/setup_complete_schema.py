#!/usr/bin/env python3
"""
Complete Database Schema Setup
Applies base schema and NFL extensions to PostgreSQL sports_db
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


def apply_schema(
    sql_content: str,
    schema_name: str,
    conn: psycopg2.extensions.connection,
) -> bool:
    """Apply SQL schema to database"""
    try:
        cursor = conn.cursor()
        logger.info(f"Applying {schema_name}...")
        cursor.execute(sql_content)
        conn.commit()
        logger.info(f"[OK] {schema_name} applied successfully")
        cursor.close()
        return True
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL error in {schema_name}: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error in {schema_name}: {e}")
        return False


def setup_complete_schema(
    dbname: str = "sports_db",
    user: str = "postgres",
    password: str = "postgres",
    host: str = "localhost",
    port: int = 5432,
) -> bool:
    """Apply complete database schema"""
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

        # Get database directory
        db_dir = Path(__file__).parent.parent.parent / "database"

        # Step 1: Apply base schema
        base_schema_file = db_dir / "schema.sql"
        base_schema_content = read_sql_file(base_schema_file)
        if not apply_schema(base_schema_content, "Base Schema", conn):
            return False

        # Step 2: Apply NFL extensions
        nfl_ext_file = db_dir / "nfl_extensions.sql"
        nfl_ext_content = read_sql_file(nfl_ext_file)
        if not apply_schema(nfl_ext_content, "NFL Extensions", conn):
            return False

        # Step 3: Verify tables
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        tables = [t[0] for t in cursor.fetchall()]
        logger.info(f"[OK] Created tables ({len(tables)}): {', '.join(tables)}")

        # Step 4: Verify views
        cursor.execute(
            """
            SELECT viewname FROM pg_views
            WHERE schemaname = 'public'
            ORDER BY viewname
            """
        )
        views = [v[0] for v in cursor.fetchall()]
        if views:
            logger.info(f"[OK] Created views ({len(views)}): {', '.join(views)}")

        cursor.close()
        conn.close()
        logger.info("[OK] Disconnected from PostgreSQL")
        return True

    except psycopg2.Error as e:
        logger.error(f"PostgreSQL connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Setup complete database schema (base + NFL extensions)"
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

    success = setup_complete_schema(
        dbname=args.dbname,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port,
    )

    if success:
        logger.info("[OK] Complete schema setup successful!")
        exit(0)
    else:
        logger.error("[ERROR] Schema setup failed!")
        exit(1)
