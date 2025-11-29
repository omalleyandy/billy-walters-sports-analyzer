#!/usr/bin/env python3
"""
NFL Official Injury Report Scraper
Scrapes injury data directly from NFL.com - the authoritative source
"""

import json
import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class NFLOfficialInjuryScraper:
    """Scraper for official NFL injury reports"""

    def __init__(self, output_dir: str = "output/injuries"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.base_url = "https://www.nfl.com"

    async def scrape_injuries(self, week: int = None, save: bool = True):
        """
        Scrape official NFL injury reports

        Args:
            week: NFL week number (None for current week)
            save: Whether to save data to file

        Returns:
            List of injury dictionaries
        """
        logger.info("=" * 60)
        logger.info(f"Scraping Official NFL Injuries (Week {week or 'Current'})")
        logger.info("=" * 60)

        url = f"{self.base_url}/injuries/"
        if week:
            url += f"?week={week}"

        injuries = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            logger.info(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for injury tables to load
            try:
                await page.wait_for_selector("table", timeout=10000)
                logger.info("Injury tables loaded, extracting data...")
            except:
                logger.warning("Could not find injury tables")

            # Extract injury data from HTML tables
            injury_data = await page.evaluate("""
                () => {
                    const injuries = [];

                    // Helper function to check if text is a date header
                    const isDateHeader = (text) => {
                        if (!text) return false;
                        const dateWords = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY',
                                          'FRIDAY', 'SATURDAY', 'SUNDAY', 'JANUARY',
                                          'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
                                          'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER',
                                          'NOVEMBER', 'DECEMBER', 'WEEK'];
                        return dateWords.some(word => text.toUpperCase().includes(word));
                    };

                    // Find all tables with injury data
                    const tables = document.querySelectorAll('table');

                    for (const table of tables) {
                        // Look for team name in headers above this table
                        let teamName = 'Unknown';

                        // Walk up the DOM to find team identifier
                        let current = table.parentElement;
                        let depth = 0;
                        while (current && depth < 10) {
                            // Check all headings in this section
                            const headings = current.querySelectorAll('h2, h3, h4, h5, [class*="team-name"], [class*="teamName"]');

                            for (const heading of headings) {
                                const text = heading.innerText?.trim();

                                // Valid team name criteria:
                                // - Not empty
                                // - Not a date header
                                // - Less than 100 chars (team names or matchups)
                                // - Contains "vs" or "at" (matchup) OR is a single team name
                                if (text && !isDateHeader(text) && text.length < 100) {
                                    // If it's a matchup, extract first team
                                    if (text.includes(' vs ') || text.includes(' vs. ')) {
                                        teamName = text.split(' vs')[0].trim();
                                        break;
                                    } else if (text.includes(' at ') || text.includes(' @ ')) {
                                        // For "Team1 at Team2", Team2 is home (we want home team)
                                        const parts = text.split(/ at | @ /);
                                        teamName = parts[parts.length - 1].trim();
                                        break;
                                    } else {
                                        // Single team name
                                        teamName = text;
                                        break;
                                    }
                                }
                            }

                            if (teamName !== 'Unknown') break;
                            current = current.parentElement;
                            depth++;
                        }

                        // Process table rows
                        const rows = table.querySelectorAll('tbody tr');

                        for (const row of rows) {
                            const cells = row.querySelectorAll('td');

                            if (cells.length >= 4) {
                                // Parse player data
                                const playerName = cells[0]?.innerText?.trim() || '';
                                const position = cells[1]?.innerText?.trim() || '';
                                const injuryType = cells[2]?.innerText?.trim() || '';
                                const practiceStatus = cells[3]?.innerText?.trim() || '';
                                const gameStatus = cells[4]?.innerText?.trim() || '';

                                if (playerName && playerName !== 'Player') {
                                    injuries.push({
                                        team: teamName,
                                        player_name: playerName,
                                        position: position,
                                        injury_type: injuryType,
                                        practice_status: practiceStatus,
                                        game_status: gameStatus || 'Questionable'
                                    });
                                }
                            }
                        }
                    }

                    return injuries;
                }
            """)

            await browser.close()

        logger.info(f"Extracted {len(injury_data)} injuries from official NFL reports")

        # Clean and normalize data
        for injury in injury_data:
            injury["source"] = "nfl_official"
            injury["league"] = "NFL"
            injury["sport"] = "nfl"
            injury["collected_at"] = datetime.now().isoformat()

            # Normalize status
            status = injury.get("game_status", "").lower()
            if "out" in status:
                injury["injury_status"] = "Out"
            elif "doubtful" in status:
                injury["injury_status"] = "Doubtful"
            elif "questionable" in status:
                injury["injury_status"] = "Questionable"
            else:
                injury["injury_status"] = "Questionable"

        injuries = injury_data

        # Save data
        if save and injuries:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save as JSON
            json_file = f"{self.output_dir}/nfl_official_injuries_{timestamp}.json"
            with open(json_file, "w") as f:
                json.dump(
                    {
                        "injuries": injuries,
                        "week": week,
                        "scraped_at": datetime.now().isoformat(),
                        "source": "NFL.com Official",
                    },
                    f,
                    indent=2,
                )
            logger.info(f"Saved to {json_file}")

            # Save as JSONL
            jsonl_file = f"{self.output_dir}/nfl_official_injuries_{timestamp}.jsonl"
            with open(jsonl_file, "w") as f:
                for injury in injuries:
                    f.write(json.dumps(injury) + "\n")
            logger.info(f"Saved JSONL to {jsonl_file}")

        return injuries


async def main():
    """Main entry point"""
    scraper = NFLOfficialInjuryScraper()

    # Scrape current week injuries
    injuries = await scraper.scrape_injuries(week=10, save=True)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("INJURY SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total injuries: {len(injuries)}")

    if injuries:
        # Group by status
        by_status = {}
        for inj in injuries:
            status = inj.get("injury_status", "Unknown")
            by_status[status] = by_status.get(status, 0) + 1

        logger.info("\nBy Status:")
        for status, count in sorted(by_status.items()):
            logger.info(f"  {status}: {count}")

        # Group by team
        by_team = {}
        for inj in injuries:
            team = inj.get("team", "Unknown")
            by_team[team] = by_team.get(team, 0) + 1

        logger.info(f"\nTeams with injuries: {len(by_team)}")

        # Show sample
        logger.info("\nSample injuries:")
        for i, inj in enumerate(injuries[:5], 1):
            logger.info(f"\n{i}. {inj['player_name']} ({inj['position']})")
            logger.info(f"   Team: {inj['team']}")
            logger.info(f"   Injury: {inj['injury_type']}")
            logger.info(f"   Status: {inj['injury_status']}")

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
