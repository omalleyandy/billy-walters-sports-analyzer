#!/usr/bin/env python3
"""Test PostgreSQL database connection - Simple version."""

import sys
import os

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection


def main():
    """Test database connection and schema."""
    print("=" * 60)
    print("BILLY WALTERS ANALYTICS - DATABASE CONNECTION TEST")
    print("=" * 60)

    # Test connection
    print("\n[1/4] Testing database connection...")
    try:
        db = get_db_connection()
    except Exception as e:
        print(f"[ERROR] Failed to create connection: {e}")
        return False

    if not db.test_connection():
        print("[ERROR] Connection failed! Check credentials in environment variables")
        return False

    # Count tables
    print("\n[2/4] Checking schema...")
    try:
        result = db.execute_query("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)

        table_count = result[0]["table_count"]
        print(f"[OK] Found {table_count} tables (expected: 10)")

        if table_count != 10:
            print("[WARNING] Table count mismatch! Re-run schema.sql")
    except Exception as e:
        print(f"[ERROR] Failed to check schema: {e}")
        return False

    # List tables
    print("\n[3/4] Listing tables...")
    try:
        result = db.execute_query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        for row in result:
            print(f"  - {row['table_name']}")
    except Exception as e:
        print(f"[ERROR] Failed to list tables: {e}")
        return False

    # Check views
    print("\n[4/4] Checking views...")
    try:
        result = db.execute_query("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        print(f"[OK] Found {len(result)} views")
        for row in result:
            print(f"  - {row['table_name']}")
    except Exception as e:
        print(f"[ERROR] Failed to check views: {e}")
        return False

    # Close connections
    db.close_all_connections()

    print("\n" + "=" * 60)
    print("[OK] DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review schema design (Option B)")
    print("2. See query examples (Option C)")
    print("3. Import Week 12 data (Option D)")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
