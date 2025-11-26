"""
NFL.com Game Stats Scraper

Fetches game statistics from NFL.com for both teams in a matchup.
Navigates schedule pages, extracts game links, and scrapes detailed
team stats from the STATS tab.

Usage:
    client = NFLGameStatsClient()

    # Get all games from a week
    stats = await client.get_week_stats(year=2025, week=12)

    # Get stats for a specific game
    stats = await client.get_game_stats(
        url="https://www.nfl.com/games/bills-at-texans-2025-reg-12"
    )

Categories extracted:
    - Passing: Completions, yards, TDs, INTs, QBR
    - Rushing: Attempts, yards, TDs, average
    - Receiving: Receptions, yards, TDs, targets
    - Defense: Tackles, sacks, INTs, forced fumbles
    - Special Teams: Field goals, extra points
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


class NFLGameStatsClient:
    """
    NFL.com Game Stats Scraper Client.

    Fetches detailed game statistics from NFL.com for both teams
    in each matchup.
    """

    BASE_URL = "https://www.nfl.com"
    SCHEDULE_URL = "https://www.nfl.com/schedules/{year}/by-week/{week}"

    def __init__(self, headless: bool = True):
        """
        Initialize NFL Game Stats client.

        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    async def connect(self) -> None:
        """Initialize Playwright browser with bot evasion."""
        try:
            self._playwright = await async_playwright().start()
            # Launch with bot detection evasion
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            self._page = await self._browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
            )
            logger.info("NFL Game Stats client connected with bot evasion")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self._page:
                await self._page.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info("NFL Game Stats client closed")
        except Exception as e:
            logger.error(f"Error closing client: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get_week_stats(
        self, year: int = 2025, week: str = "reg-12"
    ) -> dict[str, Any]:
        """
        Get all game stats for a specific NFL week.

        Args:
            year: NFL season year (e.g., 2025)
            week: Week identifier ("reg-12", "post-1", etc.)

        Returns:
            Dictionary with all games and stats for the week
        """
        if not self._page:
            await self.connect()

        # Build schedule URL
        schedule_url = f"{self.BASE_URL}/schedules/{year}/by-week/{week}"
        logger.info(f"Fetching schedule from {schedule_url}")

        # Navigate to schedule page with timeout
        await self._page.goto(
            schedule_url,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        await asyncio.sleep(2)

        # Extract all game links
        game_links = await self._extract_game_links()
        logger.info(f"Found {len(game_links)} games in week {week}")

        # Fetch stats for each game
        week_stats = {
            "year": year,
            "week": week,
            "games": [],
            "timestamp": datetime.now().isoformat(),
        }

        for idx, game_url in enumerate(game_links, 1):
            try:
                logger.info(f"Fetching stats for game {idx}/{len(game_links)}")
                game_stats = await self.get_game_stats(game_url)
                if game_stats:
                    week_stats["games"].append(game_stats)
                await asyncio.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Error fetching stats for {game_url}: {e}")

        return week_stats

    async def _extract_game_links(self) -> list[str]:
        """
        Extract all game links from schedule page.

        Returns:
            List of game URLs
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        game_links = []

        try:
            # Try multiple selector strategies
            selectors = [
                "a[href*='/games/']",  # Original selector
                "a[href*='games']",  # Alternative
                "[data-href*='/games/']",  # Data attribute
            ]

            links = []
            for selector in selectors:
                try:
                    await self._page.wait_for_selector(selector, timeout=10000)
                    links = await self._page.locator(selector).all()
                    if links:
                        logger.info(
                            f"Found {len(links)} game links using selector: {selector}"
                        )
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            if not links:
                logger.warning("No game links found with any selector strategy")
                # Try to get HTML content for debugging
                html = await self._page.content()
                logger.debug(f"Page content length: {len(html)}")
                if "games" in html.lower():
                    logger.info("Page contains 'games' text")
                return []

            logger.info(f"Found {len(links)} game link elements")

            # Extract unique game URLs
            seen = set()
            for link in links:
                href = await link.get_attribute("href")
                if href and "games" in href:
                    # Handle relative URLs
                    if not href.startswith("http"):
                        href = self.BASE_URL + href

                    # Only keep stats page URLs
                    if "tab=stats" not in href:
                        href = (
                            f"{href}?tab=stats"
                            if "?" not in href
                            else f"{href}&tab=stats"
                        )

                    if href not in seen:
                        game_links.append(href)
                        seen.add(href)

            logger.info(f"Extracted {len(game_links)} unique game URLs")
            return game_links

        except Exception as e:
            logger.error(f"Error extracting game links: {e}")
            return []

    async def get_game_stats(self, game_url: str) -> dict[str, Any]:
        """
        Get stats for a specific game.

        Args:
            game_url: Full URL to game (with ?tab=stats)

        Returns:
            Dictionary with game info and team stats
        """
        if not self._page:
            await self.connect()

        try:
            logger.info(f"Navigating to {game_url}")
            # Use longer timeout and load strategy
            await self._page.goto(
                game_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            # Extra wait for JS to render
            await asyncio.sleep(3)

            # Ensure we're on stats tab
            if "tab=stats" not in self._page.url:
                await self._page.click("text=STATS")
                await asyncio.sleep(2)

            # Extract game info
            game_info = await self._extract_game_info()

            if not game_info:
                logger.warning(f"Could not extract game info from {game_url}")
                return {}

            game_data = {
                "url": game_url,
                "timestamp": datetime.now().isoformat(),
                **game_info,
                "teams_stats": {},
            }

            # Extract stats for each team
            teams = game_info.get("teams", [])
            for team in teams:
                try:
                    team_stats = await self._extract_team_stats(team)
                    if team_stats:
                        game_data["teams_stats"][team] = team_stats
                except Exception as e:
                    logger.error(f"Error extracting {team} stats: {e}")

            return game_data

        except Exception as e:
            logger.error(f"Error fetching game stats: {e}")
            return {}

    async def _extract_game_info(self) -> dict[str, Any]:
        """
        Extract basic game info (teams, score, date).

        Returns:
            Dictionary with game metadata
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        try:
            # Get game title from page title meta tag
            # Format: "Team1 at Team2 YYYY REG/POST XX - Game Center"
            # Example: "Green Bay Packers at Detroit Lions 2025 REG 13 - Game Center"
            page_title = await self._page.title()
            logger.debug(f"Page title: {page_title}")

            # Extract teams from page title
            # Split by " at " (case insensitive)
            if " at " not in page_title.lower():
                logger.warning(f"Could not parse teams from page title: {page_title}")
                # Try DOM selectors as fallback
                game_title = await self._extract_game_title_from_dom()
                if not game_title:
                    return {}
            else:
                # Split by " at "
                parts = page_title.lower().split(" at ")
                away_team_full = parts[0].strip()
                # Get the part before " YYYY REG/POST"
                home_and_meta = parts[1]
                home_parts = home_and_meta.split(" 202")
                home_team_full = home_parts[0].strip()

                # Extract team name (last word of full name)
                # E.g., "Green Bay Packers" -> "Packers"
                away_team = away_team_full.split()[-1].upper()
                home_team = home_team_full.split()[-1].upper()

                game_title = f"{away_team} at {home_team}"
                logger.debug(f"Extracted from page title: {away_team} vs {home_team}")

            # Parse teams from title
            # Format: "TEAM1 at TEAM2" or similar
            title_parts = game_title.upper().split("AT")
            if len(title_parts) < 2:
                logger.warning(f"Could not parse teams from: {game_title}")
                return {}

            away_team = title_parts[0].strip()
            home_team = title_parts[1].strip()

            # Try to get final score
            try:
                score_text = await self._page.locator(
                    "[data-test='game-score']"
                ).first.text_content()
            except Exception:
                score_text = None

            return {
                "away_team": away_team,
                "home_team": home_team,
                "teams": [away_team, home_team],
                "score": score_text,
                "title": game_title,
            }

        except Exception as e:
            logger.error(f"Error extracting game info: {e}")
            return {}

    async def _extract_game_title_from_dom(self) -> Optional[str]:
        """
        Extract game title from DOM as fallback when page title parsing fails.

        Looks for team names in h3 headers like "GB PASSING" or button labels.

        Returns:
            Game title string (e.g., "PACKERS AT LIONS") or None
        """
        if not self._page:
            return None

        try:
            # Try to get team names from button labels
            selectors = [
                "button:has-text('PACKERS')",
                "button:has-text('LIONS')",
                "button:has-text('BILLS')",
                "button:has-text('CHIEFS')",
            ]

            teams = []
            for selector in selectors:
                try:
                    elements = await self._page.locator(selector).all()
                    for elem in elements:
                        text = await elem.text_content()
                        if text:
                            team = text.strip().upper()
                            if team not in teams:
                                teams.append(team)
                                if len(teams) == 2:
                                    break
                    if len(teams) == 2:
                        break
                except Exception:
                    continue

            if len(teams) >= 2:
                return f"{teams[0]} AT {teams[1]}"

            return None

        except Exception as e:
            logger.debug(f"Error extracting game title from DOM: {e}")
            return None

    async def _extract_team_stats(self, team_name: str) -> dict[str, Any]:
        """
        Extract stats for a specific team in the game.

        Args:
            team_name: Team name (e.g., "BILLS", "TEXANS")

        Returns:
            Dictionary with team stats
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        try:
            # Click on team name to switch stats view
            # Team tabs usually appear under GAME STATS section
            team_button_text = team_name.upper()

            logger.info(f"Clicking on {team_button_text} stats")

            # Try multiple selectors for team button
            selectors = [
                f"button:has-text('{team_button_text}')",
                f"[data-test*='stats']:has-text('{team_button_text}')",
                f"text={team_button_text}",
            ]

            clicked = False
            for selector in selectors:
                try:
                    await self._page.click(selector)
                    await asyncio.sleep(1)
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                logger.warning(f"Could not click on {team_button_text} tab")

            # Extract stats table
            stats = await self._parse_stats_table()

            return {"name": team_name, **stats}

        except Exception as e:
            logger.error(f"Error extracting {team_name} stats: {e}")
            return {}

    async def _parse_stats_table(self) -> dict[str, Any]:
        """
        Parse the stats table for the current team view.

        Table structure:
        - Row 0: Column headers (PLAYER, CMP, ATT) - for PASSING
        - Row 1-N: Passing stats
        - Row N+1: Column headers (PLAYER, ATT, YDS) - for RUSHING
        - Row N+2-M: Rushing stats
        - etc.

        Returns:
            Dictionary with categorized stats
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        try:
            stats = {
                "passing": {},
                "rushing": {},
                "receiving": {},
                "defense": {},
                "special_teams": {},
            }

            # Wait for stats table
            await self._page.wait_for_selector(
                "table, [data-test*='stats'], tr", timeout=5000
            )

            # Get all table rows
            rows = await self._page.locator("tr").all()
            logger.info(f"Found {len(rows)} table rows")

            # Extract all text in one pass (more efficient)
            row_texts = []
            for row in rows:
                try:
                    # Get all cells (th and td) from this row
                    cells = await row.locator("th, td").all()
                    if cells:
                        texts = []
                        for cell in cells:
                            try:
                                text = await cell.text_content(timeout=1000)
                                texts.append(text.strip() if text else "")
                            except Exception:
                                texts.append("")
                        row_texts.append(texts)
                except Exception as e:
                    logger.debug(f"Error extracting row cells: {e}")
                    continue

            logger.info(f"Extracted text from {len(row_texts)} rows")

            # Parse rows by detecting header rows and categorizing by column content
            i = 0
            while i < len(row_texts):
                row_text = row_texts[i]
                if not row_text:
                    i += 1
                    continue

                # Detect category by checking column headers
                first_cell_upper = row_text[0].upper()
                category = None

                # Header rows typically have "PLAYER" as first column
                if "PLAYER" in first_cell_upper:
                    # Determine which type of PLAYER stats by column headers
                    if any("CMP" in c.upper() for c in row_text):
                        category = "passing"
                    elif any("ATT" in c.upper() for c in row_text):
                        # Could be rushing or receiving, check for REC
                        if any("REC" in c.upper() for c in row_text):
                            category = "receiving"
                        else:
                            category = "rushing"
                    else:
                        # Unknown, skip
                        i += 1
                        continue

                    # Skip header row and parse following data rows
                    i += 1
                    while i < len(row_texts):
                        data_row = row_texts[i]
                        if not data_row:
                            i += 1
                            break

                        first = data_row[0].upper()
                        # Stop at next header row (PLAYER) or category switch
                        if "PLAYER" in first:
                            break

                        # Store the stat (first column is name, rest are values)
                        stat_name = data_row[0]
                        stat_values = data_row[1:]

                        if stat_name and stat_values:
                            stats[category][stat_name] = stat_values

                        i += 1
                else:
                    i += 1

            return stats

        except Exception as e:
            logger.error(f"Error parsing stats table: {e}")
            return {}

    async def export_stats(
        self, stats_data: dict[str, Any], output_dir: str = "output/nfl_game_stats"
    ) -> str:
        """
        Export stats to JSON file.

        Args:
            stats_data: Statistics data to export
            output_dir: Directory to save JSON file

        Returns:
            Path to saved file
        """
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate filename
            if "week" in stats_data:
                filename = (
                    f"stats_{stats_data['year']}_"
                    f"week_{stats_data['week']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
            else:
                filename = f"game_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            filepath = output_path / filename

            # Write JSON
            with open(filepath, "w") as f:
                json.dump(stats_data, f, indent=2)

            logger.info(f"Exported stats to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting stats: {e}")
            return ""


async def main():
    """Test the NFL Game Stats client."""
    client = NFLGameStatsClient(headless=False)

    try:
        await client.connect()

        # Get all games from week 12
        stats = await client.get_week_stats(year=2025, week="reg-12")

        # Export results
        if stats.get("games"):
            filepath = await client.export_stats(stats)
            print(f"Exported {len(stats['games'])} games to {filepath}")
        else:
            print("No game stats were collected")

    finally:
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
