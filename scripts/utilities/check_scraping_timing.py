#!/usr/bin/env python3
"""
Overtime.ag Scraping Timing Validator

Checks if current time is optimal for scraping NFL odds.
Prevents wasted scrapes during games or before lines post.

Usage:
    python scripts/utilities/check_scraping_timing.py

Exit Codes:
    0 = OPTIMAL time to scrape
    1 = SUBOPTIMAL time (scrape anyway but expect limited results)
    2 = BAD time (don't scrape - lines unavailable)
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_current_day_and_hour():
    """Get current day of week and hour (ET)"""
    now = datetime.now()
    day = now.strftime("%A")  # Monday, Tuesday, etc.
    hour = now.hour
    return day, hour, now


def check_nfl_scraping_timing():
    """
    Check if current time is good for scraping NFL odds.

    Returns:
        tuple: (status_code, status_text, message)
        status_code: 0 = optimal, 1 = suboptimal, 2 = bad
    """
    day, hour, now = get_current_day_and_hour()

    # Sunday
    if day == "Sunday":
        if hour < 13:  # Before 1 PM (games start)
            return (
                0,
                "OPTIMAL",
                "Sunday morning - lines still available for today's games",
            )
        elif hour >= 13:  # After 1 PM (games in progress)
            return (
                2,
                "BAD",
                "Sunday afternoon/evening - games in progress, lines pulled",
            )

    # Monday
    elif day == "Monday":
        if hour < 20:  # Before 8 PM (MNF starts)
            return (
                1,
                "SUBOPTIMAL",
                "Monday daytime - only TNF/Week+1 may be available",
            )
        else:  # 8 PM or later (MNF in progress)
            return (2, "BAD", "Monday evening - Monday Night Football in progress")

    # Tuesday
    elif day == "Tuesday":
        if hour < 12:  # Before noon
            return (
                1,
                "SUBOPTIMAL",
                "Tuesday early morning - lines may not be posted yet (wait until 12 PM)",
            )
        elif 12 <= hour < 18:  # 12 PM - 6 PM
            return (0, "OPTIMAL", "Tuesday afternoon - BEST TIME for next week's lines")
        else:  # After 6 PM
            return (
                0,
                "OPTIMAL",
                "Tuesday evening - next week's lines should be available",
            )

    # Wednesday
    elif day == "Wednesday":
        return (0, "OPTIMAL", "Wednesday - full betting markets available")

    # Thursday
    elif day == "Thursday":
        if hour < 18:  # Before 6 PM
            return (0, "OPTIMAL", "Thursday daytime - good time before TNF")
        elif 18 <= hour < 20:  # 6-8 PM
            return (1, "SUBOPTIMAL", "Thursday evening - TNF game starting soon")
        else:  # After 8 PM
            return (2, "BAD", "Thursday night - TNF in progress")

    # Friday
    elif day == "Friday":
        return (0, "OPTIMAL", "Friday - full betting markets available")

    # Saturday
    elif day == "Saturday":
        if hour < 13:
            return (0, "OPTIMAL", "Saturday morning - good time before games")
        else:
            return (
                1,
                "SUBOPTIMAL",
                "Saturday afternoon - some college games may be in progress",
            )

    # Default
    return (1, "UNKNOWN", "Unable to determine optimal timing")


def main():
    day, hour, now = get_current_day_and_hour()

    print("=" * 70)
    print("OVERTIME.AG SCRAPING TIMING CHECK")
    print("=" * 70)
    print(f"Current Time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}")
    print()

    status_code, status, message = check_nfl_scraping_timing()

    # Color-coded status
    if status_code == 0:
        status_symbol = "[OK]"
        color = "GREEN"
    elif status_code == 1:
        status_symbol = "[WARN]"
        color = "YELLOW"
    else:
        status_symbol = "[ERROR]"
        color = "RED"

    print(f"Status: {status_symbol} {status}")
    print(f"Message: {message}")
    print()

    # Provide guidance
    if status_code == 0:
        print("RECOMMENDATION: Good time to scrape")
        print("  -> Run: uv run python scripts/scrape_overtime_nfl.py")
        print()
    elif status_code == 1:
        print("RECOMMENDATION: Suboptimal time - consider waiting")
        print("  -> Best times: Tuesday-Thursday 12-6 PM")
        print("  -> You can scrape now, but results may be limited")
        print()
    else:
        print("RECOMMENDATION: BAD TIME - Do not scrape")
        print("  -> Lines are pulled during games")
        print("  -> Wait for:")
        if day == "Sunday":
            print("     - Monday late night (after MNF ends)")
        elif day == "Monday":
            print("     - Tuesday afternoon (12 PM - 6 PM)")
        elif day == "Thursday":
            print("     - Friday morning (after TNF ends)")
        print()

    # Optimal scraping windows
    print("-" * 70)
    print("OPTIMAL SCRAPING SCHEDULE")
    print("-" * 70)
    print("BEST TIMES:")
    print("  - Tuesday:   12 PM - 6 PM (Week+1 lines just posted)")
    print("  - Wednesday: All day (stable lines)")
    print("  - Thursday:  Before 6 PM (before TNF)")
    print()
    print("AVOID:")
    print("  - Sunday:    After 1 PM (games in progress)")
    print("  - Monday:    After 8 PM (MNF in progress)")
    print("  - Tuesday:   Before 12 PM (lines not posted yet)")
    print("  - Thursday:  After 8 PM (TNF in progress)")
    print("=" * 70)
    print()

    sys.exit(status_code)


if __name__ == "__main__":
    main()
