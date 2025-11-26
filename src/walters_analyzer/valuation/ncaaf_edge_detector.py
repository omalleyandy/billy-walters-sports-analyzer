#!/usr/bin/env python3
"""
NCAAF Edge Detection System
College football edge detection following Billy Walters methodology
with college-specific adjustments for power ratings, spreads, and situational factors.

Key Differences from NFL:
- Power ratings: 60-105 scale (vs NFL 70-100)
- Home field advantage: +3.5 pts (vs NFL +3.0)
- QB injury impact: 5.0 pts (vs NFL 4.5)
- Larger weather impacts (outdoor stadiums, regional severity)
- Conference dynamics and playoff implications
- Variable week numbering and game times (Thursday/Friday/Saturday)
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from data.accuweather_client import AccuWeatherClient
from walters_analyzer.valuation.ncaaf_situational_factors import (
    NCAAFSituationalFactors,
)
from walters_analyzer.valuation.ncaaf_injury_impacts import NCAAFInjuryImpacts

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class WeatherImpact:
    """Weather impact on NCAAF game"""

    temperature: Optional[float] = None  # Fahrenheit
    wind_speed: Optional[float] = None  # MPH
    precipitation: Optional[str] = None  # "rain", "snow", "none"
    indoor: bool = False
    total_adjustment: float = 0.0  # Points to subtract from total
    spread_adjustment: float = 0.0  # Favors defense/rushing teams


@dataclass
class BettingEdge:
    """Identified betting edge"""

    game_id: str
    matchup: str
    week: int
    game_time: str
    away_team: str
    home_team: str
    away_rating: float
    home_rating: float
    predicted_spread: float
    market_spread: float
    market_total: float
    best_odds: int = -110
    edge_points: float = 0.0
    edge_type: str = "power_rating"
    edge_strength: str = "weak"
    situational_adjustment: float = 0.0
    weather_adjustment: float = 0.0
    emotional_adjustment: float = 0.0
    injury_adjustment: float = 0.0
    recommended_bet: Optional[str] = None
    kelly_fraction: float = 0.0
    confidence_score: float = 0.0
    timestamp: str = ""
    data_sources: List[str] = None

    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = []


class NCAAFEdgeDetector:
    """College football edge detection system"""

    # NCAAF-specific thresholds and values
    NCAAF_POWER_RATING_MIN = 60
    NCAAF_POWER_RATING_MAX = 105
    HOME_FIELD_BONUS = 3.5  # vs NFL 3.0
    EDGE_THRESHOLD = 3.5
    MAX_KELLY = 0.25

    # Weather adjustments (NCAAF-specific, larger impacts than NFL)
    WIND_IMPACTS = {
        ">20mph": -6.0,  # vs NFL -5.0
        "15-20mph": -4.0,  # vs NFL -3.0
        "10-15mph": -2.0,  # vs NFL -1.0
    }

    TEMP_IMPACTS = {
        "<20F": -4.0,
        "20-25F": -3.0,
        "25-32F": -2.0,
        "32-40F": -1.0,
    }

    PRECIP_IMPACTS = {
        "snow_heavy": -5.0,
        "rain_heavy": -3.0,
        "drizzle": -0.5,
    }

    def __init__(self):
        """Initialize NCAAF edge detector"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = self.project_root / "data" / "current"
        self.output_dir = self.project_root / "output" / "edge_detection"
        self.weather_client = AccuWeatherClient(
            api_key=os.getenv("ACCUWEATHER_API_KEY")
        )
        self.situational = NCAAFSituationalFactors()
        self.injury_calc = NCAAFInjuryImpacts()

    async def detect_edges(self, week: int) -> List[BettingEdge]:
        """
        Detect all NCAAF edges for a given week.

        Args:
            week: NCAAF week number

        Returns:
            List of BettingEdge objects
        """
        try:
            logger.info(f"Detecting NCAAF edges for Week {week}...")

            # Load all required data
            games = await self._load_schedule(week)
            if not games:
                logger.error(f"No games found for NCAAF Week {week}")
                return []

            ratings = await self._load_power_ratings()
            odds = await self._load_odds(week)
            injuries = await self._load_injuries(week)

            logger.info(f"[OK] Loaded {len(games)} games for Week {week}")

            # Analyze each game
            edges = []
            for game in games:
                try:
                    edge = await self._analyze_game(game, ratings, odds, injuries, week)
                    if edge and edge.edge_points >= self.EDGE_THRESHOLD:
                        edges.append(edge)
                except Exception as e:
                    logger.warning(f"Error analyzing {game.get('matchup')}: {e}")
                    continue

            logger.info(
                f"[OK] Found {len(edges)} edges (threshold: {self.EDGE_THRESHOLD})"
            )

            # Save results
            if edges:
                await self._save_edges(edges, week)
                logger.info(f"[OK] Saved {len(edges)} edges to output file")

            return edges

        except Exception as e:
            logger.error(f"Error detecting NCAAF edges: {e}")
            raise

    async def _load_schedule(self, week: int) -> List[Dict]:
        """Load NCAAF schedule for given week"""
        try:
            schedule_file = self.data_dir / f"ncaaf_week_{week}_games.json"
            if schedule_file.exists():
                with open(schedule_file, "r") as f:
                    return json.load(f)

            logger.warning(
                f"Schedule file not found: {schedule_file}. "
                f"Please run data collection first."
            )
            return []
        except Exception as e:
            logger.error(f"Error loading NCAAF schedule: {e}")
            return []

    async def _load_power_ratings(self) -> Dict[str, float]:
        """Load NCAAF power ratings from Massey"""
        try:
            ratings_file = self.data_dir / "massey_ratings_ncaaf.json"
            if not ratings_file.exists():
                logger.warning(f"Ratings file not found: {ratings_file}")
                return {}

            with open(ratings_file, "r") as f:
                data = json.load(f)

            # Extract ratings (format varies, handle multiple structures)
            if isinstance(data, dict):
                if "ratings" in data:
                    return data["ratings"]
                elif "teams" in data:
                    return {
                        team["name"]: team.get("rating", 75.0) for team in data["teams"]
                    }
                else:
                    # Assume flat structure {team_name: rating, ...}
                    return {
                        k: v for k, v in data.items() if isinstance(v, (int, float))
                    }

            return {}
        except Exception as e:
            logger.error(f"Error loading power ratings: {e}")
            return {}

    async def _load_odds(self, week: int) -> Dict[str, Dict]:
        """Load NCAAF odds from Overtime.ag"""
        try:
            # Look for most recent odds file
            odds_dir = self.project_root / "output" / "overtime" / "ncaaf" / "pregame"
            if not odds_dir.exists():
                logger.warning(f"Odds directory not found: {odds_dir}")
                return {}

            odds_files = sorted(odds_dir.glob("api_walters_*.json"))
            if not odds_files:
                logger.warning("No odds files found")
                return {}

            latest_odds = odds_files[-1]
            logger.info(f"Loading odds from {latest_odds.name}")

            odds = {}
            with open(latest_odds, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        game = json.loads(line)
                        game_id = game.get("game_id", "")
                        if game_id:
                            odds[game_id] = game
                    except json.JSONDecodeError:
                        continue

            return odds
        except Exception as e:
            logger.error(f"Error loading odds: {e}")
            return {}

    async def _load_injuries(self, week: int) -> Dict[str, List[Dict]]:
        """Load NCAAF injury data from ESPN"""
        try:
            injuries_file = self.data_dir / f"ncaaf_week_{week}_injuries.json"
            if not injuries_file.exists():
                logger.info("No injuries file found (using empty injuries)")
                return {}

            with open(injuries_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading injuries: {e}")
            return {}

    async def _analyze_game(
        self,
        game: Dict,
        ratings: Dict[str, float],
        odds: Dict[str, Dict],
        injuries: Dict[str, List[Dict]],
        week: int,
    ) -> Optional[BettingEdge]:
        """Analyze single NCAAF game"""

        try:
            away_team = game.get("away_team", "")
            home_team = game.get("home_team", "")
            game_id = game.get("game_id", f"{away_team}_{home_team}")
            matchup = game.get("matchup", f"{away_team} @ {home_team}")
            game_time = game.get("game_time", datetime.utcnow().isoformat())

            # Get power ratings
            away_rating = ratings.get(away_team, 75.0)
            home_rating = ratings.get(home_team, 75.0)

            # Get market odds
            game_odds = odds.get(game_id, {})
            if not game_odds:
                logger.debug(f"No odds found for {matchup}")
                return None

            market_spread = game_odds.get("spread", 0.0)
            market_total = game_odds.get("total", 0.0)

            # Calculate power rating edge
            predicted_spread = await self._calculate_power_rating_edge(
                away_rating, home_rating
            )

            edge_points = abs(predicted_spread - market_spread)

            # Calculate adjustments
            situational_adj = await self.situational.calculate(game, ratings, week)
            weather_adj = await self._calculate_weather_adjustment(game)
            emotional_adj = await self.situational.emotional_adjustment(game, week)
            injury_adj = await self.injury_calc.calculate_impact(
                away_team, home_team, injuries
            )

            # Combined edge
            total_edge = (
                edge_points + situational_adj + weather_adj + emotional_adj + injury_adj
            )

            # Determine recommendation
            if total_edge < self.EDGE_THRESHOLD:
                return None

            recommended_bet = "away" if predicted_spread > market_spread else "home"
            kelly = min(abs(total_edge) / 20.0, self.MAX_KELLY)
            confidence = min(abs(total_edge) * 10.5, 100.0)

            # Determine edge strength
            edge_strength = self._classify_edge(abs(total_edge))

            return BettingEdge(
                game_id=game_id,
                matchup=matchup,
                week=week,
                game_time=game_time,
                away_team=away_team,
                home_team=home_team,
                away_rating=away_rating,
                home_rating=home_rating,
                predicted_spread=predicted_spread,
                market_spread=market_spread,
                market_total=market_total,
                best_odds=-110,
                edge_points=total_edge,
                edge_type="power_rating",
                edge_strength=edge_strength,
                situational_adjustment=situational_adj,
                weather_adjustment=weather_adj,
                emotional_adjustment=emotional_adj,
                injury_adjustment=injury_adj,
                recommended_bet=recommended_bet,
                kelly_fraction=kelly,
                confidence_score=confidence,
                timestamp=datetime.utcnow().isoformat(),
                data_sources=["massey", "action_network", "espn_injuries"],
            )

        except Exception as e:
            logger.warning(f"Error analyzing game {game.get('matchup')}: {e}")
            return None

    async def _calculate_power_rating_edge(
        self, away_rating: float, home_rating: float
    ) -> float:
        """
        Calculate predicted spread using power ratings.

        NCAAF formula:
        predicted_spread = away_rating - home_rating - home_field_bonus
        """
        predicted_spread = away_rating - home_rating - self.HOME_FIELD_BONUS
        return predicted_spread

    async def _calculate_weather_adjustment(self, game: Dict) -> float:
        """Calculate NCAAF-specific weather adjustment"""
        try:
            home_team = game.get("home_team", "")

            # Skip if indoor stadium
            if self._is_indoor_stadium(home_team):
                return 0.0

            # Get weather for game
            weather = await self.weather_client.get_game_weather(
                home_team, game.get("game_time", "")
            )

            if not weather or weather.get("temperature") is None:
                return 0.0

            adjustment = 0.0

            # Wind impact (NCAAF-specific, larger than NFL)
            wind_speed = weather.get("wind_speed", 0)
            if wind_speed > 20:
                adjustment -= 6.0
            elif wind_speed > 15:
                adjustment -= 4.0
            elif wind_speed > 10:
                adjustment -= 2.0

            # Temperature impact
            temp = weather.get("temperature", 65)
            if temp < 20:
                adjustment -= 4.0
            elif temp < 25:
                adjustment -= 3.0
            elif temp < 32:
                adjustment -= 2.0
            elif temp < 40:
                adjustment -= 1.0

            # Precipitation impact
            precip = weather.get("description", "").lower()
            if "snow" in precip and weather.get("precipitation_percent", 0) > 60:
                adjustment -= 5.0
            elif "rain" in precip and weather.get("precipitation_percent", 0) > 60:
                adjustment -= 3.0

            return adjustment

        except Exception as e:
            logger.debug(f"Error calculating weather adjustment: {e}")
            return 0.0

    def _is_indoor_stadium(self, team: str) -> bool:
        """Check if team plays in indoor stadium"""
        INDOOR_TEAMS = {
            "Duke",
            "Syracuse",
            "Miami",
            "San Jose State",
            "South Florida",
        }
        return any(indoor_team.lower() in team.lower() for indoor_team in INDOOR_TEAMS)

    def _classify_edge(self, edge_points: float) -> str:
        """Classify edge strength based on point differential"""
        if edge_points >= 7:
            return "very_strong"
        elif edge_points >= 5:
            return "strong"
        elif edge_points >= 3:
            return "medium"
        else:
            return "weak"

    async def _save_edges(self, edges: List[BettingEdge], week: int) -> None:
        """Save edges to JSONL file"""
        try:
            # Create output directory if needed
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Save to week-specific file
            output_file = self.output_dir / f"ncaaf_edges_detected_week_{week}.jsonl"

            with open(output_file, "w") as f:
                for edge in edges:
                    edge_dict = asdict(edge)
                    f.write(json.dumps(edge_dict) + "\n")

            logger.info(f"[OK] Saved edges to {output_file.name}")

            # Also save to generic file for backwards compatibility
            generic_file = self.output_dir / "ncaaf_edges_detected.jsonl"
            with open(generic_file, "w") as f:
                for edge in edges:
                    edge_dict = asdict(edge)
                    f.write(json.dumps(edge_dict) + "\n")

        except Exception as e:
            logger.error(f"Error saving edges: {e}")
            raise


async def main():
    """Run NCAAF edge detection for current week"""
    import argparse

    parser = argparse.ArgumentParser(description="NCAAF Edge Detection System")
    parser.add_argument(
        "--week", type=int, default=13, help="NCAAF week number (default: 13)"
    )
    args = parser.parse_args()

    detector = NCAAFEdgeDetector()
    edges = await detector.detect_edges(args.week)

    if edges:
        print(f"\n[OK] Generated {len(edges)} NCAAF edges for Week {args.week}")
        for edge in edges:
            print(
                f"  {edge.matchup}: {edge.edge_points:.1f} pts "
                f"({edge.edge_strength}) - {edge.recommended_bet}"
            )
    else:
        print(f"[WARNING] No edges found for Week {args.week}")


if __name__ == "__main__":
    asyncio.run(main())
