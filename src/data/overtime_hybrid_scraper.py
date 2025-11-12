#!/usr/bin/env python3
"""
Overtime.ag Hybrid Scraper (Playwright + SignalR)

Combines web scraping and real-time WebSocket updates for complete odds coverage:
- Playwright: Login, authentication, static pre-game lines
- SignalR: Real-time live odds updates via WebSocket

Author: Billy Walters Sports Analyzer
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import urlparse

from playwright.async_api import Page, async_playwright, BrowserContext
from signalrcore.hub_connection_builder import HubConnectionBuilder
from pydantic import BaseModel
import logging

from data.proxy_manager import get_proxy_manager


class OvertimeGame(BaseModel):
    """Structured game data"""

    game_id: Optional[str] = None
    league_week_info: Optional[str] = None
    game_date: Optional[str] = None
    game_time: Optional[str] = None
    visitor: Dict[str, Any]
    home: Dict[str, Any]
    period: str = "GAME"
    scraped_at: datetime
    source: str = "overtime.ag"
    is_live: bool = False


class OvertimeHybridScraper:
    """
    Hybrid scraper combining Playwright (authentication) and SignalR (real-time).

    Features:
    - Playwright handles login and initial page scraping
    - SignalR receives real-time odds updates
    - Unified output format for Billy Walters system
    - Automatic reconnection on disconnect
    """

    def __init__(
        self,
        customer_id: Optional[str] = None,
        password: Optional[str] = None,
        proxy_url: Optional[str] = None,
        headless: bool = False,
        output_dir: str = "output/overtime/nfl",
        use_smart_proxy: bool = True,
        enable_signalr: bool = True,
        signalr_duration: int = 300,
    ):
        """
        Initialize hybrid scraper.

        Args:
            customer_id: Overtime.ag customer ID
            password: Overtime.ag password
            proxy_url: Optional proxy URL
            headless: Run browser in headless mode
            output_dir: Output directory
            use_smart_proxy: Use ProxyManager for fallback
            enable_signalr: Enable real-time SignalR updates
            signalr_duration: How long to listen for SignalR updates (seconds)
        """
        self.customer_id = customer_id or os.getenv("OV_CUSTOMER_ID")
        self.password = password or os.getenv("OV_PASSWORD")
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Smart proxy handling
        if proxy_url is not None:
            self.proxy_url = proxy_url
        elif use_smart_proxy:
            proxy_manager = get_proxy_manager()
            self.proxy_url = proxy_manager.get_proxy(test_first=True)
        else:
            self.proxy_url = None

        # SignalR settings
        self.enable_signalr = enable_signalr
        self.signalr_duration = signalr_duration
        self.signalr_connection = None

        # Data storage
        self.pregame_games: List[OvertimeGame] = []
        self.live_updates: List[Dict[str, Any]] = []
        self.account_info: Optional[Dict[str, str]] = None

        # Logging
        self.logger = logging.getLogger(__name__)

    async def scrape(self) -> Dict[str, Any]:
        """
        Main scraping workflow: Playwright then SignalR.

        Returns:
            Dictionary with account info, pre-game data, live updates, and metadata
        """
        print("=" * 70)
        print("Overtime.ag Hybrid Scraper (Playwright + SignalR)")
        print("=" * 70)
        print()

        # Phase 1: Playwright scraping
        print("PHASE 1: Web Scraping (Playwright)")
        print("-" * 70)
        await self._playwright_scrape()

        # Phase 2: SignalR real-time updates
        if self.enable_signalr:
            print()
            print("PHASE 2: Real-Time Updates (SignalR)")
            print("-" * 70)
            await self._signalr_listen()

        # Phase 3: Combine and save
        print()
        print("PHASE 3: Combining Results")
        print("-" * 70)
        return self._format_output()

    async def _playwright_scrape(self) -> None:
        """Phase 1: Use Playwright to login and scrape static odds"""

        async with async_playwright() as p:
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]

            browser = await p.chromium.launch(headless=self.headless, args=browser_args)

            try:
                # Configure context with proxy
                context_kwargs = {
                    "viewport": {"width": 1920, "height": 1080},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "locale": "en-US",
                }

                if self.proxy_url:
                    context_kwargs["proxy"] = {"server": self.proxy_url}
                    parsed = urlparse(self.proxy_url)
                    print(f"Using proxy: {parsed.hostname}:{parsed.port}")

                context = await browser.new_context(**context_kwargs)
                page = await context.new_page()

                # Navigate and login
                print("1. Navigating to Overtime.ag...")
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
                    print("2. Skipping login (no credentials)")

                # Extract account info
                print("3. Extracting account information...")
                self.account_info = await self._extract_account_info(page)
                if self.account_info:
                    print(f"   Balance: {self.account_info.get('balance', 'N/A')}")
                    print(f"   Available: {self.account_info.get('available', 'N/A')}")

                # Navigate to NFL section
                print("4. Navigating to NFL section...")
                await self._navigate_to_nfl(page)
                await page.wait_for_timeout(3000)

                # Extract pre-game lines
                print("5. Extracting pre-game lines...")
                periods = ["GAME", "1ST HALF", "1ST QUARTER"]
                for period in periods:
                    games = await self._extract_games(page, period)
                    self.pregame_games.extend(games)
                    print(f"   Found {len(games)} games for {period}")

                print(f"   Total pre-game games: {len(self.pregame_games)}")

            finally:
                await browser.close()

    async def _signalr_listen(self) -> None:
        """Phase 2: Connect to SignalR for real-time updates"""

        print("1. Connecting to SignalR WebSocket...")
        print(f"   Server: wss://ws.ticosports.com/signalr")
        print(f"   Duration: {self.signalr_duration} seconds")

        # Build SignalR connection
        self.signalr_connection = (
            HubConnectionBuilder()
            .with_url(
                "https://ws.ticosports.com/signalr",
                options={
                    "skip_negotiation": False,
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    },
                },
            )
            .configure_logging(logging.WARNING)  # Reduce noise
            .with_automatic_reconnect(
                {
                    "type": "interval",
                    "keep_alive_interval": 10,  # Ping every 10 seconds
                    "intervals": [1, 3, 5, 10, 20],
                }
            )
            .build()
        )

        # Register handlers
        self._register_signalr_handlers()

        # Start connection
        try:
            self.signalr_connection.start()
            print("2. SignalR connected successfully")

            # Subscribe to sports
            if self.customer_id:
                print("3. Subscribing to customer and NFL...")
                self._subscribe_customer()
                self._subscribe_sports()

            # Listen for updates
            print(f"4. Listening for {self.signalr_duration} seconds...")
            print("   Press Ctrl+C to stop early")

            start_time = asyncio.get_event_loop().time()
            while (
                asyncio.get_event_loop().time() - start_time
            ) < self.signalr_duration:
                await asyncio.sleep(1)

                # Status update every 30 seconds
                elapsed = int(asyncio.get_event_loop().time() - start_time)
                if elapsed % 30 == 0 and elapsed > 0:
                    print(
                        f"   [{elapsed}s] Live updates received: {len(self.live_updates)}"
                    )

            print(f"5. SignalR listening complete")
            print(f"   Total live updates: {len(self.live_updates)}")

        except KeyboardInterrupt:
            print("\n   Stopped by user (Ctrl+C)")
        except Exception as e:
            print(f"   [ERROR] SignalR error: {e}")
        finally:
            if self.signalr_connection:
                self.signalr_connection.stop()
                print("6. SignalR connection closed")

    def _register_signalr_handlers(self) -> None:
        """Register handlers for SignalR events"""

        # Connection lifecycle
        self.signalr_connection.on_open = self._on_signalr_open
        self.signalr_connection.on_close = self._on_signalr_close
        self.signalr_connection.on_error = self._on_signalr_error

        # Data events (guessed based on common patterns)
        self.signalr_connection.on("gameUpdate", self._on_game_update)
        self.signalr_connection.on("linesUpdate", self._on_lines_update)
        self.signalr_connection.on("oddsUpdate", self._on_odds_update)
        self.signalr_connection.on("scoreUpdate", self._on_score_update)
        self.signalr_connection.on("message", self._on_message)

    def _on_signalr_open(self) -> None:
        """SignalR connection opened"""
        self.logger.info("SignalR connection established")

    def _on_signalr_close(self) -> None:
        """SignalR connection closed"""
        self.logger.warning("SignalR connection closed")

    def _on_signalr_error(self, error: Any) -> None:
        """SignalR error"""
        self.logger.error(f"SignalR error: {error}")

    def _on_game_update(self, data: Any) -> None:
        """Handler for game updates"""
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "game_update",
                "data": data,
            }
        )
        print(f"   [GAME UPDATE] {json.dumps(data)[:100]}...")

    def _on_lines_update(self, data: Any) -> None:
        """Handler for lines updates"""
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "lines_update",
                "data": data,
            }
        )
        print(f"   [LINES UPDATE] {json.dumps(data)[:100]}...")

    def _on_odds_update(self, data: Any) -> None:
        """Handler for odds updates"""
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "odds_update",
                "data": data,
            }
        )
        print(f"   [ODDS UPDATE] {json.dumps(data)[:100]}...")

    def _on_score_update(self, data: Any) -> None:
        """Handler for score updates"""
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "score_update",
                "data": data,
            }
        )
        print(f"   [SCORE UPDATE] {json.dumps(data)[:100]}...")

    def _on_message(self, message: Any) -> None:
        """Generic message handler"""
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "message",
                "data": message,
            }
        )
        self.logger.info(f"SignalR message: {message}")

    def _subscribe_customer(self) -> None:
        """Subscribe as customer to SignalR hub"""
        user_data = {
            "customerId": self.customer_id,
            "password": self.password,
        }
        self.signalr_connection.send("gbsHub", "SubscribeCustomer", [user_data])

    def _subscribe_sports(self) -> None:
        """Subscribe to NFL sports on SignalR hub"""
        subscriptions = [
            {"sport": "FOOTBALL", "league": "NFL"},
            {"sportId": 1},  # Football often uses sportId 1
            "NFL",
        ]

        try:
            self.signalr_connection.send("gbsHub", "SubscribeSports", [subscriptions])
        except Exception as e:
            self.logger.error(f"SubscribeSports failed: {e}")

    async def _login(self, page: Page) -> None:
        """Login using Playwright"""

        # Wait for login button
        await page.wait_for_selector("a.btn-signup", state="attached", timeout=10000)

        # Click login button (JavaScript click bypasses visibility)
        await page.evaluate("""
            () => {
                const loginBtn = document.querySelector('a.btn-signup');
                if (loginBtn) loginBtn.click();
            }
        """)
        await page.wait_for_timeout(2000)

        # Fill credentials
        customer_input = await page.query_selector('input[placeholder*="Customer"]')
        if customer_input:
            await customer_input.fill(self.customer_id)

        password_input = await page.query_selector('input[type="password"]')
        if password_input:
            await password_input.fill(self.password)

        # Submit login
        login_btn = await page.query_selector('button:has-text("LOGIN")')
        if login_btn:
            await login_btn.click()
            await page.wait_for_timeout(5000)
            print("   Login successful")

    async def _extract_account_info(self, page: Page) -> Optional[Dict[str, str]]:
        """Extract account balance and info"""

        try:
            balance_elem = await page.query_selector('[href*="dailyFigures"]')
            balance = await balance_elem.inner_text() if balance_elem else None

            available_elem = await page.query_selector('[href*="openBets"]')
            available = await available_elem.inner_text() if available_elem else None

            pending_elem = await page.query_selector('[href*="pending"]')
            pending = await pending_elem.inner_text() if pending_elem else None

            return {
                "balance": balance,
                "available": available,
                "pending": pending,
            }
        except Exception as e:
            self.logger.warning(f"Could not extract account info: {e}")
            return None

    async def _navigate_to_nfl(self, page: Page) -> None:
        """Navigate to NFL betting section"""

        # Look for NFL section label and click with JavaScript (bypasses enabled check)
        clicked = await page.evaluate("""
            () => {
                const labels = Array.from(document.querySelectorAll('label'));
                const nflLabel = labels.find(l => l.textContent.includes('NFL'));
                if (nflLabel) {
                    nflLabel.click();
                    return true;
                }
                return false;
            }
        """)

        if clicked:
            print("   Navigated to NFL section")
        else:
            print("   [WARNING] NFL section not found")

    async def _extract_games(self, page: Page, period: str) -> List[OvertimeGame]:
        """
        Extract games for a specific period (GAME, 1ST HALF, 1ST QUARTER).
        Uses JavaScript evaluation to extract all game data from the page.
        """
        try:
            # Switch period if not GAME
            if period != "GAME":
                await self._switch_period(page, period)
                await page.wait_for_timeout(2000)

            # Extract games using JavaScript (same logic as pregame scraper)
            games_data = await page.evaluate(
                """
                (period) => {
                    const result = { games: [] };

                    // Extract week info, date, time
                    const weekInfoEl = document.querySelector('[ng-bind="gameLine.Comments"]');
                    const gameDateEl = document.querySelector('[ng-bind*="GameDateTimeString | formatGameDate"]');
                    const gameTimeEl = document.querySelector('[ng-bind*="GameDateTimeString | formatGameTime"]');

                    // Get team headings
                    const teamHeadings = Array.from(document.querySelectorAll('h4'));
                    const teams = [];

                    teamHeadings.forEach(h4 => {
                        const text = h4.textContent.trim();
                        const match = text.match(/^(\\d+)\\s+(.+)$/);
                        if (match) {
                            const teamLogo = h4.querySelector('img');
                            teams.push({
                                rotationNumber: match[1],
                                teamName: match[2],
                                logoUrl: teamLogo ? teamLogo.src : null
                            });
                        }
                    });

                    // Get all betting buttons
                    const bettingButtons = Array.from(document.querySelectorAll('button[ng-click*="SendLineToWager"]'));
                    const bettingLines = bettingButtons.map(btn => btn.textContent.trim());

                    // Construct game object
                    if (teams.length >= 2) {
                        const game = {
                            leagueWeekInfo: weekInfoEl ? weekInfoEl.textContent.trim() : null,
                            gameDate: gameDateEl ? gameDateEl.textContent.trim() : null,
                            gameTime: gameTimeEl ? gameTimeEl.textContent.trim() : null,
                            visitor: teams[0],
                            home: teams[1],
                            period: period
                        };

                        // Assign betting lines
                        if (bettingLines.length >= 4) {
                            if (bettingLines.length === 4) {
                                game.visitor.spread = bettingLines[0];
                                game.visitor.total = bettingLines[1];
                                game.home.spread = bettingLines[2];
                                game.home.total = bettingLines[3];
                            } else if (bettingLines.length >= 6) {
                                game.visitor.spread = bettingLines[0];
                                game.visitor.moneyLine = bettingLines[1];
                                game.visitor.total = bettingLines[2];
                                game.home.spread = bettingLines[3];
                                game.home.moneyLine = bettingLines[4];
                                game.home.total = bettingLines[5];
                            }
                        }

                        result.games.push(game);
                    }

                    return result;
                }
            """,
                period,
            )

            # Convert to OvertimeGame objects
            games = []
            for game_data in games_data.get("games", []):
                game = OvertimeGame(
                    **game_data, scraped_at=datetime.now(), is_live=False
                )
                games.append(game)

            return games

        except Exception as e:
            print(f"   Error extracting games for {period}: {e}")
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
        """Format combined output for Billy Walters system"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output = {
            "metadata": {
                "source": "overtime.ag",
                "scraper": "hybrid (playwright + signalr)",
                "scraped_at": datetime.now().isoformat(),
                "version": "1.0.0",
            },
            "account": self.account_info,
            "pregame": {
                "games": [game.model_dump() for game in self.pregame_games],
                "count": len(self.pregame_games),
            },
            "live": {
                "updates": self.live_updates,
                "count": len(self.live_updates),
            },
        }

        # Save to file
        output_file = self.output_dir / f"overtime_hybrid_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"Saved combined output to: {output_file}")
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Pre-game games: {len(self.pregame_games)}")
        print(f"Live updates: {len(self.live_updates)}")
        print(f"Output file: {output_file}")

        return output


async def main():
    """Example usage"""

    scraper = OvertimeHybridScraper(
        headless=False,  # Set True for production
        enable_signalr=True,
        signalr_duration=120,  # Listen for 2 minutes
    )

    result = await scraper.scrape()
    return result


if __name__ == "__main__":
    asyncio.run(main())
