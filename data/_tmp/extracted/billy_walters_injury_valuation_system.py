"""
Billy Walters Advanced Player Valuation & Injury Impact System
Based on Billy Walters' methodology from his sports betting masterclass

This module provides specific player valuations and injury impact calculations
to replace generic responses with data-driven assessments.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class PlayerPosition(Enum):
    """Player positions with their base impact values"""

    # NFL Positions
    QB = "Quarterback"
    RB = "Running Back"
    WR = "Wide Receiver"
    TE = "Tight End"
    OL = "Offensive Line"
    DL = "Defensive Line"
    LB = "Linebacker"
    DB = "Defensive Back"
    K = "Kicker"
    P = "Punter"

    # NBA Positions
    PG = "Point Guard"
    SG = "Shooting Guard"
    SF = "Small Forward"
    PF = "Power Forward"
    C = "Center"


class InjuryType(Enum):
    """Injury types with severity multipliers"""

    CONCUSSION = "Concussion"
    HAMSTRING = "Hamstring"
    KNEE_SPRAIN = "Knee Sprain"
    ACL_TEAR = "ACL Tear"
    ANKLE_SPRAIN = "Ankle Sprain"
    SHOULDER = "Shoulder"
    BACK = "Back"
    GROIN = "Groin"
    QUADRICEPS = "Quadriceps"
    CALF = "Calf"
    ILLNESS = "Illness"
    REST = "Rest/Load Management"
    QUESTIONABLE = "Questionable"
    DOUBTFUL = "Doubtful"
    OUT = "Out"


@dataclass
class PlayerMetrics:
    """Core player performance metrics"""

    win_shares: float  # Player's contribution to team wins
    usage_rate: float  # Percentage of team plays involving player
    efficiency_rating: float  # Overall efficiency metric
    recent_form: float  # Last 5 games performance (0-1 scale)
    season_consistency: float  # Standard deviation of game scores
    clutch_factor: float  # Performance in close games/4th quarter


class BillyWaltersValuationSystem:
    """
    Billy Walters' Player Valuation System
    Based on his documented approach to quantifying player impact
    """

    # POSITION VALUE MULTIPLIERS (NFL)
    NFL_POSITION_VALUES = {
        PlayerPosition.QB: 3.5,  # QB has highest impact on point spread
        PlayerPosition.RB: 1.8,  # Elite RBs worth ~1.8 points
        PlayerPosition.WR: 1.2,  # #1 WR worth ~1.2 points
        PlayerPosition.TE: 0.8,  # Elite TE worth ~0.8 points
        PlayerPosition.OL: 0.6,  # Per starter on O-line
        PlayerPosition.DL: 0.9,  # Pass rushers have high value
        PlayerPosition.LB: 0.7,  # Middle linebacker impact
        PlayerPosition.DB: 0.8,  # Shutdown corner value
        PlayerPosition.K: 0.4,  # Kicker consistency matters
        PlayerPosition.P: 0.2,  # Punter least valuable
    }

    # POSITION VALUE MULTIPLIERS (NBA)
    NBA_POSITION_VALUES = {
        PlayerPosition.PG: 2.8,  # Primary ball handler/playmaker
        PlayerPosition.SG: 2.2,  # Scoring guards
        PlayerPosition.SF: 2.5,  # Two-way wings most valuable
        PlayerPosition.PF: 2.0,  # Modern stretch-4s
        PlayerPosition.C: 2.3,  # Rim protection + rebounding
    }

    # INJURY IMPACT FACTORS
    # Format: (immediate_impact, recovery_timeline_days, lingering_effect_multiplier)
    INJURY_IMPACTS = {
        InjuryType.CONCUSSION: (
            0.85,
            7,
            0.92,
        ),  # 85% if plays, 7 day recovery, 92% for 2 weeks after
        InjuryType.HAMSTRING: (0.75, 14, 0.88),  # Speed-dependent players more affected
        InjuryType.KNEE_SPRAIN: (0.70, 21, 0.85),  # Significant mobility impact
        InjuryType.ACL_TEAR: (0.0, 270, 0.75),  # Season-ending, long recovery
        InjuryType.ANKLE_SPRAIN: (0.80, 10, 0.90),  # Common, moderate impact
        InjuryType.SHOULDER: (0.78, 14, 0.88),  # Affects throwing/shooting
        InjuryType.BACK: (0.72, 21, 0.85),  # Chronic issue potential
        InjuryType.GROIN: (0.76, 14, 0.87),  # Affects lateral movement
        InjuryType.QUADRICEPS: (0.77, 10, 0.89),  # Power/explosion affected
        InjuryType.CALF: (0.79, 10, 0.91),  # Less severe typically
        InjuryType.ILLNESS: (0.88, 3, 0.95),  # Quick recovery usually
        InjuryType.REST: (1.0, 0, 1.0),  # No impact, strategic rest
        InjuryType.QUESTIONABLE: (0.92, 0, 0.98),  # 50% chance to play
        InjuryType.DOUBTFUL: (0.25, 0, 0.85),  # 25% chance to play
        InjuryType.OUT: (0.0, 0, 0.0),  # Confirmed out
    }

    @classmethod
    def calculate_player_value(
        cls, position: PlayerPosition, metrics: PlayerMetrics, is_nfl: bool = True
    ) -> float:
        """
        Calculate a player's point spread value using Billy Walters' formula

        Returns: Point spread impact (positive = helps team)
        """
        # Get base position value
        position_values = cls.NFL_POSITION_VALUES if is_nfl else cls.NBA_POSITION_VALUES
        base_value = position_values.get(position, 1.0)

        # Apply performance multipliers
        performance_multiplier = (
            (metrics.win_shares / 10.0)  # Normalize win shares
            * (metrics.usage_rate / 25.0)  # Normalize usage rate
            * (metrics.efficiency_rating / 100.0)  # Normalize efficiency
            * metrics.recent_form  # Already 0-1 scale
            * (2.0 - metrics.season_consistency)  # Consistency bonus
            * (1.0 + (metrics.clutch_factor * 0.3))  # Clutch bonus up to 30%
        )

        # Calculate final value in points
        player_value = base_value * performance_multiplier

        # Cap at realistic maximum (no player worth more than 7 points)
        return min(player_value, 7.0)

    @classmethod
    def calculate_injury_adjusted_value(
        cls,
        player_value: float,
        injury_type: Optional[InjuryType],
        days_since_injury: int = 0,
    ) -> Tuple[float, str]:
        """
        Adjust player value based on injury status

        Returns: (adjusted_value, explanation)
        """
        if not injury_type or injury_type == InjuryType.REST:
            return player_value, "Healthy - Full value"

        injury_data = cls.INJURY_IMPACTS[injury_type]
        immediate_impact, recovery_days, lingering_effect = injury_data

        if injury_type == InjuryType.OUT:
            return 0.0, f"Confirmed OUT - Line moves {player_value:.1f} points"

        # Calculate current impact based on recovery timeline
        if days_since_injury < recovery_days:
            # Still recovering
            recovery_progress = days_since_injury / recovery_days
            current_multiplier = (
                immediate_impact + (1.0 - immediate_impact) * recovery_progress
            )
            adjusted_value = player_value * current_multiplier

            explanation = (
                f"{injury_type.value}: {int(current_multiplier * 100)}% capacity "
                f"(Day {days_since_injury}/{recovery_days} recovery). "
                f"Value reduced from {player_value:.1f} to {adjusted_value:.1f} points"
            )
        else:
            # Post-recovery lingering effects
            weeks_post_recovery = (days_since_injury - recovery_days) / 7
            if weeks_post_recovery < 2:
                current_multiplier = lingering_effect + (1.0 - lingering_effect) * (
                    weeks_post_recovery / 2
                )
                adjusted_value = player_value * current_multiplier
                explanation = (
                    f"{injury_type.value}: Post-recovery phase at {int(current_multiplier * 100)}% capacity. "
                    f"Value: {adjusted_value:.1f} points (down from {player_value:.1f})"
                )
            else:
                adjusted_value = player_value
                explanation = "Fully recovered - Back to full value"

        return adjusted_value, explanation

    @classmethod
    def calculate_team_injury_impact(cls, injured_players: List[Dict]) -> Dict:
        """
        Calculate total team impact from injuries

        Args:
            injured_players: List of dicts with player info and injuries

        Returns: Comprehensive injury impact analysis
        """
        total_impact = 0.0
        critical_injuries = []
        moderate_injuries = []
        minor_injuries = []

        for player in injured_players:
            player_value = player.get("value", 1.0)
            injury_type = player.get("injury_type")
            days_since = player.get("days_since_injury", 0)

            adjusted_value, explanation = cls.calculate_injury_adjusted_value(
                player_value, injury_type, days_since
            )

            impact = player_value - adjusted_value
            total_impact += impact

            player_report = {
                "name": player.get("name"),
                "position": player.get("position"),
                "impact": impact,
                "explanation": explanation,
            }

            # Categorize by severity
            if impact >= 2.0:
                critical_injuries.append(player_report)
            elif impact >= 0.8:
                moderate_injuries.append(player_report)
            elif impact > 0:
                minor_injuries.append(player_report)

        # Generate strategic assessment
        if total_impact >= 7.0:
            assessment = (
                "SEVERE IMPACT: Line should move 7+ points. Strong fade candidate."
            )
            confidence = "HIGH"
        elif total_impact >= 4.0:
            assessment = (
                "MAJOR IMPACT: Line should move 4-7 points. Clear disadvantage."
            )
            confidence = "HIGH"
        elif total_impact >= 2.0:
            assessment = (
                "MODERATE IMPACT: Line should move 2-4 points. Notable disadvantage."
            )
            confidence = "MEDIUM"
        elif total_impact >= 1.0:
            assessment = (
                "MINOR IMPACT: Line should move 1-2 points. Slight disadvantage."
            )
            confidence = "MEDIUM"
        else:
            assessment = (
                "MINIMAL IMPACT: Line movement under 1 point. Negligible effect."
            )
            confidence = "LOW"

        return {
            "total_impact_points": round(total_impact, 1),
            "assessment": assessment,
            "confidence": confidence,
            "critical_injuries": critical_injuries,
            "moderate_injuries": moderate_injuries,
            "minor_injuries": minor_injuries,
            "recommended_line_adjustment": round(
                total_impact * 0.85, 1
            ),  # Market typically underreacts by 15%
            "betting_recommendation": cls._generate_betting_recommendation(
                total_impact
            ),
        }

    @staticmethod
    def _generate_betting_recommendation(total_impact: float) -> str:
        """Generate specific betting recommendation based on injury impact"""
        if total_impact >= 5.0:
            return "STRONG PLAY: Bet against injured team. Market unlikely to fully adjust."
        elif total_impact >= 3.0:
            return (
                "MODERATE PLAY: Consider fading injured team if line moves < 3 points."
            )
        elif total_impact >= 1.5:
            return (
                "SELECTIVE PLAY: Only bet if you have additional edges beyond injuries."
            )
        else:
            return "NO PLAY: Injury impact too small for standalone bet."


class InjuryDataValidator:
    """Validate and enhance scraped injury data with Billy Walters' methodology"""

    @staticmethod
    def parse_injury_report(raw_text: str) -> InjuryType:
        """Convert scraped injury text to typed injury"""
        text_lower = raw_text.lower()

        # Map common injury report terms
        injury_mappings = {
            "concussion": InjuryType.CONCUSSION,
            "hamstring": InjuryType.HAMSTRING,
            "knee": InjuryType.KNEE_SPRAIN,
            "acl": InjuryType.ACL_TEAR,
            "ankle": InjuryType.ANKLE_SPRAIN,
            "shoulder": InjuryType.SHOULDER,
            "back": InjuryType.BACK,
            "groin": InjuryType.GROIN,
            "quad": InjuryType.QUADRICEPS,
            "calf": InjuryType.CALF,
            "illness": InjuryType.ILLNESS,
            "rest": InjuryType.REST,
            "questionable": InjuryType.QUESTIONABLE,
            "doubtful": InjuryType.DOUBTFUL,
            "out": InjuryType.OUT,
        }

        for keyword, injury_type in injury_mappings.items():
            if keyword in text_lower:
                return injury_type

        # Default to questionable if unclear
        return InjuryType.QUESTIONABLE

    @staticmethod
    def estimate_player_value_from_stats(stats: Dict) -> float:
        """
        Estimate player value from available statistics
        Uses Billy Walters' approach of multiple metrics
        """
        # Extract key stats (adjust based on your scraped data structure)
        points_per_game = stats.get("ppg", 0)
        usage_rate = stats.get("usage", 20)
        plus_minus = stats.get("plus_minus", 0)
        games_played = stats.get("games", 0)

        # Simple formula to estimate impact
        # This should be calibrated with your actual data
        base_value = (points_per_game / 10) * (usage_rate / 25)
        consistency_bonus = min(games_played / 20, 1.0)  # Reward availability
        efficiency_bonus = max(plus_minus / 10, -0.5)  # Plus/minus impact

        estimated_value = base_value * (1 + consistency_bonus) * (1 + efficiency_bonus)

        return min(estimated_value, 7.0)  # Cap at 7 points max


