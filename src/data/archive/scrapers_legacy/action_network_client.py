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
        """Login to Action Network using provided credentials.

        Uses Playwright locators (get_by_role, get_by_placeholder) which are
        more robust than CSS selectors against UI changes.
        """
        if not self._page:
            raise RuntimeError("Browser not initialized. Call connect() first.")

        page = self._page

        logger.info("Navigating to login page")
        # Use domcontentloaded instead of networkidle (faster, less likely to timeout)
        await page.goto(self.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

        # Wait for page to stabilize
        await page.wait_for_load_state("load")

        # Fill in credentials using Playwright locators (more robust than CSS)
        logger.info("Entering credentials")

        # Try multiple approaches for email field
        email_filled = False
        try:
            # Primary: placeholder-based locator
            await page.get_by_placeholder("Email").click(timeout=10000)
            await page.get_by_role("textbox", name="Email").fill(self.username)
            email_filled = True
        except Exception as e:
            logger.debug(f"Primary email locator failed: {e}")

        if not email_filled:
            # Fallback: CSS selectors
            for selector in self.SELECTORS.get("username_input", []):
                try:
                    if selector.startswith("//"):
                        selector = f"xpath={selector}"
                    await page.fill(selector, self.username, timeout=5000)
                    email_filled = True
                    logger.warning(f"Used fallback email selector: {selector}")
                    break
                except Exception:
                    continue

        if not email_filled:
            raise RuntimeError("Could not find email input field")

        # Try multiple approaches for password field
        password_filled = False
        try:
            # Primary: role-based locator
            await page.get_by_role("textbox", name="Password").click(timeout=5000)
            await page.get_by_role("textbox", name="Password").fill(self.password)
            password_filled = True
        except Exception as e:
            logger.debug(f"Primary password locator failed: {e}")

        if not password_filled:
            # Fallback: CSS selectors
            for selector in self.SELECTORS.get("password_input", []):
                try:
                    if selector.startswith("//"):
                        selector = f"xpath={selector}"
                    await page.fill(selector, self.password, timeout=5000)
                    password_filled = True
                    logger.warning(f"Used fallback password selector: {selector}")
                    break
                except Exception:
                    continue

        if not password_filled:
            raise RuntimeError("Could not find password input field")

        # Submit login form
        logger.info("Submitting login form")
        try:
            # Primary: role-based button locator (exact match)
            await page.get_by_role("button", name="Sign In", exact=True).click(
                timeout=5000
            )
        except Exception as e:
            logger.debug(f"Primary submit button failed: {e}")
            # Fallback: CSS selectors
            submitted = False
            for selector in self.SELECTORS.get("submit_button", []):
                try:
                    if selector.startswith("//"):
                        selector = f"xpath={selector}"
                    await page.click(selector, timeout=5000)
                    submitted = True
                    logger.warning(f"Used fallback submit selector: {selector}")
                    break
                except Exception:
                    continue
            if not submitted:
                raise RuntimeError("Could not find submit button")

        # Wait for navigation to complete (use load, not networkidle)
        logger.info("Waiting for login to complete")
        await page.wait_for_load_state("load")

        # Check for CAPTCHA or security challenges
        captcha_indicators = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="captcha"]',
            '[class*="captcha"]',
            '[id*="captcha"]',
            'text="I\'m not a robot"',
            'text="Verify you are human"',
        ]

        for captcha_selector in captcha_indicators:
            try:
                if captcha_selector.startswith("text="):
                    text = captcha_selector.replace("text=", "").strip('"')
                    element = page.get_by_text(text, exact=False)
                    if await element.count() > 0:
                        logger.warning(
                            "CAPTCHA detected! Login may require manual intervention. "
                            "Consider using --no-headless to complete CAPTCHA manually."
                        )
                else:
                    element = await page.query_selector(captcha_selector)
                    if element:
                        logger.warning(
                            "CAPTCHA detected! Login may require manual intervention. "
                            "Consider using --no-headless to complete CAPTCHA manually."
                        )
            except Exception:
                continue

        await page.wait_for_timeout(5000)  # Extra time for JS redirects (5 sec)

        # First, check for error messages (most reliable failure indicator)
        error_indicators = [
            'text="Error Logging In"',
            'text="Invalid email or password"',
            'text="Incorrect password"',
            'text="User not found"',
            'text="Please check email/password"',
            '[class*="error"]',
            '[class*="alert"]',
            '[role="alert"]',
            '[data-testid*="error"]',
        ]

        for error_selector in error_indicators:
            try:
                if error_selector.startswith("text="):
                    text = error_selector.replace("text=", "").strip('"')
                    # Try exact match first, then partial match
                    element = page.get_by_text(text, exact=False)
                    count = await element.count()
                    if count > 0:
                        error_text = await element.first.text_content()
                        # Clean up the error text (remove extra whitespace)
                        if error_text:
                            error_text = " ".join(error_text.split())
                            logger.error(f"Login failed: {error_text}")
                            raise RuntimeError(f"Login failed: {error_text}")
                else:
                    # Try CSS/XPath selectors
                    elements = await page.query_selector_all(error_selector)
                    for element in elements:
                        error_text = await element.text_content()
                        if error_text and len(error_text.strip()) > 0:
                            # Check if it looks like an error message
                            error_lower = error_text.lower()
                            if any(
                                keyword in error_lower
                                for keyword in [
                                    "error",
                                    "invalid",
                                    "incorrect",
                                    "failed",
                                    "wrong",
                                    "check email",
                                    "check password",
                                ]
                            ):
                                error_text = " ".join(error_text.split())
                                logger.error(f"Login failed: {error_text}")
                                raise RuntimeError(f"Login failed: {error_text}")
            except RuntimeError:
                raise  # Re-raise login errors
            except Exception:
                continue  # Ignore selector errors

        # Check URL changed from login page (most reliable check)
        current_url = page.url
        if "/login" not in current_url.lower():
            logger.info(f"Login successful (redirected to: {current_url})")
            return

        # Try waiting a bit more if still on login page
        await page.wait_for_timeout(3000)
        current_url = page.url
        if "/login" not in current_url.lower():
            logger.info(f"Login successful (redirected to: {current_url})")
            return

        # Verify login success by checking for absence of login form
        try:
            # Check if login form is gone (most reliable success indicator)
            email_input = page.get_by_placeholder("Email")
            count = await email_input.count()
            if count == 0:
                logger.info("Login successful (email form disappeared)")
                return
            # If form is still there, check if it's actually visible
            is_visible = await email_input.first.is_visible()
            if not is_visible:
                logger.info("Login successful (email form hidden)")
                return
        except Exception as e:
            logger.debug(f"Email input check failed: {e}")
            # If we can't find the email input at all, that's likely success
            logger.info("Login successful (email form not found)")
            return

        # Try alternative success indicators
        success_selectors = [
            'a[href*="/account"]',
            'a[href*="/profile"]',
            'nav[class*="user"]',
            "div[class*='user-menu']",
            'img[alt*="avatar"]',
            'button:has-text("Log out")',
            'a[href*="/settings"]',
            '[data-testid*="user"]',
        ]

        for selector in success_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"Login successful (found: {selector})")
                    return
            except Exception:
                continue

        # If we're on any action network page that's not login, consider it success
        if "actionnetwork.com" in current_url and "/login" not in current_url:
            logger.info(f"Login assumed successful (on: {current_url})")
            return

        # Final check: If no error messages appeared and we can't verify either way,
        # try to navigate to a protected page to test authentication
        try:
            logger.info("Testing authentication by navigating to protected page")
            test_url = f"{self.BASE_URL}/nfl/odds"
            await page.goto(test_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_load_state("load")
            await page.wait_for_timeout(2000)

            # If we can access the page (not redirected to login), we're authenticated
            if "/login" not in page.url.lower():
                logger.info("Login successful (can access protected page)")
                return
        except Exception as e:
            logger.debug(f"Authentication test failed: {e}")

        # If we got here, login may have failed
        logger.warning(f"Login verification uncertain, URL: {current_url}")
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
                    # For query_all, treat empty list as failure to try next selector
                    if not element:
                        logger.debug(f"query_all returned empty for: {selector}")
                        continue
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
        """Implementation of odds fetching.

        Navigates directly to the odds URL and extracts spreads, totals, and moneylines
        by switching the odds type dropdown.
        """
        if not self._page:
            raise RuntimeError("Browser not initialized")

        page = self._page

        # Navigate directly to the odds URL (more reliable than UI navigation)
        league_slug = league.lower()  # "nfl" or "ncaaf"
        odds_url = f"https://www.actionnetwork.com/{league_slug}/odds"

        logger.debug(f"Navigating directly to {odds_url}")
        await page.goto(odds_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_load_state("load")

        # Wait for page content to stabilize
        await page.wait_for_timeout(3000)

        # Step 1: Extract spreads (default view)
        logger.debug("Extracting spread data (default view)")
        games = await self._extract_odds_from_page(page, league, odds_type="spread")

        if not games:
            logger.warning("No games found in spread view")
            return []

        # Step 2: Switch to Total view and extract totals
        logger.debug("Switching to Total view")
        totals_data = await self._extract_with_odds_type(page, league, "total")

        # Step 3: Merge totals into games
        if totals_data:
            games = self._merge_odds_data(games, totals_data, "total")
            logger.debug(f"Merged totals for {len(totals_data)} games")

        logger.info(f"Successfully extracted {len(games)} games for {league}")
        return games

    async def _extract_with_odds_type(
        self, page: Page, league: Literal["NFL", "NCAAF"], odds_type: str
    ) -> dict[str, dict[str, Any]]:
        """
        Switch odds dropdown and extract data for a specific odds type.

        Args:
            page: Playwright page
            league: NFL or NCAAF
            odds_type: 'spread', 'total', or 'ml'

        Returns:
            Dict mapping game key (away_team|home_team) to odds data
        """
        try:
            # Find the odds type dropdown (has Spread/Total/Moneyline options)
            dropdown = await page.query_selector("select:has(option[value='total'])")
            if not dropdown:
                logger.warning(f"Could not find odds type dropdown for {odds_type}")
                return {}

            # Select the desired odds type
            await dropdown.select_option(value=odds_type)
            await page.wait_for_timeout(1500)  # Wait for table to update

            # Extract data
            games = await self._extract_odds_from_page(
                page, league, odds_type=odds_type
            )

            # Convert to dict keyed by game
            result = {}
            for game in games:
                key = f"{game['away_team']}|{game['home_team']}"
                result[key] = game

            return result

        except Exception as e:
            logger.warning(f"Failed to extract {odds_type} data: {e}")
            return {}

    def _merge_odds_data(
        self,
        games: list[dict[str, Any]],
        additional_data: dict[str, dict[str, Any]],
        data_type: str,
    ) -> list[dict[str, Any]]:
        """
        Merge additional odds data (totals, moneylines) into games list.

        Args:
            games: List of game dicts with spread data
            additional_data: Dict of game key -> odds data
            data_type: 'total' or 'ml'

        Returns:
            Updated games list with merged data
        """
        for game in games:
            key = f"{game['away_team']}|{game['home_team']}"
            if key in additional_data:
                extra = additional_data[key]
                if data_type == "total":
                    game["over_under"] = extra.get("over_under")
                    game["total_odds"] = extra.get("total_odds")
                elif data_type == "ml":
                    game["moneyline_away"] = extra.get("moneyline_away")
                    game["moneyline_home"] = extra.get("moneyline_home")

        return games

    async def _extract_odds_from_page(
        self, page: Page, league: Literal["NFL", "NCAAF"], odds_type: str = "spread"
    ) -> list[dict[str, Any]]:
        """
        Extract odds data from the odds table.

        Structure discovered via DOM analysis:
        - Main table: table.css-* (CSS-in-JS class)
        - Each game is a <TR> row with 11 <TD> cells
        - TD[0]: div.best-odds__game-info (teams + rotations)
        - TD[1]: SCHEDULED/OPEN time
        - TD[2]: div.best-odds__open-container (spread: away|juice|home|juice)

        Args:
            page: Playwright page object
            league: League being scraped

        Returns:
            List of game dictionaries with odds data
        """
        games: list[dict[str, Any]] = []

        # Wait for the odds table to load
        await page.wait_for_selector("div.best-odds__game-info", timeout=10000)

        # Find the main odds table (parent of game info divs)
        # Navigate: game-info -> TD -> TR -> TBODY -> TABLE
        table = await page.query_selector("table:has(div.best-odds__game-info)")

        if not table:
            logger.warning("Could not find odds table")
            return games

        # Get all body rows (skip header row)
        rows = await table.query_selector_all("tbody tr")
        logger.info(f"Found {len(rows)} table rows to process")

        i = 0
        while i < len(rows):
            try:
                row = rows[i]
                cells = await row.query_selector_all("td")

                # Check if this is a game row (has game-info) or time row (1 cell)
                if len(cells) >= 3:
                    game_data = await self._extract_table_row(row, league, odds_type)
                    if game_data:
                        # Check if next row is a time row (1 cell)
                        if i + 1 < len(rows):
                            next_row = rows[i + 1]
                            next_cells = await next_row.query_selector_all("td")
                            if len(next_cells) == 1:
                                time_text = await next_cells[0].inner_text()
                                game_data["game_time"] = time_text.strip()
                                i += 1  # Skip the time row

                        games.append(game_data)
                        logger.debug(
                            f"  Extracted: {game_data.get('away_team')} @ "
                            f"{game_data.get('home_team')} "
                            f"(spread: {game_data.get('spread')}) "
                            f"time: {game_data.get('game_time')}"
                        )
            except Exception as e:
                logger.debug(f"Row {i + 1} skipped: {e}")

            i += 1

        return games

    async def _extract_table_row(
        self, row, league: Literal["NFL", "NCAAF"], odds_type: str = "spread"
    ) -> dict[str, Any] | None:
        """
        Extract game and odds from a table row.

        Row structure (11 cells):
        - Cell 0: Game info (teams + rotations)
        - Cell 1: Schedule/Open
        - Cell 2: Best odds container (spread or total depending on view)

        Args:
            row: TR element
            league: NFL or NCAAF
            odds_type: 'spread' or 'total' - determines how to parse odds cells

        Returns:
            Game dict or None if not a game row
        """
        # Get all cells in the row
        cells = await row.query_selector_all("td")
        if len(cells) < 3:
            return None

        # Cell 0: Game info
        game_info = await cells[0].query_selector("div.best-odds__game-info")
        if not game_info:
            return None  # Not a game row (might be header/footer)

        game_text = await game_info.inner_text()
        lines = [ln.strip() for ln in game_text.split("\n") if ln.strip()]

        if len(lines) < 4:
            return None

        away_team = lines[0]
        away_rotation = lines[1] if lines[1].isdigit() else ""
        home_team = lines[2]
        home_rotation = lines[3] if lines[3].isdigit() else ""

        # Initialize odds values
        spread_value = None
        spread_odds = None
        total_value = None
        total_odds = None
        moneyline_away = None
        moneyline_home = None
        game_time = ""

        # Cell 1 or 2 contains the odds data (OPEN column)
        # Format depends on odds_type:
        # - spread: "+2.5\n-105\n-2.5\n-115" (away spread, juice, home spread, juice)
        # - total: "o48.5\n-110\nu48.5\n-110" (over value, odds, under value, odds)

        for cell_idx in [1, 2]:
            if len(cells) <= cell_idx:
                break

            odds_text = await cells[cell_idx].inner_text()
            odds_lines = [s.strip() for s in odds_text.split("\n") if s.strip()]

            if len(odds_lines) < 2:
                # Might be game time like "Thu 8:15 PM"
                if not game_time:
                    game_time = odds_text.replace("\n", " ").strip()
                continue

            if odds_type == "total":
                # Parse total format: o48.5\n-110\nu48.5\n-110
                try:
                    first_val = odds_lines[0].lower()
                    # Check for 'o' prefix (over)
                    if first_val.startswith("o"):
                        over_str = first_val[1:]  # Strip 'o' prefix
                        if over_str.replace(".", "").replace("-", "").isdigit():
                            total_value = float(over_str)
                            if len(odds_lines) >= 2:
                                total_odds = int(odds_lines[1])
                            break
                    # Also try without prefix (number only)
                    elif first_val.replace(".", "").replace("-", "").isdigit():
                        val = float(first_val)
                        if 30 < val < 80:  # Reasonable total range
                            total_value = val
                            if len(odds_lines) >= 2:
                                total_odds = int(odds_lines[1])
                            break
                except (ValueError, IndexError):
                    pass

            else:  # spread mode (default)
                # Parse spread format: +2.5\n-105\n-2.5\n-115
                try:
                    first_val = odds_lines[0].replace("+", "")
                    # Handle cases like "SCHEDULED" or time strings
                    if first_val.replace(".", "").replace("-", "").isdigit():
                        spread_value = float(first_val)
                        spread_odds = int(odds_lines[1])
                        break
                except (ValueError, IndexError):
                    pass

        # For spread mode, also try to extract moneylines from later cells
        if odds_type == "spread":
            for cell in cells[3:7]:
                cell_text = await cell.inner_text()
                cell_lines = [s.strip() for s in cell_text.split("\n") if s.strip()]

                # Check for moneyline pattern (3-digit number with +/-)
                for line in cell_lines:
                    if line.startswith(("+", "-")) and len(line) >= 3:
                        try:
                            ml = int(line)
                            if -1000 < ml < 1000:  # Reasonable ML range
                                if moneyline_away is None:
                                    moneyline_away = ml
                                elif moneyline_home is None:
                                    moneyline_home = ml
                        except ValueError:
                            continue

        return {
            "league": league,
            "away_team": away_team,
            "home_team": home_team,
            "game_time": game_time,
            "away_rotation": away_rotation,
            "home_rotation": home_rotation,
            "spread": spread_value,
            "spread_odds": spread_odds,
            "over_under": total_value,
            "total_odds": total_odds,
            "moneyline_home": moneyline_home,
            "moneyline_away": moneyline_away,
            "sportsbook": "best_odds",
            "timestamp": datetime.now().isoformat(),
            "source": "action_network",
        }

    async def _try_row_selectors(self, row, selectors: list[str]) -> Any:
        """Try multiple selectors on a row element until one succeeds."""
        for selector in selectors:
            try:
                result = await row.query_selector(selector)
                if result:
                    return result
            except Exception:
                continue
        return None

    async def _try_row_selectors_all(self, row, selectors: list[str]) -> list:
        """Try multiple selectors on a row element, returning all matches."""
        for selector in selectors:
            try:
                results = await row.query_selector_all(selector)
                if results:
                    return results
            except Exception:
                continue
        return []

    async def _extract_game_row(
        self, row, league: Literal["NFL", "NCAAF"]
    ) -> dict[str, Any] | None:
        """
        Extract odds data from a single game row or container.

        Args:
            row: Playwright element handle for game row/container
            league: League being scraped

        Returns:
            Game dictionary or None if extraction fails
        """
        try:
            # Get team name selectors with fallbacks
            team_selectors = self.SELECTORS.get(
                "team_name",
                [
                    "div.game-info__teams",
                    ".game-info__teams",
                    ".team-name",
                    "[class*='team']",
                ],
            )

            # First, check if the row itself contains all team info (div.best-odds__game-info)
            row_class = await row.get_attribute("class") or ""
            if "best-odds__game-info" in row_class or "game-info" in row_class:
                # Row IS the game info container - read its text directly
                team_text = await row.inner_text()
            else:
                # Try to find team container as child element
                team_container = await self._try_row_selectors(row, team_selectors)
                if team_container:
                    team_text = await team_container.inner_text()
                else:
                    team_text = await row.inner_text()

            # Parse newline-separated format:
            # "Packers\n305\nLions\n306"
            lines = [
                line.strip() for line in team_text.strip().split("\n") if line.strip()
            ]

            if len(lines) >= 4:
                # Format: Team1, Rot1, Team2, Rot2 (newline-separated)
                away_team = lines[0]
                away_rotation = lines[1] if lines[1].isdigit() else ""
                home_team = lines[2]
                home_rotation = lines[3] if lines[3].isdigit() else ""
            elif len(lines) >= 2:
                # Simple format with just team names
                away_team = lines[0]
                home_team = lines[1]
                away_rotation = ""
                home_rotation = ""
            else:
                # Try space-separated fallback
                parts = team_text.strip().split()
                if len(parts) >= 2:
                    away_team = parts[0]
                    home_team = parts[-1]
                    away_rotation = ""
                    home_rotation = ""
                else:
                    # Cannot parse teams - skip this row
                    return None

            # Extract game date/time
            time_selectors = self.SELECTORS.get(
                "game_time", [".game-time", "[class*='game-time']", "[class*='time']"]
            )
            game_time_elem = await self._try_row_selectors(row, time_selectors)
            game_time_text = await game_time_elem.inner_text() if game_time_elem else ""

            # Extract best odds using multi-selector fallback
            spread_selectors = self.SELECTORS.get(
                "best_odds_spread",
                [
                    ".spread-cell .best-odds",
                    "[class*='spread'] [class*='best']",
                    "[class*='spread'] span",
                ],
            )
            total_selectors = self.SELECTORS.get(
                "best_odds_total",
                [
                    ".total-cell .best-odds",
                    "[class*='total'] [class*='best']",
                    "[class*='total'] span",
                ],
            )
            ml_selectors = self.SELECTORS.get(
                "best_odds_moneyline",
                [
                    ".moneyline-cell .best-odds",
                    "[class*='moneyline'] [class*='best']",
                    "[class*='moneyline'] span",
                ],
            )

            best_spread_elem = await self._try_row_selectors(row, spread_selectors)
            best_total_elem = await self._try_row_selectors(row, total_selectors)
            best_ml_elem = await self._try_row_selectors(row, ml_selectors)

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

            # Extract sportsbook name using multi-selector fallback
            sportsbook_selectors = self.SELECTORS.get(
                "sportsbook_name",
                [".sportsbook-name", "[class*='sportsbook']", "[class*='book']"],
            )
            sportsbook_elem = await self._try_row_selectors(row, sportsbook_selectors)
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
