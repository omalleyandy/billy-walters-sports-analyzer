#!/usr/bin/env python3
"""
ESPN NCAAF Team Information Scraper
Dynamic scraper for all NCAA FBS teams - injuries, stats, news, schedule

Usage:
    scraper = ESPNNcaafTeamScraper()

    # Single team
    data = scraper.scrape_team("Troy", team_id=2653)

    # Multiple teams
    data = scraper.scrape_matchup("Troy", "Old Dominion", troy_id=2653, odu_id=295)
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class ESPNNcaafTeamScraper:
    """Scraper for ESPN NCAAF team pages - injuries, stats, news, schedule"""

    def __init__(self, output_dir: str = "output/ncaaf/teams"):
        """
        Initialize scraper

        Args:
            output_dir: Directory to save scraped data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://www.espn.com/college-football/team"

    def build_team_url(self, team_id: int, page: str = "home") -> str:
        """
        Build ESPN team URL

        Args:
            team_id: ESPN team ID (e.g., 2653 for Troy)
            page: Page type ('home', 'injuries', 'stats', 'schedule', 'roster')

        Returns:
            Complete URL
        """
        page_map = {
            "home": f"{self.base_url}/_/id/{team_id}",
            "injuries": f"{self.base_url}/injuries/_/id/{team_id}",
            "stats": f"{self.base_url}/stats/_/id/{team_id}",
            "schedule": f"{self.base_url}/schedule/_/id/{team_id}",
            "roster": f"{self.base_url}/roster/_/id/{team_id}",
        }

        return page_map.get(page, page_map["home"])

    async def scrape_team_page(self, url: str) -> str:
        """
        Scrape a single page using Playwright

        Args:
            url: URL to scrape

        Returns:
            Page text content
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for dynamic content
                content = await page.inner_text("body")
                return content
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                return ""
            finally:
                await browser.close()

    def parse_injury_page(self, content: str) -> List[Dict]:
        """
        Parse injury report content

        Args:
            content: Page text content

        Returns:
            List of injury dictionaries
        """
        injuries = []

        if "No Data Available" in content or not content:
            logger.info("No injuries reported")
            return injuries

        # Parse injury data from text
        # Format typically: Name, Position, Status, Injury Type
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        # Look for injury patterns
        # This is simplified - would need more robust parsing for production
        for i, line in enumerate(lines):
            if any(status in line for status in ["Out", "Questionable", "Doubtful"]):
                # Try to find associated player name and position
                injury_entry = {
                    "player": lines[i - 2] if i >= 2 else "Unknown",
                    "position": lines[i - 1] if i >= 1 else "Unknown",
                    "status": line,
                    "injury_type": lines[i + 1] if i < len(lines) - 1 else "Unknown",
                }
                injuries.append(injury_entry)

        return injuries

    def parse_team_stats(self, content: str) -> Dict:
        """
        Parse team statistics from content

        Args:
            content: Page text content

        Returns:
            Dictionary of team stats
        """
        stats = {}
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        # Look for key stats
        for i, line in enumerate(lines):
            if "per game" in line.lower():
                # Try to extract stat name and value
                if i > 0:
                    stat_value = line
                    stat_name = lines[i - 1]
                    stats[stat_name] = stat_value

        return stats

    async def scrape_team(
        self, team_name: str, team_id: int, include_injuries: bool = True
    ) -> Dict:
        """
        Scrape complete team information

        Args:
            team_name: Team name (e.g., "Troy")
            team_id: ESPN team ID
            include_injuries: Whether to fetch injury data

        Returns:
            Complete team data dictionary
        """
        logger.info(f"Scraping {team_name} (ID: {team_id})")

        team_data = {
            "team_name": team_name,
            "team_id": team_id,
            "scraped_at": datetime.now().isoformat(),
        }

        # Scrape main page
        logger.info(f"Fetching {team_name} main page...")
        home_url = self.build_team_url(team_id, "home")
        home_content = await self.scrape_team_page(home_url)

        # Extract record and standing from home page
        if home_content:
            lines = home_content.split("\n")
            for line in lines:
                if "-" in line and any(
                    c.isdigit() for c in line
                ):  # Look for record pattern
                    team_data["record"] = line.strip()
                    break

        # Scrape injuries if requested
        if include_injuries:
            logger.info(f"Fetching {team_name} injury report...")
            injury_url = self.build_team_url(team_id, "injuries")
            injury_content = await self.scrape_team_page(injury_url)
            team_data["injuries"] = self.parse_injury_page(injury_content)

        return team_data

    async def scrape_matchup(
        self,
        away_team: str,
        home_team: str,
        away_id: int,
        home_id: int,
        save: bool = True,
    ) -> Dict:
        """
        Scrape both teams for a matchup

        Args:
            away_team: Away team name
            home_team: Home team name
            away_id: ESPN ID for away team
            home_id: ESPN ID for home team
            save: Whether to save to file

        Returns:
            Matchup data dictionary
        """
        logger.info("=" * 70)
        logger.info(f"SCRAPING MATCHUP: {away_team} @ {home_team}")
        logger.info("=" * 70)

        matchup_data = {
            "matchup": f"{away_team} @ {home_team}",
            "scraped_at": datetime.now().isoformat(),
            "away_team": await self.scrape_team(away_team, away_id),
            "home_team": await self.scrape_team(home_team, home_id),
        }

        # Save if requested
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = (
                f"{away_team.lower().replace(' ', '_')}_"
                f"{home_team.lower().replace(' ', '_')}_{timestamp}.json"
            )
            filepath = self.output_dir / filename

            with open(filepath, "w") as f:
                json.dump(matchup_data, f, indent=2)

            logger.info(f"Saved matchup data to {filepath}")

        return matchup_data


async def main():
    """Demo: Scrape Troy @ Old Dominion matchup"""
    scraper = ESPNNcaafTeamScraper()

    # Scrape tonight's matchup
    matchup = await scraper.scrape_matchup(
        away_team="Troy",
        home_team="Old Dominion",
        away_id=2653,
        home_id=295,
        save=True,
    )

    # Display summary
    print()
    print("=" * 70)
    print("MATCHUP SUMMARY")
    print("=" * 70)
    print(f"\n{matchup['matchup']}")
    print(f"Scraped: {matchup['scraped_at']}")
    print()

    # Away team
    away = matchup["away_team"]
    print(f"AWAY: {away['team_name']}")
    print(f"  Record: {away.get('record', 'N/A')}")
    print(f"  Injuries: {len(away.get('injuries', []))} reported")
    if away.get("injuries"):
        for inj in away["injuries"]:
            print(f"    - {inj['player']} ({inj['position']}): {inj['status']}")
    else:
        print("    [OK] No injuries reported")
    print()

    # Home team
    home = matchup["home_team"]
    print(f"HOME: {home['team_name']}")
    print(f"  Record: {home.get('record', 'N/A')}")
    print(f"  Injuries: {len(home.get('injuries', []))} reported")
    if home.get("injuries"):
        for inj in home["injuries"]:
            print(f"    - {inj['player']} ({inj['position']}): {inj['status']}")
    else:
        print("    [OK] No injuries reported")

    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
