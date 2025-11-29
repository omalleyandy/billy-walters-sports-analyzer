"""
Dynamic Adjustments Pipeline.

Real-time adjustments to edges based on:
1. Weather (temperature, wind, precipitation, humidity)
2. Injuries (key player availability, replacement level impact)
3. Situational (rest days, travel, rivalry, motivation)
4. Line movement (market implied probability changes)

These adjustments are applied AFTER edge detection but BEFORE final recommendations,
ensuring we capture late-breaking information.
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from walters_analyzer.valuation.ncaaf_edge_detector import BettingEdge

logger = logging.getLogger(__name__)


class AdjustmentType(str, Enum):
    """Types of dynamic adjustments."""

    WEATHER = "weather"
    INJURY = "injury"
    SITUATIONAL = "situational"
    LINE_MOVEMENT = "line_movement"


@dataclass
class WeatherAdjustment:
    """Weather-based adjustment to edge."""

    temperature: float  # Fahrenheit
    wind_mph: float  # Wind speed
    precipitation_pct: float  # Chance of precipitation 0-100
    humidity_pct: float  # Relative humidity
    adjustment: float = 0.0  # Points to adjust edge
    reasoning: str = ""

    def calculate_adjustment(self, is_outdoor: bool = True) -> float:
        """
        Calculate weather adjustment based on conditions.

        Billy Walters research:
        - Cold (< 20F): -1.0 to -2.0 pts (reduced scoring)
        - Wind (> 15 mph): -0.5 to -1.5 pts (kicking issues, pass game)
        - Precipitation: -0.5 pts (ball control, passing efficiency)
        """
        if not is_outdoor:
            return 0.0

        adjustment = 0.0
        reasons = []

        # Temperature adjustment
        if self.temperature < 20:
            temp_adj = (20 - self.temperature) * 0.05  # ~1pt per 20 degrees
            adjustment -= temp_adj
            reasons.append(f"Cold ({self.temperature}F): -{temp_adj:.1f}pt")
        elif self.temperature > 85:
            # Hot weather reduces scoring ability
            adjustment -= 0.3
            reasons.append(f"Hot ({self.temperature}F): -0.3pt")

        # Wind adjustment
        if self.wind_mph > 15:
            wind_adj = (self.wind_mph - 15) * 0.05  # ~0.5pt per 10mph
            adjustment -= wind_adj
            reasons.append(f"Wind ({self.wind_mph}mph): -{wind_adj:.1f}pt")

        # Precipitation adjustment
        if self.precipitation_pct > 50:
            rain_adj = (self.precipitation_pct - 50) * 0.01  # ~0.5pt at 100%
            adjustment -= rain_adj
            reasons.append(f"Rain ({self.precipitation_pct}%): -{rain_adj:.1f}pt")

        self.adjustment = adjustment
        self.reasoning = ", ".join(reasons) if reasons else "No adjustment"

        return adjustment


@dataclass
class InjuryAdjustment:
    """Injury-based adjustment to edge."""

    team: str
    away_or_home: str
    key_players_out: List[str] = field(default_factory=list)
    key_players_questionable: List[str] = field(default_factory=list)
    replacement_level_impact: float = 0.0  # Points of impact
    adjustment: float = 0.0
    reasoning: str = ""

    def calculate_adjustment(self) -> float:
        """
        Calculate injury adjustment.

        Billy Walters methodology:
        - QB out: -5.0 to -8.0 pts (most critical position)
        - RB1/WR1 out: -2.0 to -3.0 pts
        - OL/DL starter: -1.0 to -2.0 pts
        - Multiple injuries compound
        """
        adjustment = 0.0
        reasons = []

        # Key players out adjustments
        position_impact = {
            "QB": -6.0,
            "RB": -2.5,
            "WR": -2.0,
            "TE": -1.5,
            "OL": -1.0,
            "DL": -1.5,
            "LB": -0.5,
            "DB": -0.5,
        }

        for player_info in self.key_players_out:
            # Parse position from player info (e.g., "Patrick Mahomes (QB)")
            for pos, impact in position_impact.items():
                if pos in player_info.upper():
                    adjustment += impact
                    reasons.append(f"{pos} out: {impact:.1f}pt")
                    break

        # Questionable players (50% chance, so half impact)
        for player_info in self.key_players_questionable:
            for pos, impact in position_impact.items():
                if pos in player_info.upper():
                    half_impact = impact * 0.5
                    adjustment += half_impact
                    reasons.append(f"{pos} questionable: {half_impact:.1f}pt")
                    break

        # Direct replacement level impact
        if self.replacement_level_impact != 0:
            adjustment += self.replacement_level_impact
            reasons.append(f"Replacement impact: {self.replacement_level_impact:.1f}pt")

        # Determine if favors home or away
        if self.away_or_home.lower() == "away" and adjustment < 0:
            # Away team injuries hurt them (home team advantage)
            adjustment *= 1.2
            reasons.append("Away team injuries amplified")
        elif self.away_or_home.lower() == "home" and adjustment < 0:
            # Home team injuries help away team slightly
            adjustment *= 0.8
            reasons.append("Home team injuries slightly offset")

        self.adjustment = adjustment
        self.reasoning = ", ".join(reasons) if reasons else "No injuries"

        return adjustment


@dataclass
class SituationalAdjustment:
    """Situational factors adjustment to edge."""

    team: str
    rest_days: int  # Days since last game
    travel_distance_miles: Optional[int] = None
    altitude_change: Optional[int] = None  # Elevation difference in feet
    is_rivalry: bool = False
    is_playoff_implications: bool = False
    motivation: str = "neutral"  # "high", "neutral", "low"
    adjustment: float = 0.0
    reasoning: str = ""

    def calculate_adjustment(self) -> float:
        """
        Calculate situational adjustment.

        Billy Walters methodology:
        - Rest: +0.5pt per extra day (max +2.0)
        - Travel: -0.5pt per 1000 miles
        - Altitude (>5000 ft): -0.5pt to -1.0pt
        - Rivalry: +/- 1.0pt (increased emotion/motivation)
        - Playoff implications: +1.0pt (increased motivation)
        - Motivation: +/- 0.5pt
        """
        adjustment = 0.0
        reasons = []

        # Rest advantage
        # NFL teams play 7 days apart typically, so 7 days = neutral
        if self.rest_days < 7:
            rest_adj = -(7 - self.rest_days) * 0.25  # -0.25pt per day under 7
            adjustment += rest_adj
            reasons.append(f"Short rest ({self.rest_days}d): {rest_adj:.1f}pt")
        elif self.rest_days > 7:
            rest_adj = (self.rest_days - 7) * 0.25  # +0.25pt per extra day
            adjustment += rest_adj
            reasons.append(f"Extra rest ({self.rest_days}d): {rest_adj:.1f}pt")

        # Travel disadvantage
        if self.travel_distance_miles and self.travel_distance_miles > 0:
            # Teams traveling across country lose about 0.5pt per 1000 miles
            travel_adj = -(self.travel_distance_miles / 1000.0) * 0.5
            travel_adj = max(travel_adj, -2.0)  # Cap at -2.0pt
            adjustment += travel_adj
            reasons.append(
                f"Travel ({self.travel_distance_miles}mi): {travel_adj:.1f}pt"
            )

        # Altitude adjustment
        if self.altitude_change and self.altitude_change > 5000:
            # Significant altitude (Denver, Utah) affects passing and conditioning
            alt_adj = -0.5  # Denver is about -0.5 to -0.75pt
            adjustment += alt_adj
            reasons.append(f"High altitude ({self.altitude_change}ft): {alt_adj:.1f}pt")

        # Rivalry games
        if self.is_rivalry:
            # Rivalries tend to reduce spreads (emotional investment)
            adjustment -= 0.5
            reasons.append("Rivalry game: -0.5pt")

        # Playoff implications
        if self.is_playoff_implications:
            adjustment += 0.5
            reasons.append("Playoff implications: +0.5pt")

        # Motivation adjustment
        motivation_impact = {
            "high": 0.5,
            "neutral": 0.0,
            "low": -0.5,
        }
        mot_adj = motivation_impact.get(self.motivation.lower(), 0.0)
        if mot_adj != 0:
            adjustment += mot_adj
            reasons.append(f"Motivation ({self.motivation}): {mot_adj:+.1f}pt")

        self.adjustment = adjustment
        self.reasoning = ", ".join(reasons) if reasons else "No situational factors"

        return adjustment


@dataclass
class DynamicAdjustmentResult:
    """Result of applying dynamic adjustments to an edge."""

    original_edge: BettingEdge
    weather_adjustment: Optional[WeatherAdjustment] = None
    injury_adjustment: Optional[InjuryAdjustment] = None
    situational_adjustment: Optional[SituationalAdjustment] = None
    line_movement_adjustment: float = 0.0
    total_adjustment: float = 0.0
    adjusted_edge_points: float = field(default_factory=float)
    adjusted_confidence: float = field(default_factory=float)
    adjustment_reasons: List[str] = field(default_factory=list)

    def calculate_total(self) -> None:
        """Calculate total adjustments and apply to edge."""
        adjustments = []

        if self.weather_adjustment:
            adjustments.append(self.weather_adjustment.adjustment)
            self.adjustment_reasons.append(self.weather_adjustment.reasoning)

        if self.injury_adjustment:
            adjustments.append(self.injury_adjustment.adjustment)
            self.adjustment_reasons.append(self.injury_adjustment.reasoning)

        if self.situational_adjustment:
            adjustments.append(self.situational_adjustment.adjustment)
            self.adjustment_reasons.append(self.situational_adjustment.reasoning)

        if self.line_movement_adjustment != 0:
            adjustments.append(self.line_movement_adjustment)
            self.adjustment_reasons.append(
                f"Line movement: {self.line_movement_adjustment:+.1f}pt"
            )

        self.total_adjustment = sum(adjustments)
        self.adjusted_edge_points = (
            self.original_edge.edge_points + self.total_adjustment
        )

        # Confidence adjustment: larger adjustments reduce confidence
        confidence_impact = (
            abs(self.total_adjustment) * 5
        )  # 1pt adjustment = 5% confidence
        self.adjusted_confidence = max(
            0.0, self.original_edge.confidence_score - confidence_impact
        )


class DynamicAdjustmentEngine:
    """Applies dynamic adjustments to betting edges."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize engine."""
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.weather_dir = self.project_root / "output" / "weather"
        self.injuries_dir = self.project_root / "output" / "injuries"

    async def apply_adjustments(
        self,
        edge: BettingEdge,
        weather: Optional[Dict] = None,
        injuries: Optional[Dict] = None,
        situational: Optional[Dict] = None,
    ) -> DynamicAdjustmentResult:
        """
        Apply all available dynamic adjustments to an edge.

        Args:
            edge: The betting edge
            weather: Weather data dict
            injuries: Injury data dict
            situational: Situational factors dict

        Returns:
            DynamicAdjustmentResult with all adjustments applied
        """
        result = DynamicAdjustmentResult(original_edge=edge)

        # Apply weather adjustment
        if weather:
            weather_adj = WeatherAdjustment(
                temperature=weather.get("temperature", 70.0),
                wind_mph=weather.get("wind_mph", 0.0),
                precipitation_pct=weather.get("precipitation_pct", 0.0),
                humidity_pct=weather.get("humidity_pct", 50.0),
            )
            weather_adj.calculate_adjustment()
            result.weather_adjustment = weather_adj

        # Apply injury adjustment
        if injuries:
            away_team = edge.away_team
            home_team = edge.home_team

            # Check away team injuries
            away_injuries = injuries.get(away_team, {})
            if away_injuries:
                away_injury_adj = InjuryAdjustment(
                    team=away_team,
                    away_or_home="away",
                    key_players_out=away_injuries.get("out", []),
                    key_players_questionable=away_injuries.get("questionable", []),
                    replacement_level_impact=away_injuries.get("impact", 0.0),
                )
                away_injury_adj.calculate_adjustment()
                # Injuries to away team hurt them
                if away_injury_adj.adjustment < 0:
                    result.injury_adjustment = away_injury_adj

            # Check home team injuries
            home_injuries = injuries.get(home_team, {})
            if home_injuries:
                home_injury_adj = InjuryAdjustment(
                    team=home_team,
                    away_or_home="home",
                    key_players_out=home_injuries.get("out", []),
                    key_players_questionable=home_injuries.get("questionable", []),
                    replacement_level_impact=home_injuries.get("impact", 0.0),
                )
                home_injury_adj.calculate_adjustment()
                # Use whichever has bigger impact
                if not result.injury_adjustment or abs(
                    home_injury_adj.adjustment
                ) > abs(result.injury_adjustment.adjustment):
                    result.injury_adjustment = home_injury_adj

        # Apply situational adjustment
        if situational:
            sit_adj = SituationalAdjustment(
                team=situational.get("team", edge.away_team),
                rest_days=situational.get("rest_days", 7),
                travel_distance_miles=situational.get("travel_distance_miles"),
                altitude_change=situational.get("altitude_change"),
                is_rivalry=situational.get("is_rivalry", False),
                is_playoff_implications=situational.get(
                    "is_playoff_implications", False
                ),
                motivation=situational.get("motivation", "neutral"),
            )
            sit_adj.calculate_adjustment()
            result.situational_adjustment = sit_adj

        # Calculate totals
        result.calculate_total()

        return result


