"""
NCAAF Situational Factors (S-Factor) Calculator

College football specific situational adjustments including:
- Rest advantages
- Travel distance impact
- Conference games (higher intensity)
- Rivalry games
- Playoff/Bowl implications
- Schedule spot analysis (revenge, lookahead, letdown)
"""

from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NCAAFSituationalFactors:
    """Calculate NCAAF-specific situational factor adjustments"""

    # S-Factor adjustment values (in points)
    ADJUSTMENTS = {
        # Rest advantages (similar to NFL but college teams less frequently play back-to-back)
        "extra_rest": +1.5,  # 8+ days vs opponent's 6
        "short_rest": -2.0,  # <6 days rest
        "equivalent_rest": 0.0,  # Same rest as opponent
        # Travel distance (larger impact in college due to student-athlete restrictions)
        "long_travel": -1.5,  # >1500 miles
        "medium_travel": -0.8,  # 500-1500 miles
        "short_travel": -0.3,  # <500 miles
        "home_state": 0.0,  # Playing in home state
        # Conference dynamics
        "conference_game": +1.0,  # Conference play (higher intensity)
        "rivalry_game": +1.5,  # Historical rivalry
        # Schedule spot advantages
        "revenge_spot": +1.2,  # Playing team that beat them recently
        "lookahead_spot": -2.0,  # Looking ahead to big game next week
        "letdown_spot": -1.5,  # After emotional win
        # Playoff implications
        "playoff_implications": +1.5,  # Game affects bowl/playoff eligibility
        "bowl_locked_in": -0.5,  # No incentive (bowl already won)
        "elimination_game": +2.0,  # Loss ends season hopes
    }

    # Conference strength relative adjustments
    CONFERENCE_STRENGTH = {
        # Power 5 conferences (strong)
        "SEC": 0.0,  # Baseline (strongest)
        "Big Ten": 0.0,
        "ACC": 0.0,
        "Big 12": 0.0,
        "Pac-12": 0.0,
        # Group of 5 conferences
        "AAC": -0.3,
        "MAC": -0.5,
        "Mountain West": -0.3,
        "Mid-American": -0.5,
        "FBS Independent": -0.2,
    }

    def __init__(self):
        """Initialize NCAAF situational factors calculator"""
        self.logger = logging.getLogger(__name__)

    async def calculate(
        self, game: Dict, ratings: Dict[str, float], week: int
    ) -> float:
        """
        Calculate total situational factor adjustment for a game.

        Args:
            game: Game data dict containing team info, schedules
            ratings: Power ratings dict {team_name: rating}
            week: NCAAF week number

        Returns:
            Total S-factor adjustment in points
        """
        total_adjustment = 0.0

        try:
            away_team = game.get("away_team", "")
            home_team = game.get("home_team", "")

            # Rest advantage
            away_rest = game.get("away_rest_days", 7)
            home_rest = game.get("home_rest_days", 7)
            rest_adj = self._calculate_rest_advantage(away_rest, home_rest)
            total_adjustment += rest_adj

            # Travel distance
            travel_distance = game.get("travel_distance_miles", 0)
            travel_adj = self._calculate_travel_penalty(travel_distance)
            total_adjustment += travel_adj

            # Conference game bonus
            away_conf = game.get("away_conference", "")
            home_conf = game.get("home_conference", "")
            if away_conf and home_conf and away_conf == home_conf:
                total_adjustment += self.ADJUSTMENTS["conference_game"]

            # Rivalry bonus
            if self._is_rivalry_game(away_team, home_team):
                total_adjustment += self.ADJUSTMENTS["rivalry_game"]

            # Schedule spot analysis
            if game.get("revenge_spot", False):
                total_adjustment += self.ADJUSTMENTS["revenge_spot"]
            if game.get("lookahead_spot", False):
                total_adjustment += self.ADJUSTMENTS["lookahead_spot"]
            if game.get("letdown_spot", False):
                total_adjustment += self.ADJUSTMENTS["letdown_spot"]

            # Playoff/bowl implications
            playoff_adj = await self.emotional_adjustment(game, week)
            total_adjustment += playoff_adj

            return total_adjustment

        except Exception as e:
            self.logger.warning(f"Error calculating S-factor: {e}")
            return 0.0

    def _calculate_rest_advantage(
        self, away_rest: int, home_rest: int
    ) -> float:
        """
        Calculate rest advantage adjustment.

        Args:
            away_rest: Days rest for away team
            home_rest: Days rest for home team

        Returns:
            Rest adjustment in points (positive for away team)
        """
        rest_diff = away_rest - home_rest

        if rest_diff >= 2:
            return self.ADJUSTMENTS["extra_rest"]
        elif rest_diff <= -2:
            return -self.ADJUSTMENTS["short_rest"]
        else:
            return self.ADJUSTMENTS["equivalent_rest"]

    def _calculate_travel_penalty(self, distance_miles: int) -> float:
        """
        Calculate travel distance penalty (always negative for away team).

        Args:
            distance_miles: Travel distance in miles

        Returns:
            Travel penalty in points (negative)
        """
        if distance_miles > 1500:
            return self.ADJUSTMENTS["long_travel"]
        elif distance_miles > 500:
            return self.ADJUSTMENTS["medium_travel"]
        elif distance_miles > 100:
            return self.ADJUSTMENTS["short_travel"]
        else:
            return self.ADJUSTMENTS["home_state"]

    def _is_rivalry_game(self, away_team: str, home_team: str) -> bool:
        """
        Detect if game is a rivalry matchup.

        Args:
            away_team: Away team name
            home_team: Home team name

        Returns:
            True if rivalry game
        """
        rivalries = {
            ("Ohio State", "Michigan"),
            ("Michigan", "Ohio State"),
            ("Alabama", "Auburn"),
            ("Auburn", "Alabama"),
            ("Oklahoma", "Texas"),
            ("Texas", "Oklahoma"),
            ("Florida", "Georgia"),
            ("Georgia", "Florida"),
            ("LSU", "Alabama"),
            ("Alabama", "LSU"),
            ("Notre Dame", "Michigan"),
            ("Michigan", "Notre Dame"),
            ("Clemson", "South Carolina"),
            ("South Carolina", "Clemson"),
            ("Florida State", "Florida"),
            ("Florida", "Florida State"),
            ("Tennessee", "Kentucky"),
            ("Kentucky", "Tennessee"),
            ("Penn State", "Ohio State"),
            ("Ohio State", "Penn State"),
            ("Nebraska", "Iowa"),
            ("Iowa", "Nebraska"),
            ("Texas A&M", "Texas"),
            ("Texas", "Texas A&M"),
            ("Oklahoma State", "Oklahoma"),
            ("Oklahoma", "Oklahoma State"),
            ("Wisconsin", "Minnesota"),
            ("Minnesota", "Wisconsin"),
            ("Iowa State", "Kansas State"),
            ("Kansas State", "Iowa State"),
        }

        return (away_team, home_team) in rivalries

    async def emotional_adjustment(self, game: Dict, week: int) -> float:
        """
        Calculate emotional/motivational adjustment for playoff implications.

        In college football, bowl eligibility, playoff positioning, and coaching
        changes create significant emotional swings.

        Args:
            game: Game data
            week: NCAAF week number

        Returns:
            Emotional adjustment in points
        """
        try:
            adjustment = 0.0

            # Playoff implications (late season, top 25 teams)
            if game.get("playoff_implications", False):
                adjustment += self.ADJUSTMENTS["playoff_implications"]

            # Bowl game elimination (loss knocks team out)
            if game.get("elimination_game", False):
                adjustment += self.ADJUSTMENTS["elimination_game"]

            # Bowl game locked in (less motivation)
            if game.get("bowl_locked_in", False):
                adjustment -= abs(self.ADJUSTMENTS["bowl_locked_in"])

            # Senior day/emotional games
            if game.get("senior_day", False):
                adjustment += 0.8

            # Conference Championship implications
            if game.get("conference_championship_implications", False):
                adjustment += 1.5

            # Coaching change (interim or final game)
            if game.get("coaching_change", False):
                adjustment += 1.0  # Players often play harder under new coach

            return adjustment

        except Exception as e:
            self.logger.warning(f"Error calculating emotional adjustment: {e}")
            return 0.0

    def get_conference_strength_adjustment(self, away_conf: str, home_conf: str) -> float:
        """
        Get conference strength relative adjustment.

        Different conferences have different average strength levels.
        This adjusts for playing in/against stronger conferences.

        Args:
            away_conf: Away team conference
            home_conf: Home team conference

        Returns:
            Adjustment in points
        """
        away_strength = self.CONFERENCE_STRENGTH.get(away_conf, -0.3)
        home_strength = self.CONFERENCE_STRENGTH.get(home_conf, -0.3)

        # Positive adjustment if away team is in stronger conference
        return away_strength - home_strength
