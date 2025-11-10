#!/usr/bin/env python3
"""
Action Network Scraper
Captures betting odds, trends, and sharp action for NFL and NCAA FBS
"""

import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class ActionNetworkScraper:
    """Scraper for actionnetwork.com betting data"""

    def __init__(self):
        """Initialize scraper"""
        self.base_url = "https://www.actionnetwork.com"
        self.api_base = "https://api.actionnetwork.com/web"
        self.output_dir = "output/action_network"
        os.makedirs(self.output_dir, exist_ok=True)

        # Authentication (from .env)
        self.username = os.getenv("ACTION_USERNAME")
        self.password = os.getenv("ACTION_PASSWORD")

        # Track API calls
        self.captured_requests = []
        self.captured_responses = []

    async def intercept_route(self, route):
        """Intercept and log network requests"""
        request = route.request

        # Log API calls to Action Network API
        if "api.actionnetwork.com" in request.url:
            logger.info(f"API Request: {request.method} {request.url[:100]}...")
            self.captured_requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "headers": dict(request.headers),
                }
            )

        # Continue the request
        await route.continue_()

    async def handle_response(self, response):
        """Handle and log responses"""
        request = response.request

        # Capture JSON responses from Action Network API
        if response.ok and "api.actionnetwork.com" in request.url:
            try:
                # Check if response is JSON
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = await response.json()
                    logger.info(f"Captured JSON response from: {request.url[:80]}...")
                    self.captured_responses.append(
                        {
                            "url": request.url,
                            "data": data,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
            except Exception as e:
                logger.debug(f"Could not parse JSON: {e}")

    async def login(self, page):
        """
        Login to Action Network (if credentials provided)

        Args:
            page: Playwright page object
        """
        if not self.username or not self.password:
            logger.info("No credentials provided, skipping login")
            return False

        try:
            logger.info("Attempting login...")

            # Navigate to login page
            await page.goto(f"{self.base_url}/login", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")

            # Fill login form
            await page.fill('input[type="email"]', self.username)
            await page.fill('input[type="password"]', self.password)

            # Submit
            await page.click('button[type="submit"]')

            # Wait for redirect
            await page.wait_for_url(f"{self.base_url}/**", timeout=15000)

            logger.info("Login successful")
            return True

        except Exception as e:
            logger.warning(f"Login failed: {e}")
            return False

    async def scrape_nfl_odds(self, week: int = None, save: bool = True):
        """
        Scrape NFL odds and betting data

        Args:
            week: NFL week number (None for current week)
            save: Whether to save data to file

        Returns:
            dict: NFL odds data
        """
        logger.info("=" * 60)
        logger.info(f"Scraping NFL Odds{f' (Week {week})' if week else ''}")
        logger.info("=" * 60)

        url = f"{self.base_url}/nfl/odds"
        if week:
            url += f"?week={week}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Setup interception
            await page.route("**/*", self.intercept_route)
            page.on("response", self.handle_response)

            # Login if credentials available
            await self.login(page)

            # Navigate to odds page
            logger.info(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for odds table to load
            try:
                await page.wait_for_selector(
                    '.betting-odds-table__body, [class*="odds-table"]', timeout=30000
                )
                logger.info("Odds table loaded, extracting data...")
            except:
                logger.warning(
                    "Odds table selector not found, attempting alternative..."
                )
                await page.wait_for_timeout(5000)

            # Extract odds data using JavaScript
            odds_data = await page.evaluate("""
                () => {
                    const games = [];

                    // Try multiple selectors for game rows
                    const selectors = [
                        '.betting-odds-table__body [class*="row"]',
                        '[class*="game-row"]',
                        '[class*="odds-row"]',
                        'table tbody tr'
                    ];

                    let rows = [];
                    for (const selector of selectors) {
                        rows = document.querySelectorAll(selector);
                        if (rows.length > 0) break;
                    }

                    rows.forEach(row => {
                        const game = {
                            teams: [],
                            spreads: [],
                            totals: [],
                            moneylines: [],
                            rawHtml: row.innerHTML.substring(0, 500)
                        };

                        // Extract team names
                        const teamElements = row.querySelectorAll('[class*="team"]');
                        teamElements.forEach(el => {
                            const text = el.innerText?.trim();
                            if (text) game.teams.push(text);
                        });

                        // Extract all text content for parsing
                        const allText = row.innerText;
                        game.allText = allText;

                        if (game.teams.length > 0 || allText.length > 10) {
                            games.push(game);
                        }
                    });

                    return {
                        games: games,
                        scrapedAt: new Date().toISOString(),
                        pageTitle: document.title
                    };
                }
            """)

            await browser.close()

        logger.info(f"Captured {len(odds_data.get('games', []))} NFL games")
        logger.info(f"Captured {len(self.captured_responses)} API responses")

        # Save data
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save extracted odds
            odds_file = f"{self.output_dir}/nfl_odds_{timestamp}.json"
            with open(odds_file, "w") as f:
                json.dump(odds_data, f, indent=2)
            logger.info(f"Saved odds data to {odds_file}")

            # Save captured API calls
            if self.captured_responses:
                api_file = f"{self.output_dir}/nfl_api_responses_{timestamp}.json"
                with open(api_file, "w") as f:
                    json.dump(self.captured_responses, f, indent=2)
                logger.info(
                    f"Saved {len(self.captured_responses)} API responses to {api_file}"
                )

                # Also save as JSONL
                jsonl_file = f"{self.output_dir}/nfl_api_responses_{timestamp}.jsonl"
                with open(jsonl_file, "w") as f:
                    for response in self.captured_responses:
                        f.write(json.dumps(response) + "\n")
                logger.info(f"Saved JSONL to {jsonl_file}")

        return odds_data

    async def scrape_ncaaf_odds(self, week: int = None, save: bool = True):
        """
        Scrape NCAA FBS College Football odds

        Args:
            week: Week number (None for current week)
            save: Whether to save data to file

        Returns:
            dict: NCAAF odds data
        """
        logger.info("=" * 60)
        logger.info(f"Scraping NCAAF Odds{f' (Week {week})' if week else ''}")
        logger.info("=" * 60)

        url = f"{self.base_url}/ncaaf/odds"
        if week:
            url += f"?week={week}"

        # Reset capture lists
        self.captured_requests = []
        self.captured_responses = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Setup interception
            await page.route("**/*", self.intercept_route)
            page.on("response", self.handle_response)

            # Login if credentials available
            await self.login(page)

            # Navigate to odds page
            logger.info(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for odds table to load
            try:
                await page.wait_for_selector(
                    '.betting-odds-table__body, [class*="odds-table"]', timeout=30000
                )
                logger.info("Odds table loaded, extracting data...")
            except:
                logger.warning(
                    "Odds table selector not found, attempting alternative..."
                )
                await page.wait_for_timeout(5000)

            # Extract odds data
            odds_data = await page.evaluate("""
                () => {
                    const games = [];

                    const selectors = [
                        '.betting-odds-table__body [class*="row"]',
                        '[class*="game-row"]',
                        '[class*="odds-row"]',
                        'table tbody tr'
                    ];

                    let rows = [];
                    for (const selector of selectors) {
                        rows = document.querySelectorAll(selector);
                        if (rows.length > 0) break;
                    }

                    rows.forEach(row => {
                        const game = {
                            teams: [],
                            spreads: [],
                            totals: [],
                            moneylines: [],
                            rawHtml: row.innerHTML.substring(0, 500)
                        };

                        const teamElements = row.querySelectorAll('[class*="team"]');
                        teamElements.forEach(el => {
                            const text = el.innerText?.trim();
                            if (text) game.teams.push(text);
                        });

                        const allText = row.innerText;
                        game.allText = allText;

                        if (game.teams.length > 0 || allText.length > 10) {
                            games.push(game);
                        }
                    });

                    return {
                        games: games,
                        scrapedAt: new Date().toISOString(),
                        pageTitle: document.title
                    };
                }
            """)

            await browser.close()

        logger.info(f"Captured {len(odds_data.get('games', []))} NCAAF games")
        logger.info(f"Captured {len(self.captured_responses)} API responses")

        # Save data
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save extracted odds
            odds_file = f"{self.output_dir}/ncaaf_odds_{timestamp}.json"
            with open(odds_file, "w") as f:
                json.dump(odds_data, f, indent=2)
            logger.info(f"Saved odds data to {odds_file}")

            # Save captured API calls
            if self.captured_responses:
                api_file = f"{self.output_dir}/ncaaf_api_responses_{timestamp}.json"
                with open(api_file, "w") as f:
                    json.dump(self.captured_responses, f, indent=2)
                logger.info(
                    f"Saved {len(self.captured_responses)} API responses to {api_file}"
                )

                # Also save as JSONL
                jsonl_file = f"{self.output_dir}/ncaaf_api_responses_{timestamp}.jsonl"
                with open(jsonl_file, "w") as f:
                    for response in self.captured_responses:
                        f.write(json.dumps(response) + "\n")
                logger.info(f"Saved JSONL to {jsonl_file}")

        return odds_data

    async def scrape_injuries(self, league: str = "nfl", save: bool = True):
        """
        Scrape injury data from Action Network

        Args:
            league: "nfl" or "ncaaf"
            save: Whether to save data to file

        Returns:
            dict: Injury data
        """
        logger.info("=" * 60)
        logger.info(f"Scraping {league.upper()} Injuries")
        logger.info("=" * 60)

        url = f"{self.base_url}/{league}/injury-report"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Setup interception
            await page.route("**/*", self.intercept_route)
            page.on("response", self.handle_response)

            # Login if credentials available
            await self.login(page)

            # Navigate to injuries page
            logger.info(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for page to load
            try:
                await page.wait_for_timeout(3000)
                logger.info("Injuries page loaded, extracting data...")
            except:
                logger.warning("Timeout waiting for injuries page")

            # Extract injury data from Next.js page props
            injury_data = await page.evaluate("""
                () => {
                    // Try multiple locations for the data
                    let injuries = [];

                    // Method 1: Next.js page props
                    try {
                        const nextData = document.getElementById('__NEXT_DATA__');
                        if (nextData) {
                            const data = JSON.parse(nextData.textContent);
                            if (data.props && data.props.pageProps && data.props.pageProps.pageData) {
                                injuries = data.props.pageProps.pageData.injuries || [];
                            }
                        }
                    } catch (e) {
                        console.log('Method 1 failed:', e);
                    }

                    // Method 2: Window TAN_APP_DATA
                    if (injuries.length === 0 && window.TAN_APP_DATA) {
                        injuries = window.TAN_APP_DATA.injuries || [];
                    }

                    return {
                        injuries: injuries,
                        scrapedAt: new Date().toISOString()
                    };
                }
            """)

            await browser.close()

        logger.info(f"Captured {len(injury_data.get('injuries', []))} injuries")

        # Save data
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save full injury data
            injury_file = f"{self.output_dir}/{league}_injuries_{timestamp}.json"
            with open(injury_file, "w") as f:
                json.dump(injury_data, f, indent=2)
            logger.info(f"Saved injury data to {injury_file}")

            # Also save as JSONL
            if injury_data.get("injuries"):
                jsonl_file = f"{self.output_dir}/{league}_injuries_{timestamp}.jsonl"
                with open(jsonl_file, "w") as f:
                    for injury in injury_data["injuries"]:
                        f.write(json.dumps(injury) + "\n")
                logger.info(f"Saved JSONL to {jsonl_file}")

        return injury_data

    async def scrape_both(self, nfl_week: int = None, ncaaf_week: int = None):
        """Scrape both NFL and NCAAF odds"""
        nfl_data = await self.scrape_nfl_odds(week=nfl_week)
        ncaaf_data = await self.scrape_ncaaf_odds(week=ncaaf_week)

        return {"nfl": nfl_data, "ncaaf": ncaaf_data}


async def main():
    """Main entry point"""
    scraper = ActionNetworkScraper()

    # Scrape both leagues
    data = await scraper.scrape_both()

    logger.info("=" * 60)
    logger.info("Scraping Complete!")
    logger.info(f"NFL Games: {len(data['nfl'].get('games', []))}")
    logger.info(f"NCAAF Games: {len(data['ncaaf'].get('games', []))}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
