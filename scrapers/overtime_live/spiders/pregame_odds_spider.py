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
    custom_settings = {
        "BOT_NAME": "overtime_pregame",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90_000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [429, 403, 500, 502, 503, 504],
    }

    def __init__(self, sport="both", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_sport = sport.lower()  # "nfl", "cfb", or "both"

    async def start(self):
        """Entry point for the spider"""
        url = "https://overtime.ag/sports#/"
        
        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "domcontentloaded",
                "timeout": 60_000,
            },
            "playwright_page_methods": [
                PageMethod("wait_for_timeout", 1000),
            ],
        }

        yield scrapy.Request(url, meta=meta, callback=self.parse_main, errback=self.errback)

    async def errback(self, failure):
        self.logger.error("Request failed: %r", failure)
        page = failure.request.meta.get("playwright_page")
        if page:
            try:
                await page.close()
            except Exception:
                pass

    async def _perform_login(self, page: Page) -> bool:
        """
        Perform login to overtime.ag if credentials are available.
        Returns True if login successful or already logged in, False otherwise.
        """
        customer_id = os.getenv("OV_CUSTOMER_ID")
        password = os.getenv("OV_CUSTOMER_PASSWORD")

        if not customer_id or not password:
            self.logger.warning("No login credentials found in environment (OV_CUSTOMER_ID, OV_CUSTOMER_PASSWORD)")
            return False

        try:
            # Check if already logged in by looking for logout indicator
            try:
                await page.wait_for_selector("text=/logout/i", timeout=2000)
                self.logger.info("Already logged in")
                return True
            except Exception:
                pass

            # Navigate to login page
            self.logger.info("Navigating to login page...")
            await page.evaluate("() => { location.hash = '#/login'; }")
            await page.wait_for_timeout(1500)

            # Fill in credentials
            self.logger.info("Filling login credentials...")
            customer_id_input = await page.query_selector('input[placeholder*="Customer"], input[name*="customer"], input[type="text"]')
            if customer_id_input:
                await customer_id_input.fill(customer_id)
            
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(password)
            
            # Click login button
            login_btn = await page.query_selector('button:has-text("LOGIN"), button:has-text("Login")')
            if login_btn:
                await login_btn.click()
                await page.wait_for_timeout(3000)
                
                # Check for successful login
                current_hash = await page.evaluate("() => location.hash")
                if "#/login" not in current_hash:
                    self.logger.info("Login successful")
                    return True
                else:
                    self.logger.error("Login failed - still on login page")
                    return False
            else:
                self.logger.error("Login button not found")
                return False

        except Exception as e:
            self.logger.error(f"Login error: {e}", exc_info=True)
            return False

    async def parse_main(self, response: Response):
        """Main parsing logic - handles login and sport selection"""
        page: Page = response.meta["playwright_page"]
        
        # Attempt login
        await self._perform_login(page)
        
        # Navigate back to sports page
        await page.evaluate("() => { location.hash = '#/'; }")
        await page.wait_for_timeout(2000)

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
        
        # Click appropriate sport filter
        if sport == "nfl":
            selector = 'label[for="gl_Football_NFL_G"]'
            league = "NFL"
            sport_name = "nfl"
        else:  # cfb
            selector = 'label[for="gl_Football_COLLEGE_FB"]'
            league = "NCAAF"
            sport_name = "college_football"

        try:
            # Click sport selector using JavaScript for reliability
            await page.evaluate(f'() => {{ const el = document.querySelector("{selector}"); if(el) el.click(); }}')
            await page.wait_for_timeout(2500)
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
        """Extract game data from the page using JavaScript"""
        js_code = """
        () => {
            const games = [];
            
            // Find all game list items
            const listItems = document.querySelectorAll('ul li, .event-row, [class*="game"]');
            
            for (const item of listItems) {
                try {
                    const text = item.innerText || '';
                    
                    // Look for team headings with rotation numbers (e.g., "451 Chicago Bears")
                    const headings = item.querySelectorAll('h4, h3, [class*="team"]');
                    if (headings.length < 2) continue;
                    
                    const awayText = headings[0].innerText || '';
                    const homeText = headings[1].innerText || '';
                    
                    // Parse rotation and team name (e.g., "451 Chicago Bears")
                    const awayMatch = awayText.match(/^(\\d{3,4})\\s+(.+)$/);
                    const homeMatch = homeText.match(/^(\\d{3,4})\\s+(.+)$/);
                    
                    if (!awayMatch || !homeMatch) continue;
                    
                    const awayRot = awayMatch[1];
                    const awayTeam = awayMatch[2];
                    const homeRot = homeMatch[1];
                    const homeTeam = homeMatch[2];
                    
                    // Extract date and time
                    let dateStr = null;
                    let timeStr = null;
                    const dateTimeElements = item.querySelectorAll('div, span');
                    for (const el of dateTimeElements) {
                        const t = el.innerText || '';
                        if (/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\s+\\w+\\s+\\d+$/.test(t.trim())) {
                            dateStr = t.trim();
                        }
                        if (/^\\d{1,2}:\\d{2}\\s+(AM|PM)$/i.test(t.trim())) {
                            timeStr = t.trim();
                        }
                    }
                    
                    // Extract odds from buttons
                    const buttons = item.querySelectorAll('button');
                    const odds = [];
                    for (const btn of buttons) {
                        const btnText = btn.innerText || '';
                        odds.push(btnText.trim());
                    }
                    
                    // Parse markets
                    const markets = { spread: {}, total: {}, moneyline: {} };
                    
                    // Spread: look for patterns like "-2½ -115" or "+3 -110"
                    const spreadRegex = /^([+\\-]\\d+\\.?\\d?)\\s+([+\\-]\\d{2,4})$/;
                    let spreadIdx = 0;
                    for (let i = 0; i < odds.length; i++) {
                        const match = odds[i].match(spreadRegex);
                        if (match && spreadIdx < 2) {
                            const line = parseFloat(match[1].replace('½', '.5'));
                            const price = parseInt(match[2]);
                            if (spreadIdx === 0) {
                                markets.spread.away = { line, price };
                            } else {
                                markets.spread.home = { line, price };
                            }
                            spreadIdx++;
                        }
                    }
                    
                    // Total: look for patterns like "O 51 -110" or "U 48½ -105"
                    const totalRegex = /^([OU])\\s+(\\d+\\.?\\d?)\\s+([+\\-]\\d{2,4})$/i;
                    for (const odd of odds) {
                        const match = odd.match(totalRegex);
                        if (match) {
                            const side = match[1].toUpperCase();
                            const line = parseFloat(match[2].replace('½', '.5'));
                            const price = parseInt(match[3]);
                            if (side === 'O') {
                                markets.total.over = { line, price };
                            } else {
                                markets.total.under = { line, price };
                            }
                        }
                    }
                    
                    // Moneyline: look for standalone prices (e.g., "+150" or "-200")
                    // Usually displayed separately, harder to detect from buttons alone
                    // This is a best-effort extraction
                    
                    games.push({
                        rotation_number: `${awayRot}-${homeRot}`,
                        away_team: awayTeam,
                        home_team: homeTeam,
                        event_date: dateStr,
                        event_time: timeStr,
                        markets: markets,
                    });
                    
                } catch (e) {
                    console.error('Error parsing game:', e);
                }
            }
            
            return games;
        }
        """
        
        try:
            raw_games = await page.evaluate(js_code)
            
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

