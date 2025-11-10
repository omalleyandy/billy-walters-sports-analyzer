#!/usr/bin/env python3
"""
Billy Walters Totals (Over/Under) Edge Detector

Implements Billy Walters' totals betting methodology using:
- Offensive/Defensive power ratings (from Massey)
- Weather adjustments (wind, temperature, precipitation)
- Injury impacts on scoring
- Key totals analysis (41, 43, 37, 44)
- 3.5-point minimum edge threshold
- Kelly Criterion position sizing

Only bet totals when you have a LOGICAL REASON - Billy Walters
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# Import shared components from edge detector
from .billy_walters_edge_detector import (
    PowerRating,
    WeatherImpact,
    SharpAction,
    InjuryImpact,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TotalsEdge:
    """Represents a totals (over/under) betting edge"""

    # Game identification
    game_id: str
    matchup: str
    week: int
    game_time: str

    # Teams
    away_team: str
    home_team: str

    # Offensive/Defensive ratings
    away_offensive_rating: float
    away_defensive_rating: float
    home_offensive_rating: float
    home_defensive_rating: float

    # Predicted vs Market
    predicted_total: float
    market_total: float
    best_over_odds: int
    best_under_odds: int

    # Edge calculation
    edge_points: float  # Difference between predicted and market
    edge_side: str  # "over" or "under"
    edge_strength: str  # "weak", "medium", "strong", "very_strong"

    # Adjustments
    weather_adjustment: float
    injury_adjustment: float  # Net effect on total

    # Sharp action
    sharp_action: SharpAction

    # Key numbers
    crosses_key_total: bool
    key_total_value: Optional[int]

    # Recommendation
    recommended_bet: Optional[str]  # "over", "under", None
    kelly_fraction: float  # 0-0.25
    confidence_score: float  # 0-100

    # Metadata
    timestamp: str
    data_sources: List[str]

    # Injury impacts (optional, with defaults at end)
    away_injuries: Optional[InjuryImpact] = None
    home_injuries: Optional[InjuryImpact] = None


class BillyWaltersTotalsDetector:
    """
    Detects totals (over/under) betting edges using Billy Walters methodology

    Key Principles:
    - Only bet totals with logical reasons (weather, pace, injuries)
    - Use offensive/defensive ratings to predict scoring
    - Apply 3.5-point minimum edge threshold
    - Key totals: 41, 43, 37, 44
    - Conservative Kelly Criterion sizing
    """

    # Constants
    MIN_EDGE_THRESHOLD = 3.5  # Minimum edge in points
    NFL_LEAGUE_AVERAGE_TOTAL = 44.0  # NFL average total points
    KEY_TOTALS = [41, 43, 37, 44]  # Most frequent NFL totals
    KEY_TOTAL_VALUE = 0.08  # 8% extra value crossing key total

    # Kelly Criterion
    MAX_KELLY_FRACTION = 0.25  # Conservative 25% max

    # Massey rating scale conversion
    MASSEY_BASELINE_OFF = 21.0  # Average offensive rating
    MASSEY_BASELINE_DEF = 6.0  # Average defensive rating
    MASSEY_OFF_TO_POINTS = 0.3  # Each Off rating point = 0.3 points/game
    MASSEY_DEF_TO_POINTS = 0.4  # Each Def rating point = 0.4 points allowed/game

    def __init__(self, output_dir: str = "output/edge_detection"):
        """Initialize totals edge detector"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Data caches
        self.power_ratings: Dict[str, PowerRating] = {}
        self.weather_data: Dict[str, WeatherImpact] = {}
        self.injury_data: Dict[str, List[Dict]] = {}

        logger.info("Billy Walters Totals Edge Detector initialized")

    def load_power_ratings(self, ratings: Dict[str, PowerRating]):
        """
        Load power ratings with offensive/defensive components

        Args:
            ratings: Dictionary of team -> PowerRating
        """
        self.power_ratings = ratings
        logger.info(
            f"Loaded {len(self.power_ratings)} power ratings for totals analysis"
        )

    def calculate_predicted_total(
        self,
        away_team: str,
        home_team: str,
        weather_adj: float = 0.0,
        injury_adj: float = 0.0,
    ) -> Tuple[float, float, float, float, float]:
        """
        Calculate predicted game total using offensive/defensive ratings

        Formula:
            Away Expected = (League Avg / 2) + (Away Off - Baseline Off) × Scale - (Home Def - Baseline Def) × Scale
            Home Expected = (League Avg / 2) + (Home Off - Baseline Off) × Scale - (Away Def - Baseline Def) × Scale
            Base Total = Away Expected + Home Expected
            Adjusted Total = Base + Weather Adj + Injury Adj

        Massey ratings are scaled to points using empirical conversion factors:
            - Offensive: 0.3 points per rating point above/below baseline (21.0)
            - Defensive: 0.4 points per rating point above/below baseline (6.0)

        Args:
            away_team: Away team name
            home_team: Home team name
            weather_adj: Weather adjustment (from weather client)
            injury_adj: Net injury impact on scoring

        Returns:
            (predicted_total, away_off, away_def, home_off, home_def)
        """
        away_rating = self.power_ratings.get(away_team)
        home_rating = self.power_ratings.get(home_team)

        if not away_rating or not home_rating:
            logger.warning(f"Missing ratings for {away_team} vs {home_team}")
            return (self.NFL_LEAGUE_AVERAGE_TOTAL, 0.0, 0.0, 0.0, 0.0)

        away_off = away_rating.offensive_rating
        away_def = away_rating.defensive_rating
        home_off = home_rating.offensive_rating
        home_def = home_rating.defensive_rating

        # Calculate expected scoring for each team
        # Massey ratings are relative to baseline (avg team)
        # Each team's score is influenced by their offense vs opponent's defense

        # Away team expected score
        away_off_adj = (away_off - self.MASSEY_BASELINE_OFF) * self.MASSEY_OFF_TO_POINTS
        home_def_adj = (home_def - self.MASSEY_BASELINE_DEF) * self.MASSEY_DEF_TO_POINTS
        away_expected = (
            (self.NFL_LEAGUE_AVERAGE_TOTAL / 2) + away_off_adj - home_def_adj
        )

        # Home team expected score
        home_off_adj = (home_off - self.MASSEY_BASELINE_OFF) * self.MASSEY_OFF_TO_POINTS
        away_def_adj = (away_def - self.MASSEY_BASELINE_DEF) * self.MASSEY_DEF_TO_POINTS
        home_expected = (
            (self.NFL_LEAGUE_AVERAGE_TOTAL / 2) + home_off_adj - away_def_adj
        )

        # Base total prediction
        base_total = away_expected + home_expected

        # Apply adjustments
        predicted_total = base_total + weather_adj + injury_adj

        logger.debug(
            f"{away_team} @ {home_team}: Away={away_expected:.1f}, Home={home_expected:.1f}, "
            f"Base={base_total:.1f}, Weather={weather_adj:+.1f}, Injury={injury_adj:+.1f}, "
            f"Predicted={predicted_total:.1f}"
        )

        return (predicted_total, away_off, away_def, home_off, home_def)

    def calculate_injury_impact_on_total(
        self, away_injuries: InjuryImpact, home_injuries: InjuryImpact
    ) -> float:
        """
        Calculate how injuries affect total scoring

        Different from spread impact:
        - Offensive injuries reduce BOTH teams' ability to score
        - Defensive injuries increase BOTH teams' ability to score
        - Net effect on total is the sum

        Args:
            away_injuries: Away team injury impact
            home_injuries: Home team injury impact

        Returns:
            Net adjustment to total (negative reduces total)
        """
        # Offensive injuries reduce scoring
        # Use the total_impact directly as it represents point impact
        # For totals, we care about total scoring reduction

        injury_adj = 0.0

        # Away team injuries affect away team's scoring
        # If away has offensive injuries, total goes down
        injury_adj -= away_injuries.total_impact

        # Home team injuries affect home team's scoring
        # If home has offensive injuries, total goes down
        injury_adj -= home_injuries.total_impact

        logger.debug(
            f"Injury impact on total: Away={-away_injuries.total_impact:.1f}, "
            f"Home={-home_injuries.total_impact:.1f}, Total={injury_adj:.1f}"
        )

        return injury_adj

    def check_key_total(self, total: float) -> Tuple[bool, Optional[int]]:
        """
        Check if total crosses a key number

        Key totals for NFL: 41, 43, 37, 44

        Args:
            total: Total points value

        Returns:
            (crosses_key, key_value)
        """
        for key in self.KEY_TOTALS:
            # Check if total is within 0.5 of key number
            if abs(total - key) <= 0.5:
                return (True, key)

        return (False, None)

    def calculate_kelly_fraction(self, edge_points: float, confidence: float) -> float:
        """
        Calculate Kelly Criterion bet sizing for totals

        Conservative approach: max 25% of bankroll

        Args:
            edge_points: Size of edge in points
            confidence: Confidence score 0-100

        Returns:
            Kelly fraction (0-0.25)
        """
        # Normalize edge to percentage
        edge_pct = edge_points / self.NFL_LEAGUE_AVERAGE_TOTAL

        # Adjust by confidence
        kelly = edge_pct * (confidence / 100.0)

        # Cap at conservative maximum
        kelly = min(kelly, self.MAX_KELLY_FRACTION)

        return round(kelly, 4)

    def detect_totals_edge(
        self,
        game_id: str,
        away_team: str,
        home_team: str,
        market_total: float,
        market_over_odds: int,
        market_under_odds: int,
        week: int,
        game_time: str,
        weather: Optional[WeatherImpact] = None,
        sharp_action: Optional[SharpAction] = None,
        away_injuries: Optional[InjuryImpact] = None,
        home_injuries: Optional[InjuryImpact] = None,
    ) -> Optional[TotalsEdge]:
        """
        Detect totals betting edge using Billy Walters methodology

        Args:
            game_id: Unique game identifier
            away_team: Away team name
            home_team: Home team name
            market_total: Market over/under line
            market_over_odds: Best available over odds
            market_under_odds: Best available under odds
            week: NFL week number
            game_time: Game start time (ISO format)
            weather: Weather impact data
            sharp_action: Sharp betting action
            away_injuries: Away team injury impact
            home_injuries: Home team injury impact

        Returns:
            TotalsEdge if edge >= 3.5 points, else None
        """
        # Calculate adjustments
        weather_adj = weather.total_adjustment if weather else 0.0

        # Calculate injury impact on total
        injury_adj = 0.0
        if away_injuries and home_injuries:
            injury_adj = self.calculate_injury_impact_on_total(
                away_injuries, home_injuries
            )

        # Calculate predicted total
        predicted_total, away_off, away_def, home_off, home_def = (
            self.calculate_predicted_total(
                away_team, home_team, weather_adj, injury_adj
            )
        )

        # Calculate edge
        edge_points = abs(predicted_total - market_total)
        edge_side = "over" if predicted_total > market_total else "under"

        # Check if edge meets threshold
        if edge_points < self.MIN_EDGE_THRESHOLD:
            return None

        # Classify edge strength
        if edge_points >= 7.0:
            edge_strength = "very_strong"
        elif edge_points >= 5.5:
            edge_strength = "strong"
        elif edge_points >= 4.5:
            edge_strength = "medium"
        else:
            edge_strength = "weak"

        # Check key totals
        crosses_key, key_value = self.check_key_total(market_total)

        # Calculate confidence score
        confidence = min(100.0, (edge_points / self.MIN_EDGE_THRESHOLD) * 100.0)

        # Boost confidence if crosses key total
        if crosses_key:
            confidence = min(100.0, confidence * (1 + self.KEY_TOTAL_VALUE))

        # Calculate Kelly fraction
        kelly = self.calculate_kelly_fraction(edge_points, confidence)

        # Recommendation
        recommended_bet = edge_side if edge_points >= self.MIN_EDGE_THRESHOLD else None

        logger.info(
            f"TOTALS EDGE DETECTED: {away_team} @ {home_team} - "
            f"Predicted: {predicted_total:.1f}, Market: {market_total:.1f}, "
            f"Edge: {edge_points:.1f} pts ({edge_side.upper()}), "
            f"Strength: {edge_strength.upper()}"
        )

        return TotalsEdge(
            game_id=game_id,
            matchup=f"{away_team} @ {home_team}",
            week=week,
            game_time=game_time,
            away_team=away_team,
            home_team=home_team,
            away_offensive_rating=away_off,
            away_defensive_rating=away_def,
            home_offensive_rating=home_off,
            home_defensive_rating=home_def,
            predicted_total=predicted_total,
            market_total=market_total,
            best_over_odds=market_over_odds,
            best_under_odds=market_under_odds,
            edge_points=edge_points,
            edge_side=edge_side,
            edge_strength=edge_strength,
            weather_adjustment=weather_adj,
            injury_adjustment=injury_adj,
            sharp_action=sharp_action or SharpAction(),
            crosses_key_total=crosses_key,
            key_total_value=key_value,
            recommended_bet=recommended_bet,
            kelly_fraction=kelly,
            confidence_score=confidence,
            timestamp=datetime.now().isoformat(),
            data_sources=[
                "massey_offensive_defensive",
                "action_network",
                "accuweather",
            ],
            away_injuries=away_injuries,
            home_injuries=home_injuries,
        )

    def save_totals_edges(
        self, edges: List[TotalsEdge], filename: str = "nfl_totals_detected.jsonl"
    ):
        """Save detected totals edges to JSONL file"""
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            for edge in edges:
                f.write(json.dumps(asdict(edge)) + "\n")

        logger.info(f"Saved {len(edges)} totals edges to {filepath}")

    def generate_totals_report(self, edges: List[TotalsEdge]) -> str:
        """Generate human-readable totals edge report"""
        report = []
        report.append("=" * 80)
        report.append("BILLY WALTERS TOTALS EDGE DETECTION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")

        if not edges:
            report.append(
                "No totals edges detected above minimum threshold (3.5 points)"
            )
            return "\n".join(report)

        # Sort by edge strength
        edges_sorted = sorted(edges, key=lambda e: e.edge_points, reverse=True)

        for i, edge in enumerate(edges_sorted, 1):
            report.append(f"{i}. {edge.matchup} (Week {edge.week})")
            report.append(f"   Time: {edge.game_time}")
            report.append(
                f"   Offensive: {edge.away_team} {edge.away_offensive_rating:.1f} | {edge.home_team} {edge.home_offensive_rating:.1f}"
            )
            report.append(
                f"   Defensive: {edge.away_team} {edge.away_defensive_rating:.1f} | {edge.home_team} {edge.home_defensive_rating:.1f}"
            )
            report.append(f"   Predicted Total: {edge.predicted_total:.1f}")
            report.append(f"   Market Total: {edge.market_total:.1f}")
            report.append(
                f"   EDGE: {edge.edge_points:.1f} points → BET {edge.edge_side.upper()} ({edge.edge_strength.upper()})"
            )
            report.append(
                f"   Kelly Sizing: {edge.kelly_fraction * 100:.1f}% of bankroll"
            )
            report.append(f"   Confidence: {edge.confidence_score:.0f}/100")

            if edge.weather_adjustment != 0:
                report.append(f"   Weather Adj: {edge.weather_adjustment:+.1f} pts")
            if edge.injury_adjustment != 0:
                report.append(f"   Injury Adj: {edge.injury_adjustment:+.1f} pts")
            if edge.crosses_key_total:
                report.append(f"   [KEY] Crosses key total: {edge.key_total_value}")

            report.append("")

        report.append("=" * 80)
        report.append(f"Total Edges Found: {len(edges)}")
        report.append(
            f"Strong/Very Strong: {sum(1 for e in edges if e.edge_strength in ['strong', 'very_strong'])}"
        )
        report.append(f"Over bets: {sum(1 for e in edges if e.edge_side == 'over')}")
        report.append(f"Under bets: {sum(1 for e in edges if e.edge_side == 'under')}")
        report.append("=" * 80)

        return "\n".join(report)


if __name__ == "__main__":
    logger.info("Billy Walters Totals Edge Detector - Standalone mode")
    logger.info(
        "This module is designed to be imported by the main edge detection system"
    )
    logger.info("Run billy_walters_edge_detector.py for complete analysis")
