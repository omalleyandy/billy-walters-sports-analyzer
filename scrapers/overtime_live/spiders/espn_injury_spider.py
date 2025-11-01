from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, List
from datetime import datetime

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page, TimeoutError as PWTimeout

# Local modules
from ..items import InjuryReportItem, iso_now

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


class ESPNInjurySpider(scrapy.Spider):
    """
    Scraper for ESPN injury reports (focus: NCAAF).
    
    Collects player injury status (Out, Doubtful, Questionable, Probable)
    to inform betting decisions and gate logic.
    
    Usage:
        scrapy crawl espn_injuries
        
    Environment variables:
        ESPN_INJURY_URL - custom injury report URL (optional)
        ESPN_SPORT - sport filter: "football", "basketball" (default: football)
        ESPN_LEAGUE - league filter: "college-football", "nfl" (default: college-football)
    """

    name = "espn_injuries"

    custom_settings = {
        "BOT_NAME": "espn_injuries",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60_000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "CONCURRENT_REQUESTS": 2,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
    }

    def start_requests(self):
        """Entry point for the spider."""
        # Allow override via environment
        sport = os.getenv("ESPN_SPORT", "football")
        league = os.getenv("ESPN_LEAGUE", "college-football")
        
        # ESPN injury report URLs
        injury_url = os.getenv("ESPN_INJURY_URL") or f"https://www.espn.com/{sport}/{league}/injuries"
        
        self.logger.info(f"Starting ESPN injury scraper for: {injury_url}")

        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "domcontentloaded",
                "timeout": 60_000,
            },
            "playwright_page_methods": [
                PageMethod("wait_for_timeout", 2000),  # Let dynamic content load
            ],
        }

        yield scrapy.Request(
            injury_url,
            meta=meta,
            callback=self.parse_injury_page,
            errback=self.errback,
        )

    async def errback(self, failure):
        """Handle request failures."""
        self.logger.error("Request failed: %r", failure)
        page = failure.request.meta.get("playwright_page")
        if page:
            os.makedirs("snapshots", exist_ok=True)
            try:
                await page.screenshot(path="snapshots/espn_injury_error.png", full_page=True)
                self.logger.error("Saved error screenshot to snapshots/espn_injury_error.png")
            except Exception:
                self.logger.debug("Could not write error screenshot", exc_info=True)
            try:
                await page.close()
            except Exception:
                pass

    async def parse_injury_page(self, response: Response):
        """Parse the ESPN injury report page."""
        page: Page = response.meta["playwright_page"]
        
        # Take a snapshot for debugging
        os.makedirs("snapshots", exist_ok=True)
        try:
            await page.screenshot(path="snapshots/espn_injury_page.png", full_page=True)
            self.logger.info("Saved injury page screenshot")
        except Exception:
            pass

        # Try multiple parsing strategies
        injuries = []
        
        # Strategy 1: Try to extract from ESPN's JSON data embedded in page
        injuries.extend(await self._extract_from_json(page))
        
        # Strategy 2: Parse DOM structure
        if not injuries:
            injuries.extend(await self._extract_from_dom(page))
        
        # Strategy 3: Text-based extraction (fallback)
        if not injuries:
            injuries.extend(await self._extract_from_text(page))

        # Emit items
        for injury_data in injuries:
            item = InjuryReportItem(
                source="espn",
                sport=injury_data.get("sport", "college_football"),
                league=injury_data.get("league", "NCAAF"),
                collected_at=iso_now(),
                team=injury_data["team"],
                team_abbr=injury_data.get("team_abbr"),
                player_name=injury_data["player_name"],
                position=injury_data.get("position"),
                injury_status=injury_data["injury_status"],
                injury_type=injury_data.get("injury_type"),
                date_reported=injury_data.get("date_reported"),
                game_date=injury_data.get("game_date"),
                opponent=injury_data.get("opponent"),
                notes=injury_data.get("notes"),
            )
            yield json.loads(json.dumps(item, default=lambda o: o.__dict__))

        self.logger.info(f"Extracted {len(injuries)} injury reports")

        try:
            await page.close()
        except Exception:
            pass

    async def _extract_from_json(self, page: Page) -> List[Dict[str, Any]]:
        """
        Try to extract injury data from embedded JSON in the page.
        ESPN often embeds structured data in script tags.
        """
        script = """
        () => {
            // Look for ESPN's data in window object or script tags
            if (window.__espnfitt__) {
                return window.__espnfitt__;
            }
            
            // Check for JSON-LD or other structured data
            const scripts = Array.from(document.querySelectorAll('script[type="application/json"], script[type="application/ld+json"]'));
            for (const script of scripts) {
                try {
                    const data = JSON.parse(script.textContent);
                    if (data && (data.injuries || data.teams)) {
                        return data;
                    }
                } catch (e) {}
            }
            
            return null;
        }
        """
        try:
            data = await page.evaluate(script)
            if data:
                self.logger.info("Found embedded JSON data")
                return self._parse_json_injuries(data)
        except Exception:
            self.logger.debug("No JSON data found", exc_info=True)
        
        return []

    def _parse_json_injuries(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse injury data from ESPN's JSON structure."""
        injuries = []
        
        # ESPN's structure may vary - handle common patterns
        teams = data.get("teams", [])
        if isinstance(teams, list):
            for team in teams:
                team_name = team.get("team", {}).get("displayName", "")
                team_abbr = team.get("team", {}).get("abbreviation", "")
                
                players = team.get("injuries", [])
                for player in players:
                    injuries.append({
                        "team": team_name,
                        "team_abbr": team_abbr,
                        "player_name": player.get("athlete", {}).get("displayName", ""),
                        "position": player.get("athlete", {}).get("position", {}).get("abbreviation", ""),
                        "injury_status": player.get("status", ""),
                        "injury_type": player.get("type", ""),
                        "date_reported": player.get("date", ""),
                        "game_date": None,
                        "opponent": None,
                        "notes": player.get("details", ""),
                    })
        
        return injuries

    async def _extract_from_dom(self, page: Page) -> List[Dict[str, Any]]:
        """
        Parse injury data from the DOM structure.
        ESPN typically uses tables or card layouts for injury reports.
        """
        script = """
        () => {
            const injuries = [];
            
            // Look for injury tables (common ESPN pattern)
            const tables = document.querySelectorAll('table.Table, .injuries-table, [class*="InjuriesTable"]');
            
            for (const table of tables) {
                // Try to find team name (usually in header)
                let teamName = '';
                const teamHeader = table.closest('div[class*="TeamSection"]') || 
                                 table.closest('section') || 
                                 table.previousElementSibling;
                
                if (teamHeader) {
                    const teamText = teamHeader.textContent || '';
                    const teamMatch = teamText.match(/([A-Z][a-z]+(\\s+[A-Z][a-z]+)*)/);
                    if (teamMatch) teamName = teamMatch[0].trim();
                }
                
                // Parse table rows
                const rows = table.querySelectorAll('tbody tr, tr[class*="Table__TR"]');
                
                for (const row of rows) {
                    const cells = row.querySelectorAll('td, [class*="Table__TD"]');
                    if (cells.length >= 3) {
                        const playerName = cells[0]?.textContent?.trim() || '';
                        const position = cells[1]?.textContent?.trim() || '';
                        const injuryInfo = cells[2]?.textContent?.trim() || '';
                        const status = cells[3]?.textContent?.trim() || '';
                        
                        if (playerName) {
                            injuries.push({
                                team: teamName,
                                player_name: playerName,
                                position: position,
                                injury_type: injuryInfo,
                                injury_status: status || 'Unknown',
                                raw_html: row.innerHTML.slice(0, 500)
                            });
                        }
                    }
                }
            }
            
            // Alternative: Look for card-based layouts
            if (injuries.length === 0) {
                const cards = document.querySelectorAll('[class*="InjuryCard"], .injury-item, [class*="injury"]');
                
                for (const card of cards) {
                    const text = card.textContent || '';
                    const playerMatch = text.match(/([A-Z][a-z]+\\s+[A-Z][a-z]+)/);
                    const statusMatch = text.match(/\\b(Out|Doubtful|Questionable|Probable|Day-to-Day)\\b/i);
                    
                    if (playerMatch && statusMatch) {
                        injuries.push({
                            team: '',
                            player_name: playerMatch[0],
                            position: '',
                            injury_type: '',
                            injury_status: statusMatch[0],
                            raw_text: text.slice(0, 200)
                        });
                    }
                }
            }
            
            return injuries;
        }
        """
        
        try:
            results = await page.evaluate(script)
            if isinstance(results, list) and results:
                self.logger.info(f"Extracted {len(results)} injuries from DOM")
                return self._normalize_injuries(results)
        except Exception:
            self.logger.debug("DOM extraction failed", exc_info=True)
        
        return []

    async def _extract_from_text(self, page: Page) -> List[Dict[str, Any]]:
        """
        Fallback: Extract injury data from page text using pattern matching.
        """
        try:
            page_text = await page.evaluate("() => document.body.innerText")
            
            # Save for debugging
            os.makedirs("snapshots", exist_ok=True)
            with open("snapshots/espn_injury_text.txt", "w", encoding="utf-8") as f:
                f.write(page_text[:50000])
            
            injuries = []
            
            # Pattern: Look for player names followed by injury status
            # Example: "Joe Smith QB Out Knee injury"
            pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(\w{1,3})\s+(Out|Doubtful|Questionable|Probable|Day-to-Day)\s*([A-Za-z\s]*)?'
            
            matches = re.finditer(pattern, page_text, re.MULTILINE)
            for match in matches:
                injuries.append({
                    "team": "",
                    "player_name": match.group(1),
                    "position": match.group(2),
                    "injury_status": match.group(3),
                    "injury_type": match.group(4).strip() if match.group(4) else None,
                })
            
            if injuries:
                self.logger.info(f"Extracted {len(injuries)} injuries from text")
                return self._normalize_injuries(injuries)
                
        except Exception:
            self.logger.debug("Text extraction failed", exc_info=True)
        
        return []

    def _normalize_injuries(self, raw_injuries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize injury data to consistent format.
        Clean up text, standardize status values, etc.
        """
        normalized = []
        
        for injury in raw_injuries:
            # Clean up status
            status = injury.get("injury_status", "").strip()
            status_map = {
                "out": "Out",
                "doubtful": "Doubtful",
                "questionable": "Questionable",
                "probable": "Probable",
                "day-to-day": "Day-to-Day",
                "dtd": "Day-to-Day",
            }
            normalized_status = status_map.get(status.lower(), status)
            
            # Only include if we have minimum required data
            if injury.get("player_name") and normalized_status:
                normalized.append({
                    "sport": "college_football",
                    "league": "NCAAF",
                    "team": injury.get("team", "").strip(),
                    "team_abbr": injury.get("team_abbr", ""),
                    "player_name": injury.get("player_name", "").strip(),
                    "position": injury.get("position", "").strip() or None,
                    "injury_status": normalized_status,
                    "injury_type": injury.get("injury_type", "").strip() or None,
                    "date_reported": injury.get("date_reported") or datetime.now().strftime("%Y-%m-%d"),
                    "game_date": injury.get("game_date"),
                    "opponent": injury.get("opponent"),
                    "notes": injury.get("notes"),
                })
        
        return normalized

