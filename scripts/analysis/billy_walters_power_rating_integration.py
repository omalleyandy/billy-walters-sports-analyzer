#!/usr/bin/env python3
"""
Billy Walters Power Rating Integration Script

Collects and integrates all data sources needed for Billy Walters power rating methodology:
1. ESPN Team Statistics (offensive/defensive metrics)
2. Massey Ratings (fallback/composite baseline)
3. Overtime.ag Odds (market lines)
4. Weather Data (game conditions)
5. Injury Reports (player impacts)

Then calculates week-to-week power ratings and identifies mathematical edges.

Usage:
    # Complete workflow for current week
    uv run python scripts/analysis/billy_walters_power_rating_integration.py --week 11

    # Just collect data without analysis
    uv run python scripts/analysis/billy_walters_power_rating_integration.py --week 11 --collect-only

    # Analysis only (skip data collection)
    uv run python scripts/analysis/billy_walters_power_rating_integration.py --week 11 --analysis-only
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from data.espn_api_client import ESPNAPIClient
from data.massey_ratings_scraper import MasseyRatingsScraper
from data.overtime_api_client import OvertimeApiClient

# Import edge detector with proper path handling
sys.path.insert(0, str(project_root))
from src.walters_analyzer.valuation.billy_walters_edge_detector import (
    BillyWaltersEdgeDetector,
    PowerRating,
)


class BillyWaltersPowerRatingIntegration:
    """
    Integrates all data sources for Billy Walters power rating methodology.
    """

    def __init__(self, week: int, league: str = "nfl"):
        """
        Initialize integration system.

        Args:
            week: Week number
            league: 'nfl' or 'ncaaf'
        """
        self.week = week
        self.league = league
        self.league_short = "ncaaf" if league == "college-football" else "nfl"

        # Clients
        self.espn_client = ESPNAPIClient()
        self.massey_scraper = MasseyRatingsScraper()
        self.overtime_client = OvertimeApiClient()
        self.edge_detector = BillyWaltersEdgeDetector()

        # Data storage
        self.espn_team_stats: Dict[str, Dict] = {}
        self.massey_ratings: Dict[str, Dict] = {}
        self.overtime_odds: Dict[str, Dict] = {}
        self.power_ratings: Dict[str, PowerRating] = {}

        # Output directory
        self.output_dir = Path(f"output/billy_walters/week_{week}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def collect_all_data(self) -> Dict[str, bool]:
        """
        Collect all required data sources.

        Returns:
            Dictionary with collection status for each source
        """
        print("=" * 70)
        print("BILLY WALTERS POWER RATING DATA COLLECTION")
        print("=" * 70)
        print(f"Week: {self.week}")
        print(f"League: {self.league_short.upper()}")
        print()

        results = {
            "espn_stats": False,
            "massey_ratings": False,
            "overtime_odds": False,
        }

        # Step 1: Collect ESPN Team Statistics
        print("[1/3] Collecting ESPN Team Statistics...")
        try:
            if self.league_short == "nfl":
                stats_file = Path(f"data/current/nfl_team_stats_week_{self.week}.json")
            else:
                stats_file = Path(
                    f"data/current/ncaaf_team_stats_week_{self.week}.json"
                )

            if stats_file.exists():
                with open(stats_file, "r") as f:
                    data = json.load(f)
                    self.espn_team_stats = {
                        team["team_name"]: team for team in data.get("teams", [])
                    }
                print(f"    [OK] Loaded {len(self.espn_team_stats)} teams from cache")
                results["espn_stats"] = True
            else:
                print(f"    [WARNING] Stats file not found: {stats_file}")
                print(
                    f"    [INFO] Run: uv run python scripts/scrapers/scrape_espn_team_stats.py --league {self.league_short} --week {self.week}"
                )
        except Exception as e:
            print(f"    [ERROR] Failed to load ESPN stats: {e}")

        # Step 2: Collect Massey Ratings (fallback)
        print("\n[2/3] Collecting Massey Ratings (fallback)...")
        try:
            if self.league_short == "nfl":
                massey_file = list(
                    Path("output/massey/nfl/ratings").glob("nfl_ratings_*.json")
                )
            else:
                massey_file = list(
                    Path("output/massey/ncaaf/ratings").glob("ncaaf_ratings_*.json")
                )

            if massey_file:
                # Use most recent
                massey_file = sorted(massey_file, reverse=True)[0]
                with open(massey_file, "r") as f:
                    data = json.load(f)
                    # Massey format: {"sport": "NFL", "teams": [...]}
                    teams_list = data.get("teams", [])
                    if teams_list:
                        # Teams can be dict with "name" key or list format
                        for team in teams_list:
                            if isinstance(team, dict):
                                team_name = (
                                    team.get("name")
                                    or team.get("team")
                                    or team.get("Team")
                                )
                                if team_name:
                                    self.massey_ratings[team_name] = team
                print(f"    [OK] Loaded {len(self.massey_ratings)} teams from Massey")
                results["massey_ratings"] = True
            else:
                print("    [WARNING] Massey ratings not found")
                print(
                    "    [INFO] Run: uv run python -m src.data.massey_ratings_scraper"
                )
        except Exception as e:
            print(f"    [ERROR] Failed to load Massey ratings: {e}")

        # Step 3: Collect Overtime Odds
        print("\n[3/3] Collecting Overtime.ag Odds...")
        try:
            if self.league_short == "nfl":
                odds_file = list(
                    Path("output/overtime/nfl/pregame").glob("api_walters_*.json")
                )
            else:
                odds_file = list(
                    Path("output/overtime/ncaaf/pregame").glob("api_walters_*.json")
                )

            if odds_file:
                # Use most recent
                odds_file = sorted(odds_file, reverse=True)[0]
                with open(odds_file, "r") as f:
                    data = json.load(f)
                    self.overtime_odds = {
                        f"{game['away_team']}@{game['home_team']}": game
                        for game in data.get("games", [])
                    }
                print(f"    [OK] Loaded {len(self.overtime_odds)} games from Overtime")
                results["overtime_odds"] = True
            else:
                print("    [WARNING] Overtime odds not found")
                print(
                    f"    [INFO] Run: uv run python scripts/scrapers/scrape_overtime_api.py --{self.league_short}"
                )
        except Exception as e:
            print(f"    [ERROR] Failed to load Overtime odds: {e}")

        print("\n" + "=" * 70)
        print("DATA COLLECTION SUMMARY")
        print("=" * 70)
        for source, success in results.items():
            status = "[OK]" if success else "[MISSING]"
            print(f"{source}: {status}")

        return results

    def calculate_power_ratings(self) -> Dict[str, PowerRating]:
        """
        Calculate power ratings using Billy Walters methodology.

        Billy Walters Formula:
        - Base: Massey rating (70-100 scale) OR calculated from ESPN stats
        - Enhancement: ESPN team stats (offensive/defensive efficiency)
        - Fallback: Use Massey if ESPN stats unavailable

        Returns:
            Dictionary of team name -> PowerRating
        """
        print("\n" + "=" * 70)
        print("CALCULATING POWER RATINGS")
        print("=" * 70)

        power_ratings = {}

        # Get all teams from available sources
        all_teams = set()
        all_teams.update(self.espn_team_stats.keys())
        all_teams.update(self.massey_ratings.keys())

        for team_name in all_teams:
            # Try to get ESPN stats first
            espn_stats = self.espn_team_stats.get(team_name)
            massey_data = self.massey_ratings.get(team_name)

            # Calculate base rating
            if espn_stats:
                # Calculate from ESPN stats
                base_rating = self._calculate_rating_from_espn_stats(espn_stats)
                offensive_rating = self._calculate_offensive_rating(espn_stats)
                defensive_rating = self._calculate_defensive_rating(espn_stats)
                source = "espn"  # No enhancement yet - will be enhanced if Massey data available
            elif massey_data:
                # Fallback to Massey
                # Massey rating is on different scale (0-10), convert to 70-100 scale
                massey_rating_str = massey_data.get("rating", "7.5")
                try:
                    massey_rating_float = float(massey_rating_str)
                    # Convert from 0-10 scale to 70-100 scale: rating * 10 + 20
                    base_rating = (massey_rating_float * 10) + 20
                    base_rating = max(70.0, min(100.0, base_rating))
                except (ValueError, TypeError):
                    base_rating = 75.0  # Default if can't parse

                # Massey doesn't always have offensive/defensive breakdown
                # Use defaults based on base rating
                offensive_rating = base_rating * 0.55
                defensive_rating = base_rating * 0.45
                source = "massey"
            else:
                # Skip teams without data
                continue

            # Enhance with ESPN stats if available
            if espn_stats and massey_data:
                # Use ESPN for granular adjustments
                ppg = espn_stats.get("points_per_game", 0)
                papg = espn_stats.get("points_allowed_per_game", 0)
                to_margin = espn_stats.get("turnover_margin", 0)

                # Enhancement factors (Billy Walters methodology)
                offensive_enhancement = (ppg - 23.3) * 0.15  # League average ~23.3
                defensive_enhancement = (23.3 - papg) * 0.15  # Favor lower PAPG
                turnover_enhancement = to_margin * 0.3

                enhanced_rating = (
                    base_rating
                    + offensive_enhancement
                    + defensive_enhancement
                    + turnover_enhancement
                )
                # Clamp to 70-100 scale
                enhanced_rating = max(70.0, min(100.0, enhanced_rating))

                base_rating = enhanced_rating
                # Update source to reflect enhancement
                if source == "espn":
                    source = "espn_enhanced"  # ESPN base enhanced with Massey baseline
                elif source == "massey":
                    source = (
                        "massey_enhanced_espn"  # Massey base enhanced with ESPN stats
                    )

            # Standard home field advantage
            home_field_advantage = 3.0 if self.league_short == "nfl" else 3.5

            power_rating = PowerRating(
                team=team_name,
                rating=base_rating,
                offensive_rating=offensive_rating,
                defensive_rating=defensive_rating,
                home_field_advantage=home_field_advantage,
                source=source,
            )

            power_ratings[team_name] = power_rating

        self.power_ratings = power_ratings

        print(f"\nCalculated {len(power_ratings)} power ratings")
        print("\nTop 10 Power Ratings:")
        sorted_ratings = sorted(
            power_ratings.items(), key=lambda x: x[1].rating, reverse=True
        )
        for i, (team, rating) in enumerate(sorted_ratings[:10], 1):
            print(f"  {i:2d}. {team:25s} {rating.rating:5.2f} ({rating.source})")

        return power_ratings

    def _calculate_rating_from_espn_stats(self, stats: Dict) -> float:
        """Calculate base power rating from ESPN statistics."""
        ppg = stats.get("points_per_game", 23.3)
        papg = stats.get("points_allowed_per_game", 23.3)

        # Billy Walters base formula: Rating = 75 + (PPG - 23.3) * 0.5 - (PAPG - 23.3) * 0.5
        base = 75.0
        offensive_component = (ppg - 23.3) * 0.5
        defensive_component = (23.3 - papg) * 0.5

        rating = base + offensive_component + defensive_component

        # Clamp to 70-100 scale
        return max(70.0, min(100.0, rating))

    def _calculate_offensive_rating(self, stats: Dict) -> float:
        """Calculate offensive rating component."""
        ppg = stats.get("points_per_game", 23.3)
        ypg = stats.get("total_yards_per_game", 350.0)

        # Normalize to 70-100 scale (simplified)
        offensive = 75.0 + (ppg - 23.3) * 0.5 + (ypg - 350.0) * 0.01
        return max(70.0, min(100.0, offensive))

    def _calculate_defensive_rating(self, stats: Dict) -> float:
        """Calculate defensive rating component."""
        papg = stats.get("points_allowed_per_game", 23.3)
        yapg = stats.get("total_yards_allowed_per_game", 350.0)

        # Normalize to 70-100 scale (simplified)
        # Lower PAPG and YAPG = better defense
        defensive = 75.0 + (23.3 - papg) * 0.5 + (350.0 - yapg) * 0.01
        return max(70.0, min(100.0, defensive))

    def detect_edges(self) -> List[Dict]:
        """
        Detect betting edges using Billy Walters methodology.

        Returns:
            List of detected edges
        """
        print("\n" + "=" * 70)
        print("DETECTING BETTING EDGES")
        print("=" * 70)

        # Load power ratings into edge detector
        self.edge_detector.power_ratings = self.power_ratings

        edges = []

        for game_key, game_data in self.overtime_odds.items():
            away_team = game_data.get("away_team", "")
            home_team = game_data.get("home_team", "")
            spread = game_data.get("spread", {}).get("home", 0.0)
            total = game_data.get("total", {}).get("points", 0.0)

            # Skip if we don't have power ratings for both teams
            if (
                away_team not in self.power_ratings
                or home_team not in self.power_ratings
            ):
                continue

            try:
                # Detect edge
                edge = self.edge_detector.detect_edge(
                    game_id=game_key,
                    away_team=away_team,
                    home_team=home_team,
                    market_spread=spread,
                    market_total=total,
                    week=self.week,
                    game_time=game_data.get("game_time", ""),
                    best_odds=-110,
                    season=2025,  # 2025 season
                )

                if edge:
                    edges.append(
                        {
                            "game": f"{away_team} @ {home_team}",
                            "edge_points": edge.edge_points,
                            "recommended_bet": edge.recommended_bet,
                            "market_spread": spread,
                            "predicted_spread": edge.predicted_spread,
                            "confidence": edge.confidence_score,
                            "kelly_fraction": edge.kelly_fraction,
                        }
                    )

            except Exception as e:
                print(
                    f"    [ERROR] Failed to detect edge for {away_team} @ {home_team}: {e}"
                )

        print(f"\nDetected {len(edges)} betting edges")

        if edges:
            print("\nTop Edges:")
            sorted_edges = sorted(edges, key=lambda x: x["edge_points"], reverse=True)
            for i, edge in enumerate(sorted_edges[:5], 1):
                print(
                    f"  {i}. {edge['game']:35s} Edge: {edge['edge_points']:.2f} pts | {edge['recommended_bet']}"
                )

        return edges

    def save_results(self) -> Path:
        """Save integration results to JSON file."""
        power_ratings_dict = {
            team: {
                "team": rating.team,
                "rating": rating.rating,
                "offensive_rating": rating.offensive_rating,
                "defensive_rating": rating.defensive_rating,
                "source": rating.source,
            }
            for team, rating in self.power_ratings.items()
        }

        output_data = {
            "week": self.week,
            "league": self.league_short,
            "timestamp": datetime.now().isoformat(),
            "power_ratings": power_ratings_dict,
            # Use actual number of keys in power_ratings object (accounts for duplicates from different naming conventions)
            "team_count": len(power_ratings_dict),
            "games_analyzed": len(self.overtime_odds),
        }

        output_file = self.output_dir / f"power_ratings_week_{self.week}.json"
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\n[OK] Results saved to {output_file}")
        return output_file


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Billy Walters Power Rating Integration"
    )
    parser.add_argument("--week", type=int, required=True, help="Week number")
    parser.add_argument(
        "--league",
        choices=["nfl", "ncaaf"],
        default="nfl",
        help="League (default: nfl)",
    )
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Only collect data, skip analysis",
    )
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Skip data collection, use existing data",
    )

    args = parser.parse_args()

    league_api = "college-football" if args.league == "ncaaf" else "nfl"

    integration = BillyWaltersPowerRatingIntegration(week=args.week, league=league_api)

    try:
        # Step 1: Collect data
        if not args.analysis_only:
            results = await integration.collect_all_data()

            if not any(results.values()):
                print("\n[ERROR] No data collected. Cannot proceed.")
                return 1
        else:
            # In analysis-only mode, try to load existing data from disk
            print("[INFO] Analysis-only mode: Loading existing data...")
            results = await integration.collect_all_data()

            # Check if any data was loaded
            if not any(results.values()):
                print(
                    "\n[ERROR] No existing data found. Cannot run analysis-only mode."
                )
                print(
                    "[INFO] Run without --analysis-only flag to collect data first, or ensure data files exist:"
                )
                if integration.league_short == "nfl":
                    print(
                        f"  - data/current/nfl_team_stats_week_{integration.week}.json"
                    )
                    print("  - output/massey/nfl/ratings/nfl_ratings_*.json")
                    print("  - output/overtime/nfl/pregame/api_walters_*.json")
                else:
                    print(
                        f"  - data/current/ncaaf_team_stats_week_{integration.week}.json"
                    )
                    print("  - output/massey/ncaaf/ratings/ncaaf_ratings_*.json")
                    print("  - output/overtime/ncaaf/pregame/api_walters_*.json")
                return 1

        # Step 2: Calculate power ratings
        if not args.collect_only:
            # Verify we have data before calculating
            if not integration.espn_team_stats and not integration.massey_ratings:
                print(
                    "\n[ERROR] No team statistics available. Cannot calculate power ratings."
                )
                print("[INFO] Ensure ESPN stats or Massey ratings are available.")
                return 1

            if not integration.overtime_odds:
                print(
                    "\n[WARNING] No odds data available. Edge detection will be skipped."
                )

            power_ratings = integration.calculate_power_ratings()

            # Step 3: Detect edges
            edges = integration.detect_edges()

            # Step 4: Save results
            integration.save_results()

        print("\n" + "=" * 70)
        print("[SUCCESS] Billy Walters Power Rating Integration Complete")
        print("=" * 70)

        return 0

    except KeyboardInterrupt:
        print("\n\n[INFO] Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n[ERROR] Failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
