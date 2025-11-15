#!/usr/bin/env python3
"""
Massey Ratings Scraper
Captures power ratings for NFL and NCAA FBS College Football
"""

import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class MasseyRatingsScraper:
    """Scraper for masseyratings.com power rankings"""

    def __init__(self):
        """Initialize scraper"""
        self.base_url = "https://masseyratings.com"
        self.output_base_dir = "output/massey"
        os.makedirs(self.output_base_dir, exist_ok=True)

        # Track API calls
        self.captured_requests = []
        self.captured_responses = []

    async def intercept_route(self, route):
        """Intercept and log network requests"""
        request = route.request

        # Log API calls
        if "json" in request.url or "/flOm" in request.url:
            logger.info(f"API Request: {request.method} {request.url}")
            self.captured_requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "headers": request.headers,
                }
            )

        # Continue the request
        await route.continue_()

    async def handle_response(self, response):
        """Handle and log responses"""
        request = response.request

        # Capture JSON responses
        if response.ok and (
            "json" in request.url
            or "application/json" in response.headers.get("content-type", "")
        ):
            try:
                data = await response.json()
                logger.info(f"Captured JSON response from: {request.url[:100]}...")
                self.captured_responses.append(
                    {
                        "url": request.url,
                        "data": data,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as e:
                logger.debug(f"Could not parse JSON: {e}")

    async def scrape_nfl_ratings(self, save=True):
        """
        Scrape NFL power ratings

        Returns:
            dict: NFL ratings data
        """
        logger.info("=" * 60)
        logger.info("Scraping NFL Ratings")
        logger.info("=" * 60)

        url = f"{self.base_url}/nfl/ratings"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Block ads and trackers
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if any(
                        x in route.request.url
                        for x in [
                            "doubleclick.net",
                            "googlesyndication",
                            "googletagmanager",
                            "advertising",
                            "analytics",
                            "tracking",
                            "adnxs.com",
                            "amazon-adsystem",
                            "rubiconproject",
                            "pubmatic",
                            "criteo",
                        ]
                    )
                    else self.intercept_route(route)
                ),
            )
            page.on("response", self.handle_response)

            # Navigate and wait for content
            logger.info(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for table to load
            await page.wait_for_selector("#SHCtable", timeout=45000)
            logger.info("Table loaded, extracting data...")

            # Extract table data using JavaScript
            ratings_data = await page.evaluate("""
                () => {
                    const teams = [];
                    const rows = document.querySelectorAll('#SHCtable tbody tr.bodyrow');

                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 7) {
                            // Parse cells based on Massey format:
                            // 0=Team, 1=Record, 2=Δ, 3=Rat, 4=Pwr, 5=Off, 6=Def, 7=HFA, etc.
                            const teamText = cells[0]?.innerText?.trim() || '';
                            const recordText = cells[1]?.innerText?.trim() || '';
                            const deltaText = cells[2]?.innerText?.trim() || '';
                            const ratText = cells[3]?.innerText?.trim() || '';

                            // Extract team name and division (format: "Team Name\\nDivision")
                            const teamParts = teamText.split('\\n');
                            const teamName = teamParts[0] || '';
                            const division = teamParts[1] || '';

                            // Extract record and win pct (format: "W-L\\nPct")
                            const recordParts = recordText.split('\\n');
                            const record = recordParts[0] || '';
                            const winPct = recordParts[1] || '';

                            // Extract rank and rating (format: "Rank\\nRating")
                            const ratParts = ratText.split('\\n');
                            const rank = ratParts[0] || '';
                            const rating = ratParts[1] || '';

                            teams.push({
                                rank: rank,
                                team: teamName,
                                division: division,
                                record: record,
                                winPct: winPct,
                                delta: deltaText,
                                rating: rating,
                                rawData: Array.from(cells).map(c => c.innerText.trim())
                            });
                        }
                    });

                    return {
                        teams: teams,
                        headers: Array.from(document.querySelectorAll('#SHCtable thead th')).map(th => th.innerText.trim()),
                        scrapedAt: new Date().toISOString()
                    };
                }
            """)

            await browser.close()

        logger.info(f"Captured {len(ratings_data.get('teams', []))} NFL teams")

        # Save data
        if save:
            # Use new output structure: output/massey/nfl/ratings/
            output_dir = os.path.join(self.output_base_dir, "nfl", "ratings")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"nfl_ratings_{timestamp}.json")
            
            with open(filepath, "w") as f:
                json.dump(ratings_data, f, indent=2)
            logger.info(f"Saved to {filepath}")

            # Save captured API calls
            if self.captured_responses:
                api_file = os.path.join(output_dir, f"nfl_api_responses_{timestamp}.json")
                with open(api_file, "w") as f:
                    json.dump(self.captured_responses, f, indent=2)
                logger.info(
                    f"Saved {len(self.captured_responses)} API responses to {api_file}"
                )

        return ratings_data

    async def scrape_ncaaf_ratings(self, save=True):
        """
        Scrape NCAA FBS College Football power ratings

        Returns:
            dict: NCAAF ratings data
        """
        logger.info("=" * 60)
        logger.info("Scraping NCAAF Ratings")
        logger.info("=" * 60)

        url = f"{self.base_url}/cf/fbs/ratings"

        # Reset capture lists
        self.captured_requests = []
        self.captured_responses = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Block ads and trackers
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if any(
                        x in route.request.url
                        for x in [
                            "doubleclick.net",
                            "googlesyndication",
                            "googletagmanager",
                            "advertising",
                            "analytics",
                            "tracking",
                            "adnxs.com",
                            "amazon-adsystem",
                            "rubiconproject",
                            "pubmatic",
                            "criteo",
                        ]
                    )
                    else self.intercept_route(route)
                ),
            )
            page.on("response", self.handle_response)

            # Navigate and wait for content
            logger.info(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for table to load
            await page.wait_for_selector("#SHCtable", timeout=45000)
            logger.info("Table loaded, extracting data...")

            # Extract table data
            ratings_data = await page.evaluate("""
                () => {
                    const teams = [];
                    const rows = document.querySelectorAll('#SHCtable tbody tr.bodyrow');

                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 7) {
                            // Parse cells based on Massey NCAAF format:
                            // 0=Team\\nConference, 1=Record\\nWinPct, 2=Δ, 3=Rank\\nRat, 4=Rank\\nPwr, etc.
                            const teamText = cells[0]?.innerText?.trim() || '';
                            const recordText = cells[1]?.innerText?.trim() || '';
                            const deltaText = cells[2]?.innerText?.trim() || '';
                            const ratText = cells[3]?.innerText?.trim() || '';
                            const pwrText = cells[4]?.innerText?.trim() || '';

                            // Extract team name and conference (format: "Team Name\\nConference")
                            const teamParts = teamText.split('\\n');
                            const teamName = teamParts[0] || '';
                            const conference = teamParts[1] || '';

                            // Extract record and win pct (format: "W-L\\nPct")
                            const recordParts = recordText.split('\\n');
                            const record = recordParts[0] || '';
                            const winPct = recordParts[1] || '';

                            // Extract rank and rating from Rat column (format: "Rank\\nRating")
                            const ratParts = ratText.split('\\n');
                            const rank = ratParts[0] || '';
                            const rating = ratParts[1] || '';

                            // Extract power rating from Pwr column (format: "Rank\\nPower")
                            const pwrParts = pwrText.split('\\n');
                            const powerRating = pwrParts[1] || '';

                            teams.push({
                                rank: rank,
                                team: teamName,
                                conference: conference,
                                record: record,
                                winPct: winPct,
                                delta: deltaText,
                                rating: rating,
                                powerRating: powerRating,
                                rawData: Array.from(cells).map(c => c.innerText.trim())
                            });
                        }
                    });

                    return {
                        teams: teams,
                        headers: Array.from(document.querySelectorAll('#SHCtable thead th')).map(th => th.innerText.trim()),
                        scrapedAt: new Date().toISOString()
                    };
                }
            """)

            await browser.close()

        logger.info(f"Captured {len(ratings_data.get('teams', []))} NCAAF teams")

        # Save data
        if save:
            # Use new output structure: output/massey/ncaaf/ratings/
            output_dir = os.path.join(self.output_base_dir, "ncaaf", "ratings")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"ncaaf_ratings_{timestamp}.json")
            
            with open(filepath, "w") as f:
                json.dump(ratings_data, f, indent=2)
            logger.info(f"Saved to {filepath}")

            # Save captured API calls
            if self.captured_responses:
                api_file = os.path.join(output_dir, f"ncaaf_api_responses_{timestamp}.json")
                with open(api_file, "w") as f:
                    json.dump(self.captured_responses, f, indent=2)
                logger.info(
                    f"Saved {len(self.captured_responses)} API responses to {api_file}"
                )

        return ratings_data

    async def scrape_nfl_games(self, save=True):
        """
        Scrape NFL games data

        Returns:
            dict: NFL games data
        """
        logger.info("=" * 60)
        logger.info("Scraping NFL Games")
        logger.info("=" * 60)

        url = f"{self.base_url}/nfl/games"

        # Reset capture lists
        self.captured_requests = []
        self.captured_responses = []

        games_data = {"sport": "NFL", "url": url, "scraped_at": datetime.now().isoformat()}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Set up network monitoring
            page.on("response", self.handle_response)

            logger.info(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for content and extract data
            await page.wait_for_timeout(3000)
            content = await page.content()
            games_data["html_length"] = len(content)

            await browser.close()

        # Save data
        if save:
            output_dir = os.path.join(self.output_base_dir, "nfl", "games")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"nfl_games_{timestamp}.json")
            
            with open(filepath, "w") as f:
                json.dump(games_data, f, indent=2)
            logger.info(f"Saved to {filepath}")

        return games_data

    async def scrape_ncaaf_games(self, save=True):
        """
        Scrape NCAAF games data

        Returns:
            dict: NCAAF games data
        """
        logger.info("=" * 60)
        logger.info("Scraping NCAAF Games")
        logger.info("=" * 60)

        url = f"{self.base_url}/cf/fbs/games"

        # Reset capture lists
        self.captured_requests = []
        self.captured_responses = []

        games_data = {"sport": "NCAAF", "url": url, "scraped_at": datetime.now().isoformat()}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Set up network monitoring
            page.on("response", self.handle_response)

            logger.info(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for content and extract data
            await page.wait_for_timeout(3000)
            content = await page.content()
            games_data["html_length"] = len(content)

            await browser.close()

        # Save data
        if save:
            output_dir = os.path.join(self.output_base_dir, "ncaaf", "games")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"ncaaf_games_{timestamp}.json")
            
            with open(filepath, "w") as f:
                json.dump(games_data, f, indent=2)
            logger.info(f"Saved to {filepath}")

        return games_data

    async def scrape_nfl_matchups(self, save=True):
        """
        Scrape NFL matchup predictions (if endpoint exists)

        Returns:
            dict: NFL matchup data
        """
        logger.info("=" * 60)
        logger.info("Scraping NFL Matchups")
        logger.info("=" * 60)

        url = f"{self.base_url}/nfl/matchups"
        # Note: This endpoint may not exist - will need to verify

        matchups_data = {"sport": "NFL", "url": url, "scraped_at": datetime.now().isoformat()}

        # Save data
        if save:
            output_dir = os.path.join(self.output_base_dir, "nfl", "matchups")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"nfl_matchups_{timestamp}.json")
            
            with open(filepath, "w") as f:
                json.dump(matchups_data, f, indent=2)
            logger.info(f"Saved to {filepath}")

        return matchups_data

    async def scrape_ncaaf_matchups(self, save=True):
        """
        Scrape NCAAF matchup predictions (if endpoint exists)

        Returns:
            dict: NCAAF matchup data
        """
        logger.info("=" * 60)
        logger.info("Scraping NCAAF Matchups")
        logger.info("=" * 60)

        url = f"{self.base_url}/cf/fbs/matchups"
        # Note: This endpoint may not exist - will need to verify

        matchups_data = {"sport": "NCAAF", "url": url, "scraped_at": datetime.now().isoformat()}

        # Save data
        if save:
            output_dir = os.path.join(self.output_base_dir, "ncaaf", "matchups")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"ncaaf_matchups_{timestamp}.json")
            
            with open(filepath, "w") as f:
                json.dump(matchups_data, f, indent=2)
            logger.info(f"Saved to {filepath}")

        return matchups_data

    async def scrape_both(self):
        """Scrape both NFL and NCAAF ratings"""
        nfl_data = await self.scrape_nfl_ratings()
        ncaaf_data = await self.scrape_ncaaf_ratings()

        return {"nfl": nfl_data, "ncaaf": ncaaf_data}


async def main():
    """Main entry point"""
    scraper = MasseyRatingsScraper()

    # Scrape both
    data = await scraper.scrape_both()

    logger.info("=" * 60)
    logger.info("Scraping Complete!")
    logger.info(f"NFL Teams: {len(data['nfl'].get('teams', []))}")
    logger.info(f"NCAAF Teams: {len(data['ncaaf'].get('teams', []))}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
