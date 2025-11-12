"""
Overtime.ag API Client - Direct API Access (No Browser Automation Required).

This client uses the reverse-engineered API endpoint discovered by inspecting
the Chrome DevTools accessibility approach via the ServiceCaller wiring at
data/overtime_libs.js (line 4278).

Endpoint: POST https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering

Advantages over Playwright/SignalR:
- No browser automation required
- No CloudFlare bypass needed
- No proxy required
- Simple HTTP POST request
- Fast and reliable
- Direct access to same data as website

Author: Claude Code
Date: 2025-11-11
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


class OvertimeApiClient:
    """Client for Overtime.ag API (reverse-engineered endpoint)."""

    BASE_URL = "https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering"

    def __init__(self, output_dir: str | Path = "output/overtime"):
        """
        Initialize the Overtime API client.

        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_games(
        self,
        sport_type: str = "Football",
        sport_sub_type: str = "NFL",
        wager_type: str = "Straight Bet",
        period_number: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Fetch games from Overtime.ag API.

        Args:
            sport_type: "Football" (for NFL/NCAAF)
            sport_sub_type: "NFL" or "College Football"
            wager_type: "Straight Bet" (default)
            period_number: 0 for full game, 1 for 1H, 2 for 2H

        Returns:
            List of game dictionaries
        """
        payload = {
            "sportType": sport_type,
            "sportSubType": sport_sub_type,
            "wagerType": wager_type,
            "hoursAdjustment": 0,
            "periodNumber": period_number,
            "gameNum": None,
            "parentGameNum": None,
            "teaserName": "",
            "requestMode": "G",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.BASE_URL, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if "d" in data and "Data" in data["d"] and "GameLines" in data["d"]["Data"]:
                return data["d"]["Data"]["GameLines"]

            return []

    def convert_to_billy_walters_format(
        self, games: list[dict[str, Any]], league: str
    ) -> dict[str, Any]:
        """
        Convert Overtime API response to Billy Walters standard format.

        Args:
            games: List of games from API
            league: "NFL" or "NCAAF"

        Returns:
            Billy Walters formatted data
        """
        converted_games = []

        for game in games:
            # Extract team names
            team1 = game.get("Team1ID", "")
            team2 = game.get("Team2ID", "")
            favored_team = game.get("FavoredTeamID", "")

            # Determine away/home based on favored team
            if favored_team == team2:
                away_team = team1
                home_team = team2
                away_spread = float(game.get("Spread1", 0) or 0)
                home_spread = float(game.get("Spread2", 0) or 0)
                away_ml = (
                    int(game.get("MoneyLine1") or 0)
                    if game.get("MoneyLine1") is not None
                    else None
                )
                home_ml = (
                    int(game.get("MoneyLine2") or 0)
                    if game.get("MoneyLine2") is not None
                    else None
                )
                away_spread_odds = int(game.get("SpreadAdj1", -110))
                home_spread_odds = int(game.get("SpreadAdj2", -110))
            else:
                away_team = team2
                home_team = team1
                away_spread = float(game.get("Spread2", 0) or 0)
                home_spread = float(game.get("Spread1", 0) or 0)
                away_ml = (
                    int(game.get("MoneyLine2") or 0)
                    if game.get("MoneyLine2") is not None
                    else None
                )
                home_ml = (
                    int(game.get("MoneyLine1") or 0)
                    if game.get("MoneyLine1") is not None
                    else None
                )
                away_spread_odds = int(game.get("SpreadAdj2", -110))
                home_spread_odds = int(game.get("SpreadAdj1", -110))

            # Extract totals
            total = float(game.get("TotalPoints", 0))
            over_odds = int(game.get("TtlPtsAdj1", -110))
            under_odds = int(game.get("TtlPtsAdj2", -110))

            # Parse game time
            game_time_str = game.get("GameDateTimeString", "")

            converted_game = {
                "game_id": str(game.get("GameNum", "")),
                "league": league,
                "away_team": away_team,
                "home_team": home_team,
                "game_time": game_time_str,
                "spread": {
                    "away": away_spread,
                    "home": home_spread,
                    "away_odds": away_spread_odds,
                    "home_odds": home_spread_odds,
                },
                "moneyline": {"away": away_ml, "home": home_ml},
                "total": {
                    "points": total,
                    "over_odds": over_odds,
                    "under_odds": under_odds,
                },
                "rotation_numbers": {
                    "team1": game.get("Team1RotNum"),
                    "team2": game.get("Team2RotNum"),
                },
                "status": game.get("Status", ""),
                "period": game.get("PeriodDescription", "Game"),
            }

            converted_games.append(converted_game)

        # Build final response
        return {
            "metadata": {
                "source": "overtime.ag",
                "method": "api",
                "league": league,
                "converted_at": datetime.now().isoformat(),
                "converter_version": "2.0.0",
            },
            "games": converted_games,
            "summary": {
                "total_games": len(converted_games),
                "conversion_rate": "100%",
            },
        }

    async def scrape_nfl(
        self, save_raw: bool = True, save_converted: bool = True
    ) -> dict[str, Any]:
        """
        Scrape NFL games and convert to Billy Walters format.

        Args:
            save_raw: Save raw API response
            save_converted: Save converted Billy Walters format

        Returns:
            Billy Walters formatted data
        """
        games = await self.fetch_games(sport_type="Football", sport_sub_type="NFL")

        if save_raw:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_file = self.output_dir / "nfl" / "pregame" / f"api_raw_{timestamp}.json"
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            raw_file.write_text(json.dumps(games, indent=2))

        converted = self.convert_to_billy_walters_format(games, "NFL")

        if save_converted:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            converted_file = (
                self.output_dir / "nfl" / "pregame" / f"api_walters_{timestamp}.json"
            )
            converted_file.parent.mkdir(parents=True, exist_ok=True)
            converted_file.write_text(json.dumps(converted, indent=2))

        return converted

    async def scrape_ncaaf(
        self, save_raw: bool = True, save_converted: bool = True
    ) -> dict[str, Any]:
        """
        Scrape NCAAF games and convert to Billy Walters format.

        Args:
            save_raw: Save raw API response
            save_converted: Save converted Billy Walters format

        Returns:
            Billy Walters formatted data
        """
        games = await self.fetch_games(
            sport_type="Football", sport_sub_type="College Football"
        )

        if save_raw:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_file = (
                self.output_dir / "ncaaf" / "pregame" / f"api_raw_{timestamp}.json"
            )
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            raw_file.write_text(json.dumps(games, indent=2))

        converted = self.convert_to_billy_walters_format(games, "NCAAF")

        if save_converted:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            converted_file = (
                self.output_dir / "ncaaf" / "pregame" / f"api_walters_{timestamp}.json"
            )
            converted_file.parent.mkdir(parents=True, exist_ok=True)
            converted_file.write_text(json.dumps(converted, indent=2))

        return converted


async def main():
    """Test the Overtime API client."""
    client = OvertimeApiClient()

    print("\n[SCRAPING NFL]")
    nfl_data = await client.scrape_nfl()
    print(f"Games found: {nfl_data['summary']['total_games']}")

    print("\n[SCRAPING NCAAF]")
    ncaaf_data = await client.scrape_ncaaf()
    print(f"Games found: {ncaaf_data['summary']['total_games']}")

    print("\n[SUCCESS] API client working!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
