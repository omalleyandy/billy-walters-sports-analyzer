#!/usr/bin/env python3
"""
Billy Walters E-Factor (Emotional Factor) Reference System
===========================================================

Implements the complete E-Factor (Emotional Factors) system from Billy Walters'
Advanced Master Class methodology.

Key Principle: Each E-Factor is worth 0.2 points in the betting system.

E-Factors cover emotional/psychological advantages:
- Revenge games: Team playing opponent they lost to earlier
- Lookahead spots: Team distracted by important next opponent
- Letdown spots: Team playing down after big win/loss
- Coaching changes: New coach effect (mid-season replacements)
- Playoff importance: Desperation/clinching scenarios
- Winning streaks: Momentum and confidence factors
- Losing streaks: Demoralization and corrective urgency

Based on: "Gambler: Secrets from a Life at Risk" - Advanced Master Class
Version: 1.0
Date: November 27, 2025
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EFactorResult:
    """Result of E-Factor calculation."""

    total_points: float
    adjustment: float
    breakdown: Dict[str, float]  # Details by category

    def __str__(self) -> str:
        """String representation of E-Factor result."""
        return (
            f"E-Factors: {self.total_points:.2f} pts -> {self.adjustment:.2f} adjustment"
        )


class EFactorCalculator:
    """
    Calculate E-Factors (Emotional Factors) per Billy Walters methodology.

    Each E-factor is worth 0.2 points in the betting system.
    Positive values favor the team being analyzed.
    """

    # Base point value per E-Factor
    POINT_VALUE = 0.2

    # ===== REVENGE GAME (Earlier season loss) =====
    # When team plays opponent they lost to earlier
    REVENGE_SMALL_LOSS = 0.2  # Lost by <7 points
    REVENGE_MODERATE_LOSS = 0.3  # Lost by 7-14 points
    REVENGE_LARGE_LOSS = 0.5  # Lost by 15+ points

    # ===== LOOKAHEAD SPOT (Next week is important) =====
    # Team distracted by important next opponent
    LOOKAHEAD_SLIGHT = 0.3  # Next opponent slightly stronger
    LOOKAHEAD_MODERATE = 0.5  # Next opponent significantly stronger
    LOOKAHEAD_CRITICAL = 0.8  # Critical playoff game next week

    # ===== LETDOWN SPOT (After big win) =====
    # Team may play down after emotional high
    LETDOWN_BIG_WIN = 0.3  # Coming off big 10+ point win
    LETDOWN_EMOTIONAL = 0.5  # Coming off emotional/playoff win
    LETDOWN_CHAMPIONSHIP = 0.8  # Coming off championship game

    # ===== COACHING CHANGE (Mid-season replacement) =====
    # New coaching staff effect (positive or negative)
    COACHING_CHANGE_INTERIM_NEGATIVE = -0.2  # Players confused/demoralized
    COACHING_CHANGE_INTERIM_POSITIVE = 0.2  # Rally effect around new coach
    COACHING_CHANGE_PERMANENT = 0.6  # Full system change adjustment

    # ===== PLAYOFF IMPORTANCE =====
    # Desperation factor for playoff implications
    PLAYOFF_CLINCHING = 0.8  # Can clinch playoff spot this week
    PLAYOFF_ELIMINATION = 1.0  # Risk elimination this week
    PLAYOFF_WILDCARD_RACE = 0.5  # Fighting for wild card spot
    PLAYOFF_SEEDING = 0.3  # Slight seeding impact

    # ===== STREAKS =====
    WINNING_STREAK_2_GAMES = 0.2  # Won last 2
    WINNING_STREAK_3_PLUS = 0.5  # Won last 3+
    LOSING_STREAK_2_GAMES = 0.2  # Lost last 2 (corrective urgency)
    LOSING_STREAK_3_PLUS = 0.5  # Lost last 3+ (must-win mentality)

    @classmethod
    def calculate_revenge_game_factor(
        cls, played_earlier: bool, earlier_loss_margin: Optional[int] = None
    ) -> tuple[float, str]:
        """
        Calculate revenge game psychological factor.

        Args:
            played_earlier: Whether teams played earlier in season
            earlier_loss_margin: Points lost by (positive = loss, negative = win)

        Returns:
            Tuple of (point_adjustment, description)
            Positive = Favors team seeking revenge
        """
        if not played_earlier or earlier_loss_margin is None:
            return (0.0, "Not a revenge situation")

        # Earlier win is no revenge factor
        if earlier_loss_margin < 0:
            return (0.0, f"Won earlier matchup by {abs(earlier_loss_margin)}")

        # Calibrate by loss margin
        if earlier_loss_margin <= 7:
            points = cls.REVENGE_SMALL_LOSS
            desc = (
                f"Revenge spot: Lost by {earlier_loss_margin}pts -> "
                f"+{points} (slight edge)"
            )
        elif earlier_loss_margin <= 14:
            points = cls.REVENGE_MODERATE_LOSS
            desc = (
                f"Revenge spot: Lost by {earlier_loss_margin}pts -> "
                f"+{points} (moderate edge)"
            )
        else:
            points = cls.REVENGE_LARGE_LOSS
            desc = (
                f"Revenge spot: Lost by {earlier_loss_margin}pts -> "
                f"+{points} (strong edge)"
            )

        return (points, desc)

    @classmethod
    def calculate_lookahead_spot_factor(
        cls,
        next_opponent_strength: Optional[float] = None,
        next_game_playoff_implications: bool = False,
    ) -> tuple[float, str]:
        """
        Calculate lookahead spot (distraction) factor.

        Team may be distracted by important upcoming opponent.

        Args:
            next_opponent_strength: Next opponent power rating (higher = stronger)
            next_game_playoff_implications: True if next game has playoff impact

        Returns:
            Tuple of (point_adjustment, description)
            Positive = Current opponent benefits from lookahead distraction
        """
        if next_opponent_strength is None:
            return (0.0, "No lookahead information available")

        # Playoff game next week = major distraction
        if next_game_playoff_implications:
            points = cls.LOOKAHEAD_CRITICAL
            return (
                points,
                f"Critical lookahead: Playoff game next week -> "
                f"+{points} (distraction factor)",
            )

        # Calibrate by opponent strength (power rating difference)
        # Assume current opponent is ~0
        if next_opponent_strength >= 10:
            points = cls.LOOKAHEAD_CRITICAL
            desc = (
                f"Major lookahead: Next opponent +{next_opponent_strength} -> +{points}"
            )
        elif next_opponent_strength >= 5:
            points = cls.LOOKAHEAD_MODERATE
            desc = f"Moderate lookahead: Next opponent +{next_opponent_strength} -> +{points}"
        else:
            points = cls.LOOKAHEAD_SLIGHT
            desc = (
                f"Slight lookahead: Next opponent +{next_opponent_strength} -> +{points}"
            )

        return (points, desc)

    @classmethod
    def calculate_letdown_spot_factor(
        cls, coming_off_big_win: bool, win_margin: Optional[int] = None
    ) -> tuple[float, str]:
        """
        Calculate letdown spot (emotional crash) factor.

        Team may play down after emotional/dominant win.

        Args:
            coming_off_big_win: True if team won last game by large margin
            win_margin: Points won by (positive value)

        Returns:
            Tuple of (point_adjustment, description)
            Positive = Opponent benefits from letdown factor
        """
        if not coming_off_big_win or win_margin is None or win_margin <= 10:
            return (0.0, "No letdown spot identified")

        # Calibrate by win margin
        if win_margin <= 20:
            points = cls.LETDOWN_BIG_WIN
            desc = f"Letdown spot: Won by {win_margin}pts -> +{points} (slight emotional high)"
        elif win_margin <= 30:
            points = cls.LETDOWN_EMOTIONAL
            desc = f"Letdown spot: Won by {win_margin}pts -> +{points} (emotional high)"
        else:
            points = cls.LETDOWN_CHAMPIONSHIP
            desc = f"Letdown spot: Dominant {win_margin}pt win -> +{points} (maximum letdown)"

        return (points, desc)

    @classmethod
    def calculate_coaching_change_factor(
        cls,
        coaching_change_this_week: bool,
        interim_coach: bool = True,
        team_response: str = "neutral",
    ) -> tuple[float, str]:
        """
        Calculate coaching change psychological factor.

        New coach (interim or permanent) creates adjustment period.

        Args:
            coaching_change_this_week: True if coaching change occurred
            interim_coach: True if interim (vs permanent replacement)
            team_response: "positive", "negative", or "neutral" (player reaction)

        Returns:
            Tuple of (point_adjustment, description)
        """
        if not coaching_change_this_week:
            return (0.0, "No coaching change")

        if interim_coach:
            if team_response == "positive":
                points = cls.COACHING_CHANGE_INTERIM_POSITIVE
                desc = "Rally effect: Interim coach, players energized -> +{points}"
            else:
                points = cls.COACHING_CHANGE_INTERIM_NEGATIVE
                desc = "Adjustment period: Interim coach, uncertainty -> {points}"
        else:
            points = cls.COACHING_CHANGE_PERMANENT
            desc = f"Permanent coaching change: Full system adjustment -> +{points}"

        return (points, desc)

    @classmethod
    def calculate_playoff_importance_factor(
        cls,
        can_clinch_playoff: bool = False,
        risk_elimination: bool = False,
        playoff_position: str = "none",
    ) -> tuple[float, str]:
        """
        Calculate playoff importance/desperation factor.

        Teams fighting for playoff spots show different urgency.

        Args:
            can_clinch_playoff: True if team can clinch playoff spot this week
            risk_elimination: True if loss eliminates from playoff contention
            playoff_position: "clinched", "in", "fighting", "eliminated", "none"

        Returns:
            Tuple of (point_adjustment, description)
        """
        # Elimination risk = highest desperation
        if risk_elimination:
            points = cls.PLAYOFF_ELIMINATION
            return (
                points,
                f"Desperation: Risk elimination this week -> +{points}",
            )

        # Clinching opportunity
        if can_clinch_playoff:
            points = cls.PLAYOFF_CLINCHING
            return (
                points,
                f"Playoff clinch opportunity: Can lock playoff spot -> +{points}",
            )

        # Playoff position impacts
        if playoff_position == "fighting":
            points = cls.PLAYOFF_WILDCARD_RACE
            return (points, f"Wildcard race: Fighting for spot -> +{points}")
        elif playoff_position == "in":
            points = cls.PLAYOFF_SEEDING
            return (points, f"Seeding implications: Already in playoffs -> +{points}")

        return (0.0, "No playoff implications")

    @classmethod
    def calculate_winning_streak_factor(cls, games_won: int) -> tuple[float, str]:
        """
        Calculate winning streak psychological momentum factor.

        Confidence and momentum build with wins.

        Args:
            games_won: Number of consecutive wins (0+ value)

        Returns:
            Tuple of (point_adjustment, description)
            Positive = Team plays better with winning streak
        """
        if games_won < 2:
            return (0.0, "No meaningful winning streak")

        if games_won == 2:
            points = cls.WINNING_STREAK_2_GAMES
            desc = f"Winning streak: {games_won} straight wins -> +{points}"
        else:
            points = cls.WINNING_STREAK_3_PLUS
            desc = f"Strong momentum: {games_won} straight wins -> +{points}"

        return (points, desc)

    @classmethod
    def calculate_losing_streak_factor(cls, games_lost: int) -> tuple[float, str]:
        """
        Calculate losing streak corrective/desperation factor.

        Teams on losing streaks show "must-win" mentality.

        Args:
            games_lost: Number of consecutive losses (0+ value)

        Returns:
            Tuple of (point_adjustment, description)
            Positive = Team plays better with losing streak (corrective urgency)
        """
        if games_lost < 2:
            return (0.0, "No meaningful losing streak")

        if games_lost == 2:
            points = cls.LOSING_STREAK_2_GAMES
            desc = f"Corrective: {games_lost} straight losses -> +{points}"
        else:
            points = cls.LOSING_STREAK_3_PLUS
            desc = f"Must-win: {games_lost} straight losses -> +{points} (desperation)"

        return (points, desc)

    @classmethod
    def calculate_all_e_factors(
        cls,
        played_earlier: bool = False,
        earlier_loss_margin: Optional[int] = None,
        next_opponent_strength: Optional[float] = None,
        next_game_playoff_implications: bool = False,
        coming_off_big_win: bool = False,
        big_win_margin: Optional[int] = None,
        coaching_change_this_week: bool = False,
        interim_coach: bool = True,
        team_response: str = "neutral",
        can_clinch_playoff: bool = False,
        risk_elimination: bool = False,
        playoff_position: str = "none",
        games_won: int = 0,
        games_lost: int = 0,
    ) -> EFactorResult:
        """
        Calculate all E-Factors for a team in a specific game.

        Aggregates all emotional/psychological factors into single adjustment.

        Args:
            played_earlier: Earlier matchup this season
            earlier_loss_margin: Points lost by in earlier matchup
            next_opponent_strength: Next week's opponent power rating
            next_game_playoff_implications: Next week is playoff-relevant
            coming_off_big_win: Last game was dominant win
            big_win_margin: Points won by in last game
            coaching_change_this_week: New coaching staff this week
            interim_coach: Is replacement interim (vs permanent)
            team_response: How players responded to coaching change
            can_clinch_playoff: Can clinch playoff spot
            risk_elimination: Risk playoff elimination
            playoff_position: Current playoff standing
            games_won: Current winning streak length
            games_lost: Current losing streak length

        Returns:
            EFactorResult with total points and breakdown
        """
        total_points = 0.0
        breakdown = {}

        # Revenge game factor
        revenge_pts, _ = cls.calculate_revenge_game_factor(
            played_earlier, earlier_loss_margin
        )
        total_points += revenge_pts
        breakdown["revenge_game"] = revenge_pts

        # Lookahead spot factor
        lookahead_pts, _ = cls.calculate_lookahead_spot_factor(
            next_opponent_strength, next_game_playoff_implications
        )
        total_points += lookahead_pts
        breakdown["lookahead_spot"] = lookahead_pts

        # Letdown spot factor
        letdown_pts, _ = cls.calculate_letdown_spot_factor(
            coming_off_big_win, big_win_margin
        )
        total_points += letdown_pts
        breakdown["letdown_spot"] = letdown_pts

        # Coaching change factor
        coaching_pts, _ = cls.calculate_coaching_change_factor(
            coaching_change_this_week, interim_coach, team_response
        )
        total_points += coaching_pts
        breakdown["coaching_change"] = coaching_pts

        # Playoff importance factor
        playoff_pts, _ = cls.calculate_playoff_importance_factor(
            can_clinch_playoff, risk_elimination, playoff_position
        )
        total_points += playoff_pts
        breakdown["playoff_importance"] = playoff_pts

        # Winning streak factor
        winning_pts, _ = cls.calculate_winning_streak_factor(games_won)
        total_points += winning_pts
        breakdown["winning_streak"] = winning_pts

        # Losing streak factor
        losing_pts, _ = cls.calculate_losing_streak_factor(games_lost)
        total_points += losing_pts
        breakdown["losing_streak"] = losing_pts

        return EFactorResult(
            total_points=total_points,
            adjustment=total_points,  # E-Factors applied directly (0.2 per factor)
            breakdown=breakdown,
        )


def main() -> None:
    """Example usage of E-Factor calculator."""
    # Example 1: Revenge game scenario
    print("Example 1: Revenge Game")
    print("-" * 60)
    revenge_pts, revenge_desc = EFactorCalculator.calculate_revenge_game_factor(
        played_earlier=True, earlier_loss_margin=10
    )
    print(f"{revenge_desc}")
    print()

    # Example 2: Lookahead spot scenario
    print("Example 2: Lookahead Spot (Distraction)")
    print("-" * 60)
    lookahead_pts, lookahead_desc = EFactorCalculator.calculate_lookahead_spot_factor(
        next_opponent_strength=8.5, next_game_playoff_implications=False
    )
    print(f"{lookahead_desc}")
    print()

    # Example 3: Playoff desperation scenario
    print("Example 3: Playoff Desperation")
    print("-" * 60)
    playoff_pts, playoff_desc = EFactorCalculator.calculate_playoff_importance_factor(
        risk_elimination=True
    )
    print(f"{playoff_desc}")
    print()

    # Example 4: Combined E-Factors
    print("Example 4: Combined E-Factors (Full Game Scenario)")
    print("-" * 60)
    result = EFactorCalculator.calculate_all_e_factors(
        played_earlier=True,
        earlier_loss_margin=7,
        next_opponent_strength=5.0,
        next_game_playoff_implications=False,
        coming_off_big_win=True,
        big_win_margin=24,
        risk_elimination=False,
        playoff_position="fighting",
        games_won=2,
        games_lost=0,
    )
    print(f"{result}")
    print("\nDetailed Breakdown:")
    for factor, points in result.breakdown.items():
        if points != 0:
            print(f"  {factor}: {points:+.2f}")


if __name__ == "__main__":
    main()
