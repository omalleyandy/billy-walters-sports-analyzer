"""
Example: Using season calendar to fetch current week's data.

This demonstrates how to integrate the season calendar utilities
into your data collection and analysis workflows.

Run from src directory:
    cd src && python -m ../examples.current_week_example

Or use PYTHONPATH:
    PYTHONPATH=src python examples/current_week_example.py
"""

import sys
from pathlib import Path

# Add src to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from walters_analyzer.season_calendar import (
    SeasonPhase,
    format_season_status,
    get_nfl_season_phase,
    get_nfl_week,
    get_week_date_range,
)


def fetch_current_week_data():
    """Fetch data for the current NFL week."""
    # Get current week
    current_week = get_nfl_week()

    if current_week is None:
        print("WARNING: Not currently in NFL regular season")
        return

    print(f"Status: {format_season_status()}\n")

    # Get week date range
    start_date, end_date = get_week_date_range(current_week)
    print(f"Week {current_week} runs from {start_date} to {end_date}")

    # Example: Construct NFL.com schedule URL
    nfl_schedule_url = f"https://www.nfl.com/schedules/2025/REG{current_week}"
    print(f"\nSchedule URL: {nfl_schedule_url}")

    # Example: Use in data validation
    print(f"\nWeek {current_week} games are ready for analysis:")
    print(f"   - Fetch odds for Week {current_week}")
    print(f"   - Get weather forecasts for {start_date} - {end_date}")
    print(f"   - Update power ratings through Week {current_week - 1}")


def check_season_phase():
    """Check if we should be analyzing games."""
    phase = get_nfl_season_phase()

    if phase == SeasonPhase.REGULAR_SEASON:
        week = get_nfl_week()
        print(f"Regular season active - Week {week}")
        print("   Ready for game analysis and betting decisions")
    elif phase == SeasonPhase.PLAYOFFS:
        print("Playoff season - Different analysis methodology")
    elif phase == SeasonPhase.OFFSEASON:
        print("Offseason - Focus on historical analysis and backtesting")
    else:
        print(f"Current phase: {phase.value}")


if __name__ == "__main__":
    print("=" * 60)
    print("Billy Walters Sports Analyzer - Current Week Status")
    print("=" * 60)
    print()

    fetch_current_week_data()
    print("\n" + "-" * 60 + "\n")
    check_season_phase()
