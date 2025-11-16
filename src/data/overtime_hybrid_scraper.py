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
from urllib.parse import urlparse, urlencode
import httpx

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
        self.browser_cookies: Optional[str] = None  # Cookie header for SignalR auth
        self.raw_messages: List[Dict[str, Any]] = []  # All raw WebSocket messages

        # Logging
        self.logger = logging.getLogger(__name__)
        self.verbose_logging = True  # Enable detailed WebSocket logging

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

                # Extract cookies for SignalR authentication
                if self.enable_signalr:
                    print("6. Extracting session cookies for SignalR...")
                    cookies = await context.cookies()
                    self.browser_cookies = self._format_cookies(cookies)
                    print(f"   Captured {len(cookies)} cookies")

            finally:
                await browser.close()

    async def _negotiate_signalr(self) -> Optional[str]:
        """
        Perform HTTP negotiation with SignalR server to get connection token.

        Returns:
            Connection token string, or None if negotiation fails
        """
        print("   Performing HTTP negotiation...")

        negotiation_url = "https://ws.ticosports.com/signalr/negotiate"

        # Build query parameters
        params = {
            "clientProtocol": "1.5",
            "connectionData": json.dumps([{"name": "gbsHub"}]),
            "_": str(int(datetime.now().timestamp() * 1000)),  # Timestamp
        }

        # Build headers with cookies
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Origin": "https://overtime.ag",
            "Referer": "https://overtime.ag/",
            "Accept": "application/json",
        }

        if self.browser_cookies:
            headers["Cookie"] = self.browser_cookies

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    negotiation_url,
                    params=params,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    connection_token = data.get("ConnectionToken")
                    connection_id = data.get("ConnectionId")

                    if connection_token:
                        print("   [OK] Negotiation successful")
                        print(f"   Connection ID: {connection_id[:20]}...")
                        return connection_token
                    else:
                        print("   [ERROR] No ConnectionToken in response")
                        return None
                else:
                    print(f"   [ERROR] Negotiation failed: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    return None

        except Exception as e:
            print(f"   [ERROR] Negotiation exception: {e}")
            return None

    async def _signalr_listen(self) -> None:
        """Phase 2: Connect to SignalR for real-time updates"""

        print("1. Connecting to SignalR WebSocket...")
        print("   Server: wss://ws.ticosports.com/signalr")
        print(f"   Duration: {self.signalr_duration} seconds")

        # Build headers with authentication cookies from Playwright session
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Origin": "https://overtime.ag",
            "Host": "ws.ticosports.com",
        }

        # Add authentication cookies if available
        if self.browser_cookies:
            headers["Cookie"] = self.browser_cookies
            print("   Using authenticated session cookies")
        else:
            print("   [WARNING] No session cookies - authentication may fail")

        # Step 1: HTTP Negotiation to get connection token
        connection_token = await self._negotiate_signalr()

        if not connection_token:
            print("   [ERROR] SignalR negotiation failed - cannot connect")
            return

        # Step 2: Build WebSocket URL with connection token
        ws_params = {
            "transport": "webSockets",
            "clientProtocol": "1.5",
            "connectionToken": connection_token,
            "connectionData": json.dumps([{"name": "gbsHub"}]),
        }

        ws_url = f"wss://ws.ticosports.com/signalr/connect?{urlencode(ws_params)}"

        # Build SignalR connection with negotiated token
        print("2. Establishing WebSocket connection...")
        self.signalr_connection = (
            HubConnectionBuilder()
            .with_url(
                ws_url,
                options={
                    "skip_negotiation": True,  # Already negotiated
                    "headers": headers,
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

        # Register handlers BEFORE starting
        self._register_signalr_handlers()

        # Start connection
        try:
            self.signalr_connection.start()
            print("3. SignalR WebSocket connected successfully")

            # NOW monkey-patch the transport's message handler (created after start())
            self._install_raw_frame_interceptor()

            # Subscribe to sports
            if self.customer_id:
                print("4. Subscribing to customer and NFL...")
                self._subscribe_customer()
                self._subscribe_sports()

            # Listen for updates
            print(f"5. Listening for {self.signalr_duration} seconds...")
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

            print("6. SignalR listening complete")
            print(f"   Total live updates: {len(self.live_updates)}")

        except KeyboardInterrupt:
            print("\n   Stopped by user (Ctrl+C)")
        except Exception as e:
            print(f"   [ERROR] SignalR error: {e}")
        finally:
            if self.signalr_connection:
                self.signalr_connection.stop()
                print("7. SignalR connection closed")

    def _install_raw_frame_interceptor(self) -> None:
        """
        Install a raw WebSocket frame interceptor to capture ALL messages.

        This monkey-patches the transport's _on_message handler to log every
        frame BEFORE SignalR's event routing. This lets us discover actual
        event names the server uses during live games.
        """
        try:
            # Access the transport (WebSocket connection)
            if not hasattr(self.signalr_connection, "transport"):
                print("   [WARNING] No transport attribute - cannot intercept frames")
                return

            transport = self.signalr_connection.transport

            # Different signalr-client-aio versions use different attributes
            # Try multiple possible message handler names
            handler_names = ["_on_message", "on_message", "handle_message"]

            for handler_name in handler_names:
                if hasattr(transport, handler_name):
                    original_handler = getattr(transport, handler_name)

                    def make_interceptor(orig_handler):
                        def intercepted_handler(message):
                            # Log every raw frame
                            self._log_raw_message("websocket_frame", message)

                            # Print to console for real-time monitoring
                            try:
                                # Try to parse as JSON to pretty-print
                                import json

                                msg_dict = json.loads(message)
                                msg_preview = json.dumps(msg_dict)[:300]
                            except Exception:
                                # Not JSON, just truncate string
                                msg_preview = str(message)[:300]

                            print(f"\n   [RAW FRAME] {msg_preview}...")

                            # Call original handler to continue normal processing
                            return orig_handler(message)

                        return intercepted_handler

                    # Replace the handler with our interceptor
                    setattr(transport, handler_name, make_interceptor(original_handler))
                    print(
                        f"   [OK] Raw frame interceptor installed on '{handler_name}'"
                    )
                    return

            print(
                "   [WARNING] Could not find message handler - raw frames won't be logged"
            )

        except Exception as e:
            print(f"   [ERROR] Failed to install frame interceptor: {e}")

    def _register_signalr_handlers(self) -> None:
        """Register handlers for SignalR events"""

        # Connection lifecycle
        self.signalr_connection.on_open = self._on_signalr_open
        self.signalr_connection.on_close = self._on_signalr_close
        self.signalr_connection.on_error = self._on_signalr_error

        # Data events (guessed based on common patterns - we'll discover actual names)
        # During live games, check console/logs to see which events actually fire
        self.signalr_connection.on("gameUpdate", self._on_game_update)
        self.signalr_connection.on("linesUpdate", self._on_lines_update)
        self.signalr_connection.on("oddsUpdate", self._on_odds_update)
        self.signalr_connection.on("scoreUpdate", self._on_score_update)
        self.signalr_connection.on("message", self._on_message)

        # Additional potential event names to try
        self.signalr_connection.on("updateLines", self._on_universal_event)
        self.signalr_connection.on("updateOdds", self._on_universal_event)
        self.signalr_connection.on("updateGame", self._on_universal_event)
        self.signalr_connection.on("lineChange", self._on_universal_event)
        self.signalr_connection.on("broadcast", self._on_universal_event)

    def _log_raw_message(self, event_name: str, data: Any) -> None:
        """Log all raw WebSocket messages for debugging"""
        timestamp = datetime.utcnow().isoformat()
        message = {
            "timestamp": timestamp,
            "event": event_name,
            "data": data,
        }
        self.raw_messages.append(message)

        if self.verbose_logging:
            try:
                data_str = (
                    json.dumps(data) if isinstance(data, (dict, list)) else str(data)
                )
                print(
                    f"   [WebSocket] {timestamp} | {event_name} | {data_str[:200]}..."
                )
            except Exception as e:
                print(f"   [WebSocket] {timestamp} | {event_name} | <unparseable: {e}>")

    def _on_universal_event(self, *args, **kwargs) -> None:
        """Universal handler to catch any events we registered"""
        import inspect

        frame = inspect.currentframe()
        event_name = "unknown_event"

        # Try to get the event name from the call stack
        if frame and frame.f_back:
            event_name = frame.f_back.f_locals.get("event", "unknown")

        self._log_raw_message(event_name, {"args": args, "kwargs": kwargs})

        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": event_name,
                "data": {"args": args, "kwargs": kwargs},
            }
        )

        print(f"   [EVENT DETECTED] {event_name}")
        if args:
            print(f"   Args: {args}")
        if kwargs:
            print(f"   Kwargs: {kwargs}")

    def _on_signalr_open(self) -> None:
        """SignalR connection opened"""
        self.logger.info("SignalR connection established")
        print("   [CONNECTED] SignalR WebSocket is open and ready")

    def _on_signalr_close(self) -> None:
        """SignalR connection closed"""
        self.logger.warning("SignalR connection closed")
        print("   [DISCONNECTED] SignalR WebSocket closed")

    def _on_signalr_error(self, error: Any) -> None:
        """SignalR error"""
        self.logger.error(f"SignalR error: {error}")
        print(f"   [ERROR] SignalR: {error}")

    def _on_game_update(self, data: Any) -> None:
        """Handler for game updates"""
        self._log_raw_message("gameUpdate", data)
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "game_update",
                "data": data,
            }
        )
        print("   [GAME UPDATE] Data received!")
        try:
            print(f"   Preview: {json.dumps(data, default=str)[:200]}...")
        except:
            print(f"   Preview: {str(data)[:200]}...")

    def _on_lines_update(self, data: Any) -> None:
        """Handler for lines updates"""
        self._log_raw_message("linesUpdate", data)
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "lines_update",
                "data": data,
            }
        )
        print("   [LINES UPDATE] Data received!")
        try:
            print(f"   Preview: {json.dumps(data, default=str)[:200]}...")
        except:
            print(f"   Preview: {str(data)[:200]}...")

    def _on_odds_update(self, data: Any) -> None:
        """Handler for odds updates"""
        self._log_raw_message("oddsUpdate", data)
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "odds_update",
                "data": data,
            }
        )
        print("   [ODDS UPDATE] Data received!")
        try:
            print(f"   Preview: {json.dumps(data, default=str)[:200]}...")
        except:
            print(f"   Preview: {str(data)[:200]}...")

    def _on_score_update(self, data: Any) -> None:
        """Handler for score updates"""
        self._log_raw_message("scoreUpdate", data)
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "score_update",
                "data": data,
            }
        )
        print("   [SCORE UPDATE] Data received!")
        try:
            print(f"   Preview: {json.dumps(data, default=str)[:200]}...")
        except:
            print(f"   Preview: {str(data)[:200]}...")

    def _on_message(self, message: Any) -> None:
        """Generic message handler"""
        self._log_raw_message("message", message)
        self.live_updates.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "message",
                "data": message,
            }
        )
        print("   [MESSAGE] Generic message received!")
        self.logger.info(f"SignalR message: {message}")

    def _subscribe_customer(self) -> None:
        """Subscribe as customer to SignalR hub"""
        user_data = {
            "customerId": self.customer_id,
            "password": self.password,
        }
        self.signalr_connection.send("SubscribeCustomer", [user_data])

    def _subscribe_sports(self) -> None:
        """Subscribe to NFL sports on SignalR hub"""
        subscriptions = [
            {"sport": "FOOTBALL", "league": "NFL"},
            {"sportId": 1},  # Football often uses sportId 1
            "NFL",
        ]

        try:
            self.signalr_connection.send("SubscribeSports", subscriptions)
        except Exception as e:
            self.logger.error(f"SubscribeSports failed: {e}")

    async def _login(self, page: Page) -> None:
        """
        Login using Playwright with AngularJS-specific selectors.

        Login form structure:
        - Login button: <a ng-click="ShowLoginView()" class="btn btn-signup">LOGIN</a>
        - Customer ID: <input ng-model="Login.customerId" placeholder="Customer Id.">
        - Password: <input ng-model="Login.password" type="password" placeholder="Password">
        - Submit: <button ng-click="Login.Authenticate()" class="btn btn-default btn-login">LOGIN</button>
        """

        # Wait for login button
        await page.wait_for_selector("a.btn-signup", state="attached", timeout=10000)

        # Click login button (JavaScript click bypasses visibility - AngularJS ng-click handler)
        await page.evaluate("""
            () => {
                const loginBtn = document.querySelector('a.btn-signup');
                if (loginBtn) loginBtn.click();
            }
        """)
        await page.wait_for_timeout(2000)

        # Fill credentials using AngularJS ng-model selectors (more reliable than placeholder)
        customer_input = await page.query_selector(
            'input[ng-model="Login.customerId"], input[placeholder*="Customer"]'
        )
        if customer_input:
            await customer_input.fill(self.customer_id)
            print("   Customer ID filled")
        else:
            print("   [WARNING] Customer ID input not found")

        password_input = await page.query_selector(
            'input[ng-model="Login.password"], input[type="password"]'
        )
        if password_input:
            await password_input.fill(self.password)
            print("   Password filled")
        else:
            print("   [WARNING] Password input not found")

        # Submit login using specific button class (AngularJS ng-click="Login.Authenticate()")
        login_btn = await page.query_selector(
            'button.btn-login, button:has-text("LOGIN")'
        )
        if login_btn:
            # Use JavaScript click to ensure AngularJS ng-click handler fires
            await login_btn.click()
            await page.wait_for_timeout(5000)
            print("   Login submitted (waiting for authentication)")
        else:
            print("   [WARNING] Login button not found")

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

    def _format_cookies(self, cookies: List[Dict[str, Any]]) -> str:
        """
        Format Playwright cookies into Cookie header string for SignalR.

        Args:
            cookies: List of cookie dictionaries from Playwright context

        Returns:
            Cookie header string (e.g., "name1=value1; name2=value2")
        """
        cookie_pairs = []
        for cookie in cookies:
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            if name and value:
                cookie_pairs.append(f"{name}={value}")

        return "; ".join(cookie_pairs)

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

        # Save main output file
        output_file = self.output_dir / f"overtime_hybrid_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)

        # Save raw WebSocket messages debug log
        if self.raw_messages:
            debug_file = self.output_dir / f"overtime_websocket_debug_{timestamp}.json"
            debug_output = {
                "metadata": {
                    "purpose": "WebSocket debugging - raw SignalR messages",
                    "scraped_at": datetime.now().isoformat(),
                    "total_messages": len(self.raw_messages),
                },
                "messages": self.raw_messages,
            }
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(debug_output, f, indent=2, default=str)
            print(f"Saved WebSocket debug log to: {debug_file}")
            print(f"  Total raw messages captured: {len(self.raw_messages)}")

        print(f"Saved combined output to: {output_file}")
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Pre-game games: {len(self.pregame_games)}")
        print(f"Live updates: {len(self.live_updates)}")
        print(f"WebSocket messages logged: {len(self.raw_messages)}")
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
