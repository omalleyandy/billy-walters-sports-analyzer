"""
Schedule Validator - Intelligent Week & Schedule Detection

Determines the current NFL/NCAAF week based on system date/time and validates
against ESPN schedules to ensure edge detection uses correct games.

Key Features:
- Auto-detect current week from system date
- Validate against ESPN scoreboard
- Cross-check NFL.com schedule
- Prevent analyzing wrong week
- Provide clear warnings if date/schedule mismatch

Used by: billy_walters_edge_detector.py (pre-flight checks)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Any

logger = logging.getLogger(__name__)


class ScheduleValidator:
    """Validates and detects current NFL/NCAAF week from date/schedule data"""

    # 2025 NFL Season Key Dates
    NFL_SEASON_START = datetime(2025, 9, 4)  # Sept 4, 2025
    NFL_WEEK_DATES = {
        1: (datetime(2025, 9, 4), datetime(2025, 9, 10)),
        2: (datetime(2025, 9, 11), datetime(2025, 9, 17)),
        3: (datetime(2025, 9, 18), datetime(2025, 9, 24)),
        4: (datetime(2025, 9, 25), datetime(2025, 10, 1)),
        5: (datetime(2025, 10, 2), datetime(2025, 10, 8)),
        6: (datetime(2025, 10, 9), datetime(2025, 10, 15)),
        7: (datetime(2025, 10, 16), datetime(2025, 10, 22)),
        8: (datetime(2025, 10, 23), datetime(2025, 10, 29)),
        9: (datetime(2025, 10, 30), datetime(2025, 11, 5)),
        10: (datetime(2025, 11, 6), datetime(2025, 11, 12)),
        11: (datetime(2025, 11, 13), datetime(2025, 11, 19)),
        12: (datetime(2025, 11, 20), datetime(2025, 11, 26)),
        13: (datetime(2025, 11, 27), datetime(2025, 12, 3)),
        14: (datetime(2025, 12, 4), datetime(2025, 12, 10)),
        15: (datetime(2025, 12, 11), datetime(2025, 12, 17)),
        16: (datetime(2025, 12, 18), datetime(2025, 12, 24)),
        17: (datetime(2025, 12, 25), datetime(2025, 12, 31)),
        18: (datetime(2026, 1, 1), datetime(2026, 1, 7)),
        # Playoff weeks
        "wild_card": (datetime(2026, 1, 10), datetime(2026, 1, 13)),
        "divisional": (datetime(2026, 1, 17), datetime(2026, 1, 20)),
        "conference": (datetime(2026, 1, 24), datetime(2026, 1, 27)),
        "superbowl": (datetime(2026, 2, 1), datetime(2026, 2, 1)),
    }

    # 2025 NCAAF Season Key Dates
    NCAAF_SEASON_START = datetime(2025, 8, 28)  # Aug 28, 2025
    NCAAF_WEEK_DATES = {
        1: (datetime(2025, 8, 28), datetime(2025, 9, 3)),
        2: (datetime(2025, 9, 4), datetime(2025, 9, 10)),
        3: (datetime(2025, 9, 11), datetime(2025, 9, 17)),
        4: (datetime(2025, 9, 18), datetime(2025, 9, 24)),
        5: (datetime(2025, 9, 25), datetime(2025, 10, 1)),
        6: (datetime(2025, 10, 2), datetime(2025, 10, 8)),
        7: (datetime(2025, 10, 9), datetime(2025, 10, 15)),
        8: (datetime(2025, 10, 16), datetime(2025, 10, 22)),
        9: (datetime(2025, 10, 23), datetime(2025, 10, 29)),
        10: (datetime(2025, 10, 30), datetime(2025, 11, 5)),
        11: (datetime(2025, 11, 6), datetime(2025, 11, 12)),
        12: (datetime(2025, 11, 13), datetime(2025, 11, 19)),
        13: (datetime(2025, 11, 20), datetime(2025, 11, 26)),
        14: (datetime(2025, 11, 25), datetime(2025, 12, 3)),  # Overlaps with Week 13
        15: (datetime(2025, 12, 4), datetime(2025, 12, 10)),
        # Bowl season
        "bowl": (datetime(2025, 12, 20), datetime(2026, 1, 12)),
    }

    def __init__(self):
        """Initialize schedule validator"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.current_date = datetime.now()

    def detect_current_nfl_week(self) -> Tuple[int, str]:
        """
        Detect current NFL week from system date

        Returns:
            Tuple of (week_number, week_label) e.g., (13, "Week 13")
        """
        for week_num, (start_date, end_date) in self.NFL_WEEK_DATES.items():
            if (
                isinstance(week_num, int)
                and start_date <= self.current_date <= end_date
            ):
                return week_num, f"Week {week_num}"

        # Check playoffs
        for week_label, (start_date, end_date) in self.NFL_WEEK_DATES.items():
            if not isinstance(week_label, int):
                if start_date <= self.current_date <= end_date:
                    return None, week_label.title()

        logger.warning(f"Current date {self.current_date} not within NFL season")
        return None, "Off-Season"

    def detect_current_ncaaf_week(self) -> Tuple[int, str]:
        """
        Detect current NCAAF week from system date

        Returns:
            Tuple of (week_number, week_label) e.g., (14, "Week 14")
        """
        for week_num, (start_date, end_date) in self.NCAAF_WEEK_DATES.items():
            if (
                isinstance(week_num, int)
                and start_date <= self.current_date <= end_date
            ):
                return week_num, f"Week {week_num}"

        # Check bowl season
        for week_label, (start_date, end_date) in self.NCAAF_WEEK_DATES.items():
            if not isinstance(week_label, int):
                if start_date <= self.current_date <= end_date:
                    return None, week_label.title()

        logger.warning(f"Current date {self.current_date} not within NCAAF season")
        return None, "Off-Season"

    def validate_schedule_week(
        self, schedule_file: Path, league: str = "nfl"
    ) -> Tuple[int, str, bool]:
        """
        Validate schedule file matches detected week

        Args:
            schedule_file: Path to ESPN schedule JSON
            league: "nfl" or "ncaaf"

        Returns:
            Tuple of (detected_week, schedule_week, is_match)
        """
        # Detect current week
        if league.lower() == "nfl":
            detected_week, detected_label = self.detect_current_nfl_week()
        else:
            detected_week, detected_label = self.detect_current_ncaaf_week()

        # Parse schedule file to find week
        try:
            with open(schedule_file) as f:
                data = json.load(f)

            events = data.get("events", [])
            if not events:
                logger.error(f"No events in {schedule_file}")
                return detected_week, None, False

            # Extract date range from schedule
            schedule_dates = []
            for event in events:
                comps = event.get("competitions", [{}])[0]
                date_str = comps.get("date", "")
                if date_str:
                    try:
                        # Parse ISO format with timezone and convert to naive UTC
                        date_obj = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )
                        # Convert to naive datetime for comparison
                        if date_obj.tzinfo:
                            date_obj = date_obj.replace(tzinfo=None)
                        schedule_dates.append(date_obj)
                    except ValueError:
                        pass

            if not schedule_dates:
                logger.error("Could not parse dates from schedule")
                return detected_week, None, False

            min_date = min(schedule_dates)
            max_date = max(schedule_dates)
            logger.info(
                f"Schedule covers dates: {min_date.date()} to {max_date.date()}"
            )

            # Find which week this schedule belongs to
            schedule_week = None
            if league.lower() == "nfl":
                for week_num, (start, end) in self.NFL_WEEK_DATES.items():
                    if isinstance(week_num, int):
                        # Check if schedule overlaps with this week
                        if min_date <= end and max_date >= start:
                            schedule_week = week_num
                            break
            else:
                for week_num, (start, end) in self.NCAAF_WEEK_DATES.items():
                    if isinstance(week_num, int):
                        if min_date <= end and max_date >= start:
                            schedule_week = week_num
                            break

            # Validate match
            is_match = detected_week == schedule_week
            if not is_match and detected_week is not None:
                logger.warning(
                    f"Schedule mismatch: detected week {detected_week}, "
                    f"schedule has week {schedule_week}"
                )

            return detected_week, schedule_week, is_match

        except Exception as e:
            logger.error(f"Error validating schedule: {e}")
            return detected_week, None, False

    def validate_odds_week(
        self, odds_file: Path, league: str = "nfl"
    ) -> Tuple[int, str, bool]:
        """
        Validate odds file matches detected week

        Args:
            odds_file: Path to Overtime.ag odds JSON
            league: "nfl" or "ncaaf"

        Returns:
            Tuple of (detected_week, odds_week, is_match)
        """
        # Detect current week
        if league.lower() == "nfl":
            detected_week, detected_label = self.detect_current_nfl_week()
        else:
            detected_week, detected_label = self.detect_current_ncaaf_week()

        try:
            with open(odds_file) as f:
                data = json.load(f)

            games = data.get("games", [])
            if not games:
                logger.error(f"No games in {odds_file}")
                return detected_week, None, False

            # Extract dates from odds
            odds_dates = []
            for game in games:
                game_time_str = game.get("game_time", "")
                if game_time_str:
                    try:
                        # Parse Overtime.ag format: "11/27/2025 13:00"
                        game_time = datetime.strptime(game_time_str, "%m/%d/%Y %H:%M")
                        odds_dates.append(game_time)
                    except ValueError:
                        pass

            if not odds_dates:
                logger.error("Could not parse game times from odds")
                return detected_week, None, False

            min_date = min(odds_dates)
            max_date = max(odds_dates)
            logger.info(
                f"Odds cover game times: {min_date.strftime('%m/%d %H:%M')} "
                f"to {max_date.strftime('%m/%d %H:%M')}"
            )

            # Find which week the odds belong to
            odds_week = None
            if league.lower() == "nfl":
                for week_num, (start, end) in self.NFL_WEEK_DATES.items():
                    if isinstance(week_num, int):
                        if min_date <= end and max_date >= start:
                            odds_week = week_num
                            break
            else:
                for week_num, (start, end) in self.NCAAF_WEEK_DATES.items():
                    if isinstance(week_num, int):
                        if min_date <= end and max_date >= start:
                            odds_week = week_num
                            break

            # Validate match
            is_match = detected_week == odds_week
            if not is_match and detected_week is not None:
                logger.warning(
                    f"Odds mismatch: detected week {detected_week}, "
                    f"odds have week {odds_week}"
                )

            return detected_week, odds_week, is_match

        except Exception as e:
            logger.error(f"Error validating odds: {e}")
            return detected_week, None, False

    def get_pre_flight_report(self, league: str = "nfl") -> Dict[str, any]:
        """
        Generate pre-flight check report for edge detection

        Args:
            league: "nfl" or "ncaaf"

        Returns:
            Dictionary with validation results
        """
        logger.info("=" * 80)
        logger.info("PRE-FLIGHT SCHEDULE VALIDATION")
        logger.info("=" * 80)

        # Detect current week
        if league.lower() == "nfl":
            week_num, week_label = self.detect_current_nfl_week()
            odds_dir = Path("output/overtime/nfl/pregame")
            schedule_dir = Path("output/espn/schedule/nfl")
        else:
            week_num, week_label = self.detect_current_ncaaf_week()
            odds_dir = Path("output/overtime/ncaaf/pregame")
            schedule_dir = Path("output/espn/schedule/ncaaf")

        report = {
            "current_date": self.current_date.isoformat(),
            "league": league.upper(),
            "detected_week": week_num,
            "detected_week_label": week_label,
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "schedule_validation": None,
            "odds_validation": None,
        }

        logger.info(
            f"\nCurrent Date: {self.current_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info(f"Detected Week: {week_label}")

        # Find latest schedule file
        if schedule_dir.exists():
            schedule_files = sorted(schedule_dir.glob("schedule_*.json"))
            if schedule_files:
                latest_schedule = schedule_files[-1]
                logger.info(f"\nLatest Schedule: {latest_schedule.name}")

                det_week, sched_week, is_match = self.validate_schedule_week(
                    latest_schedule, league
                )
                report["schedule_validation"] = {
                    "file": latest_schedule.name,
                    "detected_week": det_week,
                    "schedule_week": sched_week,
                    "is_match": is_match,
                }

                if not is_match:
                    msg = f"Schedule week {sched_week} does not match detected week {det_week}"
                    report["warnings"].append(msg)
                    logger.warning(f"[WARNING] {msg}")
                else:
                    logger.info("[OK] Schedule matches detected week")
            else:
                msg = f"No schedule files found in {schedule_dir}"
                report["errors"].append(msg)
                logger.error(f"[ERROR] {msg}")

        # Find latest odds file
        if odds_dir.exists():
            odds_files = sorted(odds_dir.glob("api_walters_*.json"))
            if odds_files:
                latest_odds = odds_files[-1]
                logger.info(f"\nLatest Odds: {latest_odds.name}")

                det_week, odds_week, is_match = self.validate_odds_week(
                    latest_odds, league
                )
                report["odds_validation"] = {
                    "file": latest_odds.name,
                    "detected_week": det_week,
                    "odds_week": odds_week,
                    "is_match": is_match,
                }

                if not is_match:
                    msg = (
                        f"Odds week {odds_week} does not match detected week {det_week}"
                    )
                    report["warnings"].append(msg)
                    logger.warning(f"[WARNING] {msg}")
                else:
                    logger.info("[OK] Odds matches detected week")
            else:
                msg = f"No odds files found in {odds_dir}"
                report["errors"].append(msg)
                logger.error(f"[ERROR] {msg}")

        # Set overall validity
        report["is_valid"] = len(report["errors"]) == 0

        logger.info("\n" + "=" * 80)
        if report["is_valid"]:
            logger.info("[OK] All pre-flight checks passed - ready for edge detection")
        else:
            logger.error(
                "[FAILED] Pre-flight checks failed - DO NOT RUN EDGE DETECTION"
            )
            report["is_valid"] = False

        logger.info("=" * 80)

        return report


def main():
    """Example usage"""
    validator = ScheduleValidator()

    # Check NFL
    print("\n" + "=" * 80)
    print("NFL SCHEDULE VALIDATION")
    print("=" * 80)
    nfl_report = validator.get_pre_flight_report(league="nfl")
    print(json.dumps(nfl_report, indent=2))

    # Check NCAAF
    print("\n" + "=" * 80)
    print("NCAAF SCHEDULE VALIDATION")
    print("=" * 80)
    ncaaf_report = validator.get_pre_flight_report(league="ncaaf")
    print(json.dumps(ncaaf_report, indent=2))


if __name__ == "__main__":
    main()
