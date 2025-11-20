"""
Data loader for autonomous agent
Transforms Billy Walters format odds/ratings into agent format
Includes injury data integration
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from walters_analyzer.valuation.injury_impacts import InjuryImpactCalculator

logger = logging.getLogger(__name__)


class AgentDataLoader:
    """Load and transform data for autonomous agent"""

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
        self.odds_dir = project_root / "output" / "overtime" / "nfl" / "pregame"
        self.injuries_dir = project_root / "output" / "injuries"
        self.ratings_file = project_root / "data" / "power_ratings_nfl_2025.json"
        self.home_field_advantage = 2.0
        self.injury_calculator = InjuryImpactCalculator()

    def load_power_ratings(self) -> Dict[str, float]:
        """Load power ratings from JSON file"""
        try:
            with open(self.ratings_file, "r") as f:
                data = json.load(f)
                return data.get("ratings", {})
        except FileNotFoundError:
            logger.warning(f"Power ratings file not found: {self.ratings_file}")
            return {}

    def load_latest_odds(self) -> List[Dict]:
        """Load most recent odds file"""
        try:
            # Find latest odds file
            odds_files = sorted(self.odds_dir.glob("api_raw_*.json"), reverse=True)
            if not odds_files:
                logger.error(f"No odds files found in {self.odds_dir}")
                return []

            latest_file = odds_files[0]
            logger.info(f"Loading odds from {latest_file.name}")

            with open(latest_file, "r") as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error loading odds: {e}")
            return []

    def load_latest_injuries(self) -> Dict[str, List[Dict]]:
        """
        Load most recent injury file and organize by team

        Returns:
            Dict mapping team name to list of injuries
        """
        try:
            # Find latest injury file (JSONL format)
            injury_files = sorted(
                self.injuries_dir.glob("nfl_official_injuries_*.jsonl"), reverse=True
            )
            if not injury_files:
                logger.warning(f"No injury files found in {self.injuries_dir}")
                return {}

            latest_file = injury_files[0]
            logger.info(f"Loading injuries from {latest_file.name}")

            injuries_by_team = {}
            with open(latest_file, "r") as f:
                for line in f:
                    injury = json.loads(line)
                    team = injury.get("team", "Unknown")

                    # Normalize team name
                    team_normalized = self.normalize_team_name_short(team)

                    if team_normalized not in injuries_by_team:
                        injuries_by_team[team_normalized] = []

                    injuries_by_team[team_normalized].append(injury)

            logger.info(f"Loaded injuries for {len(injuries_by_team)} teams")
            return injuries_by_team

        except Exception as e:
            logger.error(f"Error loading injuries: {e}")
            return {}

    def normalize_team_name_short(self, team_name: str) -> str:
        """Normalize short team names from injury reports to power rating format"""
        # Handle short names from NFL official injury reports
        team_map = {
            "Cardinals": "Arizona",
            "Falcons": "Atlanta",
            "Ravens": "Baltimore",
            "Bills": "Buffalo",
            "Panthers": "Carolina",
            "Bears": "Chicago",
            "Bengals": "Cincinnati",
            "Browns": "Cleveland",
            "Cowboys": "Dallas",
            "Broncos": "Denver",
            "Lions": "Detroit",
            "Packers": "Green Bay",
            "Texans": "Houston",
            "Colts": "Indianapolis",
            "Jaguars": "Jacksonville",
            "Chiefs": "Kansas City",
            "Raiders": "Las Vegas",
            "Chargers": "LA Chargers",
            "Rams": "LA Rams",
            "Dolphins": "Miami",
            "Vikings": "Minnesota",
            "Patriots": "New England",
            "Saints": "New Orleans",
            "Giants": "NY Giants",
            "Jets": "NY Jets",
            "Eagles": "Philadelphia",
            "Steelers": "Pittsburgh",
            "49ers": "San Francisco",
            "Seahawks": "Seattle",
            "Buccaneers": "Tampa Bay",
            "Titans": "Tennessee",
            "Commanders": "Washington",
        }
        return team_map.get(team_name, team_name)

    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team name for power rating lookup"""
        # Handle team name variations between Overtime.ag and power ratings
        team_map = {
            # Overtime.ag format -> Power ratings format
            "Arizona Cardinals": "Arizona",
            "Atlanta Falcons": "Atlanta",
            "Baltimore Ravens": "Baltimore",
            "Buffalo Bills": "Buffalo",
            "Carolina Panthers": "Carolina",
            "Chicago Bears": "Chicago",
            "Cincinnati Bengals": "Cincinnati",
            "Cleveland Browns": "Cleveland",
            "Dallas Cowboys": "Dallas",
            "Denver Broncos": "Denver",
            "Detroit Lions": "Detroit",
            "Green Bay Packers": "Green Bay",
            "Houston Texans": "Houston",
            "Indianapolis Colts": "Indianapolis",
            "Jacksonville Jaguars": "Jacksonville",
            "Kansas City Chiefs": "Kansas City",
            "Las Vegas Raiders": "Las Vegas",
            "Los Angeles Chargers": "LA Chargers",
            "Los Angeles Rams": "LA Rams",
            "Miami Dolphins": "Miami",
            "Minnesota Vikings": "Minnesota",
            "New England Patriots": "New England",
            "New Orleans Saints": "New Orleans",
            "New York Giants": "NY Giants",
            "New York Jets": "NY Jets",
            "Philadelphia Eagles": "Philadelphia",
            "Pittsburgh Steelers": "Pittsburgh",
            "San Francisco 49ers": "San Francisco",
            "Seattle Seahawks": "Seattle",
            "Tampa Bay Buccaneers": "Tampa Bay",
            "Tennessee Titans": "Tennessee",
            "Washington Commanders": "Washington",
        }
        return team_map.get(team_name, team_name)

    def calculate_team_injury_impact(
        self, team_name: str, injuries_by_team: Dict[str, List[Dict]]
    ) -> Dict:
        """
        Calculate injury impact for a team

        Returns:
            Dict with total_impact, critical_count, injury_details
        """
        team_injuries = injuries_by_team.get(team_name, [])

        if not team_injuries:
            return {
                "total_impact": 0.0,
                "critical_count": 0,
                "injury_count": 0,
                "injury_details": [],
            }

        # Position values (points impact when player is 100% out)
        position_values = {
            "QB": 4.5,
            "RB": 2.5,
            "WR": 1.8,
            "TE": 1.5,
            "OL": 1.5,
            "OT": 1.5,
            "OG": 1.3,
            "C": 1.5,
            "DE": 2.0,
            "DT": 1.5,
            "LB": 2.0,
            "CB": 2.5,
            "S": 2.0,
            "K": 0.5,
            "P": 0.3,
        }

        # Prepare player list for injury calculator
        injured_players = []
        for injury in team_injuries:
            position = injury.get("position", "Unknown")
            game_status = injury.get("game_status", "Questionable")
            injury_type_str = injury.get("injury_type", "")

            # Get player value based on position
            player_value = position_values.get(position, 1.0)

            # Parse injury type
            injury_type = self.injury_calculator.parse_injury_status(
                game_status, injury_type_str
            )

            injured_players.append(
                {
                    "name": injury.get("player_name", "Unknown"),
                    "position": position,
                    "value": player_value,
                    "injury_type": injury_type,
                    "days_since_injury": 0,  # We don't track this currently
                }
            )

        # Calculate team impact
        if injured_players:
            impact_data = self.injury_calculator.calculate_team_injury_impact(
                injured_players
            )
            return {
                "total_impact": impact_data.get("total_impact", 0.0),
                "critical_count": len(impact_data.get("critical_injuries", [])),
                "injury_count": len(injured_players),
                "injury_details": impact_data.get("detailed_breakdown", [])[
                    :5
                ],  # Top 5
            }
        else:
            return {
                "total_impact": 0.0,
                "critical_count": 0,
                "injury_count": 0,
                "injury_details": [],
            }

    def transform_game_for_agent(
        self,
        overtime_game: Dict,
        power_ratings: Dict[str, float],
        injuries_by_team: Optional[Dict[str, List[Dict]]] = None,
    ) -> Optional[Dict]:
        """
        Transform Overtime.ag format to agent format

        Overtime format:
            Team1ID: away team
            Team2ID: home team
            Spread1: away spread (e.g., 13)
            Spread2: home spread (e.g., -13)
            TotalPoints1: total
            OrigMoneyLine1: away ML
            OrigMoneyLine2: home ML

        Agent format:
            game_id, home_team, away_team, spread (home perspective),
            total, home_rating, away_rating, home_field_advantage, etc.
        """
        try:
            away_team_raw = overtime_game.get("Team1ID")
            home_team_raw = overtime_game.get("Team2ID")

            if not away_team_raw or not home_team_raw:
                return None

            # Normalize team names
            away_team = self.normalize_team_name(away_team_raw)
            home_team = self.normalize_team_name(home_team_raw)

            # Get power ratings
            away_rating = power_ratings.get(away_team, 0.0)
            home_rating = power_ratings.get(home_team, 0.0)

            # Spread is from home perspective (negative means home favored)
            home_spread = overtime_game.get("Spread2", 0)
            total = overtime_game.get("TotalPoints1", 0)

            # Calculate predicted spread from power ratings
            # Predicted = (home_rating - away_rating) + home_field_advantage
            predicted_spread = home_rating - away_rating + self.home_field_advantage

            # Game time
            game_date_str = overtime_game.get("GameDateTimeString", "")

            # Create game ID
            game_id = f"{away_team_raw.replace(' ', '_')}_at_{home_team_raw.replace(' ', '_')}"

            # Calculate injury impacts if data available
            home_injury_impact = {
                "total_impact": 0.0,
                "critical_count": 0,
                "injury_count": 0,
            }
            away_injury_impact = {
                "total_impact": 0.0,
                "critical_count": 0,
                "injury_count": 0,
            }

            if injuries_by_team:
                home_injury_impact = self.calculate_team_injury_impact(
                    home_team, injuries_by_team
                )
                away_injury_impact = self.calculate_team_injury_impact(
                    away_team, injuries_by_team
                )

            # Adjust predicted spread for injuries
            # Positive injury impact means team is hurt (subtract from their rating)
            injury_adjusted_spread = predicted_spread + (
                away_injury_impact["total_impact"] - home_injury_impact["total_impact"]
            )

            return {
                "game_id": game_id,
                "home_team": home_team_raw,
                "away_team": away_team_raw,
                "spread": home_spread,
                "total": total,
                "home_rating": home_rating,
                "away_rating": away_rating,
                "home_field_advantage": self.home_field_advantage,
                "predicted_spread": predicted_spread,
                "injury_adjusted_spread": injury_adjusted_spread,
                "game_time": game_date_str,
                # Injury data
                "home_injury_impact": home_injury_impact["total_impact"],
                "away_injury_impact": away_injury_impact["total_impact"],
                "home_critical_injuries": home_injury_impact["critical_count"],
                "away_critical_injuries": away_injury_impact["critical_count"],
                "home_injury_count": home_injury_impact["injury_count"],
                "away_injury_count": away_injury_impact["injury_count"],
                "injury_advantage": away_injury_impact["total_impact"]
                - home_injury_impact["total_impact"],  # Positive = home healthier
                # Additional fields the agent can use
                "home_moneyline": overtime_game.get("OrigMoneyLine2"),
                "away_moneyline": overtime_game.get("OrigMoneyLine1"),
                "rotation_away": overtime_game.get("Team1RotNum"),
                "rotation_home": overtime_game.get("Team2RotNum"),
                # Placeholders for optional data
                "opening_spread": home_spread,  # Would need historical data
                "public_percentage": 50,  # Would need public betting data
                "money_percentage": 50,  # Would need sharp money data
                "home_rest_days": 7,  # Would need rest tracking
                "away_rest_days": 7,
                "away_travel_distance": 0,  # Would need distance calc
                "division_game": False,  # Would need division lookup
                "primetime": "20:15" in game_date_str or "20:25" in game_date_str,
                "revenge_game": False,  # Would need game history
            }

        except Exception as e:
            logger.error(f"Error transforming game: {e}")
            return None

    def load_all_games(self) -> List[Dict]:
        """Load all games ready for agent analysis (includes injury data)"""
        power_ratings = self.load_power_ratings()
        if not power_ratings:
            logger.warning("No power ratings loaded - using defaults")

        overtime_games = self.load_latest_odds()
        if not overtime_games:
            logger.error("No odds data loaded")
            return []

        # Load injury data
        injuries_by_team = self.load_latest_injuries()
        if injuries_by_team:
            logger.info(
                f"Loaded {sum(len(inj) for inj in injuries_by_team.values())} total injuries"
            )
        else:
            logger.warning("No injury data loaded - analysis will not include injuries")

        agent_games = []
        for game in overtime_games:
            agent_game = self.transform_game_for_agent(
                game, power_ratings, injuries_by_team
            )
            if agent_game:
                agent_games.append(agent_game)

        logger.info(f"Loaded {len(agent_games)} games for agent analysis")
        return agent_games


if __name__ == "__main__":
    # Test the loader
    logging.basicConfig(level=logging.INFO)

    loader = AgentDataLoader()
    games = loader.load_all_games()

    print(f"\nLoaded {len(games)} games\n")
    for game in games[:3]:  # Show first 3
        print(f"Game: {game['away_team']} @ {game['home_team']}")
        print(f"  Spread: {game['home_team']} {game['spread']:+.1f}")
        print(f"  Total: {game['total']}")
        print(f"  Ratings: {game['away_rating']:.1f} vs {game['home_rating']:.1f}")
        print(f"  Predicted: {game['predicted_spread']:+.1f}")
        print(f"  Injury Adjusted: {game['injury_adjusted_spread']:+.1f}")
        print(
            f"  Injuries: Home {game['home_injury_count']} ({game['home_injury_impact']:+.1f} pts), "
            f"Away {game['away_injury_count']} ({game['away_injury_impact']:+.1f} pts)"
        )
        print(
            f"  Injury Advantage: {game['injury_advantage']:+.1f} (positive = home healthier)"
        )
        print()
