#!/usr/bin/env python3
"""
Edge Detection Pipeline

Integrates:
1. Massey power ratings (scraped fresh or loaded from cache)
2. Billy Walters 90/10 smoothing formula
3. Action Network sharp money signals
4. Key number analysis
5. S-factor adjustments

Usage:
    # Full pipeline for NFL Week 13
    python -m walters_analyzer.pipelines.edge_detection_pipeline --sport nfl --week 13

    # NCAAF with fresh scrape
    python -m walters_analyzer.pipelines.edge_detection_pipeline --sport ncaaf --week 14 --scrape

    # Analyze specific game
    python -m walters_analyzer.pipelines.edge_detection_pipeline --sport nfl --matchup "GB@DET"
"""

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

from walters_analyzer.core.power_ratings_engine import PowerRatingsEngine
from walters_analyzer.core.integrated_edge_calculator import (
    IntegratedEdgeCalculator,
    IntegratedEdgeAnalysis,
)
from walters_analyzer.season_calendar import (
    get_nfl_week,
    get_ncaaf_week,
    get_nfl_season_phase,
    get_ncaaf_season_phase,
    SeasonPhase,
    League,
    format_season_status,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for edge detection pipeline."""

    sport: str  # "nfl" or "ncaaf"
    week: int
    season: int = 2025
    scrape_fresh: bool = False  # Whether to scrape new Massey data
    scrape_odds: bool = False  # Whether to scrape fresh Overtime odds
    min_edge: float = 5.5  # Minimum edge to report
    home_field_advantage: float = 2.5  # NFL HFA (NCAAF varies)
    use_power_rating: bool = True  # Use Pwr column vs Rat
    action_network_path: Optional[Path] = None


@dataclass
class EdgeDetectionResult:
    """Results from edge detection pipeline."""

    sport: str
    week: int
    season: int
    timestamp: datetime
    teams_analyzed: int
    games_analyzed: int
    edges_found: int
    best_bets: List[IntegratedEdgeAnalysis]
    all_edges: List[IntegratedEdgeAnalysis]
    power_ratings: Dict[str, float]
    warnings: List[str]


class EdgeDetectionPipeline:
    """
    Complete edge detection pipeline.

    Orchestrates:
    1. Massey ratings collection
    2. 90/10 formula application
    3. Edge calculation vs market
    4. Bet recommendations

    Example:
        >>> pipeline = EdgeDetectionPipeline()
        >>> result = await pipeline.run(PipelineConfig(sport="nfl", week=13))
        >>> for bet in result.best_bets:
        ...     print(f"{bet.game}: {bet.adjusted_edge_pct:.1f}% edge")
    """

    def __init__(self):
        self._project_root = Path(__file__).parent.parent.parent.parent
        self._data_dir = self._project_root / "src" / "data"
        self._output_dir = self._project_root / "src" / "output"

    async def run(self, config: PipelineConfig) -> EdgeDetectionResult:
        """
        Run the complete edge detection pipeline.

        Args:
            config: Pipeline configuration

        Returns:
            EdgeDetectionResult with all findings
        """
        warnings = []
        logger.info("=" * 70)
        logger.info(f"EDGE DETECTION PIPELINE - {config.sport.upper()} Week {config.week}")
        logger.info("=" * 70)

        # Step 1: Get power ratings
        logger.info("\n[INFO] Step 1: Loading Power Ratings...")
        power_ratings = await self._get_power_ratings(config)

        if not power_ratings:
            warnings.append("No power ratings available")
            logger.error("[ERROR] No power ratings found")
            return EdgeDetectionResult(
                sport=config.sport,
                week=config.week,
                season=config.season,
                timestamp=datetime.now(),
                teams_analyzed=0,
                games_analyzed=0,
                edges_found=0,
                best_bets=[],
                all_edges=[],
                power_ratings={},
                warnings=warnings,
            )

        logger.info(f"[OK] Loaded {len(power_ratings)} team ratings")

        # Step 2: Load market data (Action Network or Overtime)
        logger.info("\n[INFO] Step 2: Loading Market Data...")

        # Scrape fresh odds if requested
        if config.scrape_odds:
            await self._scrape_overtime_odds(config)

        calculator = IntegratedEdgeCalculator()
        games_loaded = self._load_market_data(calculator, config)

        if games_loaded == 0:
            warnings.append("No market data available - edge calculation limited")
            logger.warning("[WARNING] No market data found")

        # Step 3: Calculate edges for all games
        logger.info("\n[INFO] Step 3: Calculating Edges...")
        all_edges = calculator.analyze_all_games(
            power_ratings=power_ratings,
            home_advantage=config.home_field_advantage,
            min_edge=0,  # Get all, filter later
        )

        # Filter to actionable edges
        actionable_edges = [e for e in all_edges if e.adjusted_edge_pct >= config.min_edge]

        # Best bets (>= 1 star)
        best_bets = [e for e in actionable_edges if e.star_rating >= 1.0]

        logger.info(f"[OK] Found {len(actionable_edges)} edges >= {config.min_edge}%")
        logger.info(f"[OK] {len(best_bets)} rated 1+ stars")

        # Step 4: Generate results
        result = EdgeDetectionResult(
            sport=config.sport,
            week=config.week,
            season=config.season,
            timestamp=datetime.now(),
            teams_analyzed=len(power_ratings),
            games_analyzed=games_loaded,
            edges_found=len(actionable_edges),
            best_bets=best_bets,
            all_edges=actionable_edges,
            power_ratings=power_ratings,
            warnings=warnings,
        )

        # Step 5: Save results
        self._save_results(result, config)

        return result

    async def _get_power_ratings(self, config: PipelineConfig) -> Dict[str, float]:
        """Get power ratings (scrape fresh or load cached)."""
        from scrapers.massey.ratings_scraper import MasseyRatingsScraper

        scraper = MasseyRatingsScraper()
        raw_ratings = {}

        if config.scrape_fresh:
            logger.info("[INFO] Scraping fresh ratings from Massey...")
            if config.sport.lower() == "nfl":
                data = await scraper.scrape_nfl_ratings(save=True)
            else:
                data = await scraper.scrape_ncaaf_ratings(save=True)

            # Apply 90/10 formula
            engine = PowerRatingsEngine()
            updates = engine.update_ratings(
                sport=config.sport.upper(),
                week=config.week,
                season=config.season,
                new_ratings=data.to_power_ratings_dict(use_power_rating=config.use_power_rating),
                source="massey",
            )

            # Save smoothed ratings
            engine.save_ratings(
                updates=updates,
                sport=config.sport.upper(),
                week=config.week,
                season=config.season,
            )

            raw_ratings = {u.team: u.new_rating for u in updates}

        else:
            # Try to load cached ratings
            logger.info("[INFO] Loading cached ratings...")

            # First try latest Massey scrape
            data = scraper.load_latest_ratings(config.sport)
            if data:
                raw_ratings = data.to_power_ratings_dict(use_power_rating=config.use_power_rating)
            else:
                # Fall back to saved power ratings
                ratings_path = (
                    self._data_dir
                    / "power_ratings"
                    / f"{config.sport.lower()}_{config.season}_week_{config.week:02d}.json"
                )
                if ratings_path.exists():
                    with open(ratings_path) as f:
                        saved = json.load(f)
                    raw_ratings = saved.get("ratings", {})
                else:
                    logger.warning("No cached ratings found - will scrape fresh")
                    return await self._get_power_ratings(
                        PipelineConfig(
                            sport=config.sport,
                            week=config.week,
                            season=config.season,
                            scrape_fresh=True,
                            min_edge=config.min_edge,
                            home_field_advantage=config.home_field_advantage,
                            use_power_rating=config.use_power_rating,
                        )
                    )

        # Convert Massey team names to abbreviations for matching with odds data
        abbrev_mapping = self._get_massey_to_abbrev_mapping(config.sport)
        converted_ratings = {}

        for team, rating in raw_ratings.items():
            abbrev = abbrev_mapping.get(team)
            if abbrev:
                converted_ratings[abbrev] = rating
            else:
                # Keep original if no mapping (for debugging)
                converted_ratings[team] = rating
                logger.debug(f"No abbreviation mapping for: {team}")

        return converted_ratings

    def _load_market_data(
        self, calculator: IntegratedEdgeCalculator, config: PipelineConfig
    ) -> int:
        """Load market data from Action Network or Overtime.ag."""
        # Try Action Network first
        action_network_paths = [
            config.action_network_path,
            self._output_dir / "action_network" / f"week{config.week}_{config.sport}_odds.json",
            self._output_dir / "action_network" / f"{config.sport}_odds_latest.json",
            self._data_dir / "action_network" / f"week{config.week}_{config.sport}_odds.json",
            self._data_dir / "action_network" / f"{config.sport}_odds_latest.json",
        ]

        for path in action_network_paths:
            if path and Path(path).exists():
                count = calculator.load_action_network_data(path)
                if count > 0:
                    logger.info(f"Loaded {count} games from Action Network")
                    return count

        # Fall back to Overtime.ag data
        overtime_paths = [
            self._output_dir / "overtime" / config.sport.lower() / "pregame",
            self._data_dir / "overtime" / config.sport.lower() / "pregame",
        ]

        for base_path in overtime_paths:
            if base_path.exists():
                # Find most recent odds file (try multiple naming patterns)
                sport_lower = config.sport.lower()
                patterns = [
                    f"{sport_lower}_odds_*.json",  # New format: nfl_odds_20251130_123456.json
                    "api_walters_*.json",          # Legacy format
                ]
                
                for pattern in patterns:
                    odds_files = sorted(base_path.glob(pattern), reverse=True)
                    if odds_files:
                        count = self._load_overtime_data(calculator, odds_files[0], config.sport)
                        if count > 0:
                            logger.info(f"Loaded {count} games from Overtime.ag ({odds_files[0].name})")
                            return count

        return 0

    async def _scrape_overtime_odds(self, config: PipelineConfig) -> int:
        """Scrape fresh odds from Overtime.ag API."""
        from src.data.overtime_api_client import OvertimeApiClient

        logger.info("[INFO] Scraping fresh odds from Overtime.ag...")
        client = OvertimeApiClient(
            output_dir=self._output_dir / "overtime"
        )

        if config.sport.lower() == "nfl":
            data = await client.scrape_nfl(save_raw=True, save_converted=True)
        else:
            data = await client.scrape_ncaaf(save_raw=True, save_converted=True)

        games_count = data.get("summary", {}).get("total_games", 0)
        logger.info(f"[OK] Scraped {games_count} games from Overtime.ag")
        return games_count

    def _load_overtime_data(
        self, calculator: IntegratedEdgeCalculator, filepath: Path, sport: str
    ) -> int:
        """
        Load Overtime.ag data and convert to IntegratedEdgeCalculator format.

        The Overtime format has:
        - home_team, away_team (full names)
        - spread.home, spread.away (point spreads)
        - moneyline.home, moneyline.away
        - total.points

        We need to convert to the game_odds format:
        - Keyed by "AWAY@HOME" with team abbreviations
        - Spread data with value and betting percentages
        """
        with open(filepath) as f:
            data = json.load(f)

        # Team name to abbreviation mapping
        team_abbrevs = self._get_team_abbreviations(sport)

        games_loaded = 0
        for game in data.get("games", []):
            away_team = game.get("away_team", "")
            home_team = game.get("home_team", "")

            # Convert to abbreviations
            away_abbrev = team_abbrevs.get(away_team, away_team[:3].upper())
            home_abbrev = team_abbrevs.get(home_team, home_team[:3].upper())

            key = f"{away_abbrev}@{home_abbrev}"

            spread_data = game.get("spread", {})
            home_spread = spread_data.get("home")

            if home_spread is not None:
                # Build Action Network-compatible structure
                game_odds = {
                    "away_team": away_abbrev,
                    "home_team": home_abbrev,
                    "spread": {
                        "home": {
                            "value": home_spread,
                            "tickets_pct": None,  # Overtime doesn't have betting percentages
                            "money_pct": None,
                        },
                        "away": {
                            "value": spread_data.get("away"),
                            "tickets_pct": None,
                            "money_pct": None,
                        },
                    },
                    "moneyline": game.get("moneyline", {}),
                    "total": game.get("total", {}),
                    "game_time": game.get("game_time"),
                }

                calculator.game_odds[key] = game_odds
                games_loaded += 1

        return games_loaded

    def _get_team_abbreviations(self, sport: str) -> Dict[str, str]:
        """Get team name to abbreviation mapping."""
        if sport.lower() == "nfl":
            return {
                # AFC East
                "Buffalo Bills": "BUF",
                "Miami Dolphins": "MIA",
                "New England Patriots": "NE",
                "New York Jets": "NYJ",
                # AFC North
                "Baltimore Ravens": "BAL",
                "Cincinnati Bengals": "CIN",
                "Cleveland Browns": "CLE",
                "Pittsburgh Steelers": "PIT",
                # AFC South
                "Houston Texans": "HOU",
                "Indianapolis Colts": "IND",
                "Jacksonville Jaguars": "JAX",
                "Tennessee Titans": "TEN",
                # AFC West
                "Denver Broncos": "DEN",
                "Kansas City Chiefs": "KC",
                "Las Vegas Raiders": "LV",
                "Los Angeles Chargers": "LAC",
                # NFC East
                "Dallas Cowboys": "DAL",
                "New York Giants": "NYG",
                "Philadelphia Eagles": "PHI",
                "Washington Commanders": "WAS",
                # NFC North
                "Chicago Bears": "CHI",
                "Detroit Lions": "DET",
                "Green Bay Packers": "GB",
                "Minnesota Vikings": "MIN",
                # NFC South
                "Atlanta Falcons": "ATL",
                "Carolina Panthers": "CAR",
                "New Orleans Saints": "NO",
                "Tampa Bay Buccaneers": "TB",
                # NFC West
                "Arizona Cardinals": "ARI",
                "Los Angeles Rams": "LAR",
                "San Francisco 49ers": "SF",
                "Seattle Seahawks": "SEA",
            }
        else:
            # NCAAF - would need a much larger mapping
            # For now, just use first 3-4 chars
            return {}

    def _get_massey_to_abbrev_mapping(self, sport: str) -> Dict[str, str]:
        """
        Get Massey team name to abbreviation mapping.

        Massey uses short names like "LA Rams", "Philadelphia"
        We need to convert to "LAR", "PHI" for matching.
        """
        if sport.lower() == "nfl":
            return {
                # Massey name -> Abbreviation
                # AFC East
                "Buffalo": "BUF",
                "Miami": "MIA",
                "New England": "NE",
                "NY Jets": "NYJ",
                # AFC North
                "Baltimore": "BAL",
                "Cincinnati": "CIN",
                "Cleveland": "CLE",
                "Pittsburgh": "PIT",
                # AFC South
                "Houston": "HOU",
                "Indianapolis": "IND",
                "Jacksonville": "JAX",
                "Tennessee": "TEN",
                # AFC West
                "Denver": "DEN",
                "Kansas City": "KC",
                "Las Vegas": "LV",
                "LA Chargers": "LAC",
                # NFC East
                "Dallas": "DAL",
                "NY Giants": "NYG",
                "Philadelphia": "PHI",
                "Washington": "WAS",
                # NFC North
                "Chicago": "CHI",
                "Detroit": "DET",
                "Green Bay": "GB",
                "Minnesota": "MIN",
                # NFC South
                "Atlanta": "ATL",
                "Carolina": "CAR",
                "New Orleans": "NO",
                "Tampa Bay": "TB",
                # NFC West
                "Arizona": "ARI",
                "LA Rams": "LAR",
                "San Francisco": "SF",
                "Seattle": "SEA",
            }
        else:
            return {}

    def _save_results(self, result: EdgeDetectionResult, config: PipelineConfig) -> None:
        """Save pipeline results."""
        output_dir = self._output_dir / "edge_detection" / config.sport.lower()
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"week{config.week}_edges_{timestamp}.json"

        # Convert to serializable format
        output_data = {
            "sport": result.sport,
            "week": result.week,
            "season": result.season,
            "timestamp": result.timestamp.isoformat(),
            "summary": {
                "teams_analyzed": result.teams_analyzed,
                "games_analyzed": result.games_analyzed,
                "edges_found": result.edges_found,
                "best_bets_count": len(result.best_bets),
            },
            "best_bets": [
                {
                    "game": e.game,
                    "pick": e.our_pick,
                    "edge_pct": round(e.adjusted_edge_pct, 1),
                    "stars": e.star_rating,
                    "confidence": e.confidence_level,
                    "bet_size_pct": round(e.recommended_bet_pct * 100, 1),
                    "sharp_alignment": e.sharp_alignment,
                    "crossed_key_numbers": e.crossed_key_numbers,
                }
                for e in result.best_bets
            ],
            "all_edges": [
                {
                    "game": e.game,
                    "pick": e.our_pick,
                    "edge_pct": round(e.adjusted_edge_pct, 1),
                    "stars": e.star_rating,
                    "confidence": e.confidence_level,
                }
                for e in result.all_edges
            ],
            "power_ratings": {k: round(v, 2) for k, v in result.power_ratings.items()},
            "warnings": result.warnings,
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"[OK] Results saved to {output_path}")

    def print_results(self, result: EdgeDetectionResult) -> None:
        """Pretty print pipeline results."""
        print("\n" + "=" * 70)
        print(f"[NFL] {result.sport.upper()} WEEK {result.week} - EDGE DETECTION RESULTS")
        print("=" * 70)

        print("\n[SUMMARY]")
        print(f"   Teams Analyzed: {result.teams_analyzed}")
        print(f"   Games Analyzed: {result.games_analyzed}")
        print(f"   Edges Found: {result.edges_found}")
        print(f"   Best Bets (1+ stars): {len(result.best_bets)}")

        if result.best_bets:
            print("\n[BEST BETS]")
            print("-" * 70)
            for i, bet in enumerate(result.best_bets, 1):
                stars = "*" * int(bet.star_rating * 2)
                sharp = f" [{bet.sharp_alignment}]" if bet.sharp_alignment != "UNKNOWN" else ""
                print(
                    f"   {i}. {bet.game}: {bet.our_pick}"
                    f"\n      Edge: {bet.adjusted_edge_pct:.1f}% | {stars} | "
                    f"{bet.confidence_level}{sharp}"
                    f"\n      Bet: {bet.recommended_bet_pct * 100:.1f}% of bankroll"
                )
                if bet.crossed_key_numbers:
                    print(f"      Key numbers crossed: {bet.crossed_key_numbers}")
                print()

        if result.all_edges and len(result.all_edges) > len(result.best_bets):
            print(f"\n[OTHER EDGES] ({len(result.all_edges) - len(result.best_bets)} more):")
            for bet in result.all_edges:
                if bet.star_rating < 1.0:
                    print(f"   - {bet.game}: {bet.our_pick} ({bet.adjusted_edge_pct:.1f}%)")

        if result.warnings:
            print("\n[WARNINGS]")
            for w in result.warnings:
                print(f"   - {w}")

        print("\n" + "=" * 70)


def get_current_week(sport: str) -> int:
    """Get current week for a sport."""
    today = date.today()
    if sport.lower() == "nfl":
        week = get_nfl_week(today)
        return week if week else 1
    else:
        week = get_ncaaf_week(today)
        return week if week is not None else 1


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Edge Detection Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--sport",
        choices=["nfl", "ncaaf"],
        required=True,
        help="Sport to analyze",
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        help="Week number (auto-detects if not specified)",
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Season year",
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Scrape fresh Massey ratings",
    )
    parser.add_argument(
        "--scrape-odds",
        action="store_true",
        help="Scrape fresh Overtime.ag odds",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scrape both ratings and odds (equivalent to --scrape --scrape-odds)",
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=5.5,
        help="Minimum edge percentage to report",
    )
    parser.add_argument(
        "--hfa",
        type=float,
        default=None,
        help="Home field advantage (default: 2.5 NFL, 3.0 NCAAF)",
    )

    args = parser.parse_args()

    # Auto-detect week if not specified
    week = args.week
    if week is None:
        week = get_current_week(args.sport)
        logger.info(f"Auto-detected week: {week}")

    # Default HFA by sport
    hfa = args.hfa
    if hfa is None:
        hfa = 2.5 if args.sport == "nfl" else 3.0

    # Handle --all flag
    scrape_fresh = args.scrape or args.all
    scrape_odds = args.scrape_odds or args.all

    # Print current status
    league = League.NFL if args.sport == "nfl" else League.NCAAF
    print(f"\n📅 {format_season_status(league=league)}\n")

    # Run pipeline
    pipeline = EdgeDetectionPipeline()
    config = PipelineConfig(
        sport=args.sport,
        week=week,
        season=args.season,
        scrape_fresh=scrape_fresh,
        scrape_odds=scrape_odds,
        min_edge=args.min_edge,
        home_field_advantage=hfa,
    )

    result = await pipeline.run(config)
    pipeline.print_results(result)


if __name__ == "__main__":
    asyncio.run(main())
