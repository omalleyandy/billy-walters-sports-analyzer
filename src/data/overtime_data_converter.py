#!/usr/bin/env python3
"""
Overtime.ag Data Converter

Converts scraped Overtime.ag betting data to Billy Walters format
for integration with the sports analyzer system.

Supports both NFL and NCAAF (College Football).
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .models import Game, League, OddsMovement, Team
from walters_analyzer.season_calendar import get_nfl_week


class OvertimeToWaltersConverter:
    """
    Converts Overtime.ag data format to Billy Walters analyzer format.

    Handles:
    - Team name normalization (NFL and NCAAF)
    - Odds format conversion (American odds)
    - Spread and total parsing
    - Multi-period data (Game, 1H, 1Q)
    """

    # NFL Team name mapping for normalization
    NFL_TEAM_MAPPINGS = {
        "Philadelphia Eagles": "PHI",
        "Green Bay Packers": "GB",
        "Kansas City Chiefs": "KC",
        "Buffalo Bills": "BUF",
        "San Francisco 49ers": "SF",
        "Dallas Cowboys": "DAL",
        "Detroit Lions": "DET",
        "Baltimore Ravens": "BAL",
        "Miami Dolphins": "MIA",
        "Los Angeles Rams": "LAR",
        "Los Angeles Chargers": "LAC",
        "Cincinnati Bengals": "CIN",
        "Jacksonville Jaguars": "JAX",
        "Cleveland Browns": "CLE",
        "Pittsburgh Steelers": "PIT",
        "Houston Texans": "HOU",
        "Seattle Seahawks": "SEA",
        "Tampa Bay Buccaneers": "TB",
        "Minnesota Vikings": "MIN",
        "Atlanta Falcons": "ATL",
        "New Orleans Saints": "NO",
        "Indianapolis Colts": "IND",
        "Las Vegas Raiders": "LV",
        "New York Jets": "NYJ",
        "New York Giants": "NYG",
        "Tennessee Titans": "TEN",
        "New England Patriots": "NE",
        "Arizona Cardinals": "ARI",
        "Washington Commanders": "WAS",
        "Chicago Bears": "CHI",
        "Denver Broncos": "DEN",
        "Carolina Panthers": "CAR",
    }

    # NCAAF Team mappings loaded from JSON file
    _NCAAF_MAPPINGS: Optional[Dict[str, str]] = None

    def __init__(self, league: League = League.NFL):
        """
        Initialize converter.

        Args:
            league: League to convert data for (NFL or NCAAF)
        """
        self.league = league

        # Load NCAAF mappings if needed
        if league == League.NCAAF and self._NCAAF_MAPPINGS is None:
            self._load_ncaaf_mappings()

    @classmethod
    def _load_ncaaf_mappings(cls):
        """Load NCAAF team mappings from JSON file"""
        mappings_file = Path(__file__).parent / "ncaaf_team_mappings.json"
        try:
            with open(mappings_file, "r") as f:
                data = json.load(f)
                cls._NCAAF_MAPPINGS = data.get("mappings", {})
        except FileNotFoundError:
            print(f"Warning: NCAAF team mappings file not found: {mappings_file}")
            cls._NCAAF_MAPPINGS = {}
        except Exception as e:
            print(f"Error loading NCAAF mappings: {e}")
            cls._NCAAF_MAPPINGS = {}

    def convert_game(self, overtime_game: Dict[str, Any]) -> Optional[Game]:
        """
        Convert a single Overtime.ag game to Billy Walters Game format.

        Args:
            overtime_game: Raw game data from Overtime scraper

        Returns:
            Game object in Billy Walters format, or None if conversion fails
        """
        try:
            # Extract basic info
            visitor_team = self._normalize_team_name(
                overtime_game["visitor"]["teamName"]
            )
            home_team = self._normalize_team_name(overtime_game["home"]["teamName"])

            # Parse game date and time
            game_date, game_time = self._parse_datetime(
                overtime_game.get("gameDate"), overtime_game.get("gameTime")
            )

            # Extract odds
            odds = self._extract_odds(overtime_game)

            if not odds:
                return None

            # Validate game_date is not None (required by Game model)
            if game_date is None:
                print(
                    f"Skipping game: game_date is None for {visitor_team} @ {home_team}"
                )
                return None

            # Generate game_id (format: AWAY_HOME_YYYYMMDD)
            game_date_str = game_date.strftime("%Y%m%d")
            game_id = f"{visitor_team}_{home_team}_{game_date_str}"

            # Calculate week number from game date
            if self.league == League.NFL:
                week = get_nfl_week(game_date.date())
                if week is None:
                    week = 1
                    print(
                        f"Warning: Could not determine week for {game_id}, defaulting to week 1"
                    )
            else:
                # NCAAF: Use week 1-15 based on date (simple fallback)
                # TODO: Implement proper NCAAF week calculation
                week = 1

            # Create Game object (with only valid fields)
            game = Game(
                game_id=game_id,
                league=self.league,
                away_team=Team(
                    name=overtime_game["visitor"]["teamName"],
                    abbreviation=visitor_team,
                    league=self.league,
                    rotation_number=overtime_game["visitor"].get("rotationNumber"),
                ),
                home_team=Team(
                    name=overtime_game["home"]["teamName"],
                    abbreviation=home_team,
                    league=self.league,
                    rotation_number=overtime_game["home"].get("rotationNumber"),
                ),
                game_date=game_date,
                week=week,
                odds=odds,
            )

            return game

        except Exception as e:
            print(f"Error converting game: {e}")
            return None

    def convert_batch(self, overtime_games: List[Dict[str, Any]]) -> List[Game]:
        """
        Convert multiple Overtime.ag games to Billy Walters format.

        Args:
            overtime_games: List of raw game data from Overtime scraper

        Returns:
            List of Game objects
        """
        games = []

        for ot_game in overtime_games:
            game = self.convert_game(ot_game)
            if game:
                games.append(game)

        return games

    def _normalize_team_name(self, full_name: str) -> str:
        """
        Convert full team name to abbreviation.

        Args:
            full_name: Full team name (e.g., "Philadelphia Eagles" or "Ohio St")

        Returns:
            Team abbreviation (e.g., "PHI" or "OSU")
        """
        # Select appropriate mappings based on league
        if self.league == League.NCAAF:
            mappings = self._NCAAF_MAPPINGS or {}
        else:
            mappings = self.NFL_TEAM_MAPPINGS

        # Check direct mapping
        abbr = mappings.get(full_name)
        if abbr:
            return abbr

        # Fallback: extract first letters of last word
        words = full_name.split()
        if len(words) > 1:
            # Use last word (team name)
            return words[-1][:3].upper()

        # Last resort: first 3 letters
        return full_name[:3].upper()

    def _parse_datetime(
        self, game_date: Optional[str], game_time: Optional[str]
    ) -> tuple[Optional[datetime], Optional[str]]:
        """
        Parse game date and time from Overtime format.

        Args:
            game_date: Date string (e.g., "Mon Nov 10")
            game_time: Time string (e.g., "8:15 PM")

        Returns:
            Tuple of (datetime object, time string)
        """
        if not game_date or not game_time:
            return None, game_time

        try:
            # Parse date (e.g., "Mon Nov 10")
            # Assume current year
            current_year = datetime.now().year
            date_with_year = f"{game_date} {current_year}"

            # Parse to datetime
            dt = datetime.strptime(date_with_year, "%a %b %d %Y")

            return dt, game_time

        except Exception as e:
            print(f"Error parsing datetime: {e}")
            return None, game_time

    def _extract_odds(self, overtime_game: Dict[str, Any]) -> Optional[OddsMovement]:
        """
        Extract and parse odds from Overtime game data.

        Args:
            overtime_game: Raw game data

        Returns:
            OddsMovement object with spread and totals
        """
        try:
            visitor = overtime_game["visitor"]
            home = overtime_game["home"]

            # Parse spread (e.g., "+1 -113" or "-1 -107")
            visitor_spread_str = visitor.get("spread", "")
            home_spread_str = home.get("spread", "")

            visitor_spread, visitor_spread_odds = self._parse_line(visitor_spread_str)
            home_spread, home_spread_odds = self._parse_line(home_spread_str)

            # Parse totals (e.g., "O 45½ -112" or "U 45½ -108")
            visitor_total_str = visitor.get("total", "")
            home_total_str = home.get("total", "")

            over_total, over_odds = self._parse_total(visitor_total_str)
            under_total, under_odds = self._parse_total(home_total_str)

            # Use visitor spread as the line (home will be inverse)
            spread = visitor_spread or (home_spread * -1 if home_spread else 0.0)
            spread_odds = visitor_spread_odds or -110

            # Over/under total (should be same number)
            over_under = over_total or under_total or 0.0
            total_odds = over_odds or -110

            return OddsMovement(
                spread=spread,
                spread_odds=spread_odds,
                over_under=over_under,
                total_odds=total_odds,
                timestamp=overtime_game.get("scraped_at", datetime.now()),
            )

        except Exception as e:
            print(f"Error extracting odds: {e}")
            return None

    def _parse_line(self, line_str: str) -> tuple[Optional[float], Optional[int]]:
        """
        Parse a betting line string (spread or moneyline).

        Args:
            line_str: Line string (e.g., "+1 -113", "-3.5 -110")

        Returns:
            Tuple of (line value, odds)
        """
        if not line_str:
            return None, None

        try:
            # Extract line and odds
            # Pattern: [+/-]X.X [+/-]XXX
            parts = line_str.strip().split()

            if len(parts) >= 2:
                # Parse line (handle ½ as .5)
                line_part = parts[0].replace("½", ".5")
                line = float(line_part)

                # Parse odds
                odds = int(parts[1])

                return line, odds
            elif len(parts) == 1:
                # Only line, no odds
                line_part = parts[0].replace("½", ".5")
                line = float(line_part)
                return line, -110  # Default odds

        except Exception as e:
            print(f"Error parsing line '{line_str}': {e}")

        return None, None

    def _parse_total(self, total_str: str) -> tuple[Optional[float], Optional[int]]:
        """
        Parse a total betting line string.

        Args:
            total_str: Total string (e.g., "O 45½ -112", "U 45½ -108")

        Returns:
            Tuple of (total value, odds)
        """
        if not total_str:
            return None, None

        try:
            # Remove O/U prefix and parse
            cleaned = total_str.strip()

            # Extract total and odds
            # Pattern: O/U X.X [+/-]XXX
            match = re.search(
                r"([OU])\s*([\d½.]+)\s*([+\-]\d+)", cleaned, re.IGNORECASE
            )

            if match:
                # Parse total (handle ½ as .5)
                total_part = match.group(2).replace("½", ".5")
                total = float(total_part)

                # Parse odds
                odds = int(match.group(3))

                return total, odds

        except Exception as e:
            print(f"Error parsing total '{total_str}': {e}")

        return None, None


def convert_overtime_to_walters(
    overtime_data: Dict[str, Any], league: League = League.NFL
) -> Dict[str, Any]:
    """
    Convert complete Overtime.ag scrape output to Billy Walters format.

    Args:
        overtime_data: Complete output from OvertimeNFLScraper or OvertimeNCAAFScraper
        league: League type (NFL or NCAAF), auto-detected from scrape_metadata if available

    Returns:
        Dictionary with converted games and metadata
    """
    # Auto-detect league from scrape metadata
    sport = overtime_data.get("scrape_metadata", {}).get("sport", "NFL")
    if sport == "NCAAF":
        league = League.NCAAF

    converter = OvertimeToWaltersConverter(league=league)

    # Convert games
    converted_games = converter.convert_batch(overtime_data.get("games", []))

    return {
        "metadata": {
            "source": "overtime.ag",
            "league": league.value,
            "converted_at": datetime.now().isoformat(),
            "original_scrape_time": (
                overtime_data.get("scrape_metadata", {}).get("timestamp")
            ),
            "converter_version": "1.1.0",
        },
        "account_info": overtime_data.get("account_info"),
        "games": [game.model_dump() for game in converted_games],
        "summary": {
            "total_converted": len(converted_games),
            "conversion_rate": (
                f"{len(converted_games) / len(overtime_data.get('games', [])) * 100:.1f}%"
                if overtime_data.get("games")
                else "0%"
            ),
        },
    }


if __name__ == "__main__":
    """Example usage"""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python overtime_data_converter.py <input_json_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Load Overtime data
    with open(input_file, "r") as f:
        overtime_data = json.load(f)

    # Convert
    walters_data = convert_overtime_to_walters(overtime_data)

    # Save
    output_file = input_file.replace(".json", "_walters.json")
    with open(output_file, "w") as f:
        json.dump(walters_data, f, indent=2, default=str)

    print(f"✓ Converted {walters_data['summary']['total_converted']} games")
    print(f"✓ Saved to: {output_file}")