# Example usage function
def analyze_game_injuries(home_injuries: List[Dict], away_injuries: List[Dict]) -> Dict:
    """
    Comprehensive injury analysis for a specific game

    Args:
        home_injuries: List of injured players for home team
        away_injuries: List of injured players for away team

    Returns: Complete game injury analysis with betting implications
    """
    valuation_system = BillyWaltersValuationSystem()

    # Analyze each team
    home_analysis = valuation_system.calculate_team_injury_impact(home_injuries)
    away_analysis = valuation_system.calculate_team_injury_impact(away_injuries)

    # Calculate net impact
    net_impact = (
        away_analysis["total_impact_points"] - home_analysis["total_impact_points"]
    )

    # Generate game-specific recommendation
    if abs(net_impact) >= 3.0:
        if net_impact > 0:
            game_rec = f"STRONG PLAY: Home team advantage of {abs(net_impact):.1f} points due to injuries"
        else:
            game_rec = f"STRONG PLAY: Away team advantage of {abs(net_impact):.1f} points due to injuries"
    elif abs(net_impact) >= 1.5:
        if net_impact > 0:
            game_rec = f"LEAN HOME: {abs(net_impact):.1f} point injury advantage"
        else:
            game_rec = f"LEAN AWAY: {abs(net_impact):.1f} point injury advantage"
    else:
        game_rec = "NO EDGE: Injuries relatively balanced"

    return {
        "home_team_analysis": home_analysis,
        "away_team_analysis": away_analysis,
        "net_injury_impact": round(net_impact, 1),
        "game_recommendation": game_rec,
        "suggested_line_move": round(
            net_impact * 0.85, 1
        ),  # Market underreaction factor
        "confidence_level": "HIGH"
        if abs(net_impact) >= 3.0
        else "MEDIUM"
        if abs(net_impact) >= 1.5
        else "LOW",
    }


