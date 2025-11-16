#!/usr/bin/env python3
"""
Power Rating Updater - Billy Walters 90/10 Formula
Automatically updates team power ratings after each week's games
"""

import json
import asyncio
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import pandas as pd

# Import existing scrapers
from massey_ratings_live_scraper import MasseyRatingsScraper


@dataclass
class GameResult:
    """Represents a completed game result"""

    week: int
    season: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    margin: int  # Positive = home won, Negative = away won

    def adjust_for_home_field(self, hfa: float = 2.5) -> float:
        """
        Adjust margin for home field advantage

        Args:
            hfa: Home field advantage in points (default 2.5 for NFL)

        Returns:
            Adjusted margin (positive favors better team regardless of location)
        """
        if self.margin > 0:  # Home team won
            return self.margin - hfa
        else:  # Away team won
            return self.margin + hfa


class PowerRatingManager:
    """
    Manages power ratings using Billy Walters 90/10 formula

    Formula: New Rating = (Old Rating × 0.90) + (Game Result × 0.10)
    """

    def __init__(self, sport: str = "nfl"):
        """
        Initialize power rating manager

        Args:
            sport: 'nfl' or 'ncaaf'
        """
        self.sport = sport
        self.ratings_file = Path(f"data/power_ratings/{sport}_ratings.json")
        self.ratings_file.parent.mkdir(parents=True, exist_ok=True)
        self.ratings: Dict[str, float] = {}
        self.history: List[Dict] = []

    async def initialize_from_massey(self):
        """
        Get Week 1 baseline power ratings from Massey Ratings

        This should be run at the start of the season to establish
        the initial ratings that will be updated weekly.
        """
        print(f"\n🔧 Initializing {self.sport.upper()} power ratings from Massey...")

        scraper = MasseyRatingsScraper()

        try:
            await scraper.initialize()
            print("✅ Browser initialized")

            # Map sport names
            massey_sport = "nfl" if self.sport == "nfl" else "cf"

            # Scrape ratings
            ratings_data = await scraper.scrape_team_ratings(massey_sport)

            # Convert to our format
            self.ratings = {}
            for team_data in ratings_data:
                team_name = team_data.team_name
                rating = team_data.rating
                self.ratings[team_name] = rating

            await scraper.close()

            # Save baseline
            self.save_ratings(week=0, label="Baseline_Massey")

            print(f"✅ Initialized {len(self.ratings)} teams")
            print("📊 Sample ratings:")
            for team, rating in list(self.ratings.items())[:5]:
                print(f"  {team}: {rating:.2f}")

        except Exception as e:
            print(f"❌ Error initializing from Massey: {e}")
            await scraper.close()

    def load_ratings(self, week: int = None):
        """
        Load power ratings from file

        Args:
            week: Specific week to load (None = latest)
        """
        try:
            with open(self.ratings_file, "r") as f:
                data = json.load(f)

            if week is None:
                # Get latest
                latest = max(data["history"], key=lambda x: x["week"])
                self.ratings = latest["ratings"]
                print(f"✅ Loaded ratings from Week {latest['week']}")
            else:
                # Get specific week
                week_data = next(
                    (h for h in data["history"] if h["week"] == week), None
                )
                if week_data:
                    self.ratings = week_data["ratings"]
                    print(f"✅ Loaded ratings from Week {week}")
                else:
                    print(f"❌ No ratings found for Week {week}")

        except FileNotFoundError:
            print(f"⚠️  No ratings file found at {self.ratings_file}")
            self.ratings = {}

    def save_ratings(self, week: int, label: str = ""):
        """
        Save current power ratings to file

        Args:
            week: Week number
            label: Optional label (e.g., "Baseline", "Updated")
        """
        try:
            # Load existing history
            try:
                with open(self.ratings_file, "r") as f:
                    data = json.load(f)
                history = data.get("history", [])
            except FileNotFoundError:
                history = []

            # Add current state
            history.append(
                {
                    "week": week,
                    "label": label,
                    "timestamp": datetime.now().isoformat(),
                    "ratings": self.ratings.copy(),
                }
            )

            # Save
            with open(self.ratings_file, "w") as f:
                json.dump(
                    {
                        "sport": self.sport,
                        "last_updated": datetime.now().isoformat(),
                        "history": history,
                    },
                    f,
                    indent=2,
                )

            print(f"💾 Saved ratings for Week {week} {label}")

        except Exception as e:
            print(f"❌ Error saving ratings: {e}")

    def update_with_90_10_formula(
        self,
        team: str,
        game_result_margin: float,
        weight_old: float = 0.90,
        weight_new: float = 0.10,
    ) -> float:
        """
        Apply Billy Walters 90/10 formula to update a team's rating

        Formula: New Rating = (Old Rating × 0.90) + (Game Result × 0.10)

        Args:
            team: Team name
            game_result_margin: Adjusted margin of victory/defeat
            weight_old: Weight for old rating (default 0.90)
            weight_new: Weight for game result (default 0.10)

        Returns:
            New power rating
        """
        old_rating = self.ratings.get(team, 0.0)
        new_rating = (old_rating * weight_old) + (game_result_margin * weight_new)
        return new_rating

    def update_from_game_result(self, game: GameResult):
        """
        Update both teams' ratings based on game result

        Args:
            game: GameResult object with final scores
        """
        # Adjust margin for home field advantage
        adjusted_margin = game.adjust_for_home_field()

        # Determine winner and loser
        if game.margin > 0:
            winner = game.home_team
            loser = game.away_team
        else:
            winner = game.away_team
            loser = game.home_team

        # Update winner (positive margin)
        winner_new = self.update_with_90_10_formula(winner, abs(adjusted_margin))

        # Update loser (negative margin)
        loser_new = self.update_with_90_10_formula(loser, -abs(adjusted_margin))

        # Save changes
        old_winner = self.ratings.get(winner, 0.0)
        old_loser = self.ratings.get(loser, 0.0)

        self.ratings[winner] = winner_new
        self.ratings[loser] = loser_new

        print(f"\n📊 Updated ratings for {winner} vs {loser}:")
        print(
            f"  {winner}: {old_winner:.2f} → {winner_new:.2f} ({winner_new - old_winner:+.2f})"
        )
        print(
            f"  {loser}: {old_loser:.2f} → {loser_new:.2f} ({loser_new - old_loser:+.2f})"
        )

    def update_from_week_results(self, week: int, games: List[GameResult]):
        """
        Update all ratings from a week's worth of games

        Args:
            week: Week number
            games: List of GameResult objects
        """
        print(f"\n{'=' * 60}")
        print(f"UPDATING POWER RATINGS - WEEK {week}")
        print(f"{'=' * 60}")

        # Load current ratings
        self.load_ratings(week - 1)

        # Update each game
        for game in games:
            self.update_from_game_result(game)

        # Save updated ratings
        self.save_ratings(week, label="Updated_90_10")

        print(f"\n✅ Updated {len(games)} games for Week {week}")

    def export_to_excel(self, filename: str = None):
        """
        Export power ratings to Excel for tracking

        Args:
            filename: Output filename (optional)
        """
        if filename is None:
            filename = (
                f"power_ratings_{self.sport}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )

        # Convert to DataFrame
        df = pd.DataFrame(
            [
                {"Team": team, "Power_Rating": rating}
                for team, rating in sorted(
                    self.ratings.items(), key=lambda x: x[1], reverse=True
                )
            ]
        )

        # Add rank
        df["Rank"] = range(1, len(df) + 1)

        # Reorder columns
        df = df[["Rank", "Team", "Power_Rating"]]

        # Save
        df.to_excel(filename, index=False)
        print(f"📊 Exported to {filename}")


# Example usage and testing
async def main():
    """Test power rating manager"""

    print("\n" + "=" * 60)
    print("POWER RATING MANAGER - BILLY WALTERS 90/10 FORMULA")
    print("=" * 60)

    # Initialize manager
    manager = PowerRatingManager(sport="nfl")

    # Option 1: Initialize from Massey (Week 0 baseline)
    print("\n1️⃣  Initialize from Massey Ratings...")
    await manager.initialize_from_massey()

    # Option 2: Load existing ratings
    # manager.load_ratings(week=5)

    # Example: Update with sample game results
    print("\n2️⃣  Example: Update from Week 1 games...")

    sample_games = [
        GameResult(
            week=1,
            season=2025,
            home_team="Kansas City Chiefs",
            away_team="Detroit Lions",
            home_score=21,
            away_score=20,
            margin=1,  # Chiefs win by 1
        ),
        GameResult(
            week=1,
            season=2025,
            home_team="Buffalo Bills",
            away_team="New York Jets",
            home_score=31,
            away_score=10,
            margin=21,  # Bills win by 21
        ),
    ]

    # Update ratings
    for game in sample_games:
        manager.update_from_game_result(game)

    # Save updated ratings
    manager.save_ratings(week=1, label="Example_Update")

    # Export to Excel
    manager.export_to_excel()

    print("\n✅ Power rating update complete!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SETUP INSTRUCTIONS:")
    print("=" * 60)
    print("\n1. Initialize baseline ratings:")
    print("   python power_rating_updater.py")
    print("\n2. After each week, update with game results")
    print("\n3. Ratings saved to: data/power_ratings/")
    print("\n" + "=" * 60 + "\n")

    asyncio.run(main())
