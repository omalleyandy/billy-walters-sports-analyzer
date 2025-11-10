#!/usr/bin/env python3
"""
Weekly Power Rating Update Script

Automatically updates power ratings after each week's games using Billy Walters' 90/10 formula.
Designed to be run Tuesday mornings after Monday Night Football.

Usage:
    python weekly_power_rating_update.py --week 10
    python weekly_power_rating_update.py --week 11 --games-file data/week11_games.json
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from walters_analyzer.valuation.power_ratings import (
    PowerRatingSystem,
    GameResult
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class WeeklyPowerRatingUpdater:
    """
    Update power ratings for a single week using actual game results
    """

    def __init__(self, week_num: int, ratings_dir: str = "data/power_ratings"):
        """
        Initialize updater

        Args:
            week_num: Week number to update (1-18)
            ratings_dir: Directory containing power rating snapshots
        """
        self.week_num = week_num
        self.ratings_dir = Path(ratings_dir)
        self.ratings_dir.mkdir(parents=True, exist_ok=True)

        # Initialize power rating system
        self.prs = PowerRatingSystem()

        # Load previous week's ratings
        self.load_previous_week_ratings()

    def load_previous_week_ratings(self) -> None:
        """
        Load power ratings from previous week as starting point
        """
        if self.week_num == 1:
            # Week 1: Load from master initial ratings file
            master_file = Path("data/power_ratings_nfl_2025.json")
            if master_file.exists():
                self.prs.load_ratings(master_file)
                logger.info(f"Loaded initial ratings from {master_file}")
            else:
                logger.warning("No initial ratings file found, starting from scratch")
            return

        # Load from previous week's snapshot
        prev_week = self.week_num - 1
        prev_file = self.ratings_dir / f"nfl_2025_week_{prev_week:02d}.json"

        if not prev_file.exists():
            logger.error(f"Previous week's ratings not found: {prev_file}")
            logger.error("Please run backfill script first or manually create previous week")
            raise FileNotFoundError(f"Missing {prev_file}")

        with open(prev_file, 'r') as f:
            data = json.load(f)

        self.prs.import_ratings(data['ratings'])
        logger.info(f"Loaded Week {prev_week} ratings from {prev_file}")
        logger.info(f"Starting with {len(self.prs.ratings)} team ratings")

    def load_week_games(self, games_file: Optional[str] = None) -> List[Dict]:
        """
        Load game results for the week

        Args:
            games_file: Optional custom games file. If None, uses standard naming

        Returns:
            List of game dictionaries for this week
        """
        if games_file:
            filepath = Path(games_file)
        else:
            # Try standard naming: data/nfl_2025_week_10_games.json
            filepath = Path(f"data/nfl_2025_week_{self.week_num:02d}_games.json")

            # Fallback: Check in unified data directory
            if not filepath.exists():
                filepath = Path(f"output/unified/nfl_week_{self.week_num}_games.json")

        if not filepath.exists():
            logger.error(f"Games file not found: {filepath}")
            logger.error("Please provide game results with --games-file option")
            raise FileNotFoundError(f"Missing {filepath}")

        with open(filepath, 'r') as f:
            data = json.load(f)

        # Handle different formats
        if isinstance(data, list):
            games = data
        elif 'games' in data:
            games = data['games']
        else:
            raise ValueError(f"Unexpected format in {filepath}")

        # Filter to this week only
        week_games = [g for g in games if g.get('week') == self.week_num]

        logger.info(f"Loaded {len(week_games)} games for Week {self.week_num} from {filepath}")

        return week_games

    def parse_game_to_result(self, game_dict: Dict) -> GameResult:
        """
        Convert game dictionary to GameResult object

        Args:
            game_dict: Game data from JSON

        Returns:
            GameResult object
        """
        # Parse date
        game_date = date.fromisoformat(game_dict['date'])

        # Create GameResult
        return GameResult(
            date=game_date,
            home_team=game_dict['home_team'],
            away_team=game_dict['away_team'],
            home_score=game_dict['home_score'],
            away_score=game_dict['away_score'],
            home_injury_level=game_dict.get('home_injury_level', 0.0),
            away_injury_level=game_dict.get('away_injury_level', 0.0),
            location=game_dict.get('location', 'home')
        )

    def update_ratings_for_week(self, games: List[Dict]) -> None:
        """
        Update power ratings for all games in the week

        Args:
            games: List of game dictionaries
        """
        logger.info("=" * 60)
        logger.info(f"PROCESSING WEEK {self.week_num}")
        logger.info("=" * 60)

        if not games:
            logger.warning(f"No games found for Week {self.week_num}")
            return

        # Process each game
        games_processed = 0
        for game_dict in games:
            game_result = self.parse_game_to_result(game_dict)
            self.prs.update_ratings_from_game(game_result)
            games_processed += 1

        logger.info(f"Processed {games_processed} games for Week {self.week_num}")

    def save_weekly_snapshot(self) -> Path:
        """
        Save power ratings snapshot for this week

        Returns:
            Path to saved snapshot file
        """
        snapshot_file = self.ratings_dir / f"nfl_2025_week_{self.week_num:02d}.json"

        # Create snapshot data
        snapshot = {
            "season": "2025",
            "week": self.week_num,
            "ratings": self.prs.export_ratings(),
            "games_processed_total": len(self.prs.history),
            "timestamp": datetime.now().isoformat(),
            "system_constants": {
                "old_rating_weight": self.prs.OLD_RATING_WEIGHT,
                "true_performance_weight": self.prs.TRUE_PERFORMANCE_WEIGHT,
                "home_field_advantage": self.prs.HOME_FIELD_ADVANTAGE,
            }
        }

        # Save to file
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)

        logger.info(f"Saved Week {self.week_num} snapshot to {snapshot_file}")

        return snapshot_file

    def save_master_ratings(self) -> None:
        """
        Update master ratings file with latest ratings
        """
        master_file = Path("data/power_ratings_nfl_2025.json")
        self.prs.save_ratings(master_file)
        logger.info(f"Updated master ratings file: {master_file}")

    def generate_rating_change_report(self) -> None:
        """
        Generate report showing rating changes for this week
        """
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"WEEK {self.week_num} RATING CHANGES")
        logger.info("=" * 60)

        # Get top 10 teams
        top_10 = self.prs.get_top_teams(10)
        logger.info("\nTop 10 Power Ratings:")
        for rank, (team, rating) in enumerate(top_10, 1):
            logger.info(f"  {rank:2d}. {team:25s} {rating:.2f}")

        # Analyze this week's games for biggest movers
        if self.prs.history:
            logger.info(f"\nBiggest Rating Changes This Week:")

            # Get only this week's games (last N entries)
            week_history = self.prs.history[-20:]  # Assume max 20 games per week

            changes = []
            for game in week_history:
                home_change = game['home_rating_after'] - game['home_rating_before']
                away_change = game['away_rating_after'] - game['away_rating_before']

                changes.append({
                    'team': game['home_team'],
                    'change': home_change,
                    'before': game['home_rating_before'],
                    'after': game['home_rating_after']
                })
                changes.append({
                    'team': game['away_team'],
                    'change': away_change,
                    'before': game['away_rating_before'],
                    'after': game['away_rating_after']
                })

            # Top 5 improvers this week
            changes.sort(key=lambda x: x['change'], reverse=True)
            logger.info("\n  Top Improvers:")
            for i, change_data in enumerate(changes[:5], 1):
                logger.info(
                    f"    {i}. {change_data['team']:20s} "
                    f"{change_data['before']:.2f} → {change_data['after']:.2f} "
                    f"({change_data['change']:+.2f})"
                )

            # Top 5 decliners this week
            logger.info("\n  Top Decliners:")
            for i, change_data in enumerate(changes[-5:], 1):
                logger.info(
                    f"    {i}. {change_data['team']:20s} "
                    f"{change_data['before']:.2f} → {change_data['after']:.2f} "
                    f"({change_data['change']:+.2f})"
                )

        logger.info("=" * 60)
        logger.info("")

    def run_update(self, games_file: Optional[str] = None) -> None:
        """
        Execute complete weekly update process

        Args:
            games_file: Optional custom games file path
        """
        logger.info("=" * 60)
        logger.info("BILLY WALTERS POWER RATINGS WEEKLY UPDATE")
        logger.info(f"Week {self.week_num} - 2025 NFL Season")
        logger.info("=" * 60)
        logger.info("")

        try:
            # Load game results
            games = self.load_week_games(games_file)

            # Update ratings
            self.update_ratings_for_week(games)

            # Save weekly snapshot
            self.save_weekly_snapshot()

            # Update master file
            self.save_master_ratings()

            # Generate report
            self.generate_rating_change_report()

            logger.info("✅ WEEKLY UPDATE COMPLETE!")
            logger.info(f"Power ratings updated through Week {self.week_num}")
            logger.info("")

        except Exception as e:
            logger.error(f"❌ Update failed: {e}")
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Update power ratings for a specific NFL week'
    )
    parser.add_argument(
        '--week',
        type=int,
        required=True,
        help='NFL week number to update (1-18)'
    )
    parser.add_argument(
        '--games-file',
        type=str,
        help='Path to JSON file containing game results (optional)'
    )

    args = parser.parse_args()

    # Validate week number
    if not 1 <= args.week <= 18:
        logger.error(f"Invalid week number: {args.week}. Must be 1-18")
        sys.exit(1)

    # Run update
    updater = WeeklyPowerRatingUpdater(week_num=args.week)
    updater.run_update(games_file=args.games_file)


if __name__ == "__main__":
    main()
