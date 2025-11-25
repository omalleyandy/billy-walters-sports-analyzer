"""
Action Network Web Scraper Client

Fetches NFL and NCAAF odds data from Action Network using Playwright.
Implements rate limiting, retry logic, and data validation with multi-selector
fallback support for resilience against CSS class changes.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from playwright.async_api import Browser, Page, async_playwright

logger = logging.getLogger(__name__)


class ActionNetworkClient:
    """Client for scraping odds data from Action Network."""

    BASE_URL = "https://www.actionnetwork.com"
    LOGIN_URL = f"{BASE_URL}/login"

    @staticmethod
    def _init_selectors() -> dict[str, list[str]]:
        """Load multi-selector config from JSON file with fallbacks."""
        config_file = Path(__file__).parent / "action_network_selectors.json"

        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    logger.debug(f"Loaded config from {config_file.name}")
                    return config.get("selectors", {})
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config: {e}. Using fallbacks.")

        # Fallback selectors if config not available
        return {
            "login_button": [
                (".user-component__button.user-component__login.css-1wwjzac.epb8che0"),
                ".user-component__button.user-component__login",
                "button[class*='user-component__login']",
            ],
            "username_input": [
                'input[placeholder="Email"]',
                "input[type='email']",
                "input[name='email']",
            ],
            "password_input": [
                'input[placeholder="Password"]',
                "input[type='password']",
            ],
            "submit_button": [
                'button[type="submit"]',
                "button:has-text('Sign In')",
            ],
            "sport_nfl": [
                (
                    "//div[@class='css-p3ig27 emv4lho0']//div//"
                    "span[@class='nav-link__title']"
                    "[normalize-space()='NFL']"
                ),
                ("//span[@class='nav-link__title'][normalize-space()='NFL']"),
                "a[href*='/nfl']:has-text('NFL')",
            ],
            "sport_ncaaf": [
                (
                    "//div[@class='css-p3ig27 emv4lho0']//div//"
                    "span[@class='nav-link__title']"
                    "[normalize-space()='NCAAF']"
                ),
                ("//span[@class='nav-link__title'][normalize-space()='NCAAF']"),
                "a[href*='/college-football']:has-text('NCAAF')",
            ],
            "odds_tab": [
                ("//a[contains(@class,'subNav__navLink')][normalize-space()='Odds']"),
                "a[class*='subNav__navLink']:has-text('Odds')",
            ],
        }

    SELECTORS = _init_selectors()

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        headless: bool = True,
        rate_limit_delay: float = 2.0,
    ):
        """
        Initialize Action Network client.

        Args:
            username: Action Network username (defaults to ACTION_USERNAME env var)
            password: Action Network password (defaults to ACTION_PASSWORD env var)
            headless: Run browser in headless mode
            rate_limit_delay: Delay between requests in seconds
        """
        self.username = username or os.getenv("ACTION_USERNAME")
        self.password = password or os.getenv("ACTION_PASSWORD")
        self.headless = headless
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time: float = 0.0
        self._browser: Browser | None = None
        self._page: Page | None = None

        if not self.username or not self.password:
            raise ValueError(
                "ACTION_USERNAME and ACTION_PASSWORD must be set "
                "either as arguments or environment variables"
            )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize browser and login to Action Network."""
        logger.info("Initializing Playwright browser")
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()

        # Login to Action Network
        await self._login()
        logger.info("Successfully logged in to Action Network")

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
        logger.info("Closed Action Network client")

    async def _login(self) -> None:
        """Login to Action Network using provided credentials."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call connect() first.")

        page = self._page

        logger.info("Navigating to login page")
        await page.goto(self.LOGIN_URL, wait_until="networkidle")

        # Click login button to reveal login form (use fallback)
        try:
            await self._try_selectors(
                page,
                self.SELECTORS["login_button"],
                action="click",
                timeout=5000,
            )
        except Exception:
            # Login form may already be visible
            logger.debug("Login button not found, form may already be visible")

        # Fill in credentials (use fallback selectors)
        logger.info("Entering credentials")
        username_selector = self.SELECTORS.get("username_input", [])
        password_selector = self.SELECTORS.get("password_input", [])

        if username_selector and password_selector:
            try:
                # Try to fill username using fallback
                for selector in username_selector:
                    try:
                        if selector.startswith("//"):
                            selector = f"xpath={selector}"
                        await page.fill(selector, self.username)
                        break
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"Could not fill username: {e}")

            try:
                # Try to fill password using fallback
                for selector in password_selector:
                    try:
                        if selector.startswith("//"):
                            selector = f"xpath={selector}"
                        await page.fill(selector, self.password)
                        break
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"Could not fill password: {e}")

        # Submit login form (use fallback)
        try:
            await self._try_selectors(
                page,
                self.SELECTORS["submit_button"],
                action="click",
                timeout=5000,
            )
        except Exception as e:
            logger.warning(f"Could not submit login form: {e}")

        # Wait for navigation to complete
        await page.wait_for_load_state("networkidle")

        # Verify login success by checking for absence of login form
        # (more reliable than waiting for specific elements)
        try:
            # Check if login form is gone (most reliable success indicator)
            login_form = await page.query_selector('input[placeholder="Email"]')
            if login_form is None:
                logger.info("Login successful (form disappeared)")
                return
        except Exception:
            pass

        # Try alternative success indicators
        success_selectors = [
            'a[href*="/account"]',
            'a[href*="/profile"]',
            'nav[class*="user"]',
            "div[class*='user-menu']",
        ]

        for selector in success_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"Login successful (found: {selector})")
                    return
            except Exception:
                continue

        # If we got here, login may have failed
        raise RuntimeError("Login failed: Could not verify login success")

    async def _try_selectors(
        self,
        page: Page,
        selector_list: list[str],
        action: str = "wait",
        timeout: int = 5000,
    ) -> Any:
        """
        Try multiple selectors until one succeeds (multi-selector fallback).

        Args:
            page: Playwright page object
            selector_list: List of CSS/XPath selectors to try in order
            action: Action to perform ('wait', 'click', 'fill', 'query')
            timeout: Timeout in milliseconds

        Returns:
            Element handle or result depending on action

        Raises:
            RuntimeError: If all selectors fail
        """
        last_error = None

        for i, selector in enumerate(selector_list):
            try:
                # Convert XPath selectors to Playwright format
                if selector.startswith("//"):
                    selector = f"xpath={selector}"

                if action == "wait":
                    element = await page.wait_for_selector(selector, timeout=timeout)
                elif action == "click":
                    await page.click(selector, timeout=timeout)
                    element = True
                elif action == "query":
                    element = await page.query_selector(selector)
                elif action == "query_all":
                    element = await page.query_selector_all(selector)
                else:
                    raise ValueError(f"Unknown action: {action}")

                # Log if fallback was used
                if i > 0:
                    logger.warning(
                        f"Primary selector failed, used fallback "
                        f"#{i + 1}/{len(selector_list)}: {selector}"
                    )
                else:
                    logger.debug(f"Selector matched (attempt 1): {selector}")

                return element

            except Exception as e:
                last_error = e
                logger.debug(
                    f"Selector attempt {i + 1}/{len(selector_list)} failed: {selector}"
                )
                if i < len(selector_list) - 1:
                    continue

        # All selectors failed
        raise RuntimeError(
            f"All {len(selector_list)} selectors failed for action '{action}': "
            f"{last_error}"
        ) from last_error

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = asyncio.get_event_loop().time()

    async def fetch_odds(
        self,
        league: Literal["NFL", "NCAAF"],
        max_retries: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Fetch odds data for specified league.

        Args:
            league: League to fetch odds for ("NFL" or "NCAAF")
            max_retries: Maximum number of retry attempts

        Returns:
            List of game odds dictionaries

        Raises:
            RuntimeError: If browser not initialized or fetch fails
        """
        if not self._page:
            raise RuntimeError("Browser not initialized. Call connect() first.")

        await self._rate_limit()

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Fetching {league} odds (attempt {attempt + 1}/{max_retries})"
                )
                return await self._fetch_odds_impl(league)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"Failed to fetch {league} odds after {max_retries} attempts"
                    ) from e

        return []  # Should never reach here

    async def _fetch_odds_impl(
        self, league: Literal["NFL", "NCAAF"]
    ) -> list[dict[str, Any]]:
        """Implementation of odds fetching."""
        if not self._page:
            raise RuntimeError("Browser not initialized")

        page = self._page

        # Navigate to league (use fallback selectors)
        sport_selector = (
            self.SELECTORS["sport_nfl"]
            if league == "NFL"
            else self.SELECTORS["sport_ncaaf"]
        )
        logger.debug(f"Clicking {league} navigation")
        await self._try_selectors(page, sport_selector, action="click", timeout=10000)
        await page.wait_for_load_state("networkidle")

        # Navigate to odds page (use fallback selectors)
        logger.debug("Clicking Odds tab")
        await self._try_selectors(
            page, self.SELECTORS["odds_tab"], action="click", timeout=10000
        )
        await page.wait_for_load_state("networkidle")

        # Extract odds data from table
        logger.debug("Extracting odds data from page")
        games = await self._extract_odds_from_page(page, league)

        logger.info(f"Successfully extracted {len(games)} games for {league}")
        return games

    async def _extract_odds_from_page(
        self, page: Page, league: Literal["NFL", "NCAAF"]
    ) -> list[dict[str, Any]]:
        """
        Extract odds data from the odds table.

        Args:
            page: Playwright page object
            league: League being scraped

        Returns:
            List of game dictionaries with odds data
        """
        games: list[dict[str, Any]] = []

        # Wait for odds table to load
        await page.wait_for_selector("table.odds-table", timeout=10000)

        # Extract game rows
        game_rows = await page.query_selector_all("tr.game-row")

        for row in game_rows:
            try:
                game_data = await self._extract_game_row(row, league)
                if game_data:
                    games.append(game_data)
            except Exception as e:
                logger.warning(f"Failed to extract game row: {e}")
                continue

        return games

    async def _extract_game_row(
        self, row, league: Literal["NFL", "NCAAF"]
    ) -> dict[str, Any] | None:
        """
        Extract odds data from a single game row.

        Args:
            row: Playwright element handle for game row
            league: League being scraped

        Returns:
            Game dictionary or None if extraction fails
        """
        try:
            # Extract team names
            teams = await row.query_selector_all(".team-name")
            if len(teams) < 2:
                return None

            away_team = await teams[0].inner_text()
            home_team = await teams[1].inner_text()

            # Extract game date/time
            game_time_elem = await row.query_selector(".game-time")
            game_time_text = await game_time_elem.inner_text() if game_time_elem else ""

            # Extract rotation numbers
            rotation_elems = await row.query_selector_all(".rotation-number")
            away_rotation = (
                await rotation_elems[0].inner_text() if len(rotation_elems) > 0 else ""
            )
            home_rotation = (
                await rotation_elems[1].inner_text() if len(rotation_elems) > 1 else ""
            )

            # Extract best odds (marked with bookmark icon)
            best_spread_elem = await row.query_selector(".spread-cell .best-odds")
            best_total_elem = await row.query_selector(".total-cell .best-odds")
            best_ml_elem = await row.query_selector(".moneyline-cell .best-odds")

            # Extract spread data
            spread_value = None
            spread_odds = None
            if best_spread_elem:
                spread_text = await best_spread_elem.inner_text()
                spread_parts = spread_text.strip().split()
                if len(spread_parts) >= 2:
                    spread_value = float(spread_parts[0])
                    spread_odds = int(spread_parts[1])

            # Extract total (over/under) data
            total_value = None
            total_odds = None
            if best_total_elem:
                total_text = await best_total_elem.inner_text()
                total_parts = total_text.strip().split()
                if len(total_parts) >= 2:
                    # Format: "O 47.5 -110" or "U 47.5 -110"
                    total_value = float(total_parts[1])
                    total_odds = int(total_parts[2])

            # Extract moneyline
            moneyline_home = None
            moneyline_away = None
            if best_ml_elem:
                ml_text = await best_ml_elem.inner_text()
                ml_parts = ml_text.strip().split()
                if len(ml_parts) >= 2:
                    moneyline_away = int(ml_parts[0])
                    moneyline_home = int(ml_parts[1])

            # Extract sportsbook name
            sportsbook_elem = await row.query_selector(".sportsbook-name")
            sportsbook = await sportsbook_elem.inner_text() if sportsbook_elem else None

            # Build game data dictionary
            game_data: dict[str, Any] = {
                "league": league,
                "away_team": away_team.strip(),
                "home_team": home_team.strip(),
                "game_time": game_time_text.strip(),
                "away_rotation": away_rotation.strip(),
                "home_rotation": home_rotation.strip(),
                "spread": spread_value,
                "spread_odds": spread_odds,
                "over_under": total_value,
                "total_odds": total_odds,
                "moneyline_home": moneyline_home,
                "moneyline_away": moneyline_away,
                "sportsbook": sportsbook,
                "timestamp": datetime.now().isoformat(),
                "source": "action_network",
            }

            return game_data

        except Exception as e:
            logger.warning(f"Error extracting game row: {e}", exc_info=True)
            return None

    async def fetch_nfl_odds(self, max_retries: int = 3) -> list[dict[str, Any]]:
        """Convenience method to fetch NFL odds."""
        return await self.fetch_odds("NFL", max_retries=max_retries)

    async def fetch_ncaaf_odds(self, max_retries: int = 3) -> list[dict[str, Any]]:
        """Convenience method to fetch NCAAF odds."""
        return await self.fetch_odds("NCAAF", max_retries=max_retries)


# Example usage
async def main():
    """Example usage of ActionNetworkClient."""
    async with ActionNetworkClient(headless=False) as client:
        # Fetch NFL odds
        nfl_odds = await client.fetch_nfl_odds()
        print(f"Fetched {len(nfl_odds)} NFL games")
        for game in nfl_odds[:3]:  # Print first 3 games
            print(f"\n{game['away_team']} @ {game['home_team']}")
            print(f"  Spread: {game['spread']} ({game['spread_odds']})")
            print(f"  O/U: {game['over_under']} ({game['total_odds']})")
            print(f"  ML: {game['moneyline_away']} / {game['moneyline_home']}")

        # Fetch NCAAF odds
        ncaaf_odds = await client.fetch_ncaaf_odds()
        print(f"\nFetched {len(ncaaf_odds)} NCAAF games")


if __name__ == "__main__":
    asyncio.run(main())
