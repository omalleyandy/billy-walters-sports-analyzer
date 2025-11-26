#!/usr/bin/env python3
"""
Action Network Odds Scraper using Playwright

Scrapes betting odds, betting percentages (tickets vs money), and line movements
from Action Network. This data is critical for Billy Walters methodology to
identify sharp vs public money divergence.

Designed for automated periodic collection with CloudFlare bypass.
"""

import asyncio
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict, field

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BettingPercentages:
    """Betting percentages for sharp money analysis."""
    tickets_pct: Optional[int] = None
    money_pct: Optional[int] = None
    
    @property
    def divergence(self) -> Optional[int]:
        """Money % minus Tickets % - positive means sharp side."""
        if self.tickets_pct is not None and self.money_pct is not None:
            return self.money_pct - self.tickets_pct
        return None


@dataclass
class SpreadLine:
    """Spread betting line."""
    value: float
    odds: int = -110
    betting: BettingPercentages = field(default_factory=BettingPercentages)


@dataclass
class MoneylineLine:
    """Moneyline betting line."""
    odds: int
    betting: BettingPercentages = field(default_factory=BettingPercentages)


@dataclass
class TotalLine:
    """Total (over/under) betting line."""
    value: float
    odds: int = -110
    betting: BettingPercentages = field(default_factory=BettingPercentages)


@dataclass
class GameOdds:
    """Complete odds for a single game."""
    game_id: int
    away_team: str
    home_team: str
    away_record: str
    home_record: str
    start_time: str
    week: int
    broadcast: Optional[str] = None
    
    # Spreads
    home_spread: Optional[SpreadLine] = None
    away_spread: Optional[SpreadLine] = None
    opening_spread: Optional[float] = None
    
    # Moneylines
    home_ml: Optional[MoneylineLine] = None
    away_ml: Optional[MoneylineLine] = None
    
    # Totals
    over: Optional[TotalLine] = None
    under: Optional[TotalLine] = None
    
    @property
    def spread_line(self) -> Optional[float]:
        """Get home spread value."""
        return self.home_spread.value if self.home_spread else None
    
    @property
    def total_line(self) -> Optional[float]:
        """Get total value."""
        return self.over.value if self.over else None
    
    @property
    def line_movement(self) -> Optional[float]:
        """Calculate spread movement from open."""
        if self.opening_spread is not None and self.spread_line is not None:
            return self.spread_line - self.opening_spread
        return None
    
    @property
    def sharp_spread_side(self) -> Optional[str]:
        """Determine which spread side has sharp action (5+ divergence)."""
        if self.home_spread and self.away_spread:
            home_div = self.home_spread.betting.divergence
            away_div = self.away_spread.betting.divergence
            
            if home_div is not None and home_div >= 5:
                return self.home_team
            if away_div is not None and away_div >= 5:
                return self.away_team
            if home_div is not None and home_div <= -5:
                return self.away_team  # Fade public
            if away_div is not None and away_div <= -5:
                return self.home_team  # Fade public
        return None


