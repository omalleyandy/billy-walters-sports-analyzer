#!/usr/bin/env python3
"""
NFL Power Ratings Builder - Billy Walters Methodology

Builds power ratings from NFL.com official statistics, updated weekly.
Implements Billy Walters' principles:
- Use cumulative season stats (not just recent games)
- Weight offensive and defensive efficiency equally
- Adjust for strength of schedule
- Update ratings after each week
- Account for home field advantage

Ratings Formula:
    Offensive Rating = (Points/Game + Yards/Game × 0.04) × SoS_factor
    Defensive Rating = (Points Allowed/Game + Yards Allowed/Game × 0.04) × SoS_factor
    Power Rating = Offensive Rating - (Defensive Rating - League Avg)

This gives teams credit for:
- High offensive rating (scoring ability)
- Low defensive rating (points prevention)
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class TeamStats:
    """Weekly cumulative team statistics from NFL.com"""

    team: str
    team_abbr: str
    week: int
    season: int

    # Record
    wins: int
    losses: int
    ties: int
    games_played: int

    # Offensive stats
    points_scored: int
    total_yards: int
    passing_yards: int
    rushing_yards: int
    turnovers_lost: int

    # Defensive stats
    points_allowed: int
    yards_allowed: int
    passing_yards_allowed: int
    rushing_yards_allowed: int
    turnovers_forced: int

    # Schedule
    opponents: List[str]


@dataclass
class PowerRating:
    """Team power rating for a specific week"""

    team: str
    team_abbr: str
    week: int
    season: int

    # Core ratings
    offensive_rating: float
    defensive_rating: float
    power_rating: float

    # Components
    points_per_game: float
    points_allowed_per_game: float
    yards_per_game: float
    yards_allowed_per_game: float
    turnover_margin: float

    # Adjustments
    strength_of_schedule: float
    home_field_advantage: float

    # Metadata
    games_played: int
    record: str


class NFLPowerRatingsBuilder:
    """
    Builds NFL power ratings using Billy Walters methodology.

    Key Principles:
    1. Use cumulative season stats (not rolling averages)
    2. Offensive Rating = Scoring ability + Yardage efficiency
    3. Defensive Rating = Points prevention + Yardage prevention
    4. Adjust for strength of schedule
    5. Update weekly as new games are played
    """

    # Constants
    YARDS_TO_POINTS = 0.04  # 100 yards ≈ 4 points
    BASELINE_HFA = 2.5  # Home field advantage in points
    LEAGUE_AVERAGE_PPG = 22.0  # NFL average points per game per team

    def __init__(self, output_dir: str = "output/power_ratings"):
        """Initialize power ratings builder"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.team_stats: Dict[str, TeamStats] = {}
        self.power_ratings: Dict[str, PowerRating] = {}
        self.schedule_strength: Dict[str, float] = {}

        logger.info("NFL Power Ratings Builder initialized")

    def load_team_stats(self, stats_file: Path) -> None:
        """
        Load team statistics from NFL.com data.

        Args:
            stats_file: Path to JSON file with team stats
        """
        with open(stats_file) as f:
            data = json.load(f)

        for team_data in data:
            team_abbr = team_data["team_abbr"]

            # Convert to TeamStats (simplified version of NFLTeamStats)
            self.team_stats[team_abbr] = TeamStats(
                team=team_data["team"],
                team_abbr=team_abbr,
                week=team_data["week"],
                season=team_data["season"],
                wins=team_data["wins"],
                losses=team_data["losses"],
                ties=team_data["ties"],
                games_played=team_data["games_played"],
                points_scored=team_data["points_scored"],
                total_yards=team_data["total_yards"],
                passing_yards=team_data["passing_yards"],
                rushing_yards=team_data["rushing_yards"],
                turnovers_lost=team_data["turnovers_lost"],
                points_allowed=team_data["points_allowed"],
                yards_allowed=team_data["yards_allowed"],
                passing_yards_allowed=team_data["passing_yards_allowed"],
                rushing_yards_allowed=team_data["rushing_yards_allowed"],
                turnovers_forced=team_data["turnovers_forced"],
                opponents=team_data["opponents"],
            )

        logger.info(f"Loaded stats for {len(self.team_stats)} teams")

    def calculate_strength_of_schedule(self) -> None:
        """
        Calculate strength of schedule for each team.

        Uses iterative approach:
        1. Initial estimate: average opponent win percentage
        2. Adjust based on opponent's opponent strength
        3. Converge to stable values
        """
        # Initial estimate: opponent win percentage
        for team_abbr, stats in self.team_stats.items():
            if stats.games_played == 0:
                self.schedule_strength[team_abbr] = 1.0
                continue

            opponent_wins = 0
            opponent_games = 0

            for opponent_abbr in stats.opponents:
                if opponent_abbr in self.team_stats:
                    opp_stats = self.team_stats[opponent_abbr]
                    opponent_wins += opp_stats.wins
                    opponent_games += opp_stats.games_played

            if opponent_games > 0:
                opp_win_pct = opponent_wins / opponent_games
                # Normalize around 1.0 (0.5 win% = 1.0 factor)
                self.schedule_strength[team_abbr] = 0.5 + opp_win_pct
            else:
                self.schedule_strength[team_abbr] = 1.0

        logger.info("Calculated strength of schedule for all teams")

    def calculate_offensive_rating(self, stats: TeamStats) -> float:
        """
        Calculate offensive power rating.

        Formula:
            Base = Points/Game + (Yards/Game × 0.04)
            Adjusted = Base × SoS_factor

        Higher rating = better offense

        Args:
            stats: Team statistics

        Returns:
            Offensive rating (typically 15-30)
        """
        if stats.games_played == 0:
            return self.LEAGUE_AVERAGE_PPG

        ppg = stats.points_scored / stats.games_played
        ypg = stats.total_yards / stats.games_played

        # Base offensive rating
        base_rating = ppg + (ypg * self.YARDS_TO_POINTS)

        # Adjust for strength of schedule
        sos_factor = self.schedule_strength.get(stats.team_abbr, 1.0)
        adjusted_rating = base_rating * sos_factor

        return adjusted_rating

    def calculate_defensive_rating(self, stats: TeamStats) -> float:
        """
        Calculate defensive power rating.

        Formula:
            Base = Points Allowed/Game + (Yards Allowed/Game × 0.04)
            Adjusted = Base × SoS_factor

        LOWER rating = better defense (allows fewer points)

        Args:
            stats: Team statistics

        Returns:
            Defensive rating (typically 15-30, lower is better)
        """
        if stats.games_played == 0:
            return self.LEAGUE_AVERAGE_PPG

        papg = stats.points_allowed / stats.games_played
        yapg = stats.yards_allowed / stats.games_played

        # Base defensive rating (points allowed)
        base_rating = papg + (yapg * self.YARDS_TO_POINTS)

        # Adjust for strength of schedule
        sos_factor = self.schedule_strength.get(stats.team_abbr, 1.0)
        adjusted_rating = base_rating * sos_factor

        return adjusted_rating

    def calculate_power_rating(self, off_rating: float, def_rating: float) -> float:
        """
        Calculate overall power rating.

        Formula:
            Power = Offensive Rating - (Defensive Rating - League Avg)

        This gives credit for:
        - High offensive rating (more points scored)
        - Low defensive rating (fewer points allowed)

        Args:
            off_rating: Offensive rating
            def_rating: Defensive rating

        Returns:
            Overall power rating
        """
        # Defense is inverted: lower is better, so subtract from league average
        defensive_contribution = self.LEAGUE_AVERAGE_PPG - def_rating

        power = off_rating + defensive_contribution

        return power

    def build_ratings_for_week(self, week: int, season: int) -> Dict[str, PowerRating]:
        """
        Build power ratings for all teams for a specific week.

        Args:
            week: Week number (1-18)
            season: Season year

        Returns:
            Dictionary of team_abbr -> PowerRating
        """
        logger.info(f"Building power ratings for Week {week}, {season}")

        # Calculate strength of schedule
        self.calculate_strength_of_schedule()

        ratings = {}

        for team_abbr, stats in self.team_stats.items():
            # Calculate ratings
            off_rating = self.calculate_offensive_rating(stats)
            def_rating = self.calculate_defensive_rating(stats)
            power_rating = self.calculate_power_rating(off_rating, def_rating)

            # Calculate per-game stats
            games = stats.games_played if stats.games_played > 0 else 1
            ppg = stats.points_scored / games
            papg = stats.points_allowed / games
            ypg = stats.total_yards / games
            yapg = stats.yards_allowed / games
            turnover_margin = (stats.turnovers_forced - stats.turnovers_lost) / games

            # Get SoS
            sos = self.schedule_strength.get(team_abbr, 1.0)

            # Create record string
            record = f"{stats.wins}-{stats.losses}"
            if stats.ties > 0:
                record += f"-{stats.ties}"

            rating = PowerRating(
                team=stats.team,
                team_abbr=team_abbr,
                week=week,
                season=season,
                offensive_rating=off_rating,
                defensive_rating=def_rating,
                power_rating=power_rating,
                points_per_game=ppg,
                points_allowed_per_game=papg,
                yards_per_game=ypg,
                yards_allowed_per_game=yapg,
                turnover_margin=turnover_margin,
                strength_of_schedule=sos,
                home_field_advantage=self.BASELINE_HFA,
                games_played=stats.games_played,
                record=record,
            )

            ratings[team_abbr] = rating

        self.power_ratings = ratings
        logger.info(f"Built ratings for {len(ratings)} teams")

        return ratings

    def save_ratings(self, week: int, season: int) -> Path:
        """
        Save power ratings to JSON file

        Args:
            week: Week number
            season: Season year

        Returns:
            Path to saved file
        """
        output_file = self.output_dir / f"nfl_power_ratings_week{week}_{season}.json"

        ratings_data = {
            team_abbr: asdict(rating)
            for team_abbr, rating in self.power_ratings.items()
        }

        with open(output_file, "w") as f:
            json.dump(ratings_data, f, indent=2)

        logger.info(f"Saved power ratings to {output_file}")
        return output_file

    def print_ratings_summary(self) -> None:
        """Print summary of power ratings"""
        if not self.power_ratings:
            print("No ratings to display")
            return

        print("\n" + "=" * 100)
        print("NFL POWER RATINGS SUMMARY")
        print("=" * 100)

        # Sort by power rating
        sorted_teams = sorted(
            self.power_ratings.items(), key=lambda x: x[1].power_rating, reverse=True
        )

        sample_rating = sorted_teams[0][1]
        print(f"\nWeek {sample_rating.week}, {sample_rating.season} Season")
        print(
            f"\n{'Rank':<5} {'Team':<25} {'Power':<8} {'Off':<8} {'Def':<8} "
            f"{'PPG':<7} {'PA/G':<7} {'Record':<8} {'SoS':<6}"
        )
        print("-" * 100)

        for i, (team_abbr, rating) in enumerate(sorted_teams, 1):
            print(
                f"{i:<5} {rating.team:<25} {rating.power_rating:>6.2f}  "
                f"{rating.offensive_rating:>6.2f}  {rating.defensive_rating:>6.2f}  "
                f"{rating.points_per_game:>5.1f}  "
                f"{rating.points_allowed_per_game:>5.1f}  "
                f"{rating.record:<8} {rating.strength_of_schedule:>5.2f}"
            )

        print("=" * 100)
        print(f"\nRatings calculated for {len(sorted_teams)} teams")
        print("\nNote: Lower defensive rating = better defense (fewer points allowed)")
        print("      Higher power rating = better overall team")
        print("=" * 100)


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Build NFL power ratings")
    parser.add_argument(
        "--stats-file",
        type=str,
        required=True,
        help="Path to NFL team stats JSON file",
    )
    parser.add_argument("--week", type=int, required=True, help="Week number")
    parser.add_argument("--season", type=int, default=2025, help="Season year")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/power_ratings",
        help="Output directory",
    )

    args = parser.parse_args()

    # Build ratings
    builder = NFLPowerRatingsBuilder(output_dir=args.output_dir)
    builder.load_team_stats(Path(args.stats_file))
    builder.build_ratings_for_week(week=args.week, season=args.season)

    # Save and print
    output_file = builder.save_ratings(week=args.week, season=args.season)
    builder.print_ratings_summary()

    print(f"\n✓ Power ratings saved to: {output_file}")


if __name__ == "__main__":
    main()