def main():
    """Example usage."""
    from walters_analyzer.valuation.ncaaf_edge_detector import BettingEdge

    edge = BettingEdge(
        game_id="401752788",
        matchup="Cold Team @ Warm Team",
        week=13,
        game_time="2025-12-14T18:00:00",
        away_team="Cold Team",
        home_team="Warm Team",
        away_rating=85.0,
        home_rating=90.0,
        predicted_spread=-5.0,
        market_spread=-5.0,
        market_total=48.5,
        edge_points=5.0,
        edge_strength="strong",
        recommended_bet="home",
        confidence_score=80.0,
    )

    engine = DynamicAdjustmentEngine()

    # Example adjustments
    weather = {
        "temperature": 15.0,  # Cold
        "wind_mph": 18.0,
        "precipitation_pct": 60.0,
        "humidity_pct": 45.0,
    }

    injuries = {
        "Cold Team": {
            "out": ["Patrick Mahomes (QB)"],
            "questionable": ["Travis Kelce (TE)"],
            "impact": -5.0,
        }
    }

    situational = {
        "team": "Cold Team",
        "rest_days": 5,
        "travel_distance_miles": 1200,
        "is_rivalry": False,
        "is_playoff_implications": True,
        "motivation": "high",
    }

    # Apply adjustments
    import asyncio

    result = asyncio.run(engine.apply_adjustments(edge, weather, injuries, situational))

    print(f"Original edge: {edge.edge_points:.1f}pt")
    print(f"Total adjustment: {result.total_adjustment:+.1f}pt")
    print(f"Adjusted edge: {result.adjusted_edge_points:.1f}pt")
    print(f"Original confidence: {edge.confidence_score:.1f}%")
    print(f"Adjusted confidence: {result.adjusted_confidence:.1f}%")
    print(f"\nReasons:")
    for reason in result.adjustment_reasons:
        print(f"  - {reason}")


if __name__ == "__main__":
    main()
