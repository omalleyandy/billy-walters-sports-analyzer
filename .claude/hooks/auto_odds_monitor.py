#!/usr/bin/env python3
"""
Automatic Odds Monitor and Edge Detector Trigger

Monitors for new odds data and automatically triggers edge detection when:
1. New odds are detected
2. Odds are <5 minutes old (fresh data)
3. Edge detection hasn't been run recently for this data

This allows continuous monitoring throughout the week.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db import get_db_connection
from scripts.utilities.nfl_week_detector import NFLWeekDetector


class OddsMonitor:
    """Monitor for new odds and trigger edge detection."""

    FRESHNESS_THRESHOLD = 5  # Minutes
    CACHE_FILE = Path(".claude/hooks/.odds_monitor_cache.json")

    def __init__(self):
        """Initialize monitor."""
        self.db = None
        self.week = None
        self.new_odds_detected = False
        self.trigger_edge_detection = False

    def connect_database(self) -> bool:
        """Connect to database."""
        try:
            self.db = get_db_connection()
            if self.db.test_connection():
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False

    def detect_week(self) -> bool:
        """Detect current NFL week."""
        try:
            detector = NFLWeekDetector()
            season_info = detector.get_season_info()

            if not season_info["is_regular_season"]:
                print(f"[INFO] Not regular season (offseason/playoffs)")
                return False

            self.week = season_info["current_week"]
            return True
        except Exception as e:
            print(f"[ERROR] Week detection failed: {e}")
            return False

    def get_latest_odds_timestamp(self) -> datetime:
        """Get timestamp of most recent odds data."""
        try:
            result = self.db.execute_query(
                """
                SELECT MAX(o.created_at) as latest
                FROM odds o
                WHERE o.game_id IN (
                    SELECT game_id FROM games
                    WHERE season = 2025 AND week = %s AND league = 'NFL'
                )
                """,
                (self.week,),
            )

            if result and result[0]["latest"]:
                return result[0]["latest"]
            else:
                return None

        except Exception as e:
            print(f"[ERROR] Could not get latest odds timestamp: {e}")
            return None

    def load_cache(self) -> dict:
        """Load monitor cache from file."""
        if not self.CACHE_FILE.exists():
            return {"last_odds_timestamp": None, "last_edge_detection": None}

        try:
            with open(self.CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Could not load cache: {e}")
            return {"last_odds_timestamp": None, "last_edge_detection": None}

    def save_cache(self, cache: dict) -> bool:
        """Save monitor cache to file."""
        try:
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"[WARNING] Could not save cache: {e}")
            return False

    def check_odds_freshness(self) -> bool:
        """Check if odds data is fresh (within last 5 minutes)."""
        latest_timestamp = self.get_latest_odds_timestamp()

        if not latest_timestamp:
            print("[INFO] No odds data found")
            return False

        # Make timestamp timezone-aware if needed
        if latest_timestamp.tzinfo is None:
            from datetime import timezone

            latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)

        now = datetime.now(latest_timestamp.tzinfo)
        age_minutes = (now - latest_timestamp).total_seconds() / 60

        print(f"[INFO] Latest odds: {age_minutes:.1f} minutes old")

        return age_minutes <= self.FRESHNESS_THRESHOLD

    def has_new_odds(self, cache: dict) -> bool:
        """Check if new odds data has arrived."""
        latest_timestamp = self.get_latest_odds_timestamp()

        if not latest_timestamp:
            return False

        if cache["last_odds_timestamp"] is None:
            return True  # First run

        # Parse cached timestamp
        cached_timestamp = datetime.fromisoformat(cache["last_odds_timestamp"])

        return latest_timestamp > cached_timestamp

    def should_run_edge_detection(self, cache: dict) -> bool:
        """Determine if edge detection should be triggered."""
        # Check 1: New odds data must exist
        if not self.has_new_odds(cache):
            print("[INFO] No new odds detected - skipping edge detection")
            return False

        # Check 2: Odds must be fresh
        if not self.check_odds_freshness():
            print("[INFO] Odds not fresh enough - skipping edge detection")
            return False

        # Check 3: Edge detection shouldn't have run recently for this data
        latest_odds = self.get_latest_odds_timestamp()
        if latest_odds and cache["last_edge_detection"]:
            last_edge_run = datetime.fromisoformat(cache["last_edge_detection"])

            if latest_odds < last_edge_run:
                print("[INFO] Edge detection already run for this odds data")
                return False

        print("[OK] Conditions met for edge detection trigger")
        return True

    def monitor(self) -> bool:
        """Run monitoring and return whether edge detection should trigger."""
        print("=" * 70)
        print("ODDS MONITOR - AUTO EDGE DETECTION TRIGGER")
        print("=" * 70)

        # Step 1: Connect and detect week
        if not self.connect_database():
            print("[ERROR] Cannot connect to database")
            return False

        if not self.detect_week():
            print("[ERROR] Not in regular season")
            return False

        print(f"\n[OK] Monitoring Week {self.week}")

        # Step 2: Load cache
        cache = self.load_cache()
        print(f"\n[INFO] Last odds timestamp: {cache['last_odds_timestamp']}")
        print(f"[INFO] Last edge detection: {cache['last_edge_detection']}")

        # Step 3: Check for new odds and freshness
        print("\n[CHECK] Analyzing odds data...")
        self.trigger_edge_detection = self.should_run_edge_detection(cache)

        # Step 4: Update cache
        latest_odds = self.get_latest_odds_timestamp()
        if latest_odds:
            cache["last_odds_timestamp"] = latest_odds.isoformat()

        if self.trigger_edge_detection:
            cache["last_edge_detection"] = datetime.now().isoformat()

        self.save_cache(cache)

        # Step 5: Generate report
        print("\n" + "=" * 70)
        print("MONITOR RESULT")
        print("=" * 70)

        if self.trigger_edge_detection:
            print("\n[TRIGGER] Edge detection should run")
            print("\nNext action:")
            print("  uv run python scripts/database/analyze_week12_edges.py")
            return True
        else:
            print("\n[SKIP] Edge detection not needed at this time")
            return False

        self.db.close_all_connections()


def main():
    """Main function."""
    monitor = OddsMonitor()

    try:
        trigger = monitor.monitor()
        return 0 if trigger else 1
    except Exception as e:
        print(f"[FATAL] {str(e)}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        if monitor.db:
            monitor.db.close_all_connections()


if __name__ == "__main__":
    sys.exit(main())
