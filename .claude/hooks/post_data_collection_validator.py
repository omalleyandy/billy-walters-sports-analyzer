#!/usr/bin/env python3
"""
Post-Data Collection Validation Hook

Runs after data collection to ensure:
1. All required data was collected
2. Data quality is acceptable
3. No data inconsistencies
4. Ready for analysis

Exit codes:
- 0: All data quality checks passed
- 1: Data quality issues, manual review needed
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db import get_db_connection
from scripts.utilities.nfl_week_detector import NFLWeekDetector


class PostFlightValidator:
    """Post-flight validation system."""

    def __init__(self, week: int = None):
        """Initialize validator."""
        self.week = week or self._detect_week()
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.db = None

    def _detect_week(self) -> int:
        """Auto-detect current week if not provided."""
        detector = NFLWeekDetector()
        week = detector.get_current_week()
        if week is None:
            raise ValueError("Cannot auto-detect week (offseason/playoffs)")
        return week

    def connect_database(self) -> bool:
        """Connect to database."""
        print("\n[SETUP] Connecting to database...")
        try:
            self.db = get_db_connection()
            if self.db.test_connection():
                print(f"  [OK] Connected")
                return True
            else:
                print("  [ERROR] Connection test failed")
                return False
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            return False

    def check_games_loaded(self) -> bool:
        """Check if games were loaded."""
        print("\n[CHECK 1/6] Games Loaded...")

        try:
            result = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM games
                WHERE season = 2025 AND week = %s AND league = 'NFL'
                """,
                (self.week,),
            )

            count = result[0]["count"]
            expected = 1  # At least 1 game

            if count >= expected:
                print(f"  [OK] Found {count} games (expected: >{expected})")
                self.checks_passed += 1
                return True
            else:
                print(f"  [ERROR] Found {count} games (expected: >{expected})")
                self.checks_failed += 1
                return False

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def check_power_ratings_loaded(self) -> bool:
        """Check if power ratings were loaded."""
        print("\n[CHECK 2/6] Power Ratings Loaded...")

        try:
            result = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM power_ratings
                WHERE season = 2025 AND week = %s
                """,
                (self.week,),
            )

            count = result[0]["count"]
            expected = 2  # At least 2 teams

            if count >= expected:
                print(f"  [OK] Found {count} power ratings (expected: >{expected})")
                self.checks_passed += 1
                return True
            else:
                print(f"  [ERROR] Found {count} power ratings (expected: >{expected})")
                self.checks_failed += 1
                return False

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def check_odds_loaded(self) -> bool:
        """Check if odds were loaded."""
        print("\n[CHECK 3/6] Odds Data Loaded...")

        try:
            # Get game count
            games = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM games
                WHERE season = 2025 AND week = %s
                """,
                (self.week,),
            )
            game_count = games[0]["count"]

            # Get odds count
            odds = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM odds o
                WHERE o.game_id IN (
                    SELECT game_id FROM games
                    WHERE season = 2025 AND week = %s
                )
                """,
                (self.week,),
            )
            odds_count = odds[0]["count"]

            # Should have at least 1 odds record per game
            if odds_count >= game_count:
                print(f"  [OK] Found {odds_count} odds records for {game_count} games")
                self.checks_passed += 1
                return True
            else:
                print(f"  [WARNING] Found {odds_count} odds, expected >{game_count}")
                self.checks_failed += 1
                return False

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def check_data_freshness(self) -> bool:
        """Check if data is recent (not stale)."""
        print("\n[CHECK 4/6] Data Freshness...")

        try:
            result = self.db.execute_query(
                """
                SELECT MAX(created_at) as last_update FROM odds
                WHERE game_id IN (
                    SELECT game_id FROM games
                    WHERE season = 2025 AND week = %s
                )
                """,
                (self.week,),
            )

            if result and result[0]["last_update"]:
                last_update = result[0]["last_update"]
                now = datetime.now()
                time_diff = (now - last_update).total_seconds() / 3600

                if time_diff < 24:  # Within 24 hours
                    print(f"  [OK] Data is fresh ({time_diff:.1f} hours old)")
                    self.checks_passed += 1
                    return True
                else:
                    print(f"  [WARNING] Data is {time_diff:.1f} hours old")
                    self.warnings += 1
                    return True
            else:
                print("  [ERROR] No data timestamp found")
                self.checks_failed += 1
                return False

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def check_weather_data(self) -> bool:
        """Check if weather data exists."""
        print("\n[CHECK 5/6] Weather Data...")

        try:
            result = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM weather w
                WHERE w.game_id IN (
                    SELECT game_id FROM games
                    WHERE season = 2025 AND week = %s AND is_outdoor = TRUE
                )
                """,
                (self.week,),
            )

            count = result[0]["count"]
            if count > 0:
                print(f"  [OK] Found {count} weather records")
                self.checks_passed += 1
                return True
            else:
                print("  [WARNING] No weather data found (may not be needed)")
                self.warnings += 1
                return True

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def check_null_values(self) -> bool:
        """Check for unexpected NULL values."""
        print("\n[CHECK 6/6] Data Completeness...")

        try:
            # Check for NULL spreads (critical)
            result = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM odds o
                WHERE o.game_id IN (
                    SELECT game_id FROM games
                    WHERE season = 2025 AND week = %s
                )
                AND (o.home_spread IS NULL OR o.total IS NULL)
                """,
                (self.week,),
            )

            null_count = result[0]["count"]
            if null_count == 0:
                print("  [OK] No NULL spreads or totals")
                self.checks_passed += 1
                return True
            else:
                print(f"  [WARNING] Found {null_count} records with NULL odds")
                self.warnings += 1
                return True

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            self.checks_failed += 1
            return False

    def generate_data_quality_report(self) -> str:
        """Generate detailed data quality report."""
        report = "\n" + "=" * 70 + "\n"
        report += "DATA QUALITY REPORT\n"
        report += "=" * 70 + "\n\n"

        try:
            # Games summary
            games = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM games
                WHERE season = 2025 AND week = %s
                """,
                (self.week,),
            )
            report += f"Week {self.week} NFL Games: {games[0]['count']}\n"

            # Power ratings summary
            ratings = self.db.execute_query(
                """
                SELECT COUNT(DISTINCT team) as count FROM power_ratings
                WHERE season = 2025 AND week = %s
                """,
                (self.week,),
            )
            report += f"Power Ratings: {ratings[0]['count']} teams\n"

            # Odds summary
            odds = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM odds
                WHERE game_id IN (
                    SELECT game_id FROM games
                    WHERE season = 2025 AND week = %s
                )
                """,
                (self.week,),
            )
            report += f"Odds Records: {odds[0]['count']}\n"

            # Missing moneylines
            missing_ml = self.db.execute_query(
                """
                SELECT COUNT(*) as count FROM odds
                WHERE game_id IN (
                    SELECT game_id FROM games
                    WHERE season = 2025 AND week = %s
                )
                AND (home_moneyline IS NULL OR away_moneyline IS NULL)
                """,
                (self.week,),
            )
            report += f"Missing Moneylines: {missing_ml[0]['count']} records\n"

            report += "\n" + "=" * 70 + "\n"

        except Exception as e:
            report += f"Error generating report: {e}\n"

        return report

    def run_all_checks(self) -> bool:
        """Run all validation checks."""
        print("=" * 70)
        print(f"POST-FLIGHT VALIDATION - WEEK {self.week}")
        print("=" * 70)

        if not self.connect_database():
            return False

        checks = [
            self.check_games_loaded,
            self.check_power_ratings_loaded,
            self.check_odds_loaded,
            self.check_data_freshness,
            self.check_weather_data,
            self.check_null_values,
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"[FATAL] Check failed: {e}")
                self.checks_failed += 1

        # Generate report
        report = self.generate_data_quality_report()
        print(report)

        print("=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Checks Passed: {self.checks_passed}")
        print(f"Checks Failed: {self.checks_failed}")
        print(f"Warnings:     {self.warnings}")

        if self.checks_failed == 0:
            print("\n[OK] Data quality acceptable - ready for analysis")
            if self.warnings > 0:
                print(f"[WARNING] {self.warnings} warning(s) - review report above")
            return True
        else:
            print(f"\n[ERROR] {self.checks_failed} check(s) failed - review data")
            return False

    def cleanup(self):
        """Clean up resources."""
        if self.db:
            self.db.close_all_connections()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Post-flight validation")
    parser.add_argument(
        "--week", type=int, default=None, help="NFL week (auto-detect if not provided)"
    )

    args = parser.parse_args()

    validator = PostFlightValidator(week=args.week)

    try:
        success = validator.run_all_checks()
        return 0 if success else 1
    except Exception as e:
        print(f"[FATAL] {str(e)}")
        return 1
    finally:
        validator.cleanup()


if __name__ == "__main__":
    sys.exit(main())
