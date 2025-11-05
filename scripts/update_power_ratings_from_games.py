#!/usr/bin/env python3
"""
Power Ratings Updater

Updates Billy Walters power ratings based on completed NFL games.
Reads game data from JSONL files and applies the exponential weighted formula.

Usage:
    # Update from single file
    python scripts/update_power_ratings_from_games.py --file data/nfl_schedule/week9.jsonl

    # Update from directory (all JSONL files)
    python scripts/update_power_ratings_from_games.py --dir data/nfl_schedule

    # Update from specific weeks (sequential order)
    python scripts/update_power_ratings_from_games.py --dir data/nfl_schedule --weeks 1 2 3 4 5
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from walters.power_ratings import PowerRatingEngine, GameResult
from walters.nfl_data import (
    NFLGame,
    load_games_from_jsonl,
    filter_completed_games,
    nfl_game_to_game_results,
    normalize_team_name
)


class PowerRatingsUpdater:
    """Updates power ratings from NFL game data."""

    def __init__(self, ratings_file: str = "data/power_ratings/team_ratings.json"):
        """
        Initialize power ratings updater.

        Args:
            ratings_file: Path to power ratings JSON file
        """
        self.engine = PowerRatingEngine(ratings_file)
        self.ratings_file = ratings_file
        self.games_processed = 0
        self.ratings_updated = 0

    def update_from_game(
        self,
        game: NFLGame,
        injury_differential_home: float = 0.0,
        injury_differential_away: float = 0.0,
        verbose: bool = True
    ) -> tuple[Optional[GameResult], Optional[GameResult]]:
        """
        Update power ratings from a single game.

        Args:
            game: NFLGame object
            injury_differential_home: Injury impact for home team
            injury_differential_away: Injury impact for away team
            verbose: Print update details

        Returns:
            Tuple of (home_game_result, away_game_result) or (None, None) if skipped
        """
        # Skip incomplete games
        if not game.is_completed:
            if verbose:
                print(f"  [SKIP] {game.away_team} @ {game.home_team} - Not completed ({game.status})")
            return None, None

        # Convert to GameResult objects
        home_result, away_result = nfl_game_to_game_results(
            game,
            injury_differential_home=injury_differential_home,
            injury_differential_away=injury_differential_away
        )

        # Update ratings for both teams
        home_rating = self.engine.update_rating(home_result)
        away_rating = self.engine.update_rating(away_result)

        self.games_processed += 1
        self.ratings_updated += 2  # Both teams

        if verbose:
            score_str = f"{game.away_team} {game.away_score} @ {game.home_team} {game.home_score}"
            print(f"  [OK] {score_str}")
            print(f"    {home_result.team}: {home_rating.rating:.2f}")
            print(f"    {away_result.team}: {away_rating.rating:.2f}")

        return home_result, away_result

    def update_from_games(
        self,
        games: List[NFLGame],
        verbose: bool = True
    ) -> int:
        """
        Update power ratings from multiple games.

        Args:
            games: List of NFLGame objects
            verbose: Print progress

        Returns:
            Number of games processed
        """
        if verbose:
            print(f"\nProcessing {len(games)} games...")

        for game in games:
            self.update_from_game(game, verbose=verbose)

        return self.games_processed

    def update_from_file(
        self,
        file_path: str,
        verbose: bool = True
    ) -> int:
        """
        Update power ratings from JSONL file.

        Args:
            file_path: Path to JSONL file
            verbose: Print progress

        Returns:
            Number of games processed
        """
        if verbose:
            print(f"\nLoading games from: {file_path}")

        games = load_games_from_jsonl(file_path)
        completed_games = filter_completed_games(games)

        if verbose:
            print(f"Found {len(games)} total games, {len(completed_games)} completed")

        return self.update_from_games(completed_games, verbose=verbose)

    def update_from_directory(
        self,
        directory: str,
        pattern: str = "*.jsonl",
        weeks: Optional[List[int]] = None,
        verbose: bool = True
    ) -> int:
        """
        Update power ratings from all JSONL files in a directory.

        Args:
            directory: Directory path
            pattern: File pattern to match (default: *.jsonl)
            weeks: Optional list of weeks to process (in order)
            verbose: Print progress

        Returns:
            Number of games processed
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")

        # Get all matching files
        files = sorted(dir_path.glob(pattern))

        if not files:
            print(f"No files found matching pattern: {pattern}")
            return 0

        # Filter by weeks if specified
        if weeks:
            week_files = []
            for week in weeks:
                # Find file matching this week
                week_pattern = f"*week{week}_*.jsonl"
                matching = list(dir_path.glob(week_pattern))
                if matching:
                    week_files.append(matching[0])  # Take most recent
                else:
                    print(f"WARNING: No file found for Week {week}")

            files = week_files

        if verbose:
            print(f"\nFound {len(files)} files to process")

        # Process each file
        for file_path in files:
            self.update_from_file(str(file_path), verbose=verbose)

        return self.games_processed

    def save_ratings(self, verbose: bool = True):
        """Save updated ratings to JSON file."""
        self.engine.save_ratings()

        if verbose:
            print(f"\n[SUCCESS] Ratings saved to: {self.ratings_file}")

    def print_summary(self):
        """Print summary of updates."""
        print(f"\n{'='*60}")
        print(f"Power Ratings Update Summary")
        print(f"{'='*60}")
        print(f"Games processed: {self.games_processed}")
        print(f"Team ratings updated: {self.ratings_updated}")
        print(f"Ratings file: {self.ratings_file}")
        print(f"{'='*60}")

    def print_top_ratings(self, limit: int = 10):
        """
        Print top-rated teams.

        Args:
            limit: Number of teams to show
        """
        ratings = self.engine.get_all_ratings(sport="nfl")

        print(f"\n{'='*60}")
        print(f"Top {limit} NFL Power Ratings")
        print(f"{'='*60}")
        print(f"{'Rank':<6} {'Team':<30} {'Rating':<10} {'Games'}")
        print(f"{'-'*60}")

        for i, rating in enumerate(ratings[:limit], 1):
            print(f"{i:<6} {rating.team:<30} {rating.rating:>8.2f} {rating.games_played:>6}")

        print(f"{'='*60}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update Billy Walters power ratings from NFL game data"
    )

    # Input source
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--file",
        type=str,
        help="Single JSONL file to process"
    )
    input_group.add_argument(
        "--dir",
        type=str,
        help="Directory containing JSONL files"
    )

    # Options
    parser.add_argument(
        "--weeks",
        type=int,
        nargs="+",
        help="Specific weeks to process (in order, e.g., --weeks 1 2 3)"
    )
    parser.add_argument(
        "--ratings-file",
        type=str,
        default="data/power_ratings/team_ratings.json",
        help="Power ratings file path (default: data/power_ratings/team_ratings.json)"
    )
    parser.add_argument(
        "--show-top",
        type=int,
        default=10,
        help="Show top N teams after update (default: 10)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )

    args = parser.parse_args()

    verbose = not args.quiet

    # Initialize updater
    updater = PowerRatingsUpdater(ratings_file=args.ratings_file)

    try:
        # Process input
        if args.file:
            updater.update_from_file(args.file, verbose=verbose)
        elif args.dir:
            updater.update_from_directory(
                args.dir,
                weeks=args.weeks,
                verbose=verbose
            )

        # Save ratings
        updater.save_ratings(verbose=verbose)

        # Print results
        if verbose:
            updater.print_summary()
            updater.print_top_ratings(limit=args.show_top)

        print("\n[SUCCESS] Power ratings updated successfully!\n")

    except Exception as e:
        print(f"\n[ERROR] {e}\n", file=sys.stderr)
        import traceback
        if verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
