#!/usr/bin/env python3
"""
Update Power Ratings from Latest Massey Scrape

Converts Massey composite ratings to Billy Walters scale (70-100) and
applies the 90/10 update formula to blend with previous week's ratings.

Billy Walters 90/10 Formula:
    New Rating = (0.90 × Old Rating) + (0.10 × Current Massey)

This prevents overreaction to weekly variance while incorporating
new information from game results.

Usage:
    python scripts/analysis/update_power_ratings_from_massey.py
    python scripts/analysis/update_power_ratings_from_massey.py --week 12
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Billy Walters Constants
OLD_RATING_WEIGHT = 0.90  # 90% weight to previous rating
NEW_RATING_WEIGHT = 0.10  # 10% weight to new performance
NFL_SCALE_MIN = 70.0  # Worst NFL team
NFL_SCALE_MAX = 100.0  # Best NFL team
NFL_SCALE_AVERAGE = 85.0  # Average NFL team


class PowerRatingUpdater:
    """Update power ratings from Massey composite data"""

    def __init__(self, week: Optional[int] = None):
        """
        Initialize updater

        Args:
            week: NFL week number (auto-detected if None)
        """
        self.week = week
        self.project_root = Path(__file__).parent.parent.parent
        self.massey_dir = self.project_root / "output" / "massey" / "nfl" / "ratings"
        self.data_dir = self.project_root / "data"
        self.current_dir = self.data_dir / "current"

        # Ensure directories exist
        self.current_dir.mkdir(parents=True, exist_ok=True)

        # Rating storage
        self.current_massey = {}  # Fresh Massey ratings
        self.previous_ratings = {}  # Previous week's Billy Walters ratings
        self.updated_ratings = {}  # New Billy Walters ratings after 90/10

    def get_latest_massey_file(self) -> Optional[Path]:
        """Find the most recent Massey ratings file"""
        if not self.massey_dir.exists():
            logger.error(f"Massey directory not found: {self.massey_dir}")
            return None

        files = sorted(self.massey_dir.glob("nfl_ratings_*.json"))
        if not files:
            logger.error(f"No Massey rating files found in {self.massey_dir}")
            return None

        return files[-1]

    def load_massey_ratings(self) -> bool:
        """Load latest Massey composite ratings"""
        logger.info("=" * 60)
        logger.info("LOADING MASSEY RATINGS")
        logger.info("=" * 60)

        massey_file = self.get_latest_massey_file()
        if not massey_file:
            return False

        logger.info(f"Loading: {massey_file.name}")

        try:
            with open(massey_file, "r") as f:
                data = json.load(f)

            teams = data.get("teams", [])
            logger.info(f"Found {len(teams)} teams")

            # Extract ratings (Massey uses ~0-25 scale, negative for bad teams)
            for team_data in teams:
                team_name = team_data.get("team", "")
                rating_str = team_data.get("rating", "0")

                try:
                    rating = float(rating_str)
                    self.current_massey[team_name] = rating
                except ValueError:
                    logger.warning(
                        f"Could not parse rating for {team_name}: {rating_str}"
                    )

            logger.info(f"Loaded {len(self.current_massey)} team ratings")
            return True

        except Exception as e:
            logger.error(f"Failed to load Massey ratings: {e}")
            return False

    def load_previous_ratings(self) -> bool:
        """Load previous week's Billy Walters ratings"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("LOADING PREVIOUS RATINGS")
        logger.info("=" * 60)

        ratings_file = self.data_dir / "power_ratings_nfl_2025.json"

        if not ratings_file.exists():
            logger.warning(f"No previous ratings found at {ratings_file}")
            logger.info("Will use Massey ratings only (no blending)")
            return False

        try:
            with open(ratings_file, "r") as f:
                data = json.load(f)

            prev_ratings_raw = data.get("ratings", {})

            # Check if previous ratings are on the correct scale
            if prev_ratings_raw:
                ratings_list = list(prev_ratings_raw.values())
                avg = sum(ratings_list) / len(ratings_list)

                # If average is way off from expected (85), don't use previous ratings
                # Expected range is 70-100, so average should be around 80-90
                if avg < 50 or avg > 120:
                    logger.warning(
                        f"Previous ratings appear to be on wrong scale (avg={avg:.2f})"
                    )
                    logger.info("Skipping 90/10 blend, will use pure Massey conversion")
                    return False

            self.previous_ratings = prev_ratings_raw
            logger.info(f"Loaded {len(self.previous_ratings)} previous ratings")

            # Show some examples
            sorted_teams = sorted(
                self.previous_ratings.items(), key=lambda x: x[1], reverse=True
            )[:5]
            logger.info("\nTop 5 Previous Ratings:")
            for team, rating in sorted_teams:
                logger.info(f"  {team:25s} {rating:.2f}")

            return True

        except Exception as e:
            logger.error(f"Failed to load previous ratings: {e}")
            return False

    def massey_to_billy_walters_scale(self, massey_rating: float) -> float:
        """
        Convert Massey rating to Billy Walters scale (70-100)

        Current Massey ratings (Week 12, 2025):
        - Best team (LA Rams): 9.26
        - Worst team (Tennessee): 7.74
        - Range: ~1.5 points

        We map this to Billy Walters scale where:
        - 95-100: Championship contenders (top 3-4 teams)
        - 90-95: Elite teams (top 8-10 teams)
        - 85-90: Good teams (middle tier)
        - 80-85: Average teams
        - 75-80: Below average
        - 70-75: Poor teams (bottom 3-4 teams)

        Strategy: Use a wider input range to spread teams across scale
        Map Massey 6.0-10.0 → Billy Walters 70-100

        Args:
            massey_rating: Massey composite rating

        Returns:
            Rating on Billy Walters 70-100 scale
        """
        # Use wider range for better spread
        # Historical Massey typically ranges from ~6.0 (worst) to ~10.0 (best)
        massey_min = 6.0
        massey_max = 10.0
        massey_range = massey_max - massey_min

        # Normalize to 0-1
        normalized = (massey_rating - massey_min) / massey_range

        # Clamp to valid range
        normalized = max(0.0, min(1.0, normalized))

        # Scale to Billy Walters range
        bw_range = NFL_SCALE_MAX - NFL_SCALE_MIN
        bw_rating = NFL_SCALE_MIN + (normalized * bw_range)

        return round(bw_rating, 2)

    def apply_90_10_formula(self, team: str, new_massey: float) -> float:
        """
        Apply Billy Walters 90/10 update formula

        Args:
            team: Team name
            new_massey: New Massey rating (raw scale)

        Returns:
            Updated Billy Walters rating
        """
        # Convert Massey to BW scale
        new_bw = self.massey_to_billy_walters_scale(new_massey)

        # Check if we have a previous rating
        if team not in self.previous_ratings:
            # No previous rating, just use converted Massey
            return new_bw

        old_rating = self.previous_ratings[team]

        # Apply 90/10 formula
        updated = (OLD_RATING_WEIGHT * old_rating) + (NEW_RATING_WEIGHT * new_bw)

        return round(updated, 2)

    def update_all_ratings(self):
        """Apply 90/10 formula to all teams"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("APPLYING 90/10 UPDATE FORMULA")
        logger.info("=" * 60)

        for team, massey_rating in self.current_massey.items():
            updated = self.apply_90_10_formula(team, massey_rating)
            self.updated_ratings[team] = updated

        logger.info(f"Updated {len(self.updated_ratings)} team ratings")

    def save_ratings(self):
        """Save updated ratings to files"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("SAVING UPDATED RATINGS")
        logger.info("=" * 60)

        # Save to master file
        master_file = self.data_dir / "power_ratings_nfl_2025.json"
        master_data = {
            "ratings": self.updated_ratings,
            "last_updated": datetime.now().isoformat(),
            "week": self.week,
            "formula": "Billy Walters 90/10",
            "source": "Massey Composite",
            "system_constants": {
                "old_rating_weight": OLD_RATING_WEIGHT,
                "new_rating_weight": NEW_RATING_WEIGHT,
                "scale_min": NFL_SCALE_MIN,
                "scale_max": NFL_SCALE_MAX,
                "scale_average": NFL_SCALE_AVERAGE,
            },
        }

        with open(master_file, "w") as f:
            json.dump(master_data, f, indent=2)

        logger.info(f"Saved master ratings: {master_file}")

        # Save to current directory (for edge detection)
        current_file = self.current_dir / "nfl_power_ratings.json"
        with open(current_file, "w") as f:
            json.dump(self.updated_ratings, f, indent=2)

        logger.info(f"Saved current ratings: {current_file}")

    def generate_report(self):
        """Generate comprehensive power ratings report"""
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"NFL POWER RATINGS - WEEK {self.week or 'Current'}")
        logger.info("=" * 60)

        # Sort teams by rating
        sorted_teams = sorted(
            self.updated_ratings.items(), key=lambda x: x[1], reverse=True
        )

        logger.info("")
        logger.info("COMPLETE POWER RATINGS (Billy Walters Scale: 70-100)")
        logger.info("-" * 60)

        for rank, (team, rating) in enumerate(sorted_teams, 1):
            # Get previous rating for change calculation
            prev_rating = self.previous_ratings.get(team, rating)
            change = rating - prev_rating

            # Get raw Massey rating
            massey = self.current_massey.get(team, 0.0)

            # Tier classification
            if rating >= 95:
                tier = "ELITE+"
            elif rating >= 90:
                tier = "ELITE"
            elif rating >= 85:
                tier = "GOOD"
            elif rating >= 80:
                tier = "AVERAGE"
            elif rating >= 75:
                tier = "BELOW AVG"
            else:
                tier = "POOR"

            logger.info(
                f"{rank:2d}. {team:25s} {rating:5.2f} "
                f"({change:+.2f}) [{tier:9s}] Massey: {massey:+6.2f}"
            )

        # Summary statistics
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARY STATISTICS")
        logger.info("=" * 60)

        ratings_list = list(self.updated_ratings.values())
        avg_rating = sum(ratings_list) / len(ratings_list)
        max_rating = max(ratings_list)
        min_rating = min(ratings_list)

        logger.info(f"Average Rating:  {avg_rating:.2f}")
        logger.info(f"Highest Rating:  {max_rating:.2f}")
        logger.info(f"Lowest Rating:   {min_rating:.2f}")
        logger.info(f"Rating Range:    {max_rating - min_rating:.2f}")

        # Tier distribution
        elite_plus = sum(1 for r in ratings_list if r >= 95)
        elite = sum(1 for r in ratings_list if 90 <= r < 95)
        good = sum(1 for r in ratings_list if 85 <= r < 90)
        average = sum(1 for r in ratings_list if 80 <= r < 85)
        below_avg = sum(1 for r in ratings_list if 75 <= r < 80)
        poor = sum(1 for r in ratings_list if r < 75)

        logger.info("")
        logger.info("TIER DISTRIBUTION:")
        logger.info(f"  Elite+ (95-100):    {elite_plus:2d} teams")
        logger.info(f"  Elite (90-95):      {elite:2d} teams")
        logger.info(f"  Good (85-90):       {good:2d} teams")
        logger.info(f"  Average (80-85):    {average:2d} teams")
        logger.info(f"  Below Avg (75-80):  {below_avg:2d} teams")
        logger.info(f"  Poor (70-75):       {poor:2d} teams")

        # Biggest movers (if we have previous ratings)
        if self.previous_ratings:
            logger.info("")
            logger.info("BIGGEST MOVERS THIS WEEK:")

            changes = []
            for team, rating in self.updated_ratings.items():
                prev = self.previous_ratings.get(team, rating)
                change = rating - prev
                changes.append((team, change, prev, rating))

            # Top improvers
            changes.sort(key=lambda x: x[1], reverse=True)
            logger.info("\n  Top 5 Improvers:")
            for i, (team, change, prev, curr) in enumerate(changes[:5], 1):
                logger.info(
                    f"    {i}. {team:25s} {prev:.2f} → {curr:.2f} ({change:+.2f})"
                )

            # Top decliners
            logger.info("\n  Top 5 Decliners:")
            for i, (team, change, prev, curr) in enumerate(changes[-5:], 1):
                logger.info(
                    f"    {i}. {team:25s} {prev:.2f} → {curr:.2f} ({change:+.2f})"
                )

        logger.info("")
        logger.info("=" * 60)

    def run(self) -> bool:
        """Execute full power rating update"""
        try:
            # Auto-detect week if not provided
            if self.week is None:
                try:
                    from walters_analyzer.season_calendar import get_nfl_week

                    self.week = get_nfl_week()
                    logger.info(f"Auto-detected NFL Week: {self.week}")
                except Exception as e:
                    logger.warning(f"Could not auto-detect week: {e}")
                    self.week = 12

            # Load data
            if not self.load_massey_ratings():
                return False

            self.load_previous_ratings()  # Optional, won't fail if missing

            # Update ratings
            self.update_all_ratings()

            # Save results
            self.save_ratings()

            # Generate report
            self.generate_report()

            logger.info("")
            logger.info("[OK] POWER RATINGS UPDATE COMPLETE!")
            logger.info("")

            return True

        except Exception as e:
            logger.error(f"Update failed: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Update power ratings from Massey composite"
    )
    parser.add_argument(
        "--week", type=int, help="NFL week number (auto-detected if not provided)"
    )

    args = parser.parse_args()

    updater = PowerRatingUpdater(week=args.week)
    success = updater.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
