#!/usr/bin/env python3
"""
Pre-Data Collection Validation Hook

Runs before any data collection to ensure:
1. Environment variables are set
2. Database connection works
3. Required directories exist
4. Current NFL week detected
5. No data collection already in progress

Exit codes:
- 0: All checks passed, proceed with collection
- 1: Critical error, abort collection
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db import get_db_connection
from scripts.utilities.nfl_week_detector import NFLWeekDetector


class PreFlightValidator:
    """Pre-flight validation system."""

    def __init__(self):
        """Initialize validator."""
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def check_environment_variables(self) -> bool:
        """Check if required environment variables are set."""
        print("\n[CHECK 1/6] Environment Variables...")

        required_vars = {
            "DB_HOST": "Database host",
            "DB_PORT": "Database port",
            "DB_NAME": "Database name",
            "DB_USER": "Database user",
            "DB_PASSWORD": "Database password",
        }

        all_set = True
        for var, description in required_vars.items():
            if os.getenv(var):
                print(f"  [OK] {var:<15} = {description}")
                self.checks_passed += 1
            else:
                print(f"  [ERROR] {var:<15} NOT SET - {description}")
                self.checks_failed += 1
                all_set = False

        return all_set

    def check_database_connection(self) -> bool:
        """Check if database connection works."""
        print("\n[CHECK 2/6] Database Connection...")

        try:
            db = get_db_connection()
            if db.test_connection():
                print(f"  [OK] Connected to {db.database}@{db.host}:{db.port}")
                self.checks_passed += 1
                db.close_all_connections()
                return True
            else:
                print("  [ERROR] Connection test failed")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def check_output_directories(self) -> bool:
        """Check if required output directories exist."""
        print("\n[CHECK 3/6] Output Directories...")

        required_dirs = [
            "output",
            "output/edge_detection",
            "output/overtime",
            "output/massey",
            "data/current",
            "docs/performance_reports",
        ]

        all_exist = True
        for dir_path in required_dirs:
            full_path = Path(dir_path)
            if full_path.exists():
                print(f"  [OK] {dir_path}")
                self.checks_passed += 1
            else:
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    print(f"  [CREATED] {dir_path}")
                    self.checks_passed += 1
                except Exception as e:
                    print(f"  [ERROR] Cannot create {dir_path}: {e}")
                    self.checks_failed += 1
                    all_exist = False

        return all_exist

    def check_current_nfl_week(self) -> bool:
        """Detect current NFL week."""
        print("\n[CHECK 4/6] Current NFL Week...")

        try:
            detector = NFLWeekDetector()
            season_info = detector.get_season_info()

            week = season_info["current_week"]
            is_regular_season = season_info["is_regular_season"]

            if is_regular_season:
                print(f"  [OK] Week {week} of {season_info['season']} season")
                print(f"       Dates: {season_info['week_start']} to {season_info['week_end']}")
                self.checks_passed += 1
                return True
            else:
                if season_info["is_offseason"]:
                    print("  [WARNING] Currently in offseason - no games scheduled")
                    self.warnings += 1
                    return False
                elif season_info["is_playoffs"]:
                    print("  [WARNING] Currently in playoffs - use different schedule")
                    self.warnings += 1
                    return False

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def check_no_collection_in_progress(self) -> bool:
        """Check if data collection is already running."""
        print("\n[CHECK 5/6] No Collection in Progress...")

        lock_file = Path(".claude/hooks/.collection_lock")

        if lock_file.exists():
            try:
                with open(lock_file, "r") as f:
                    lock_info = f.read()
                print(f"  [ERROR] Collection already in progress:")
                print(f"         {lock_info}")
                self.checks_failed += 1
                return False
            except Exception as e:
                print(f"  [WARNING] Cannot read lock file: {e}")
                self.warnings += 1
                return True
        else:
            print("  [OK] No collection in progress")
            self.checks_passed += 1

            # Create lock file
            try:
                lock_file.parent.mkdir(parents=True, exist_ok=True)
                with open(lock_file, "w") as f:
                    f.write(
                        f"Started: {datetime.now().isoformat()}\n"
                        f"Process: {os.getpid()}"
                    )
            except Exception as e:
                print(f"  [WARNING] Cannot create lock file: {e}")
                self.warnings += 1

            return True

    def check_database_schema(self) -> bool:
        """Verify database schema is complete."""
        print("\n[CHECK 6/6] Database Schema...")

        try:
            db = get_db_connection()

            # Check table count
            result = db.execute_query(
                """
                SELECT COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
            )

            table_count = result[0]["table_count"]
            expected_tables = 10

            if table_count == expected_tables:
                print(f"  [OK] Found {table_count} tables (expected: {expected_tables})")
                self.checks_passed += 1
                db.close_all_connections()
                return True
            else:
                print(
                    f"  [ERROR] Found {table_count} tables "
                    f"(expected: {expected_tables})"
                )
                self.checks_failed += 1
                db.close_all_connections()
                return False

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def run_all_checks(self) -> bool:
        """Run all validation checks."""
        print("=" * 70)
        print("PRE-FLIGHT VALIDATION")
        print("=" * 70)

        checks = [
            self.check_environment_variables,
            self.check_database_connection,
            self.check_output_directories,
            self.check_current_nfl_week,
            self.check_no_collection_in_progress,
            self.check_database_schema,
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"[FATAL] Check failed: {e}")
                self.checks_failed += 1

        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Checks Passed: {self.checks_passed}")
        print(f"Checks Failed: {self.checks_failed}")
        print(f"Warnings:     {self.warnings}")

        if self.checks_failed == 0:
            print("\n[OK] All checks passed - ready for data collection")
            return True
        else:
            print(f"\n[ERROR] {self.checks_failed} check(s) failed - aborting")
            return False


def cleanup_lock_file():
    """Remove lock file on exit."""
    lock_file = Path(".claude/hooks/.collection_lock")
    try:
        if lock_file.exists():
            lock_file.unlink()
    except Exception as e:
        print(f"[WARNING] Could not remove lock file: {e}")


def main():
    """Main function."""
    validator = PreFlightValidator()

    try:
        success = validator.run_all_checks()
        return 0 if success else 1
    finally:
        cleanup_lock_file()


if __name__ == "__main__":
    sys.exit(main())
