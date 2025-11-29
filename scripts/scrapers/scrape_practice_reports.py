#!/usr/bin/env python3
"""
NFL.com Practice Reports Scraper

Scrapes NFL.com official injury/practice reports (Wed-Fri).

Parses:
- Player participation status (FP/LP/DNP)
- Practice date and day of week
- Severity from participation level
- Trend from week-to-week changes

Output: output/practice_reports/nfl/week_N_practices.json

Usage:
    python scrape_practice_reports.py --week 13 --season 2025
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class PracticeReportsScraper:
    """Scrape NFL practice reports from NFL.com."""

    # NFL team IDs and names
    NFL_TEAMS = {
        1: "Kansas City Chiefs",
        2: "Buffalo Bills",
        3: "Miami Dolphins",
        4: "New England Patriots",
        5: "Philadelphia Eagles",
        6: "Dallas Cowboys",
        7: "Washington Commanders",
        8: "New York Giants",
        9: "Chicago Bears",
        10: "Green Bay Packers",
        11: "Detroit Lions",
        12: "Minnesota Vikings",
        13: "New Orleans Saints",
        14: "Tampa Bay Buccaneers",
        15: "Atlanta Falcons",
        16: "Carolina Panthers",
        17: "Baltimore Ravens",
        18: "Cincinnati Bengals",
        19: "Cleveland Browns",
        20: "Pittsburgh Steelers",
        21: "Houston Texans",
        22: "Tennessee Titans",
        23: "Jacksonville Jaguars",
        24: "Indianapolis Colts",
        25: "Denver Broncos",
        26: "Las Vegas Raiders",
        27: "Los Angeles Chargers",
        28: "Los Angeles Rams",
        29: "San Francisco 49ers",
        30: "Seattle Seahawks",
        31: "Arizona Cardinals",
        32: "New York Jets",
    }

    # Participation status levels
    PARTICIPATION_LEVELS = {
        "FP": "full",
        "LP": "limited",
        "DNP": "did_not_practice",
        "OOA": "out_of_action",
        "": "not_listed",
    }

    def __init__(self):
        """Initialize scraper."""
        self.output_dir = (
            Path(__file__).parent.parent.parent
            / "output"
            / "practice_reports"
            / "nfl"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_nfl_week_dates(
        self, season: int, week: int
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """
        Calculate practice week dates (Wed-Fri of NFL week).

        Args:
            season: NFL season year
            week: Week number (1-18)

        Returns:
            Tuple of (wednesday_date, friday_date)
        """
        # NFL 2025 season starts September 4, 2025 (Thursday)
        season_start = datetime(season, 9, 4)  # Thursday of Week 1
        # Back up to Wednesday of Week 1
        week_1_wednesday = season_start - timedelta(days=1)

        # Calculate Wednesday of target week
        days_diff = (week - 1) * 7
        wednesday = week_1_wednesday + timedelta(days=days_diff)
        friday = wednesday + timedelta(days=2)

        return wednesday, friday

    def parse_participation_status(
        self, status_text: Optional[str]
    ) -> Dict[str, any]:
        """
        Parse participation status text.

        Args:
            status_text: Text like "FP", "LP", "DNP"

        Returns:
            Dictionary with participation and severity
        """
        if not status_text:
            return {
                "participation": "",
                "severity": "unknown",
                "is_available": None,
            }

        status_upper = status_text.strip().upper()

        # Map to severity
        severity_map = {
            "FP": "mild",  # Full participation
            "LP": "moderate",  # Limited participation
            "DNP": "severe",  # Did not practice
            "OOA": "out",  # Out of action
        }

        # Availability inference
        available_map = {
            "FP": True,
            "LP": True,
            "DNP": None,  # Unknown
            "OOA": False,
        }

        return {
            "participation": status_upper,
            "severity": severity_map.get(status_upper, "unknown"),
            "is_available": available_map.get(status_upper),
        }

    def calculate_trend(
        self,
        current_status: str,
        previous_status: Optional[str],
    ) -> Optional[str]:
        """
        Calculate trend from previous week's status.

        Args:
            current_status: Current week status (FP/LP/DNP)
            previous_status: Previous week status

        Returns:
            Trend: "improving", "declining", "stable", or None
        """
        if not previous_status:
            return None

        status_order = ["DNP", "LP", "FP"]

        try:
            current_idx = status_order.index(current_status)
            prev_idx = status_order.index(previous_status)

            if current_idx > prev_idx:
                return "improving"
            elif current_idx < prev_idx:
                return "declining"
            else:
                return "stable"
        except ValueError:
            return None

    def load_previous_reports(self, season: int, week: int) -> Dict:
        """
        Load previous week's reports for trend analysis.

        Args:
            season: Season year
            week: Current week number

        Returns:
            Dictionary of player_id -> previous_status
        """
        if week <= 1:
            return {}

        prev_file = (
            self.output_dir / f"week_{week - 1}_practices.json"
        )
        if not prev_file.exists():
            return {}

        try:
            with open(prev_file) as f:
                data = json.load(f)
                # Build lookup by player_id
                lookup = {}
                for player_report in data.get("practices", []):
                    player_id = player_report.get("player_id")
                    participation = player_report.get("participation")
                    if player_id and participation:
                        lookup[player_id] = participation
                return lookup
        except Exception as e:
            logger.warning(
                f"Could not load previous week reports: {e}"
            )
            return {}

    def scrape_team_practices(
        self,
        team_id: int,
        team_name: str,
        season: int,
        week: int,
        wednesday: datetime,
        friday: datetime,
    ) -> List[Dict]:
        """
        Scrape practice reports for a single team.

        NOTE: This is a placeholder. Actual implementation would use:
        - Playwright for browser automation
        - Selector-based parsing of NFL.com injury report pages
        - Multi-day scraping (Wed, Thu, Fri)

        Args:
            team_id: Team ID
            team_name: Team name
            season: Season year
            week: Week number
            wednesday: Wednesday date of practice week
            friday: Friday date of practice week

        Returns:
            List of practice reports
        """
        # Placeholder: Return empty list
        # Real implementation would:
        # 1. Navigate to NFL.com/{team_id}/injury-report
        # 2. Extract player table rows
        # 3. Parse: name, position, status, body_part
        # 4. For Wed/Thu/Fri dates
        # 5. Return structured data

        logger.debug(
            f"Scraping {team_name} practices for "
            f"week {week} ({wednesday.date()}-{friday.date()})"
        )
        return []

    def scrape_week(
        self, season: int, week: int
    ) -> Dict[str, any]:
        """
        Scrape all practice reports for a week.

        Args:
            season: Season year
            week: Week number

        Returns:
            Dictionary with all practice data
        """
        logger.info(
            f"Scraping practice reports for "
            f"NFL {season} Week {week}"
        )

        wednesday, friday = self.get_nfl_week_dates(season, week)
        if not wednesday:
            logger.error(f"Invalid week number: {week}")
            return {"practices": []}

        logger.info(
            f"Practice week: {wednesday.date()} - {friday.date()}"
        )

        # Load previous week's data for trend analysis
        prev_reports = self.load_previous_reports(season, week)

        all_practices = []
        scraped_teams = 0

        for team_id, team_name in self.NFL_TEAMS.items():
            try:
                practices = self.scrape_team_practices(
                    team_id, team_name, season, week, wednesday, friday
                )
                all_practices.extend(practices)
                scraped_teams += 1
            except Exception as e:
                logger.warning(
                    f"Error scraping {team_name}: {e}"
                )

        logger.info(
            f"Scraped {scraped_teams} teams, "
            f"{len(all_practices)} practice reports"
        )

        return {
            "metadata": {
                "source": "nfl.com",
                "season": season,
                "week": week,
                "scrape_date": datetime.now().isoformat(),
                "practice_week_start": wednesday.isoformat(),
                "practice_week_end": friday.isoformat(),
                "teams_scraped": scraped_teams,
            },
            "practices": all_practices,
        }

    def save_reports(
        self, data: Dict, season: int, week: int
    ) -> Path:
        """
        Save practice reports to JSON file.

        Args:
            data: Practice data dictionary
            season: Season year
            week: Week number

        Returns:
            Path to saved file
        """
        output_file = self.output_dir / f"week_{week}_practices.json"

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved practice reports to {output_file}")
        return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape NFL.com practice reports"
    )
    parser.add_argument(
        "--season", type=int, default=2025, help="Season (default 2025)"
    )
    parser.add_argument(
        "--week", type=int, required=True, help="Week number (1-18)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not 1 <= args.week <= 18:
        logger.error("Week must be between 1 and 18")
        sys.exit(1)

    scraper = PracticeReportsScraper()
    data = scraper.scrape_week(args.season, args.week)
    scraper.save_reports(data, args.season, args.week)

    logger.info(
        f"Practice reports scraping complete "
        f"({len(data['practices'])} reports)"
    )


if __name__ == "__main__":
    main()
