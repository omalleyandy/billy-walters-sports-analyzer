#!/usr/bin/env python3
"""
NFL Week Auto-Detector

Automatically detects the current NFL week based on system date.
Handles regular season, playoffs, and offseason.
"""

from datetime import datetime, date, timedelta
from typing import Optional, Tuple


class NFLWeekDetector:
    """Detect current NFL week from date."""

    # 2025 NFL Season - Week 1 starts Thursday, Sept 4
    SEASON = 2025
    WEEK_1_START = date(2025, 9, 4)  # Thursday
    REGULAR_SEASON_WEEKS = 18
    FIRST_PLAYOFF_DATE = date(2026, 1, 10)  # Wild Card Saturday
    SUPER_BOWL_DATE = date(2026, 2, 8)  # Super Bowl Sunday

    @classmethod
    def get_current_week(cls) -> Optional[int]:
        """
        Get current NFL week.

        Returns:
            int: Week number (1-18 for regular season), or None if offseason/playoffs
        """
        today = date.today()

        # Offseason (before Week 1)
        if today < cls.WEEK_1_START:
            return None

        # Regular season
        if today < cls.FIRST_PLAYOFF_DATE:
            # Calculate week based on days since Week 1 start
            days_since_week1 = (today - cls.WEEK_1_START).days
            week = (days_since_week1 // 7) + 1

            # Cap at 18 (regular season only)
            if week <= cls.REGULAR_SEASON_WEEKS:
                return week

        # Playoffs/Super Bowl
        if today <= cls.SUPER_BOWL_DATE:
            return None  # Could return 'PLAYOFFS', but keeping it simple

        # Offseason (after Super Bowl)
        return None

    @classmethod
    def get_week_date_range(cls, week: int) -> Tuple[date, date]:
        """
        Get start and end date for a given week.

        Args:
            week: Week number (1-18)

        Returns:
            Tuple of (start_date, end_date)
        """
        if week < 1 or week > cls.REGULAR_SEASON_WEEKS:
            raise ValueError(f"Invalid week: {week}")

        # Each week spans 7 days (Thu-Wed typically)
        start_date = cls.WEEK_1_START + timedelta(days=(week - 1) * 7)
        end_date = start_date + timedelta(days=6)

        return start_date, end_date

    @classmethod
    def get_season_info(cls) -> dict:
        """Get comprehensive season information."""
        current_week = cls.get_current_week()
        today = date.today()

        info = {
            "season": cls.SEASON,
            "current_week": current_week,
            "today": today.isoformat(),
            "is_regular_season": current_week is not None
            and 1 <= current_week <= cls.REGULAR_SEASON_WEEKS,
            "is_offseason": current_week is None,
            "is_playoffs": (
                current_week is None
                and today >= cls.FIRST_PLAYOFF_DATE
                and today <= cls.SUPER_BOWL_DATE
            ),
            "season_start": cls.WEEK_1_START.isoformat(),
            "regular_season_end": (
                cls.WEEK_1_START + timedelta(days=(cls.REGULAR_SEASON_WEEKS - 1) * 7 + 6)
            ).isoformat(),
            "playoff_start": cls.FIRST_PLAYOFF_DATE.isoformat(),
            "super_bowl_date": cls.SUPER_BOWL_DATE.isoformat(),
        }

        if current_week:
            start, end = cls.get_week_date_range(current_week)
            info["week_start"] = start.isoformat()
            info["week_end"] = end.isoformat()

        return info


if __name__ == "__main__":
    detector = NFLWeekDetector()
    season_info = detector.get_season_info()

    print("=" * 60)
    print("NFL WEEK AUTO-DETECTOR")
    print("=" * 60)

    for key, value in season_info.items():
        print(f"{key:.<40} {value}")

    if season_info["current_week"]:
        print(f"\n[OK] Current week: {season_info['current_week']}")
        print(f"[OK] Week dates: {season_info['week_start']} to {season_info['week_end']}")
    else:
        if season_info["is_offseason"]:
            print("\n[INFO] Currently in offseason")
        elif season_info["is_playoffs"]:
            print("\n[INFO] Currently in playoffs/postseason")
