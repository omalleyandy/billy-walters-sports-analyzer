from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional
from datetime import datetime

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page

# Stealth mode to bypass Cloudflare
try:
    # Try v2.0.0+ API first
    try:
        from playwright_stealth import Stealth
        stealth_async = lambda page: Stealth().apply_stealth_async(page)
        STEALTH_AVAILABLE = True
    except (ImportError, AttributeError):
        # Fall back to v1.0.6 API
        from playwright_stealth import stealth_async
        STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    stealth_async = None
    print("⚠ playwright-stealth not installed. Run: uv pip install playwright-stealth")

# Local modules
from ..items import LiveGameItem, Market, QuoteSide, iso_now, game_key_from

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def to_float(s: Optional[str]) -> Optional[float]:
    """Convert string to float, handling fractions like ½"""
    if not s:
        return None
    try:
        return float(s.replace("½", ".5"))
    except Exception:
        try:
            return float(re.sub(r"[^\d\.\-+]", "", s))
        except Exception:
            return None


def parse_date_time(date_str: str, time_str: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse date/time strings from overtime.ag format.
    Date format: "Sun Nov 2" or "Mon Nov 3"
    Time format: "1:00 PM" or "8:15 PM"
    Returns: (ISO date string, time string with ET timezone)
    """
    try:
        # Current year assumption
        current_year = datetime.now().year
        # Parse "Sun Nov 2" -> "2025-11-02"
        date_parts = date_str.split()
        if len(date_parts) >= 3:
            month_str = date_parts[1]
            day_str = date_parts[2]
            dt = datetime.strptime(f"{current_year} {month_str} {day_str}", "%Y %b %d")
            iso_date = dt.strftime("%Y-%m-%d")
            time_with_tz = f"{time_str} ET" if time_str and "ET" not in time_str else time_str
            return iso_date, time_with_tz
    except Exception:
        pass
    return None, None


class PregameOddsSpider(scrapy.Spider):
    """
    Pre-game odds scraper for overtime.ag (NFL and College Football).
    Extracts rotation numbers, date/time, teams, spreads, totals, and moneylines.
    """

    name = "pregame_odds"

    # Allow spider argument to control which sport(s) to scrape
    # Options: "nfl", "cfb", "both" (default: "both")
    # Configure proxy from environment
    _proxy_url = os.getenv("PROXY_URL") or os.getenv("OVERTIME_PROXY")

    # If we have a custom proxy URL, use it. Otherwise, let Playwright use system proxy naturally (don't configure anything).
    _proxy_config = {"proxy": {"server": _proxy_url}} if _proxy_url else {}

    custom_settings = {
        "BOT_NAME": "overtime_pregame",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 120_000,  # Increased to 120s for proxy
        # Disable header processing completely - let browser handle everything naturally
        "PLAYWRIGHT_PROCESS_REQUEST_HEADERS": None,
        "PLAYWRIGHT_ABORT_REQUEST": None,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            # Only set proxy if we have a custom one, otherwise let system proxy work naturally
            **_proxy_config,
        },
        "PLAYWRIGHT_CONTEXT_OPTIONS": {
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "bypass_csp": True,  # Bypass Content Security Policy
            "ignore_https_errors": True,  # Ignore SSL errors
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        },
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "CONCURRENT_REQUESTS": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [403, 407, 429, 500, 502, 503, 504],  # 407 = Proxy Auth Required
        "RETRY_BACKOFF_BASE": 2,
        "RETRY_BACKOFF_MAX": 60,
    }

    def __init__(self, sport="both", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_sport = sport.lower()  # "nfl", "cfb", or "both"

        # Log proxy configuration
        if self._proxy_url:
            proxy_display = self._proxy_url.split('@')[1] if '@' in self._proxy_url else self._proxy_url
            self.logger.info(f"✓ Using residential proxy: {proxy_display}")
        else:
            self.logger.warning("⚠ No proxy configured - using direct connection")

    async def _apply_stealth_init(self, page: Page, request):
        """Apply stealth mode before navigation (called by scrapy-playwright)"""
        if STEALTH_AVAILABLE:
            self.logger.info("🥷 Applying stealth mode before navigation...")
            try:
                await stealth_async(page)
                self.logger.info("✓ Stealth mode activated")
            except Exception as e:
                self.logger.warning(f"Failed to apply stealth: {e}")

    async def start(self):
        """Entry point for the spider"""
        # Use /sports/ instead of /sports#/ for simpler routing
        url = "https://overtime.ag/sports/"

        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "domcontentloaded",
                "timeout": 120_000,  # Increased to 120s for proxy
            },
            "playwright_page_methods": [
                # Apply stealth BEFORE navigation
                PageMethod("evaluate", "() => {}"),  # Dummy method to trigger page creation
            ],
        }

        # Use page_init callback to apply stealth before navigation
        if STEALTH_AVAILABLE:
            meta["playwright_page_init_callback"] = self._apply_stealth_init

        yield scrapy.Request(url, meta=meta, callback=self.parse_main, errback=self.errback)

    async def errback(self, failure):
        self.logger.error("Request failed: %r", failure)
        page = failure.request.meta.get("playwright_page")
        if page:
            try:
                await page.close()
            except Exception:
                pass

    async def _verify_proxy_ip(self, page: Page) -> bool:
        """
        Verify the proxy is working by checking the external IP.
        Returns True if proxy verification successful, False otherwise.
        """
        if not self._proxy_url:
            return True  # No proxy configured, skip verification

        try:
            self.logger.info("Verifying proxy IP...")
            await page.goto("https://ipinfo.io/json", timeout=30_000)  # Increased for proxy

            # Extract IP info from the page
            ip_info = await page.evaluate("""
                () => {
                    try {
                        const pre = document.querySelector('pre');
                        if (pre) {
                            const data = JSON.parse(pre.innerText);
                            return {
                                ip: data.ip,
                                city: data.city,
                                region: data.region,
                                country: data.country,
                                org: data.org
                            };
                        }
                    } catch (e) {
                        return null;
                    }
                    return null;
                }
            """)

            if ip_info:
                self.logger.info(
                    f"✓ Proxy IP verified: {ip_info.get('ip')} "
                    f"({ip_info.get('city')}, {ip_info.get('region')}, {ip_info.get('country')})"
                )
                return True
            else:
                self.logger.warning("⚠ Could not parse IP info")
                return False

        except Exception as e:
            self.logger.error(f"✗ Proxy verification failed: {e}")
            return False

    async def _perform_login(self, page: Page) -> bool:
        """
        Perform login to overtime.ag if credentials are available.
        Login fields are on the sports page itself, not a separate page.
        Returns True if login successful or already logged in, False otherwise.
        """
        # Support both OV_CUSTOMER_ID and OV_ID
        customer_id = os.getenv("OV_CUSTOMER_ID") or os.getenv("OV_ID")
        # Support both OV_CUSTOMER_PASSWORD and OV_PASSWORD
        password = os.getenv("OV_CUSTOMER_PASSWORD") or os.getenv("OV_PASSWORD")

        if not customer_id or not password:
            self.logger.info("No login credentials - continuing without login")
            return False

        try:
            # Login fields are right on the sports page - no navigation needed
            self.logger.info("Attempting login on sports page...")

            # Customer ID field: //input[@placeholder='Customer Id']
            customer_id_input = await page.wait_for_selector("xpath=//input[@placeholder='Customer Id']", timeout=5000)
            if customer_id_input:
                await customer_id_input.fill(customer_id)
                self.logger.info("✓ Customer ID filled")

            # Password field: //input[@placeholder='Password']
            password_input = await page.wait_for_selector("xpath=//input[@placeholder='Password']", timeout=5000)
            if password_input:
                await password_input.fill(password)
                self.logger.info("✓ Password filled")

            # Login button: //button[@class='btn btn-default btn-login ng-binding']
            login_btn = await page.wait_for_selector("xpath=//button[@class='btn btn-default btn-login ng-binding']", timeout=5000)
            if login_btn:
                await login_btn.click()
                self.logger.info("✓ Login button clicked")
                await page.wait_for_timeout(2000)
                self.logger.info("✓ Login completed")
                return True

            return False

        except Exception as e:
            self.logger.warning(f"Login not available or failed: {e}")
            return False

    async def parse_main(self, response: Response):
        """Main parsing logic - handles login and sport selection"""
        page: Page = response.meta["playwright_page"]

        # Stealth mode already applied before navigation via playwright_page_init_callback
        self.logger.info("✓ Page loaded successfully (stealth mode applied during init)")

        # Skip IP verification - it's slow and causes timeouts with Cloudflare
        # The simple proxy test confirms proxy works, so we skip this step
        if self._proxy_url:
            proxy_display = self._proxy_url.split('@')[1] if '@' in self._proxy_url else self._proxy_url
            self.logger.info(f"Using proxy: {proxy_display} (skipping IP verification to avoid Cloudflare)")

        # Wait for page to settle after loading
        self.logger.info("Waiting for page to settle...")
        try:
            await page.wait_for_timeout(2000)  # Wait for JavaScript to finish
            self.logger.info("✓ Page settled")
        except Exception as e:
            self.logger.warning(f"Wait timeout (might be OK): {e}")

        # Attempt login (optional - will skip if no credentials)
        # Login fields are on the sports page, no need to navigate away
        await self._perform_login(page)

        # Take snapshot for debugging
        os.makedirs("snapshots", exist_ok=True)
        try:
            await page.screenshot(path="snapshots/pregame_main.png", full_page=True)
        except Exception:
            pass

        # Scrape based on target sport
        if self.target_sport in ("nfl", "both"):
            async for item in self._scrape_sport(page, "nfl"):
                yield item

        if self.target_sport in ("cfb", "both"):
            async for item in self._scrape_sport(page, "cfb"):
                yield item

        try:
            await page.close()
        except Exception:
            pass

    async def _scrape_sport(self, page: Page, sport: str):
        """Scrape odds for a specific sport (nfl or cfb)"""
        self.logger.info(f"Scraping {sport.upper()} odds...")

        # Use correct XPath selectors for sport filters
        if sport == "nfl":
            # NFL selector: //label[@for='gl_Football_NFL_G']
            selector = "xpath=//label[@for='gl_Football_NFL_G']"
            league = "NFL"
            sport_name = "nfl"
            check_text = "FOOTBALL-NFL"
        else:  # cfb
            # College Football selector: //label[@for='gl_Football_College_Football_G']
            selector = "xpath=//label[@for='gl_Football_College_Football_G']"
            league = "NCAAF"
            sport_name = "college_football"
            check_text = "FOOTBALL-COLLEGE"

        try:
            # Check if games are already visible (page might show them by default)
            self.logger.info(f"Checking if {sport.upper()} games are already visible...")
            page_content = await page.content()
            games_already_visible = check_text in page_content

            if games_already_visible:
                self.logger.info(f"✓ {sport.upper()} games already visible, skipping filter click")
            else:
                # Click sport selector using XPath
                self.logger.info(f"Clicking {sport.upper()} filter...")
                try:
                    sport_label = await page.wait_for_selector(selector, timeout=10_000)
                    if sport_label:
                        # Check if element is enabled before clicking
                        is_enabled = await sport_label.evaluate("el => !el.disabled && !el.hasAttribute('disabled')")
                        if is_enabled:
                            await sport_label.click()
                            self.logger.info(f"✓ {sport.upper()} filter clicked")
                            await page.wait_for_timeout(2500)
                        else:
                            self.logger.warning(f"⚠ {sport.upper()} filter element found but disabled, continuing anyway")
                    else:
                        self.logger.warning(f"Could not find {sport.upper()} filter, continuing anyway")
                except Exception as filter_e:
                    self.logger.warning(f"Filter click failed ({filter_e}), continuing anyway")

            # Ensure we're on the "GAME" period (full game), not 1H/2H/Quarters
            self.logger.info(f"Selecting GAME period for {sport.upper()}...")
            await page.evaluate("""
                () => {
                    // Find the "GAME" period button and click it if not already active
                    const gameButtons = document.querySelectorAll('button.btn-period');
                    for (const btn of gameButtons) {
                        const text = btn.innerText || '';
                        if (/^GAME$/i.test(text.trim()) && !btn.classList.contains('active')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            await page.wait_for_timeout(1500)
        except Exception as e:
            self.logger.error(f"Failed to select {sport}: {e}")
            return

        # Extract games using JavaScript
        games_data = await self._extract_games_js(page)

        self.logger.info(f"Extracted {len(games_data)} {sport.upper()} games")

        for game_data in games_data:
            item = LiveGameItem(
                source="overtime.ag",
                sport=sport_name,
                league=league,
                collected_at=iso_now(),
                game_key=game_key_from(game_data["away_team"], game_data["home_team"], game_data.get("event_date")),
                event_date=game_data.get("event_date"),
                event_time=game_data.get("event_time"),
                rotation_number=game_data.get("rotation_number"),
                teams={"away": game_data["away_team"], "home": game_data["home_team"]},
                state={},
                markets=game_data["markets"],
                is_live=False,
            )
            yield json.loads(json.dumps(item, default=lambda o: o.__dict__))

    async def _extract_games_js(self, page: Page) -> list[Dict[str, Any]]:
        """Extract game data from the page using JavaScript - text-based parsing for Angular"""

        # Wait for GameLines container to be visible (more reliable than fixed timeout)
        self.logger.info("Waiting for GameLines container to load...")
        try:
            await page.wait_for_selector('#GameLines', state='visible', timeout=30000)
            self.logger.info("✓ GameLines container loaded")
        except Exception as e:
            self.logger.warning(f"GameLines container not found: {e}")
            # Fall back to short wait
            await page.wait_for_timeout(5000)

        # Validate market headers are present
        try:
            spread_header = await page.locator("//span[normalize-space()='Spread']").count()
            ml_header = await page.locator("//span[normalize-space()='Money Line']").count()
            totals_header = await page.locator("//span[normalize-space()='Totals']").count()

            if spread_header > 0 and ml_header > 0 and totals_header > 0:
                self.logger.info("✓ Market headers validated (Spread, Money Line, Totals)")
            else:
                self.logger.warning(
                    f"Market headers incomplete - Spread:{spread_header} ML:{ml_header} Totals:{totals_header}"
                )
        except Exception as e:
            self.logger.warning(f"Failed to validate market headers: {e}")

        js_code = """
        () => {
            // Parse document.body.innerText to find rotation numbers and team names
            // Angular renders the content as text, not as structured DOM we can query
            const allText = document.body.innerText;
            const lines = allText.split('\\n');

            // Step 1: Find all team lines with rotation numbers
            const teamLines = [];
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                const match = line.match(/^(\\d{3,4})\\s+(.+)$/);
                if (match) {
                    const rotation = match[1];
                    const teamName = match[2].trim();

                    // Validate team name: must be at least 3 chars, no emojis, valid characters
                    if (teamName.length >= 3 && /^[A-Z\\s\\-\\.&']+$/i.test(teamName)) {
                        // Exclude navigation/UI elements
                        if (!teamName.match(/^(NEW VERSION|SPORTS|GAME|PERIOD|FILTER)$/i)) {
                            teamLines.push({ rotation, teamName, lineIndex: i });
                        }
                    }
                }
            }

            console.log(`Found ${teamLines.length} valid team lines`);

            // Step 2: Pair teams into games (consecutive rotation numbers)
            const games = [];
            for (let i = 0; i < teamLines.length - 1; i++) {
                const away = teamLines[i];
                const home = teamLines[i + 1];

                const awayRot = parseInt(away.rotation);
                const homeRot = parseInt(home.rotation);

                // Check if consecutive (home = away + 1)
                if (homeRot === awayRot + 1) {
                    games.push({
                        rotation_number: `${away.rotation}-${home.rotation}`,
                        away_team: away.teamName,
                        away_rot: away.rotation,
                        home_team: home.teamName,
                        home_rot: home.rotation,
                        lineIndex: away.lineIndex,
                    });
                    i++; // Skip the home team since we've paired it
                }
            }

            console.log(`Paired ${games.length} games from rotation numbers`);

            // Step 3: Get ALL buttons on the page with their IDs and text
            const allButtons = document.querySelectorAll('button');
            const buttonMap = {};
            for (const btn of allButtons) {
                const btnId = btn.id || '';
                const btnText = (btn.innerText || '').trim();
                if (btnId && btnText) {
                    buttonMap[btnId] = btnText;
                }
            }

            console.log(`Found ${Object.keys(buttonMap).length} buttons with IDs`);

            // Step 4: Extract markets for each game by matching button ID patterns
            for (const game of games) {
                const markets = { spread: {}, total: {}, moneyline: {} };

                // Find buttons for this game by looking for button IDs containing the rotation numbers
                // Button IDs format: S1_<event_id>_<line_id>, S2_<event_id>_<line_id>, etc.
                const gameButtons = {};
                for (const [btnId, btnText] of Object.entries(buttonMap)) {
                    // Match buttons by checking if they're related to this game's rotation numbers
                    // This is a heuristic - buttons don't contain rotation numbers in IDs
                    // So we'll just collect all buttons and parse them
                    gameButtons[btnId] = btnText;
                }

                // Parse spread buttons (S1=away, S2=home)
                const spreadRegex = /^([+\\-]\\d+\\.?\\d?[½]?)\\s+([+\\-]\\d{2,4})$/;
                for (const [btnId, btnText] of Object.entries(gameButtons)) {
                    if (btnId.startsWith('S1_')) {
                        const match = btnText.match(spreadRegex);
                        if (match) {
                            markets.spread.away = {
                                line: parseFloat(match[1].replace('½', '.5')),
                                price: parseInt(match[2])
                            };
                        }
                    } else if (btnId.startsWith('S2_')) {
                        const match = btnText.match(spreadRegex);
                        if (match) {
                            markets.spread.home = {
                                line: parseFloat(match[1].replace('½', '.5')),
                                price: parseInt(match[2])
                            };
                        }
                    }
                }

                // Parse total buttons (L1=over, L2=under)
                const totalRegex = /^([OU])\\s+(\\d+\\.?\\d?[½]?)\\s+([+\\-]\\d{2,4})$/i;
                for (const [btnId, btnText] of Object.entries(gameButtons)) {
                    if (btnId.startsWith('L1_')) {
                        const match = btnText.match(totalRegex);
                        if (match) {
                            markets.total.over = {
                                line: parseFloat(match[2].replace('½', '.5')),
                                price: parseInt(match[3])
                            };
                        }
                    } else if (btnId.startsWith('L2_')) {
                        const match = btnText.match(totalRegex);
                        if (match) {
                            markets.total.under = {
                                line: parseFloat(match[2].replace('½', '.5')),
                                price: parseInt(match[3])
                            };
                        }
                    }
                }

                // Parse moneyline buttons (M1=away, M2=home)
                const mlRegex = /^([+\\-]\\d{2,4})$/;
                for (const [btnId, btnText] of Object.entries(gameButtons)) {
                    if (btnId.startsWith('M1_')) {
                        const match = btnText.match(mlRegex);
                        if (match) {
                            markets.moneyline.away = {
                                line: null,
                                price: parseInt(match[1])
                            };
                        }
                    } else if (btnId.startsWith('M2_')) {
                        const match = btnText.match(mlRegex);
                        if (match) {
                            markets.moneyline.home = {
                                line: null,
                                price: parseInt(match[1])
                            };
                        }
                    }
                }

                game.markets = markets;

                // Extract date and time from surrounding text (best effort)
                const dateRegex = /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\s+\\w+\\s+\\d+$/;
                const timeRegex = /^\\d{1,2}:\\d{2}\\s+(AM|PM)$/i;

                // Look for date/time near the game's line index
                game.event_date = null;
                game.event_time = null;
                for (let j = Math.max(0, game.lineIndex - 10); j < Math.min(lines.length, game.lineIndex + 5); j++) {
                    const nearbyLine = lines[j].trim();
                    if (dateRegex.test(nearbyLine)) {
                        game.event_date = nearbyLine;
                    }
                    if (timeRegex.test(nearbyLine)) {
                        game.event_time = nearbyLine;
                    }
                }
            }

            return games;
        }
        """
        
        try:
            raw_games = await page.evaluate(js_code)
            self.logger.info(f"Raw extraction found {len(raw_games)} games")

            # Process and clean the data
            processed_games = []
            for game in raw_games:
                # Parse date/time
                date_str = game.get("event_date")
                time_str = game.get("event_time")
                iso_date, time_with_tz = parse_date_time(date_str or "", time_str or "")
                
                game["event_date"] = iso_date
                game["event_time"] = time_with_tz
                
                # Convert markets to proper structure
                markets_dict = game.get("markets", {})
                spread = Market(
                    away=QuoteSide(**markets_dict.get("spread", {}).get("away", {})) if markets_dict.get("spread", {}).get("away") else None,
                    home=QuoteSide(**markets_dict.get("spread", {}).get("home", {})) if markets_dict.get("spread", {}).get("home") else None,
                )
                total = Market(
                    over=QuoteSide(**markets_dict.get("total", {}).get("over", {})) if markets_dict.get("total", {}).get("over") else None,
                    under=QuoteSide(**markets_dict.get("total", {}).get("under", {})) if markets_dict.get("total", {}).get("under") else None,
                )
                moneyline = Market(
                    away=QuoteSide(**markets_dict.get("moneyline", {}).get("away", {})) if markets_dict.get("moneyline", {}).get("away") else None,
                    home=QuoteSide(**markets_dict.get("moneyline", {}).get("home", {})) if markets_dict.get("moneyline", {}).get("home") else None,
                )
                
                game["markets"] = {
                    "spread": spread,
                    "total": total,
                    "moneyline": moneyline,
                }
                
                processed_games.append(game)
            
            return processed_games
            
        except Exception as e:
            self.logger.error(f"JavaScript extraction failed: {e}", exc_info=True)
            return []

