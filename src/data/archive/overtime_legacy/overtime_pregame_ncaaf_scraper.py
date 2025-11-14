#!/usr/bin/env python3
"""
Overtime.ag Pre-Game NCAAF Odds Scraper

Scrapes NCAAF (NCAA College Football) pre-game betting lines (spreads, totals, moneylines)
from Overtime.ag using Playwright browser automation.
Supports multiple betting periods (Game, 1st Half, 1st Quarter).

Author: Billy Walters Sports Analyzer
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Page, async_playwright
from pydantic import BaseModel

from data.proxy_manager import get_proxy_manager


class OvertimeGame(BaseModel):
    """Structured game data from Overtime.ag"""

    league_week_info: Optional[str] = None
    game_date: Optional[str] = None
    game_time: Optional[str] = None
    visitor: Dict[str, Any]
    home: Dict[str, Any]
    period: str = "GAME"
    scraped_at: datetime
    source: str = "overtime.ag"


class OvertimeAccount(BaseModel):
    """Account information"""

    balance: Optional[str] = None
    available_balance: Optional[str] = None
    pending: Optional[str] = None


class OvertimeNCAAFScraper:
    """
    Scraper for Overtime.ag NCAAF pre-game betting lines.

    Features:
    - Automatic login with credentials from environment
    - Extracts Game, 1st Half, and 1st Quarter lines
    - Parses spreads, totals, and moneylines
    - Uses XPath selectors for precise element targeting
    - Exports to JSON format compatible with Billy Walters system
    """

    def __init__(
        self,
        customer_id: Optional[str] = None,
        password: Optional[str] = None,
        proxy_url: Optional[str] = None,
        headless: bool = False,
        output_dir: str = "output/overtime/ncaaf/pregame",
        use_smart_proxy: bool = True,
    ):
        """
        Initialize the scraper.

        Args:
            customer_id: Overtime.ag customer ID (defaults to OV_CUSTOMER_ID env var)
            password: Overtime.ag password (defaults to OV_PASSWORD env var)
            proxy_url: Optional proxy URL with credentials (overrides smart proxy)
            headless: Run browser in headless mode
            output_dir: Directory to save scraped data (default: output/overtime/ncaaf/pregame)
            use_smart_proxy: Use ProxyManager for automatic fallback (default: True)
        """
        self.customer_id = customer_id or os.getenv("OV_CUSTOMER_ID")
        self.password = password or os.getenv("OV_PASSWORD")
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Smart proxy handling
        if proxy_url is not None:
            # Explicit proxy provided (use as-is)
            self.proxy_url = proxy_url
        elif use_smart_proxy:
            # Use ProxyManager for automatic testing and fallback
            proxy_manager = get_proxy_manager()
            self.proxy_url = proxy_manager.get_proxy(test_first=True)
        else:
            # No proxy
            self.proxy_url = None

        self.account_info: Optional[OvertimeAccount] = None
        self.games: List[OvertimeGame] = []

    async def scrape(self) -> Dict[str, Any]:
        """
        Main scraping workflow.

        Returns:
            Dictionary with account info, games, and metadata
        """
        print("=" * 70)
        print("Overtime.ag Pre-Game NCAAF Odds Scraper")
        print("=" * 70)

        async with async_playwright() as p:
            # Launch browser
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]

            browser = await p.chromium.launch(headless=self.headless, args=browser_args)

            try:
                # Configure proxy if provided
                context_kwargs = {
                    "viewport": {"width": 1920, "height": 1080},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "locale": "en-US",
                }

                if self.proxy_url:
                    # Some residential proxies require credentials in URL
                    context_kwargs["proxy"] = {"server": self.proxy_url}
                    from urllib.parse import urlparse

                    parsed = urlparse(self.proxy_url)
                    print(f"Using proxy: {parsed.hostname}:{parsed.port}")

                context = await browser.new_context(**context_kwargs)

                page = await context.new_page()

                # Navigate and login
                print("\n1. Navigating to Overtime.ag...")
                await page.goto(
                    "https://overtime.ag/sports#/",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                await page.wait_for_timeout(3000)

                # Login
                if self.customer_id and self.password:
                    print("2. Logging in...")
                    await self._login(page)
                    await page.wait_for_timeout(2000)
                else:
                    print("2. Skipping login (no credentials provided)")

                # Extract account info
                print("3. Extracting account information...")
                self.account_info = await self._extract_account_info(page)
                if self.account_info:
                    print(f"   Balance: {self.account_info.balance}")
                    print(f"   Available: {self.account_info.available_balance}")
                    print(f"   Pending: {self.account_info.pending}")

                # Click on COLLEGE FOOTBALL section
                print("4. Navigating to NCAAF betting lines...")
                await self._navigate_to_ncaaf(page)
                await page.wait_for_timeout(3000)

                # Enhanced debug: Check what's on the page
                debug_info = await page.evaluate("""
                    () => {
                        const h4Elements = Array.from(document.querySelectorAll('h4'));
                        const buttons = document.querySelectorAll('button[ng-click*="SendLineToWager"]');
                        const bodyText = document.body.innerText;

                        // Check for common "no games" indicators
                        const noGamesIndicators = [
                            'No games available',
                            'Lines not available',
                            'Coming soon',
                            'Check back later',
                            'All games started'
                        ];

                        const hasNoGamesMessage = noGamesIndicators.some(indicator =>
                            bodyText.includes(indicator)
                        );

                        // Check current hash/route
                        const currentHash = window.location.hash;

                        return {
                            h4Count: h4Elements.length,
                            h4Texts: h4Elements.slice(0, 10).map(h => h.textContent.trim()),
                            buttonCount: buttons.length,
                            allButtonsCount: document.querySelectorAll('button').length,
                            hasNoGamesMessage: hasNoGamesMessage,
                            currentHash: currentHash,
                            bodySnippet: bodyText.substring(0, 800),
                            ncaafSectionVisible: bodyText.includes('COLLEGE FOOTBALL') || bodyText.includes('College Football')
                        };
                    }
                """)

                # Clean debug output for Windows console
                debug_clean = {
                    "h4Count": debug_info.get("h4Count", 0),
                    "h4Texts": debug_info.get("h4Texts", []),
                    "buttonCount": debug_info.get("buttonCount", 0),
                    "allButtonsCount": debug_info.get("allButtonsCount", 0),
                    "hasNoGamesMessage": debug_info.get("hasNoGamesMessage", False),
                    "currentHash": debug_info.get("currentHash", ""),
                    "ncaafSectionVisible": debug_info.get("ncaafSectionVisible", False),
                }
                print(f"   DEBUG - Page elements: {debug_clean}")

                # Print snippet safely (ASCII only)
                snippet = (
                    debug_info.get("bodySnippet", "")
                    .encode("ascii", "ignore")
                    .decode("ascii")
                )
                print(f"   DEBUG - Page snippet:\n{snippet[:400]}")

                # Provide helpful diagnosis
                if debug_info.get("buttonCount", 0) == 0:
                    print("\n   [WARNING] No betting buttons found!")
                    if debug_info.get("hasNoGamesMessage", False):
                        print("   -> Site indicates no games available")
                    print("   -> This is normal during games (Saturday evenings)")
                    print("   -> Best scraping times: Sunday-Wednesday 12PM-6PM ET")
                    print("   -> Lines post after Saturday's games end")

                print("   Waiting for games to load...")
                await page.wait_for_timeout(5000)  # Wait longer for games to load

                # Extract all periods (GAME, 1st Half, 1st Quarter)
                periods = ["GAME", "1ST HALF", "1ST QUARTER"]
                for period in periods:
                    print(f"5. Extracting {period} lines...")
                    games = await self._extract_games(page, period)
                    self.games.extend(games)
                    print(f"   Found {len(games)} games for {period}")

                # Save results
                print("\n6. Saving results...")
                output = self._format_output()
                output_file = (
                    self.output_dir
                    / f"overtime_ncaaf_odds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(output, f, indent=2, default=str)

                print(f"   Saved to: {output_file}")

                # Display validation results
                validation = output["scrape_metadata"]["data_validation"]
                print("\n7. Data Validation Results:")
                print(
                    f"   Status: {'[OK] VALID' if validation['is_valid'] else '[WARNING] INVALID'}"
                )
                print(f"   Games found: {validation['game_count']}")
                print(f"   Has team names: {validation['has_team_names']}")
                print(f"   Has betting lines: {validation['has_odds']}")

                if validation["warnings"]:
                    print("\n   Warnings:")
                    for warning in validation["warnings"]:
                        print(f"   -> {warning}")

                if len(self.games) > 0:
                    print(f"\n[OK] Successfully scraped {len(self.games)} game entries")
                else:
                    print("\n[WARNING] Scrape completed but found 0 games")
                    print("   This is expected during games or outside betting windows")

                return output

            finally:
                await browser.close()

    async def _login(self, page: Page) -> bool:
        """Perform login to Overtime.ag"""
        try:
            # Wait for LOGIN button to exist in DOM (don't require visible)
            await page.wait_for_selector(
                "a.btn-signup", state="attached", timeout=10000
            )

            # Click LOGIN button using JavaScript (bypasses visibility checks)
            login_clicked = await page.evaluate("""
                () => {
                    const loginBtn = document.querySelector('a.btn-signup');
                    if (loginBtn) {
                        loginBtn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if login_clicked:
                await page.wait_for_timeout(2000)
            else:
                print("   LOGIN button not found")
                return False

            # Fill customer ID using XPath
            customer_input = await page.query_selector('input[placeholder*="Customer"]')
            if customer_input:
                await customer_input.fill(self.customer_id)

            # Fill password using XPath
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(self.password)

            # Click login button
            login_btn = await page.query_selector('button:has-text("LOGIN")')
            if login_btn:
                await login_btn.click()
                await page.wait_for_timeout(5000)  # Wait for security checks
                print("   Login successful!")
                return True

            return False

        except Exception as e:
            print(f"   Login failed: {e}")
            return False

    async def _extract_account_info(self, page: Page) -> Optional[OvertimeAccount]:
        """Extract account balance information"""
        try:
            account_data = await page.evaluate("""
                () => {
                    const balanceLinks = document.querySelectorAll('[href*="dailyFigures"], [href*="openBets"]');
                    const info = {};

                    balanceLinks.forEach(link => {
                        const text = link.textContent.trim();
                        if (text.includes('Balance')) {
                            info.balance = text.replace('Balance', '').trim();
                        } else if (text.includes('Avail Bal')) {
                            info.available_balance = text.replace('Avail Bal', '').trim();
                        } else if (text.includes('Pending')) {
                            info.pending = text.replace('Pending', '').trim();
                        }
                    });

                    return info;
                }
            """)

            if account_data:
                return OvertimeAccount(**account_data)
            return None

        except Exception as e:
            print(f"   Could not extract account info: {e}")
            return None

    async def _navigate_to_ncaaf(self, page: Page) -> None:
        """Navigate to NCAAF betting section using XPath"""
        try:
            # Use JavaScript with XPath to click COLLEGE FOOTBALL section
            # XPath: //label[@for='gl_Football_College_Football_G']
            clicked = await page.evaluate("""
                () => {
                    const xpath = "//label[@for='gl_Football_College_Football_G']";
                    const result = document.evaluate(
                        xpath,
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    );
                    const element = result.singleNodeValue;
                    if (element) {
                        element.click();
                        return true;
                    }
                    // Fallback: try finding by text content
                    const labels = Array.from(document.querySelectorAll('label'));
                    const cfbLabel = labels.find(el =>
                        el.textContent.includes('COLLEGE FOOTBALL') ||
                        el.textContent.includes('College Football')
                    );
                    if (cfbLabel) {
                        cfbLabel.click();
                        return true;
                    }
                    return false;
                }
            """)

            if clicked:
                print("   Navigated to COLLEGE FOOTBALL section")
            else:
                print("   [WARNING] Could not find COLLEGE FOOTBALL section")

        except Exception as e:
            print(f"   Could not navigate to NCAAF section: {e}")

    async def _extract_games(self, page: Page, period: str) -> List[OvertimeGame]:
        """
        Extract game data for a specific period using XPath selectors.

        Args:
            page: Playwright page object
            period: Betting period (GAME, 1ST HALF, 1ST QUARTER)

        Returns:
            List of OvertimeGame objects
        """
        try:
            # Click the period button if not GAME
            if period != "GAME":
                await self._switch_period(page, period)
                await page.wait_for_timeout(2000)

            # Extract games using JavaScript with XPath
            games_data = await page.evaluate(
                """
                (period) => {
                    const result = {
                        games: []
                    };

                    // XPath: //div[@class='col-xs-12 col-sm-12 GameBlock']
                    const gameBlocksXPath = "//div[@class='col-xs-12 col-sm-12 GameBlock']";
                    const gameBlocksResult = document.evaluate(
                        gameBlocksXPath,
                        document,
                        null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                        null
                    );

                    // Process each game block
                    for (let i = 0; i < gameBlocksResult.snapshotLength; i++) {
                        const gameBlock = gameBlocksResult.snapshotItem(i);

                        // Extract week info, date, time from game block
                        const weekInfoEl = gameBlock.querySelector('[ng-bind="gameLine.Comments"]');
                        const gameDateEl = gameBlock.querySelector('[ng-bind*="GameDateTimeString | formatGameDate"]');
                        const gameTimeEl = gameBlock.querySelector('[ng-bind*="GameDateTimeString | formatGameTime"]');

                        // XPath: .//h4[@class='ng-binding'] (team names)
                        const teamNamesXPath = ".//h4[@class='ng-binding']";
                        const teamNamesResult = document.evaluate(
                            teamNamesXPath,
                            gameBlock,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null
                        );

                        const teams = [];
                        for (let j = 0; j < teamNamesResult.snapshotLength; j++) {
                            const h4 = teamNamesResult.snapshotItem(j);
                            const teamName = h4.textContent.trim();
                            const teamLogo = h4.querySelector('img');

                            // NCAAF doesn't use rotation numbers in team names
                            teams.push({
                                teamName: teamName,
                                logoUrl: teamLogo ? teamLogo.src : null
                            });
                        }

                        // Extract betting buttons using XPath
                        // Spread buttons: contains('-') or contains('+')
                        const spreadXPath = ".//button[contains(@ng-click, 'SendLineToWager') and (contains(text(), '-') or contains(text(), '+'))]";
                        const spreadResult = document.evaluate(
                            spreadXPath,
                            gameBlock,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null
                        );

                        // Total buttons: starts with 'O' or 'U'
                        const totalXPath = ".//button[contains(@ng-click, 'SendLineToWager') and (starts-with(text(), 'O') or starts-with(text(), 'U'))]";
                        const totalResult = document.evaluate(
                            totalXPath,
                            gameBlock,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null
                        );

                        // MoneyLine buttons: doesn't contain 'O', 'U', '+', '-' at start
                        const mlXPath = ".//button[contains(@ng-click, 'SendLineToWager') and not(contains(text(), 'O')) and not(contains(text(), 'U')) and not(contains(text(), '+')) and not(contains(text(), '-'))]";
                        const mlResult = document.evaluate(
                            mlXPath,
                            gameBlock,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null
                        );

                        // Collect betting lines
                        const spreads = [];
                        for (let k = 0; k < spreadResult.snapshotLength; k++) {
                            spreads.push(spreadResult.snapshotItem(k).textContent.trim());
                        }

                        const totals = [];
                        for (let k = 0; k < totalResult.snapshotLength; k++) {
                            totals.push(totalResult.snapshotItem(k).textContent.trim());
                        }

                        const moneylines = [];
                        for (let k = 0; k < mlResult.snapshotLength; k++) {
                            moneylines.push(mlResult.snapshotItem(k).textContent.trim());
                        }

                        // Construct game object if we have at least 2 teams
                        if (teams.length >= 2) {
                            const game = {
                                leagueWeekInfo: weekInfoEl ? weekInfoEl.textContent.trim() : null,
                                gameDate: gameDateEl ? gameDateEl.textContent.trim() : null,
                                gameTime: gameTimeEl ? gameTimeEl.textContent.trim() : null,
                                visitor: teams[0],
                                home: teams[1],
                                period: period
                            };

                            // Assign betting lines (visitor first, then home)
                            if (spreads.length >= 2) {
                                game.visitor.spread = spreads[0];
                                game.home.spread = spreads[1];
                            }

                            if (totals.length >= 2) {
                                game.visitor.total = totals[0];
                                game.home.total = totals[1];
                            }

                            if (moneylines.length >= 2) {
                                game.visitor.moneyLine = moneylines[0];
                                game.home.moneyLine = moneylines[1];
                            }

                            result.games.push(game);
                        }
                    }

                    return result;
                }
            """,
                period,
            )

            # Convert to OvertimeGame objects
            games = []
            for game_data in games_data.get("games", []):
                game = OvertimeGame(**game_data, scraped_at=datetime.now())
                games.append(game)

            return games

        except Exception as e:
            print(f"   Error extracting games for {period}: {e}")
            import traceback

            traceback.print_exc()
            return []

    async def _switch_period(self, page: Page, period: str) -> None:
        """Switch to a different betting period"""
        try:
            # Map period names to button text
            period_map = {"1ST HALF": "1 HLF", "1ST QUARTER": "1 QT"}

            button_text = period_map.get(period, period)

            await page.evaluate(
                """
                (buttonText) => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const periodBtn = buttons.find(btn => btn.textContent.trim() === buttonText);
                    if (periodBtn) {
                        periodBtn.click();
                        return true;
                    }
                    return false;
                }
            """,
                button_text,
            )

        except Exception as e:
            print(f"   Could not switch to period {period}: {e}")

    def _format_output(self) -> Dict[str, Any]:
        """Format scraped data for output with validation"""
        # Validate data quality
        validation_status = self._validate_scraped_data()

        return {
            "scrape_metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": "overtime.ag",
                "sport": "NCAAF",
                "scraper_version": "1.0.0",
                "data_validation": validation_status,
            },
            "account_info": (
                self.account_info.model_dump() if self.account_info else None
            ),
            "games": [game.model_dump() for game in self.games],
            "summary": {
                "total_games": len(self.games),
                "periods": list(set(game.period for game in self.games)),
                "unique_matchups": len(
                    set(
                        f"{game.visitor['teamName']} @ {game.home['teamName']}"
                        for game in self.games
                    )
                ),
            },
        }

    def _validate_scraped_data(self) -> Dict[str, Any]:
        """
        Validate scraped data to ensure it contains real game information.

        Returns:
            Dictionary with validation results and warnings
        """
        validation = {
            "is_valid": True,
            "warnings": [],
            "game_count": len(self.games),
            "has_odds": False,
            "has_team_names": False,
        }

        # Check if we have any games
        if len(self.games) == 0:
            validation["is_valid"] = False
            validation["warnings"].append(
                "No games found - may be outside betting window"
            )
            return validation

        # Validate game data quality
        games_with_odds = 0
        games_with_teams = 0

        for game in self.games:
            # Check for team names
            visitor_name = game.visitor.get("teamName", "")
            home_name = game.home.get("teamName", "")

            if visitor_name and home_name:
                games_with_teams += 1

            # Check for betting lines (spread, total, or moneyline)
            has_spread = game.visitor.get("spread") or game.home.get("spread")
            has_total = game.visitor.get("total") or game.home.get("total")
            has_ml = game.visitor.get("moneyLine") or game.home.get("moneyLine")

            if has_spread or has_total or has_ml:
                games_with_odds += 1

        validation["has_team_names"] = games_with_teams > 0
        validation["has_odds"] = games_with_odds > 0

        # Add warnings for data quality issues
        if games_with_teams == 0:
            validation["is_valid"] = False
            validation["warnings"].append("No valid team names found")

        if games_with_odds == 0:
            validation["is_valid"] = False
            validation["warnings"].append(
                "No betting lines found - games may have started"
            )

        if games_with_teams < len(self.games):
            validation["warnings"].append(
                f"Only {games_with_teams}/{len(self.games)} games have team names"
            )

        if games_with_odds < len(self.games):
            validation["warnings"].append(
                f"Only {games_with_odds}/{len(self.games)} games have betting lines"
            )

        return validation


async def main():
    """Main entry point for scraper"""
    scraper = OvertimeNCAAFScraper(
        headless=False,  # Set to True for production
        output_dir="output/overtime/ncaaf/pregame",
    )

    result = await scraper.scrape()

    # Print summary
    print("\n" + "=" * 70)
    print("SCRAPE SUMMARY")
    print("=" * 70)
    print(f"Total game entries: {result['summary']['total_games']}")
    print(f"Unique matchups: {result['summary']['unique_matchups']}")
    print(f"Periods scraped: {', '.join(result['summary']['periods'])}")

    if result.get("account_info"):
        print(f"\nAccount Balance: {result['account_info']['balance']}")
        print(f"Available: {result['account_info']['available_balance']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
