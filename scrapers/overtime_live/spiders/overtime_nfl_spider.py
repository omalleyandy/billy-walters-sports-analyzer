"""
Overtime.ag NFL Spider using YAML Clickmaps.

Reads clickmaps/nfl_clickmap.yaml to:
- Authenticate
- Navigate to NFL markets
- Extract game lines and odds
- Track odds changes with CDP integration
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page

# Local modules
from ..clickmap_executor import ClickmapExecutor
from ..cdp_helpers import setup_cdp_interception, save_api_response


class OvertimeNFLSpider(scrapy.Spider):
    """
    NFL odds scraper using YAML clickmap navigation.
    
    Reads: clickmaps/nfl_clickmap.yaml
    Outputs: data/overtime_nfl/ (JSONL, Parquet, CSV)
    
    Usage:
        uv run scrapy crawl overtime_nfl
        uv run scrapy crawl overtime_nfl -a flow=nfl_1h  # For 1st half lines
    """
    
    name = "overtime_nfl"
    
    def __init__(self, flow: str = None, *args, **kwargs):
        """
        Initialize NFL spider with optional flow override.
        
        Args:
            flow: Override the active_flow from YAML (e.g., 'nfl_1h')
        """
        super().__init__(*args, **kwargs)
        self.flow_override = flow
        self.cdp_session = None
        
        # Load clickmap
        clickmap_path = Path(__file__).parents[3] / "clickmaps" / "nfl_clickmap.yaml"
        self.executor = ClickmapExecutor(str(clickmap_path))
        self.executor.logger = self.logger
        
        # Override flow if specified
        if self.flow_override:
            self.executor.config['active_flow'] = self.flow_override
            self.logger.info(f"Flow overridden to: {self.flow_override}")
    
    custom_settings = {
        "BOT_NAME": "overtime_nfl",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90_000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [429, 403, 500, 502, 503, 504],
        "ITEM_PIPELINES": {
            "scrapers.overtime_live.pipelines.ParquetPipeline": 300,
            "scrapers.overtime_live.pipelines.CSVPipeline": 310,
            "scrapers.overtime_live.pipelines.OddsChangeTrackerPipeline": 320,
        },
        "OVERTIME_OUT_DIR": "data/overtime_nfl",
    }
    
    async def start(self):
        """Entry point for the spider."""
        start_url = self.executor.config.get('start_url', 'https://overtime.ag/sports')
        
        # Check proxy configuration
        proxy_url = os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")
        context_kwargs = {"proxy": {"server": proxy_url}} if proxy_url else None
        
        goto_kwargs = {
            "wait_until": "commit",  # Don't wait for page load - just navigate
            "timeout": 15_000,  # 15 seconds max
        }
        
        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": goto_kwargs,
            "playwright_page_methods": [
                PageMethod("wait_for_timeout", 3000),  # Wait 3s after navigation
            ],
        }
        
        if context_kwargs:
            meta["playwright_context_kwargs"] = context_kwargs
        
        self.logger.info(f"Starting scrape: {start_url}")
        
        yield scrapy.Request(
            start_url,
            meta=meta,
            callback=self.parse_board,
            errback=self.errback,
        )
    
    async def errback(self, failure):
        """Handle request failures."""
        self.logger.error(f"Request failed: {failure}")
        page = failure.request.meta.get("playwright_page")
        if page:
            os.makedirs("snapshots", exist_ok=True)
            try:
                await page.screenshot(path="snapshots/overtime_nfl_error.png", full_page=True)
                self.logger.info("Error screenshot saved")
            except Exception:
                pass
            try:
                await page.close()
            except Exception:
                pass
    
    async def _setup_cdp_session(self, page: Page):
        """Setup CDP session for network interception."""
        try:
            async def api_response_handler(url: str, body: str):
                """Handle captured API responses."""
                try:
                    save_api_response(url, body, "data/overtime_nfl")
                except Exception as e:
                    self.logger.error(f"Error saving API response: {e}")
            
            self.cdp_session = await setup_cdp_interception(
                page,
                api_response_handler
            )
            self.logger.info("CDP network interception enabled")
        except Exception as e:
            self.logger.warning(f"Could not enable CDP interception: {e}")
    
    async def parse_board(self, response: Response):
        """Main parsing logic using clickmap executor."""
        page: Page = response.meta["playwright_page"]
        
        try:
            # Setup CDP interception
            await self._setup_cdp_session(page)
            
            # Take initial screenshot
            os.makedirs("snapshots", exist_ok=True)
            try:
                await page.screenshot(path="snapshots/overtime_nfl_initial.png", full_page=True)
                self.logger.info("Initial screenshot saved")
            except Exception:
                pass
            
            # Step 1: Authenticate
            self.logger.info("Starting authentication...")
            await self.executor.authenticate(page)
            await page.wait_for_timeout(1500)
            
            # Screenshot after auth
            try:
                await page.screenshot(path="snapshots/overtime_nfl_after_auth.png", full_page=True)
            except Exception:
                pass
            
            # Step 2: Execute navigation flow
            flow_name = self.executor.config.get('active_flow')
            self.logger.info(f"Executing flow: {flow_name}")
            await self.executor.execute_flow(page, flow_name)
            await page.wait_for_timeout(2000)
            
            # Screenshot after navigation
            try:
                await page.screenshot(path="snapshots/overtime_nfl_after_nav.png", full_page=True)
            except Exception:
                pass
            
            # Step 3: Extract data
            self.logger.info("Extracting game data...")
            games = await self.executor.extract_data(page)
            
            self.logger.info(f"Extracted {len(games)} games")
            
            # Step 4: Yield items
            for game in games:
                item = self._build_item(game)
                yield item
            
            # Final screenshot
            try:
                await page.screenshot(path="snapshots/overtime_nfl_final.png", full_page=True)
            except Exception:
                pass
        
        finally:
            try:
                await page.close()
            except Exception:
                pass
    
    def _build_item(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build standardized item from extracted game data.
        
        Args:
            game_data: Raw game data from clickmap extraction
            
        Returns:
            Standardized item dictionary
        """
        meta = game_data.get('_meta', {})
        
        # Build teams dict
        teams = {
            "away": game_data.get('away_team', ''),
            "home": game_data.get('home_team', ''),
        }
        
        # Build markets dict (simplified for now - parser will enhance later)
        markets = {
            "spread": {
                "raw": game_data.get('spread_raw', ''),
            },
            "total": {
                "raw": game_data.get('totals_raw', ''),
            },
            "moneyline": {
                "raw": game_data.get('moneyline_raw', ''),
            },
        }
        
        # Build game key
        game_key = f"{teams['away']}_{teams['home']}".lower().replace(' ', '_')
        
        item = {
            "source": "overtime.ag",
            "sport": "nfl",
            "league": meta.get('league', 'NFL'),
            "scope": meta.get('scope', 'GAME'),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "game_key": game_key,
            "event_date": game_data.get('date'),
            "event_time": game_data.get('time'),
            "rotation_number": f"{game_data.get('visitor_rot', '')}-{game_data.get('home_rot', '')}",
            "teams": teams,
            "markets": markets,
            "is_live": False,  # This is pregame from /sports
            "raw_data": game_data,  # Keep raw data for debugging
        }
        
        return item

