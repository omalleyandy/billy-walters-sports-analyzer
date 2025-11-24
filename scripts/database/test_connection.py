"""Test PostgreSQL database connection."""

import os
from src.db import get_db_connection


def main():
    """Test database connection and schema."""
    print("=" * 60)
    print("BILLY WALTERS ANALYTICS - DATABASE CONNECTION TEST")
    print("=" * 60)

    # Test connection
    print("\n[1/4] Testing database connection...")
    db = get_db_connection()

    if not db.test_connection():
        print("[ERROR] Connection failed! Check credentials in .env")
        return False

    # Count tables
    print("\n[2/4] Checking schema...")
    result = db.execute_query("""
        SELECT COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)

    table_count = result[0]['table_count']
    print(f"[OK] Found {table_count} tables (expected: 9)")

    if table_count != 9:
        print("[WARNING] Table count mismatch! Re-run schema.sql")

    # List tables
    print("\n[3/4] Listing tables...")
    result = db.execute_query("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)

    for row in result:
        print(f"  - {row['table_name']}")

    # Check views
    print("\n[4/4] Checking views...")
    result = db.execute_query("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    print(f"[OK] Found {len(result)} views")
    for row in result:
        print(f"  - {row['table_name']}")

    print("\n" + "=" * 60)
    print("[OK] DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run data migration: uv run python scripts/database/migrate_week_12.py")
    print("2. Verify data: SELECT COUNT(*) FROM games;")
    print("3. Start using database in edge detection!")

    return True


if __name__ == "__main__":
    main()