class ActionNetworkScraper:
    """
    Playwright-based scraper for Action Network odds data.
    
    Extracts:
    - Betting odds (spreads, moneylines, totals)
    - Betting percentages (tickets vs money)
    - Opening lines for line movement tracking
    
    Usage:
        scraper = ActionNetworkScraper()
        await scraper.initialize()
        games = await scraper.scrape_nfl_odds()
        await scraper.close()
    """
    
    URLS = {
        'nfl': 'https://www.actionnetwork.com/nfl/odds',
        'ncaaf': 'https://www.actionnetwork.com/ncaaf/odds',
        'nba': 'https://www.actionnetwork.com/nba/odds',
        'ncaab': 'https://www.actionnetwork.com/ncaab/odds',
    }
    
    # League-specific divergence thresholds
    # NFL has efficient markets with lower divergences
    # NCAAF has less betting volume, resulting in higher divergences
    DIVERGENCE_THRESHOLDS = {
        'nfl': {
            'moderate': 5,    # 5+ = moderate sharp signal
            'strong': 10,     # 10+ = strong sharp signal  
            'very_strong': 15 # 15+ = very strong sharp signal
        },
        'ncaaf': {
            'moderate': 20,   # 20+ = moderate sharp signal
            'strong': 30,     # 30+ = strong sharp signal
            'very_strong': 40 # 40+ = very strong sharp signal
        },
        'nba': {
            'moderate': 5,
            'strong': 10,
            'very_strong': 15
        },
        'ncaab': {
            'moderate': 15,   # College basketball similar to NCAAF
            'strong': 25,
            'very_strong': 35
        }
    }
    
    @classmethod
    def get_min_divergence(cls, league: str) -> int:
        """Get minimum divergence threshold for a league."""
        thresholds = cls.DIVERGENCE_THRESHOLDS.get(league.lower(), cls.DIVERGENCE_THRESHOLDS['nfl'])
        return thresholds['moderate']
    
    @classmethod
    def get_signal_strength(cls, league: str, divergence: int) -> str:
        """
        Get signal strength label for a divergence value.
        
        Args:
            league: League identifier ('nfl', 'ncaaf', etc.)
            divergence: Absolute divergence value
            
        Returns:
            Signal strength: 'VERY_STRONG', 'STRONG', 'MODERATE', or 'NONE'
        """
        thresholds = cls.DIVERGENCE_THRESHOLDS.get(league.lower(), cls.DIVERGENCE_THRESHOLDS['nfl'])
        abs_div = abs(divergence)
        
        if abs_div >= thresholds['very_strong']:
            return 'VERY_STRONG'
        elif abs_div >= thresholds['strong']:
            return 'STRONG'
        elif abs_div >= thresholds['moderate']:
            return 'MODERATE'
        return 'NONE'
    
    def __init__(self, headless: bool = True, data_dir: Optional[Path] = None):
        """
        Initialize scraper.
        
        Args:
            headless: Run browser in headless mode
            data_dir: Directory to save scraped data
        """
        self.headless = headless
        self.data_dir = Path(data_dir) if data_dir else Path('data/action_network')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def initialize(self):
        """Initialize Playwright browser with anti-detection settings."""
        self.playwright = await async_playwright().start()
        
        # Launch options with stealth settings
        launch_options = {
            'headless': self.headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
            ]
        }
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        
        # Create context with realistic browser fingerprint
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            color_scheme='light',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        self.page = await self.context.new_page()
        
        # Add stealth scripts to evade detection
        await self.page.add_init_script("""
            // Hide webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // Add chrome object
            window.chrome = { runtime: {} };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Fake plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Fake languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        logger.info("Browser initialized with stealth settings")
    
    async def _wait_for_cloudflare(self):
        """Handle CloudFlare challenge if present."""
        try:
            await self.page.wait_for_selector('body', timeout=5000)
            
            # Check for CloudFlare challenge
            cf_check = await self.page.locator('text="Checking your browser"').count()
            if cf_check > 0:
                logger.info("CloudFlare challenge detected, waiting...")
                await self.page.wait_for_selector(
                    'text="Checking your browser"', 
                    state='hidden', 
                    timeout=30000
                )
                await asyncio.sleep(2)
                logger.info("CloudFlare challenge passed")
                
        except Exception as e:
            logger.debug(f"No CloudFlare challenge or already passed: {e}")
    
    async def _extract_next_data(self) -> Optional[dict]:
        """Extract __NEXT_DATA__ JSON from page."""
        try:
            # Wait for the script to be attached to DOM (not visible - script tags are always hidden)
            await self.page.wait_for_selector('script#__NEXT_DATA__', state='attached', timeout=10000)
            
            # Extract JSON content
            script_content = await self.page.evaluate("""
                () => {
                    const script = document.getElementById('__NEXT_DATA__');
                    return script ? script.textContent : null;
                }
            """)
            
            if script_content:
                return json.loads(script_content)
            
        except Exception as e:
            logger.error(f"Error extracting __NEXT_DATA__: {e}")
        
        return None
    
    def _parse_game_data(self, game_data: dict, all_books: dict) -> Optional[GameOdds]:
        """Parse a single game's data from Action Network format."""
        try:
            teams = game_data.get('teams', [])
            if len(teams) < 2:
                return None
            
            away = teams[0]
            home = teams[1]
            
            # Extract standings
            away_standings = away.get('standings', {})
            home_standings = home.get('standings', {})
            
            away_record = f"{away_standings.get('win', 0)}-{away_standings.get('loss', 0)}"
            home_record = f"{home_standings.get('win', 0)}-{home_standings.get('loss', 0)}"
            
            # Get broadcast info
            broadcast_info = game_data.get('broadcast', {})
            broadcast = broadcast_info.get('network') if isinstance(broadcast_info, dict) else None
            
            game = GameOdds(
                game_id=game_data.get('id', 0),
                away_team=away.get('abbr', ''),
                home_team=home.get('abbr', ''),
                away_record=away_record,
                home_record=home_record,
                start_time=game_data.get('start_time', ''),
                week=game_data.get('week', 0),
                broadcast=broadcast
            )
            
            # Parse markets
            markets = game_data.get('markets', {})
            
            # Get consensus odds (book_id = 15)
            consensus = markets.get('15', {})
            if consensus:
                inner = list(consensus.values())[0] if consensus else {}
                self._parse_consensus_odds(game, inner)
            
            # Get opening lines (book_id = 30)
            opening = markets.get('30', {})
            if opening:
                inner = list(opening.values())[0] if opening else {}
                for s in inner.get('spread', []):
                    if s.get('side') == 'home':
                        game.opening_spread = s.get('value')
                        break
            
            return game
            
        except Exception as e:
            logger.error(f"Error parsing game: {e}")
            return None
    
    def _parse_consensus_odds(self, game: GameOdds, odds_data: dict) -> None:
        """Parse consensus odds from Action Network data."""
        # Parse spreads
        for spread in odds_data.get('spread', []):
            side = spread.get('side')
            bet_info = spread.get('bet_info', {})
            
            spread_line = SpreadLine(
                value=spread.get('value', 0),
                odds=spread.get('odds', -110),
                betting=BettingPercentages(
                    tickets_pct=bet_info.get('tickets', {}).get('percent'),
                    money_pct=bet_info.get('money', {}).get('percent')
                )
            )
            
            if side == 'home':
                game.home_spread = spread_line
            else:
                game.away_spread = spread_line
        
        # Parse moneylines
        for ml in odds_data.get('moneyline', []):
            side = ml.get('side')
            bet_info = ml.get('bet_info', {})
            
            ml_line = MoneylineLine(
                odds=ml.get('odds', 0),
                betting=BettingPercentages(
                    tickets_pct=bet_info.get('tickets', {}).get('percent'),
                    money_pct=bet_info.get('money', {}).get('percent')
                )
            )
            
            if side == 'home':
                game.home_ml = ml_line
            else:
                game.away_ml = ml_line
        
        # Parse totals
        for total in odds_data.get('total', []):
            side = total.get('side')
            bet_info = total.get('bet_info', {})
            
            total_line = TotalLine(
                value=total.get('value', 0),
                odds=total.get('odds', -110),
                betting=BettingPercentages(
                    tickets_pct=bet_info.get('tickets', {}).get('percent'),
                    money_pct=bet_info.get('money', {}).get('percent')
                )
            )
            
            if side == 'over':
                game.over = total_line
            else:
                game.under = total_line
    
    async def scrape_odds(self, league: str = 'nfl') -> list[GameOdds]:
        """
        Scrape odds for a specific league.
        
        Args:
            league: 'nfl', 'ncaaf', 'nba', or 'ncaab'
            
        Returns:
            List of GameOdds objects
        """
        url = self.URLS.get(league.lower())
        if not url:
            raise ValueError(f"Unknown league: {league}")
        
        games = []
        
        try:
            logger.info(f"Navigating to {url}")
            
            # Navigate with retries
            for attempt in range(3):
                try:
                    await self.page.goto(url, wait_until='networkidle', timeout=60000)
                    await self._wait_for_cloudflare()
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == 2:
                        raise
                    await asyncio.sleep(5)
            
            # Wait for page to fully load
            await asyncio.sleep(3)
            
            # Extract __NEXT_DATA__
            data = await self._extract_next_data()
            
            if not data:
                logger.error("Failed to extract __NEXT_DATA__")
                # Save screenshot for debugging
                await self.page.screenshot(path=str(self.data_dir / 'error_screenshot.png'))
                return games
            
            # Parse games - __NEXT_DATA__ structure is props.pageProps
            props = data.get('props', {})
            page_props = props.get('pageProps', {})
            all_books = page_props.get('allBooks', {})
            sb_response = page_props.get('scoreboardResponse', {})
            
            for game_data in sb_response.get('games', []):
                game = self._parse_game_data(game_data, all_books)
                if game:
                    games.append(game)
            
            logger.info(f"Scraped {len(games)} {league.upper()} games")
            
        except Exception as e:
            logger.error(f"Error scraping {league}: {e}")
            await self.page.screenshot(path=str(self.data_dir / f'error_{league}.png'))
        
        return games
    
    async def scrape_nfl_odds(self) -> list[GameOdds]:
        """Convenience method for NFL odds."""
        return await self.scrape_odds('nfl')
    
    async def scrape_ncaaf_odds(self) -> list[GameOdds]:
        """Convenience method for NCAAF odds."""
        return await self.scrape_odds('ncaaf')
    
    def get_sharp_plays(self, games: list[GameOdds], league: str = 'nfl', min_divergence: Optional[int] = None) -> list[dict]:
        """
        Identify games with sharp money divergence.
        
        Uses league-specific thresholds:
        - NFL: 5+ (moderate), 10+ (strong), 15+ (very strong)
        - NCAAF: 20+ (moderate), 30+ (strong), 40+ (very strong)
        
        NOTE: Action Network's "home"/"away" labels in their API data may not match
        physical home/away teams. We determine the correct team based on spread value:
        - Negative spread = favorite (laying points)
        - Positive spread = underdog (getting points)
        
        Args:
            games: List of GameOdds
            league: League identifier for threshold selection
            min_divergence: Override minimum divergence (uses league default if None)
            
        Returns:
            List of sharp play dictionaries with signal strength
        """
        # Use league-specific threshold if not overridden
        if min_divergence is None:
            min_divergence = self.get_min_divergence(league)
        
        sharp_plays = []
        
        for game in games:
            if not (game.home_spread and game.away_spread):
                continue
            
            home_div = game.home_spread.betting.divergence or 0
            away_div = game.away_spread.betting.divergence or 0
            
            # Check for significant divergence
            if abs(away_div) >= min_divergence or abs(home_div) >= min_divergence:
                # Determine which spread LINE has sharp money
                # (Don't trust "home"/"away" labels - they may be inverted)
                
                if home_div >= min_divergence:
                    sharp_spread_value = game.home_spread.value
                    div = home_div
                    tickets_pct = game.home_spread.betting.tickets_pct
                    money_pct = game.home_spread.betting.money_pct
                elif away_div >= min_divergence:
                    sharp_spread_value = game.away_spread.value
                    div = away_div
                    tickets_pct = game.away_spread.betting.tickets_pct
                    money_pct = game.away_spread.betting.money_pct
                elif home_div <= -min_divergence:
                    # Fade public on "home" line = bet "away" line
                    sharp_spread_value = game.away_spread.value
                    div = away_div
                    tickets_pct = game.away_spread.betting.tickets_pct
                    money_pct = game.away_spread.betting.money_pct
                else:
                    # Fade public on "away" line = bet "home" line
                    sharp_spread_value = game.home_spread.value
                    div = home_div
                    tickets_pct = game.home_spread.betting.tickets_pct
                    money_pct = game.home_spread.betting.money_pct
                
                # Determine which team the spread belongs to based on value:
                # - Negative spread value = favorite (laying points)
                # - Positive spread value = underdog (getting points)
                # 
                # We use the GAME FORMAT to determine teams:
                # "AWAY @ HOME" means away_team is visitor, home_team is at home
                #
                # Check which team is ACTUALLY the underdog by looking at
                # WHICH spread line has the positive value
                # If away_spread.value > 0, the physically away team is underdog
                # If home_spread.value > 0, the physically home team is underdog
                
                if game.away_spread.value > 0:
                    # Away team is underdog (getting points)
                    underdog = game.away_team
                    favorite = game.home_team
                else:
                    # Home team is underdog (getting points)
                    underdog = game.home_team
                    favorite = game.away_team
                
                # Now match the sharp spread to the correct team
                if sharp_spread_value > 0:
                    # Sharp money on the underdog
                    sharp_side = underdog
                else:
                    # Sharp money on the favorite
                    sharp_side = favorite
                
                sharp_plays.append({
                    'game': f"{game.away_team} @ {game.home_team}",
                    'pick': f"{sharp_side} {sharp_spread_value:+.1f}",
                    'tickets_pct': tickets_pct,
                    'money_pct': money_pct,
                    'divergence': div,
                    'line_move': game.line_movement,
                    'signal': 'SHARP' if div > 0 else 'FADE_PUBLIC',
                    'signal_strength': self.get_signal_strength(league, div)
                })
        
        return sorted(sharp_plays, key=lambda x: abs(x['divergence']), reverse=True)
    
    def save_data(self, games: list[GameOdds], league: str = 'nfl') -> Path:
        """
        Save scraped data to JSON file.
        
        Args:
            games: List of GameOdds
            league: League identifier
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now()
        
        # Determine week number from first game
        week = games[0].week if games else 0
        
        # Build output data
        output = {
            'source': 'action_network',
            'league': league,
            'week': week,
            'scraped_at': timestamp.isoformat(),
            'game_count': len(games),
            'games': []
        }
        
        for game in games:
            game_dict = {
                'game_id': game.game_id,
                'away_team': game.away_team,
                'home_team': game.home_team,
                'away_record': game.away_record,
                'home_record': game.home_record,
                'start_time': game.start_time,
                'week': game.week,
                'broadcast': game.broadcast,
            }
            
            # Add spread data
            if game.home_spread:
                game_dict['spread'] = {
                    'home': {
                        'value': game.home_spread.value,
                        'odds': game.home_spread.odds,
                        'tickets_pct': game.home_spread.betting.tickets_pct,
                        'money_pct': game.home_spread.betting.money_pct
                    }
                }
            if game.away_spread:
                game_dict['spread']['away'] = {
                    'value': game.away_spread.value,
                    'odds': game.away_spread.odds,
                    'tickets_pct': game.away_spread.betting.tickets_pct,
                    'money_pct': game.away_spread.betting.money_pct
                }
            
            game_dict['opening_spread'] = game.opening_spread
            game_dict['line_movement'] = game.line_movement
            
            # Add moneyline data
            if game.home_ml or game.away_ml:
                game_dict['moneyline'] = {}
                if game.home_ml:
                    game_dict['moneyline']['home'] = {
                        'odds': game.home_ml.odds,
                        'tickets_pct': game.home_ml.betting.tickets_pct,
                        'money_pct': game.home_ml.betting.money_pct
                    }
                if game.away_ml:
                    game_dict['moneyline']['away'] = {
                        'odds': game.away_ml.odds,
                        'tickets_pct': game.away_ml.betting.tickets_pct,
                        'money_pct': game.away_ml.betting.money_pct
                    }
            
            # Add total data
            if game.over or game.under:
                game_dict['total'] = {}
                if game.over:
                    game_dict['total']['over'] = {
                        'value': game.over.value,
                        'odds': game.over.odds,
                        'tickets_pct': game.over.betting.tickets_pct,
                        'money_pct': game.over.betting.money_pct
                    }
                if game.under:
                    game_dict['total']['under'] = {
                        'value': game.under.value,
                        'odds': game.under.odds,
                        'tickets_pct': game.under.betting.tickets_pct,
                        'money_pct': game.under.betting.money_pct
                    }
            
            # Add sharp indicator
            game_dict['sharp_side'] = game.sharp_spread_side
            
            output['games'].append(game_dict)
        
        # Add sharp plays summary (use league-specific thresholds)
        output['sharp_plays'] = self.get_sharp_plays(games, league=league)
        output['divergence_thresholds'] = self.DIVERGENCE_THRESHOLDS.get(league, self.DIVERGENCE_THRESHOLDS['nfl'])
        
        # Save to file
        filename = f"{league}_odds_week{week}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Saved data to {filepath}")
        
        # Also save a "latest" symlink/copy
        latest_path = self.data_dir / f"{league}_odds_latest.json"
        with open(latest_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        return filepath
    
    async def close(self):
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")


async def main():
    """Main execution for standalone use."""
    print("\n" + "=" * 60)
    print("ACTION NETWORK ODDS SCRAPER")
    print("Sharp Money Detection for Billy Walters System")
    print("=" * 60 + "\n")
    
    scraper = ActionNetworkScraper(headless=True)
    
    try:
        print("🚀 Initializing browser...")
        await scraper.initialize()
        
        print("🏈 Scraping NFL odds from Action Network...")
        games = await scraper.scrape_nfl_odds()
        print(f"✅ Found {len(games)} NFL games")
        
        if games:
            # Save data
            filepath = scraper.save_data(games, 'nfl')
            print(f"💾 Data saved to {filepath}")
            
            # Show sharp plays
            sharp_plays = scraper.get_sharp_plays(games)
            if sharp_plays:
                print(f"\n🎯 SHARP MONEY SIGNALS ({len(sharp_plays)} games):")
                print("-" * 50)
                for play in sharp_plays:
                    print(f"\n{play['game']}")
                    print(f"  Pick: {play['pick']}")
                    print(f"  Tickets: {play['tickets_pct']}% | Money: {play['money_pct']}%")
                    print(f"  Divergence: {play['divergence']:+d} pts")
                    if play['line_move']:
                        print(f"  Line Move: {play['line_move']:+.1f}")
                    print(f"  Signal: {play['signal']}")
            
            # Show all games summary
            print(f"\n📊 ALL GAMES SUMMARY:")
            print("-" * 70)
            for game in games:
                spread = f"{game.home_team} {game.spread_line:+.1f}" if game.spread_line else "N/A"
                sharp = f" ⭐ Sharp: {game.sharp_spread_side}" if game.sharp_spread_side else ""
                print(f"{game.away_team} @ {game.home_team}: {spread}{sharp}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.close()
    
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
