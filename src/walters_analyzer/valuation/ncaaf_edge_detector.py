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

from scrapers.weather import AccuWeatherClient
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

    def __init__(self, db_ops=None):
        """
        Initialize NCAAF edge detector

        Args:
            db_ops: Optional RawDataOperations instance for database queries
        """
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = self.project_root / "data" / "current"
        self.output_dir = self.project_root / "output" / "edge_detection"
        self.weather_client = AccuWeatherClient(
            api_key=os.getenv("ACCUWEATHER_API_KEY")
        )
        self.situational = NCAAFSituationalFactors()
        self.injury_calc = NCAAFInjuryImpacts()

        # Database operations (optional)
        self.db_ops = db_ops

        # Load comprehensive team name mappings
        self.team_name_map = self._load_team_mappings()

    async def get_player_value_for_injury(
        self, player_id: str, team_id: int, season: int, week: int, position: str
    ) -> float:
        """
        Get player value from database for injury impact calculation.
        Falls back to default NCAAF injury impact if not found.

        Args:
            player_id: Player ID
            team_id: Team ID
            season: Season year
            week: Week number
            position: Player position (fallback)

        Returns:
            Player point value (0.5-5.0)
        """
        if not self.db_ops or not player_id or not team_id:
            # Return default NCAAF injury impact for position
            default_impacts = {
                "QB": 5.0,  # NCAAF: Higher than NFL 4.5
                "RB": 2.0,
                "WR": 1.5,
                "TE": 1.2,
                "OL": 1.0,
                "DL": 1.5,
                "LB": 1.3,
                "DB": 1.2,
            }
            return default_impacts.get(position.upper(), 1.0)

        try:
            valuation = self.db_ops.get_player_valuation(
                league_id=2,  # NCAAF
                team_id=team_id,
                player_id=player_id,
                season=season,
                week=week,
            )
            if valuation:
                return float(valuation.point_value)
        except Exception:
            pass  # Silently fall back

        # Default for position
        default_impacts = {
            "QB": 5.0,
            "RB": 2.0,
            "WR": 1.5,
            "TE": 1.2,
            "OL": 1.0,
            "DL": 1.5,
            "LB": 1.3,
            "DB": 1.2,
        }
        return default_impacts.get(position.upper(), 1.0)

    async def check_wednesday_signal_ncaaf(
        self, team_id: int, team_name: str, season: int, week: int
    ) -> tuple[bool, float]:
        """
        Check Wednesday practice status for NCAAF team.

        Billy Walters: "Wednesday practice = Sunday play"
        For college: Check practice participation for key players.

        Args:
            team_id: Team ID
            team_name: Team name
            season: Season year
            week: Week number

        Returns:
            Tuple of (signal_detected, confidence_multiplier)
        """
        if not self.db_ops or not team_id:
            return (False, 1.0)

        try:
            wednesday_reports = self.db_ops.get_wednesday_practice_status(
                league_id=2,  # NCAAF
                team_id=team_id,
                season=season,
                week=week,
            )

            if not wednesday_reports:
                return (False, 1.0)

            fully_participating = sum(
                1
                for report in wednesday_reports
                if report.participation == "FP" and report.impact_rating >= 2.5
            )
            limited_participating = sum(
                1
                for report in wednesday_reports
                if report.participation == "LP" and report.impact_rating >= 2.0
            )
            did_not_participate = sum(
                1
                for report in wednesday_reports
                if report.participation == "DNP" and report.impact_rating >= 2.5
            )

            # Positive signal: Key players practicing
            if (
                fully_participating >= 2
                or (fully_participating + limited_participating) >= 3
            ):
                return (True, 1.15)  # +15% confidence

            # Negative signal: Key player didn't participate
            if did_not_participate >= 1:
                return (True, 0.95)  # -5% confidence

        except Exception:
            pass  # Silently fall back

        return (False, 1.0)

    async def get_game_swe_adjustments_ncaaf(
        self, game_id: str, season: int, week: int
    ) -> dict:
        """
        Get S-W-E (Special/Weather/Emotional) adjustments for NCAAF game.

        Args:
            game_id: Game identifier
            season: Season year
            week: Week number

        Returns:
            Dictionary with special, weather, emotional adjustments
        """
        if not self.db_ops:
            return {
                "special": 0.0,
                "weather": 0.0,
                "emotional": 0.0,
                "total": 0.0,
                "confidence_impact": 1.0,
            }

        try:
            swe_factors = self.db_ops.get_game_swe_factors(
                league_id=2,  # NCAAF
                game_id=game_id,
                season=season,
                week=week,
            )

            if swe_factors:
                return {
                    "special": swe_factors.special_adjustment or 0.0,
                    "weather": swe_factors.weather_adjustment or 0.0,
                    "emotional": swe_factors.emotional_adjustment or 0.0,
                    "total": swe_factors.total_adjustment or 0.0,
                    "confidence_impact": swe_factors.confidence_level or 1.0,
                }

        except Exception:
            pass  # Silently fall back

        return {
            "special": 0.0,
            "weather": 0.0,
            "emotional": 0.0,
            "total": 0.0,
            "confidence_impact": 1.0,
        }

    async def calculate_team_trend_adjustment_ncaaf(
        self, team_id: int, season: int, week: int
    ) -> float:
        """
        Calculate confidence adjustment based on NCAAF team trends.

        Args:
            team_id: Team ID
            season: Season year
            week: Week number

        Returns:
            Confidence multiplier (0.8-1.2)
        """
        if not self.db_ops or not team_id:
            return 1.0

        try:
            team_trends = self.db_ops.get_team_trends(
                league_id=2,  # NCAAF
                team_id=team_id,
                season=season,
                week=week,
            )

            if not team_trends:
                return 1.0

            confidence_adj = 1.0

            # Streak impact
            if team_trends.streak_length and team_trends.streak_length >= 2:
                if team_trends.streak_direction == "W":
                    confidence_adj += 0.05
                elif team_trends.streak_direction == "L":
                    confidence_adj -= 0.05

            # Desperation (playoff/bowl implications)
            if team_trends.desperation_level and team_trends.desperation_level >= 7:
                confidence_adj += 0.10

            # Revenge factor
            if team_trends.revenge_factor:
                confidence_adj += 0.05

            # Rest advantage
            if team_trends.rest_advantage and team_trends.rest_advantage >= 2:
                confidence_adj += 0.05

            return max(0.8, min(1.2, confidence_adj))

        except Exception:
            pass  # Silently fall back

        return 1.0

    def _load_team_mappings(self) -> Dict[str, str]:
        """
        Load comprehensive team name mappings from Overtime.ag to Massey format.

        Loads Overtime.ag -> Massey mappings and adds ESPN-specific overrides
        for teams that have different names in different systems.

        Returns:
            Dictionary mapping team names to Massey rating format
        """
        mappings = {}

        # Try to load from comprehensive mapping file first
        mapping_file = (
            self.project_root / "src" / "data" / "ncaaf_team_name_mapping.json"
        )

        if mapping_file.exists():
            try:
                with open(mapping_file, "r") as f:
                    data = json.load(f)
                    if "overtime_to_massey" in data:
                        mappings = data["overtime_to_massey"].copy()
                        logger.info(
                            f"[OK] Loaded {len(mappings)} "
                            "team mappings from comprehensive mapping file"
                        )
            except Exception as e:
                logger.warning(f"Error loading team mappings: {e}")

        # Add ESPN-specific overrides for teams with different display names
        # These handle special cases where ESPN uses different names than Overtime.ag
        espn_overrides = {
            "Ole Miss": "Mississippi",  # ESPN: "Ole Miss Rebels" -> Massey: "Mississippi"
            "Central Florida": "UCF",  # ESPN: "Central Florida Knights"
            "Miami Florida": "Miami FL",
            "Miami Ohio": "Miami OH",
        }

        # Merge ESPN overrides into mappings (ESPN names may not be in Overtime map)
        for espn_name, massey_name in espn_overrides.items():
            if espn_name not in mappings:
                mappings[espn_name] = massey_name

        if not mappings:
            # Fallback to basic ESPN -> Massey mappings if file not found
            logger.info("Using fallback team name mappings")
            mappings = {
                "Ohio State": "Ohio St",
                "Penn State": "Penn St",
                "Mississippi State": "Mississippi St",
                "Iowa State": "Iowa St",
                "Arizona State": "Arizona St",
                "Oklahoma State": "Oklahoma St",
                "Texas State": "Texas St",
                "San Jose State": "San Jose St",
                "North Carolina State": "NC State",
                "South Carolina State": "S.Carolina St",
                "Colorado State": "Colorado St",
                "Kansas State": "Kansas St",
                "Utah State": "Utah St",
                "Ball State": "Ball St",
                "Arkansas State": "Arkansas St",
                "Portland State": "Portland St",
                "Appalachian State": "App State",
                "New Mexico State": "New Mexico St",
                "South Dakota State": "South Dakota St",
                "Ole Miss": "Mississippi",
            }

        return mappings

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

            # Initialize weather client for weather adjustments
            try:
                await self.weather_client.connect()
            except Exception as e:
                logger.warning(
                    f"Weather client init failed (weather adjustments disabled): {e}"
                )

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
        finally:
            # Clean up weather client
            try:
                await self.weather_client.close()
            except Exception:
                pass  # Ignore cleanup errors

    async def _load_schedule(self, week: int) -> List[Dict]:
        """Load NCAAF schedule for given week"""
        try:
            schedule_file = self.data_dir / f"ncaaf_week_{week}_games.json"
            if schedule_file.exists():
                with open(schedule_file, "r") as f:
                    raw_games = json.load(f)

                # Normalize ESPN format to edge detector format
                normalized_games = []
                for game in raw_games:
                    # Extract game info from ESPN structure
                    game_id = game.get("id", "")
                    game_name = game.get("name", "")
                    short_name = game.get("shortName", "")

                    # Extract teams from competitions
                    comps = game.get("competitions", [])
                    if comps:
                        comp = comps[0]
                        competitors = comp.get("competitors", [])

                        # Find home and away teams
                        home_team = ""
                        away_team = ""
                        for competitor in competitors:
                            team_data = competitor.get("team", {})
                            # ESPN displayName has full team name with mascot
                            # (e.g., "Ohio State Buckeyes")
                            display_name = team_data.get("displayName", "")

                            # Normalize to Overtime.ag format for odds matching
                            # This strips mascots and applies special mappings
                            team_name = self._normalize_for_odds_matching(display_name)

                            if competitor.get("homeAway") == "home":
                                home_team = team_name
                            elif competitor.get("homeAway") == "away":
                                away_team = team_name

                        game_time = comp.get("date", "")

                        if home_team and away_team:
                            normalized_game = {
                                "game_id": game_id,
                                "away_team": away_team,
                                "home_team": home_team,
                                "matchup": f"{away_team} @ {home_team}",
                                "game_time": game_time,
                            }
                            normalized_games.append(normalized_game)

                logger.info(
                    f"[OK] Normalized {len(normalized_games)} games from ESPN schedule"
                )
                # DEBUG: Log first few normalized games
                for game in normalized_games[:3]:
                    logger.debug(
                        f"  Normalized game: {game['away_team']} @ {game['home_team']}"
                    )
                return normalized_games

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
                    # Handle Massey format: teams list with "team" and "powerRating" keys
                    ratings_dict = {}
                    for team in data["teams"]:
                        team_name = team.get("team") or team.get("name", "")
                        power_rating = team.get("powerRating") or team.get(
                            "rating", 75.0
                        )
                        if team_name:
                            try:
                                # Convert power rating to float if it's a string
                                if isinstance(power_rating, str):
                                    power_rating = float(power_rating)
                                ratings_dict[team_name] = power_rating
                            except (ValueError, TypeError):
                                ratings_dict[team_name] = 75.0
                    return ratings_dict
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

            odds_files = sorted(odds_dir.glob("ncaaf_odds_*.json"))
            if not odds_files:
                logger.warning("No odds files found")
                return {}

            latest_odds = odds_files[-1]
            logger.info(f"Loading odds from {latest_odds.name}")

            odds = {}
            with open(latest_odds, "r") as f:
                data = json.load(f)
                # NCAAF format: {"metadata": {...}, "games": [...]}
                if isinstance(data, dict) and "games" in data:
                    for game in data["games"]:
                        away_team = game.get("away_team", "")
                        home_team = game.get("home_team", "")

                        if away_team and home_team:
                            try:
                                # Normalize team names to Overnight.ag format for
                                # consistent key construction with _load_schedule()
                                norm_away = self._normalize_for_odds_matching(away_team)
                                norm_home = self._normalize_for_odds_matching(home_team)

                                # Normalize odds structure for edge detector
                                normalized_game = {
                                    "game_id": game.get("game_id", ""),
                                    "away_team": norm_away,
                                    "home_team": norm_home,
                                    "game_time": game.get("game_time", ""),
                                    # Handle nested spread structure
                                    "spread": game.get("spread", {}).get("home", 0.0),
                                    # Handle nested total structure
                                    "total": game.get("total", {}).get("points", 0.0),
                                }
                                # Key by normalized team matchup (same format as
                                # schedule for consistent matching)
                                matchup_key = f"{norm_away}_{norm_home}"
                                odds[matchup_key] = normalized_game
                            except Exception as e:
                                logger.debug(
                                    f"Error normalizing odds game "
                                    f"{away_team} @ {home_team}: {e}"
                                )
                elif isinstance(data, list):
                    # Handle JSONL-like format (list of games)
                    for game in data:
                        away_team = game.get("away_team", "")
                        home_team = game.get("home_team", "")
                        if away_team and home_team:
                            matchup_key = f"{away_team}_{home_team}"
                            odds[matchup_key] = game

            logger.info(f"[OK] Loaded {len(odds)} games from odds file")
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
            # NOTE: odds dict is keyed by "{normalized_away}_{normalized_home}"
            # from _load_odds, NOT by the ESPN game_id, so construct the key
            # from normalized team names
            odds_key = f"{away_team}_{home_team}"
            game_odds = odds.get(odds_key, {})
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

            # Apply TIER 1 database-driven adjustments (SWE factors)
            swe_adjustments = await self.get_game_swe_adjustments_ncaaf(
                game_id,
                2025,
                week,  # Using 2025 as default season
            )

            # Use database-driven adjustments if available, else use calculated ones
            if swe_adjustments["total"] != 0.0:
                situational_adj = swe_adjustments["special"] or situational_adj
                weather_adj = swe_adjustments["weather"] or weather_adj
                emotional_adj = swe_adjustments["emotional"] or emotional_adj

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

            # Apply SWE confidence impact
            confidence = min(confidence * swe_adjustments["confidence_impact"], 100.0)

            # Apply Wednesday signal confidence adjustment
            (
                away_wed_signal_detected,
                away_wed_multiplier,
            ) = await self.check_wednesday_signal_ncaaf(
                1,
                away_team,
                2025,
                week,  # team_id=1 is placeholder (would need actual ID)
            )
            (
                home_wed_signal_detected,
                home_wed_multiplier,
            ) = await self.check_wednesday_signal_ncaaf(
                1,
                home_team,
                2025,
                week,  # team_id=1 is placeholder
            )

            if recommended_bet == "away" and away_wed_signal_detected:
                confidence = min(confidence * away_wed_multiplier, 100.0)
            elif recommended_bet == "home" and home_wed_signal_detected:
                confidence = min(confidence * home_wed_multiplier, 100.0)

            # Apply team trend adjustments
            trend_adj_away = await self.calculate_team_trend_adjustment_ncaaf(
                1, 2025, week
            )
            trend_adj_home = await self.calculate_team_trend_adjustment_ncaaf(
                1, 2025, week
            )

            if recommended_bet == "away":
                confidence = min(confidence * trend_adj_away, 100.0)
            elif recommended_bet == "home":
                confidence = min(confidence * trend_adj_home, 100.0)

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

            # Get game time - prefer ISO format if available
            game_time = (
                game.get("game_datetime_utc")
                or game.get("game_datetime_et")
                or game.get("game_time", "")
            )

            # Get weather for game
            weather = await self.weather_client.get_game_weather(home_team, game_time)

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

    def _strip_mascot(self, team_name: str) -> str:
        """
        Strip ESPN mascot suffix from team name.

        Examples:
        - "Ohio State Buckeyes" -> "Ohio State"
        - "Georgia Bulldogs" -> "Georgia"
        - "Utah Utes" -> "Utah"
        """
        # Common NCAAF mascots (multi-word first for proper matching)
        mascots = [
            # Multi-word mascots (check these first - order matters!)
            "Crimson Tide",
            "Scarlet Knights",
            "Golden Eagles",
            "Golden Gophers",
            "Golden Bears",  # California
            "Golden Flashes",  # Kent State
            "Nittany Lions",
            "Yellow Jackets",
            "Demon Deacons",
            "Blue Devils",
            "Green Wave",
            "Tar Heels",
            "Fighting Illini",
            "Fighting Irish",  # Notre Dame
            "Sun Devils",
            "Red Raiders",  # Texas Tech
            # Single-word mascots
            "Wildcats",
            "Bulldogs",
            "Tide",
            "Tigers",
            "Gators",
            "Sooners",
            "Longhorns",
            "Cowboys",
            "Aggies",
            "Mavericks",
            "Commodores",
            "Vols",
            "Volunteers",
            "Rebels",
            "Razorbacks",
            "Gamecocks",
            "Jayhawks",
            "Utes",
            "Buffaloes",
            "Rams",
            "Broncos",
            "Falcons",
            "Panthers",
            "Hurricanes",
            "Orange",
            "Mountaineers",
            "Hokies",
            "Boilermakers",
            "Hoosiers",
            "Hawkeyes",
            "Badgers",
            "Spartans",
            "Wolverines",
            "Buckeyes",
            "Terrapins",
            "Bearcats",
            "Cardinals",
            "Cardinal",  # Stanford (singular)
            "Cavaliers",
            "49ers",
            "Knights",
            "Bears",
            "Cougars",  # BYU, Houston, Washington State
            "Ducks",  # Oregon
            "Huskies",  # Washington, UConn
            "Trojans",  # USC
            "Bruins",  # UCLA
            "Mustangs",  # SMU
            "Beavers",  # Oregon State
        ]

        for mascot in mascots:
            if team_name.endswith(f" {mascot}"):
                return team_name[: -len(mascot) - 1].strip()

        return team_name

    def _normalize_for_odds_matching(self, team_name: str) -> str:
        """
        Normalize team name to Overtime.ag format for odds matching.

        This converts ESPN display names to match Overtime.ag format:
        - Strip ESPN mascots first
        - Apply any special mappings for teams with unique names
        - Keep base team names (e.g., "Ohio State" not "Ohio St")

        Examples:
        - "Ohio State Buckeyes" -> "Ohio State"
        - "Ole Miss Rebels" -> "Ole Miss"
        - "San Jose State Spartans" -> "San Jose State"
        - "Kent State Golden Flashes" -> "Kent"
        - "Northern Illinois Huskies" -> "Northern Illinois"
        """
        # First strip the mascot
        stripped = self._strip_mascot(team_name)

        # Special case mappings for teams with unique Overtime.ag names
        # Maps ESPN names (after mascot stripping) to Overtime.ag names
        special_mappings = {
            # ESPN -> Overtime.ag format differences
            "Ole Miss": "Mississippi",  # Overtime uses full state name
            "UCF": "Central Florida",  # Overtime uses full name
            "Miami": "Miami Florida",  # Distinguish from Miami OH
            "Miami Hurricanes": "Miami Florida",  # If mascot not stripped
            # Standard mappings
            "Kent State": "Kent",
            "Northern Illinois": "Northern Illinois",
            "Central Michigan": "Central Michigan",
            "Western Michigan": "Western Michigan",
            "Eastern Michigan": "Eastern Michigan",
            "Ball State": "Ball State",
            "Miami (OH)": "Miami OH",
            "Miami (FL)": "Miami FL",
            "San Diego State": "San Diego State",
            "San Jose State": "San Jose State",
            "Florida Atlantic": "Florida Atlantic",
            "Florida International": "Florida International",
            "UL Monroe": "UL Monroe",
            "South Alabama": "South Alabama",
            "Arkansas State": "Arkansas State",
            "Texas State": "Texas State",
            "New Mexico State": "New Mexico State",
            "Louisiana Tech": "Louisiana Tech",
        }

        if stripped in special_mappings:
            return special_mappings[stripped]

        return stripped

    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize ESPN/Overtime.ag team name to Massey ratings format.

        Handles both ESPN names (with mascots) and Overtime.ag names:
        Examples:
        - "Ole Miss Rebels" (ESPN) -> "Ole Miss" -> "Mississippi"
        - "Mississippi" (Overtime.ag) -> "Mississippi"
        - "Ohio State Buckeyes" (ESPN) -> "Ohio State" -> "Ohio St"
        - "Ohio State" (Overtime.ag) -> "Ohio State" -> "Ohio St"
        """
        # First, try direct mapping (for Overtime.ag names already in map)
        if team_name in self.team_name_map:
            return self.team_name_map[team_name]

        # Strip mascot if present
        stripped = self._strip_mascot(team_name)

        # Try mapping again with stripped name
        if stripped != team_name and stripped in self.team_name_map:
            return self.team_name_map[stripped]

        # Default handling: abbreviated states
        if stripped.endswith(" State"):
            return stripped.replace(" State", " St")

        return stripped

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