if __name__ == "__main__":
    # Example: Analyzing a game with specific injuries

    # Home team injuries
    home_injuries = [
        {
            "name": "Star Quarterback",
            "position": PlayerPosition.QB,
            "value": 3.5,  # Elite QB worth 3.5 points
            "injury_type": InjuryType.ANKLE_SPRAIN,
            "days_since_injury": 5,
        },
        {
            "name": "Starting Center",
            "position": PlayerPosition.OL,
            "value": 0.6,
            "injury_type": InjuryType.KNEE_SPRAIN,
            "days_since_injury": 3,
        },
    ]

    # Away team injuries
    away_injuries = [
        {
            "name": "Top Wide Receiver",
            "position": PlayerPosition.WR,
            "value": 1.2,
            "injury_type": InjuryType.OUT,
            "days_since_injury": 0,
        }
    ]

    # Run analysis
    game_analysis = analyze_game_injuries(home_injuries, away_injuries)

    # Print results
    print("=" * 60)
    print("BILLY WALTERS INJURY IMPACT ANALYSIS")
    print("=" * 60)
    print(
        f"\nHome Team Impact: -{game_analysis['home_team_analysis']['total_impact_points']} points"
    )
    print(
        f"Away Team Impact: -{game_analysis['away_team_analysis']['total_impact_points']} points"
    )
    print(f"\nNet Impact: {game_analysis['net_injury_impact']} points")
    print(f"Recommendation: {game_analysis['game_recommendation']}")
    print(f"Suggested Line Move: {game_analysis['suggested_line_move']} points")
    print(f"Confidence: {game_analysis['confidence_level']}")
