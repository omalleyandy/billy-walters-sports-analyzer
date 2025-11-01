#!/usr/bin/env python3
"""
ESPN College Football FBS Data Scraper

This script systematically crawls ESPN's college football pages to collect
comprehensive data for all 136 FBS teams, including:
- Team statistics
- Player rosters
- Game schedules
- Odds and betting lines
- Rankings and power ratings
- Injury reports
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESPNCFBScraper:
    """Main scraper class for ESPN College Football data"""
    
    BASE_URL = "https://www.espn.com"
    CFB_BASE = f"{BASE_URL}/college-football"
    
    # Main page URLs
    URLS = {
        "homepage": f"{CFB_BASE}/",
        "scoreboard": f"{CFB_BASE}/scoreboard",
        "schedule": f"{CFB_BASE}/schedule",
        "sp_plus": f"{CFB_BASE}/story/_/id/46128861/2025-college-football-sp+-rankings-all-136-fbs-teams",
        "fpi": f"{CFB_BASE}/fpi",
        "standings": f"{CFB_BASE}/standings",
        "stats": f"{CFB_BASE}/stats",
        "team_stats": f"{CFB_BASE}/stats/_/view/team",
        "teams": f"{CFB_BASE}/teams",
        "odds": f"{CFB_BASE}/odds",
        "rankings": f"{CFB_BASE}/rankings"
    }
    
    def __init__(self, output_dir: str = "data/espn_cfb"):
        """Initialize scraper with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "teams").mkdir(exist_ok=True)
        (self.output_dir / "games").mkdir(exist_ok=True)
        (self.output_dir / "stats").mkdir(exist_ok=True)
        (self.output_dir / "odds").mkdir(exist_ok=True)
        (self.output_dir / "rankings").mkdir(exist_ok=True)
        
        self.browser: Optional[Browser] = None
        self.teams_data: Dict[str, Any] = {}
        
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        logger.info("Initializing browser...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        logger.info("Browser initialized")
        
    async def close_browser(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
    
    async def fetch_page(self, url: str, wait_for: Optional[str] = None) -> str:
        """Fetch page content using Playwright"""
        page = await self.browser.new_page()
        try:
            logger.info(f"Fetching: {url}")
            await page.goto(url, wait_until="networkidle")
            
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=10000)
            
            content = await page.content()
            return content
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""
        finally:
            await page.close()
    
    async def scrape_teams_list(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape the teams page to get all FBS team IDs and metadata
        Returns: Dict mapping team_id to team info
        """
        logger.info("Scraping teams list...")
        content = await self.fetch_page(self.URLS["teams"])
        soup = BeautifulSoup(content, 'html.parser')
        
        teams = {}
        
        # Find all team links
        team_links = soup.find_all('a', href=re.compile(r'/college-football/team/_/id/\d+'))
        
        for link in team_links:
            href = link.get('href', '')
            team_id_match = re.search(r'/id/(\d+)', href)
            
            if team_id_match:
                team_id = team_id_match.group(1)
                team_name = link.get_text(strip=True)
                
                # Extract conference if available
                conference_elem = link.find_parent('div')
                conference = "Unknown"
                if conference_elem:
                    conf_header = conference_elem.find_previous('h3')
                    if conf_header:
                        conference = conf_header.get_text(strip=True)
                
                if team_id not in teams and team_name:
                    teams[team_id] = {
                        "id": team_id,
                        "name": team_name,
                        "conference": conference,
                        "url": urljoin(self.BASE_URL, href)
                    }
        
        logger.info(f"Found {len(teams)} FBS teams")
        
        # Save teams data
        output_file = self.output_dir / "teams_list.json"
        with open(output_file, 'w') as f:
            json.dump(teams, f, indent=2)
        
        logger.info(f"Teams list saved to {output_file}")
        return teams
    
    async def scrape_team_stats(self, team_id: str, team_name: str) -> Dict[str, Any]:
        """Scrape statistics for a specific team"""
        logger.info(f"Scraping stats for {team_name} (ID: {team_id})")
        
        stats_url = f"{self.CFB_BASE}/team/stats/_/id/{team_id}"
        content = await self.fetch_page(stats_url)
        soup = BeautifulSoup(content, 'html.parser')
        
        stats = {
            "team_id": team_id,
            "team_name": team_name,
            "scraped_at": datetime.now().isoformat(),
            "offensive_stats": {},
            "defensive_stats": {},
            "per_game_stats": {}
        }
        
        # Parse stats tables
        tables = soup.find_all('table', class_='Table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    stat_name = cells[0].get_text(strip=True)
                    stat_value = cells[1].get_text(strip=True)
                    
                    # Categorize stats
                    if stat_name and stat_value:
                        if 'offense' in stat_name.lower():
                            stats['offensive_stats'][stat_name] = stat_value
                        elif 'defense' in stat_name.lower():
                            stats['defensive_stats'][stat_name] = stat_value
                        else:
                            stats['per_game_stats'][stat_name] = stat_value
        
        # Save team stats
        output_file = self.output_dir / "stats" / f"team_{team_id}_stats.json"
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        return stats
    
    async def scrape_team_roster(self, team_id: str, team_name: str) -> List[Dict[str, str]]:
        """Scrape roster for a specific team"""
        logger.info(f"Scraping roster for {team_name} (ID: {team_id})")
        
        roster_url = f"{self.CFB_BASE}/team/roster/_/id/{team_id}"
        content = await self.fetch_page(roster_url)
        soup = BeautifulSoup(content, 'html.parser')
        
        roster = []
        
        # Parse roster table
        tables = soup.find_all('table', class_='Table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    player = {
                        "number": cells[0].get_text(strip=True),
                        "name": cells[1].get_text(strip=True),
                        "position": cells[2].get_text(strip=True),
                        "height": cells[3].get_text(strip=True),
                        "weight": cells[4].get_text(strip=True),
                        "class": cells[5].get_text(strip=True) if len(cells) > 5 else ""
                    }
                    roster.append(player)
        
        # Save roster
        output_file = self.output_dir / "teams" / f"team_{team_id}_roster.json"
        with open(output_file, 'w') as f:
            json.dump({
                "team_id": team_id,
                "team_name": team_name,
                "roster": roster,
                "scraped_at": datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Found {len(roster)} players for {team_name}")
        return roster
    
    async def scrape_schedule(self) -> List[Dict[str, Any]]:
        """Scrape the schedule page for all games"""
        logger.info("Scraping schedule...")
        content = await self.fetch_page(self.URLS["schedule"])
        soup = BeautifulSoup(content, 'html.parser')
        
        games = []
        
        # Parse schedule
        game_elements = soup.find_all('div', class_='ScheduleTables')
        
        for game_elem in game_elements:
            game_links = game_elem.find_all('a', href=re.compile(r'/game/_/gameId/\d+'))
            
            for link in game_links:
                href = link.get('href', '')
                game_id_match = re.search(r'/gameId/(\d+)', href)
                
                if game_id_match:
                    game_id = game_id_match.group(1)
                    
                    game = {
                        "game_id": game_id,
                        "url": urljoin(self.BASE_URL, href),
                        "teams": link.get_text(strip=True)
                    }
                    games.append(game)
        
        # Save schedule
        output_file = self.output_dir / "schedule.json"
        with open(output_file, 'w') as f:
            json.dump({
                "games": games,
                "scraped_at": datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Found {len(games)} scheduled games")
        return games
    
    async def scrape_game_details(self, game_id: str) -> Dict[str, Any]:
        """Scrape detailed information for a specific game"""
        logger.info(f"Scraping game details for game {game_id}")
        
        game_url = f"{self.CFB_BASE}/game/_/gameId/{game_id}"
        content = await self.fetch_page(game_url)
        soup = BeautifulSoup(content, 'html.parser')
        
        game_data = {
            "game_id": game_id,
            "scraped_at": datetime.now().isoformat(),
            "score": {},
            "stats": {},
            "odds": {},
            "weather": {}
        }
        
        # Parse game details
        # Score
        score_elem = soup.find('div', class_='ScoreCell')
        if score_elem:
            game_data['score'] = {
                "text": score_elem.get_text(strip=True)
            }
        
        # Save game data
        output_file = self.output_dir / "games" / f"game_{game_id}.json"
        with open(output_file, 'w') as f:
            json.dump(game_data, f, indent=2)
        
        return game_data
    
    async def scrape_odds(self) -> Dict[str, Any]:
        """Scrape current odds and betting lines"""
        logger.info("Scraping odds...")
        content = await self.fetch_page(self.URLS["odds"])
        soup = BeautifulSoup(content, 'html.parser')
        
        odds_data = {
            "scraped_at": datetime.now().isoformat(),
            "games": []
        }
        
        # Parse odds tables
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    game = {
                        "matchup": cells[0].get_text(strip=True),
                        "spread": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                        "total": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                        "moneyline": cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    }
                    odds_data['games'].append(game)
        
        # Save odds
        output_file = self.output_dir / "odds" / f"odds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(odds_data, f, indent=2)
        
        logger.info(f"Scraped odds for {len(odds_data['games'])} games")
        return odds_data
    
    async def scrape_rankings(self) -> Dict[str, Any]:
        """Scrape current rankings (AP, Coaches, CFP)"""
        logger.info("Scraping rankings...")
        content = await self.fetch_page(self.URLS["rankings"])
        soup = BeautifulSoup(content, 'html.parser')
        
        rankings = {
            "scraped_at": datetime.now().isoformat(),
            "ap_poll": [],
            "coaches_poll": [],
            "cfp_rankings": []
        }
        
        # Parse rankings tables
        tables = soup.find_all('table', class_='Table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    rank_entry = {
                        "rank": cells[0].get_text(strip=True),
                        "team": cells[1].get_text(strip=True),
                        "record": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                        "points": cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    }
                    rankings['ap_poll'].append(rank_entry)
        
        # Save rankings
        output_file = self.output_dir / "rankings" / f"rankings_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w') as f:
            json.dump(rankings, f, indent=2)
        
        logger.info(f"Scraped {len(rankings['ap_poll'])} ranked teams")
        return rankings
    
    async def scrape_fpi(self) -> Dict[str, Any]:
        """Scrape FPI (Football Power Index) data"""
        logger.info("Scraping FPI data...")
        content = await self.fetch_page(self.URLS["fpi"])
        soup = BeautifulSoup(content, 'html.parser')
        
        fpi_data = {
            "scraped_at": datetime.now().isoformat(),
            "teams": []
        }
        
        # Parse FPI table
        tables = soup.find_all('table', class_='Table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    team_fpi = {
                        "rank": cells[0].get_text(strip=True),
                        "team": cells[1].get_text(strip=True),
                        "fpi": cells[2].get_text(strip=True),
                        "win_total_proj": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                        "playoff_prob": cells[4].get_text(strip=True) if len(cells) > 4 else ""
                    }
                    fpi_data['teams'].append(team_fpi)
        
        # Save FPI data
        output_file = self.output_dir / "fpi_data.json"
        with open(output_file, 'w') as f:
            json.dump(fpi_data, f, indent=2)
        
        logger.info(f"Scraped FPI data for {len(fpi_data['teams'])} teams")
        return fpi_data
    
    async def scrape_all_teams(self, limit: Optional[int] = None):
        """
        Scrape data for all FBS teams
        
        Args:
            limit: Optional limit on number of teams to scrape (for testing)
        """
        teams = await self.scrape_teams_list()
        
        team_list = list(teams.values())
        if limit:
            team_list = team_list[:limit]
            logger.info(f"Limiting to first {limit} teams for testing")
        
        for team in team_list:
            try:
                # Scrape team stats
                await self.scrape_team_stats(team['id'], team['name'])
                
                # Scrape team roster
                await self.scrape_team_roster(team['id'], team['name'])
                
                # Small delay to be respectful
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping team {team['name']}: {e}")
                continue
    
    async def run_full_scrape(self, scrape_teams: bool = True, teams_limit: Optional[int] = None):
        """
        Run a complete scrape of all ESPN CFB data
        
        Args:
            scrape_teams: Whether to scrape individual team data
            teams_limit: Optional limit on teams to scrape
        """
        try:
            await self.initialize_browser()
            
            # Scrape main pages
            logger.info("=== Starting Full ESPN CFB Data Scrape ===")
            
            # 1. Scrape schedule
            await self.scrape_schedule()
            
            # 2. Scrape odds
            await self.scrape_odds()
            
            # 3. Scrape rankings
            await self.scrape_rankings()
            
            # 4. Scrape FPI
            await self.scrape_fpi()
            
            # 5. Scrape all teams (if enabled)
            if scrape_teams:
                await self.scrape_all_teams(limit=teams_limit)
            
            logger.info("=== Scraping Complete ===")
            logger.info(f"Data saved to: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
        finally:
            await self.close_browser()


async def main():
    """Main entry point"""
    scraper = ESPNCFBScraper(output_dir="data/espn_cfb")
    
    # Run full scrape
    # Set teams_limit=5 for testing, None for all teams
    await scraper.run_full_scrape(
        scrape_teams=True,
        teams_limit=5  # Remove or set to None to scrape all 136 teams
    )


if __name__ == "__main__":
    asyncio.run(main())

