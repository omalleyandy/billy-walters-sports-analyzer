#!/usr/bin/env python3
"""
Overtime.ag Requests-based Scraper with Proxy Support
Uses requests + BeautifulSoup to scrape live betting odds
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OvertimeRequestsScraper:
    """Scraper for overtime.ag using requests library with proxy support"""

    def __init__(self):
        """Initialize scraper with proxy and credentials"""
        # Proxy configuration - build from components like test_proxy.py
        username = "5iwdzupyp3mzyv6-country-us"
        password = "z26z5o33jbnoi0h"
        proxy = "rp.scrapegw.com:6060"
        proxy_auth = "{}:{}@{}".format(username, password, proxy)

        # Use http:// scheme for both HTTP and HTTPS (requests library requirement)
        self.proxies = {
            "http": "http://{}".format(proxy_auth),
            "https": "http://{}".format(proxy_auth)
        }

        print(f"Configured proxy: {proxy}")
        print(f"Proxy auth format: http://{username}:***@{proxy}")

        # Overtime credentials
        self.customer_id = os.getenv("OV_CUSTOMER_ID")
        self.password = os.getenv("OV_PASSWORD")

        if not self.customer_id or not self.password:
            raise ValueError("OV_CUSTOMER_ID or OV_PASSWORD not found")

        # Session for maintaining login state
        self.session = requests.Session()
        self.session.proxies.update(self.proxies)
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

        self.base_url = "https://overtime.ag"
        self.live_betting_url = "https://overtime.ag/sports#/integrations/liveBetting"

    def login(self) -> bool:
        """
        Login to overtime.ag using customer ID and password

        Returns:
            True if login successful, False otherwise
        """
        print(f"Logging in as {self.customer_id}...")

        # First, get the main page to establish session
        try:
            r = self.session.get(self.base_url, timeout=30)
            print(f"Main page status: {r.status_code}")
        except Exception as e:
            print(f"Failed to access main page: {e}")
            return False

        # Try to login via API endpoint (common pattern)
        login_endpoints = [
            f"{self.base_url}/api/login",
            f"{self.base_url}/api/auth/login",
            f"{self.base_url}/login",
        ]

        login_data = {
            "customerId": self.customer_id,
            "password": self.password,
        }

        for endpoint in login_endpoints:
            try:
                print(f"Trying login endpoint: {endpoint}")
                r = self.session.post(
                    endpoint,
                    json=login_data,
                    timeout=30
                )
                if r.status_code == 200:
                    print("Login successful!")
                    return True
                else:
                    print(f"Login attempt returned {r.status_code}")
            except Exception as e:
                print(f"Login endpoint {endpoint} failed: {e}")
                continue

        # If API login fails, we may already be authenticated via session
        # or login might happen via JavaScript
        print("Warning: Direct API login failed, proceeding anyway...")
        return True

    def fetch_live_odds(self) -> Optional[str]:
        """
        Fetch the live betting page content

        Returns:
            HTML content or None if failed
        """
        print("Fetching live betting page...")

        # Try API endpoints first (AngularJS likely uses these)
        api_endpoints = [
            # Common API patterns
            f"{self.base_url}/api/live",
            f"{self.base_url}/api/live/odds",
            f"{self.base_url}/api/odds/live",
            f"{self.base_url}/api/games/live",
            f"{self.base_url}/api/events/live",
            f"{self.base_url}/api/integrations/liveBetting",
            f"{self.base_url}/api/sports/live",
            f"{self.base_url}/api/sports/events",
            f"{self.base_url}/sports/api/live",
            f"{self.base_url}/sports/api/odds",
            # Try with sport/league filters
            f"{self.base_url}/api/sports?sport=FOOTBALL",
            f"{self.base_url}/api/odds?league=NFL",
            f"{self.base_url}/api/odds?league=NCAAF",
        ]

        for endpoint in api_endpoints:
            try:
                print(f"Trying API endpoint: {endpoint}")
                r = self.session.get(endpoint, timeout=30)
                if r.status_code == 200:
                    try:
                        # Check if it's JSON
                        data = r.json()
                        print(f"Got JSON response from {endpoint}")
                        return json.dumps(data)
                    except:
                        # Not JSON, treat as HTML
                        pass
            except Exception as e:
                print(f"API endpoint {endpoint} failed: {e}")
                continue

        # Fall back to HTML page
        try:
            print(f"Fetching HTML page: {self.live_betting_url}")
            r = self.session.get(self.live_betting_url, timeout=30)
            if r.status_code == 200:
                print(f"Got HTML response ({len(r.content)} bytes)")
                return r.text
            else:
                print(f"Failed with status {r.status_code}")
                return None
        except Exception as e:
            print(f"Failed to fetch live betting page: {e}")
            return None

    def parse_odds(self, content: str) -> List[Dict]:
        """
        Parse odds data from HTML or JSON content

        Args:
            content: HTML or JSON string content

        Returns:
            List of game dictionaries in Billy Walters format
        """
        games = []

        # Try parsing as JSON first
        try:
            data = json.loads(content)
            print("Content is JSON, parsing...")
            games = self._parse_json_odds(data)
            if games:
                return games
        except:
            print("Content is HTML, parsing...")
            pass

        # Save HTML for debugging
        os.makedirs('snapshots', exist_ok=True)
        snapshot_file = f'snapshots/overtime_html_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved HTML snapshot to {snapshot_file}")

        # Parse as HTML
        soup = BeautifulSoup(content, 'html.parser')

        # Look for embedded JSON in script tags (common in SPAs)
        for script in soup.find_all('script'):
            if script.string and ('odds' in script.string.lower() or 'game' in script.string.lower()):
                # Try to extract JSON objects
                matches = re.findall(r'\{[^{}]*"(?:odds|game|event)"[^{}]*\}', script.string)
                for match in matches:
                    try:
                        game_data = json.loads(match)
                        game = self._parse_game_data(game_data)
                        if game:
                            games.append(game)
                    except:
                        continue

        # If no embedded JSON found, parse HTML structure
        if not games:
            print("No JSON found in scripts, parsing HTML structure...")
            games = self._parse_html_odds(soup)

        return games

    def _parse_json_odds(self, data: dict) -> List[Dict]:
        """Parse odds from JSON API response"""
        games = []

        # Handle different possible JSON structures
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try common keys
            items = data.get('games') or data.get('events') or data.get('data') or [data]
        else:
            return games

        for item in items:
            game = self._parse_game_data(item)
            if game:
                games.append(game)

        return games

    def _parse_game_data(self, data: dict) -> Optional[Dict]:
        """Parse individual game data into Billy Walters format"""
        try:
            # Extract team names
            home_team = data.get('homeTeam') or data.get('home') or data.get('team1')
            away_team = data.get('awayTeam') or data.get('away') or data.get('team2')

            if not home_team or not away_team:
                return None

            # Extract markets
            markets = data.get('markets') or data.get('odds') or {}

            game = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "overtime.ag",
                "sport": data.get('sport', 'FOOTBALL'),
                "league": data.get('league', 'NFL'),
                "home_team": home_team,
                "away_team": away_team,
                "game_time": data.get('gameTime') or data.get('startTime'),
                "markets": {
                    "spread": self._extract_market(markets, 'spread'),
                    "total": self._extract_market(markets, 'total'),
                    "moneyline": self._extract_market(markets, 'moneyline'),
                }
            }

            return game
        except Exception as e:
            print(f"Error parsing game data: {e}")
            return None

    def _extract_market(self, markets: dict, market_type: str) -> Optional[Dict]:
        """Extract specific market data (spread, total, moneyline)"""
        market = markets.get(market_type)
        if not market:
            return None

        return {
            "home": market.get('home') or market.get('home_odds'),
            "away": market.get('away') or market.get('away_odds'),
            "line": market.get('line') or market.get('handicap'),
        }

    def _parse_html_odds(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse odds from HTML structure"""
        games = []

        # This will need to be customized based on actual HTML structure
        # For now, return empty list - will need live game to inspect HTML
        print("HTML parsing not yet implemented - need live game HTML to inspect structure")

        return games

    def save_to_jsonl(self, games: List[Dict], output_file: str):
        """
        Save games to JSONL file

        Args:
            games: List of game dictionaries
            output_file: Path to output file
        """
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for game in games:
                f.write(json.dumps(game) + '\n')

        print(f"Saved {len(games)} games to {output_file}")

    def scrape(self, output_file: str = "output/overtime_odds.jsonl") -> List[Dict]:
        """
        Main scraping method

        Args:
            output_file: Path to save JSONL output

        Returns:
            List of scraped games
        """
        print("=" * 60)
        print("Overtime.ag Requests Scraper")
        print("=" * 60)

        # Login
        if not self.login():
            print("Login failed, continuing anyway...")

        # Fetch live odds
        content = self.fetch_live_odds()
        if not content:
            print("Failed to fetch live odds")
            return []

        # Parse odds
        games = self.parse_odds(content)
        print(f"Extracted {len(games)} games")

        if not games:
            print("No games found - this is normal if no games are currently live")
            return []

        # Save to JSONL
        self.save_to_jsonl(games, output_file)

        # Print sample
        if games:
            print("\nSample game:")
            print(json.dumps(games[0], indent=2))

        return games


def main():
    """Main entry point"""
    try:
        scraper = OvertimeRequestsScraper()
        games = scraper.scrape()

        print("\n" + "=" * 60)
        if games:
            print(f"[SUCCESS] Scraped {len(games)} games!")
        else:
            print("[INFO] No games extracted")
            print("This is normal if no NFL/NCAAF games are currently live")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
