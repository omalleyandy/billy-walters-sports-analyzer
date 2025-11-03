"""
CDP (Chrome DevTools Protocol) helpers for network interception and odds tracking.

Provides utilities for:
- Network request/response interception via Playwright CDP
- Odds change detection and logging
- Console formatting for odds display
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from colorama import Fore, Style, init

# Initialize colorama for colored output
init()

logger = logging.getLogger(__name__)


def is_odds_api_response(url: str) -> bool:
    """
    Check if a URL corresponds to an odds API endpoint.
    
    Args:
        url: The URL to check
        
    Returns:
        True if URL matches known odds API patterns
    """
    odds_patterns = [
        '/api/',
        'GetCurrent',
        'BetType',
        'Offering.asmx',
        'GetSportOffering',
        'GetSports',
        '/sports/',
        '/odds/',
        '/betting/',
    ]
    url_lower = url.lower()
    return any(pattern.lower() in url_lower for pattern in odds_patterns)


def format_odds_display(game: Dict[str, Any]) -> str:
    """
    Format game odds for colorful console display.
    
    Args:
        game: Game data dictionary with teams and markets
        
    Returns:
        Formatted string with colorama styling
    """
    teams = game.get('teams', {})
    away_team = teams.get('away', 'Unknown')
    home_team = teams.get('home', 'Unknown')
    
    markets = game.get('markets', {})
    spread = markets.get('spread', {})
    total = markets.get('total', {})
    moneyline = markets.get('moneyline', {})
    
    state = game.get('state', {})
    quarter = state.get('quarter', '')
    clock = state.get('clock', '')
    
    lines = []
    lines.append(f"\n{Fore.CYAN}[GAME] {away_team} @ {home_team}{Style.RESET_ALL}")
    
    if quarter or clock:
        lines.append(f"   Status: Q{quarter} {clock}")
    
    # Spread
    spread_away = spread.get('away', {})
    spread_home = spread.get('home', {})
    if spread_away or spread_home:
        away_line = spread_away.get('line', '')
        away_price = spread_away.get('price', '')
        home_line = spread_home.get('line', '')
        home_price = spread_home.get('price', '')
        lines.append(
            f"   {Fore.YELLOW}Spread:{Style.RESET_ALL} "
            f"{away_line} ({away_price}) / {home_line} ({home_price})"
        )
    
    # Total
    total_over = total.get('over', {})
    total_under = total.get('under', {})
    if total_over or total_under:
        over_line = total_over.get('line', '')
        over_price = total_over.get('price', '')
        under_line = total_under.get('line', '')
        under_price = total_under.get('price', '')
        lines.append(
            f"   {Fore.YELLOW}Total:{Style.RESET_ALL} "
            f"O{over_line} ({over_price}) / U{under_line} ({under_price})"
        )
    
    # Moneyline
    ml_away = moneyline.get('away', {})
    ml_home = moneyline.get('home', {})
    if ml_away or ml_home:
        away_price = ml_away.get('price', '')
        home_price = ml_home.get('price', '')
        lines.append(
            f"   {Fore.YELLOW}ML:{Style.RESET_ALL} "
            f"Away: {away_price} / Home: {home_price}"
        )
    
    return '\n'.join(lines)


class OddsStorage(Protocol):
    """Protocol for odds storage backends."""
    
    def get_previous_odds(self, game_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve previous odds for a game."""
        ...
    
    def store_odds(self, game_key: str, odds_data: Dict[str, Any]) -> None:
        """Store current odds for a game."""
        ...
    
    def close(self) -> None:
        """Clean up storage resources."""
        ...


class SQLiteOddsStorage:
    """SQLite-based odds storage for change detection."""
    
    def __init__(self, db_path: str = "data/overtime_live/odds_changes.db"):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create necessary database tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS odds_history (
                game_key TEXT PRIMARY KEY,
                odds_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self.conn.commit()
    
    def get_previous_odds(self, game_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve previous odds for a game.
        
        Args:
            game_key: Unique game identifier
            
        Returns:
            Previous odds dictionary or None
        """
        cursor = self.conn.execute(
            "SELECT odds_json FROM odds_history WHERE game_key = ?",
            (game_key,)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None
    
    def store_odds(self, game_key: str, odds_data: Dict[str, Any]) -> None:
        """
        Store current odds for a game.
        
        Args:
            game_key: Unique game identifier
            odds_data: Odds data to store
        """
        self.conn.execute(
            """
            INSERT OR REPLACE INTO odds_history (game_key, odds_json, updated_at)
            VALUES (?, ?, ?)
            """,
            (game_key, json.dumps(odds_data), datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


class RedisOddsStorage:
    """Redis-based odds storage for distributed change detection."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Initialize Redis storage.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        try:
            import redis
            self.redis_client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.available = True
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.available = False
            self.redis_client = None
    
    def get_previous_odds(self, game_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve previous odds for a game.
        
        Args:
            game_key: Unique game identifier
            
        Returns:
            Previous odds dictionary or None
        """
        if not self.available:
            return None
        
        key = f"game:odds:{game_key}"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def store_odds(self, game_key: str, odds_data: Dict[str, Any]) -> None:
        """
        Store current odds for a game.
        
        Args:
            game_key: Unique game identifier
            odds_data: Odds data to store
        """
        if not self.available:
            return
        
        key = f"game:odds:{game_key}"
        self.redis_client.set(key, json.dumps(odds_data))
        # Expire after 48 hours
        self.redis_client.expire(key, 172800)
    
    def close(self) -> None:
        """Close Redis connection."""
        if self.available and self.redis_client:
            self.redis_client.close()


class OddsChangeDetector:
    """
    Detects and logs odds changes for sports betting markets.
    
    Tracks spread, total, and moneyline changes and logs them to CSV.
    """
    
    def __init__(
        self,
        storage: OddsStorage,
        output_dir: str = "data/overtime_live"
    ):
        """
        Initialize odds change detector.
        
        Args:
            storage: Odds storage backend (SQLite or Redis)
            output_dir: Directory for change logs
        """
        self.storage = storage
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def check_and_log_changes(self, game_data: Dict[str, Any]) -> bool:
        """
        Check for odds changes and log if detected.
        
        Args:
            game_data: Current game data with odds
            
        Returns:
            True if changes were detected, False otherwise
        """
        game_key = game_data.get('game_key')
        if not game_key:
            return False
        
        # Get previous odds
        previous = self.storage.get_previous_odds(game_key)
        
        # Store current odds
        current_markets = game_data.get('markets', {})
        self.storage.store_odds(game_key, current_markets)
        
        # Check for changes
        if not previous:
            return False
        
        changes = self._detect_changes(previous, current_markets)
        if changes:
            self._log_changes(game_data, changes)
            self._display_change_alert(game_data, changes)
            return True
        
        return False
    
    def _detect_changes(
        self,
        previous: Dict[str, Any],
        current: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect specific odds changes.
        
        Args:
            previous: Previous market odds
            current: Current market odds
            
        Returns:
            List of change descriptions
        """
        changes = []
        
        # Check spread changes
        prev_spread = previous.get('spread', {})
        curr_spread = current.get('spread', {})
        
        prev_away_line = prev_spread.get('away', {}).get('line')
        curr_away_line = curr_spread.get('away', {}).get('line')
        
        if prev_away_line != curr_away_line and curr_away_line is not None:
            changes.append({
                'market': 'spread',
                'field': 'away_line',
                'old_value': prev_away_line,
                'new_value': curr_away_line
            })
        
        # Check total changes
        prev_total = previous.get('total', {})
        curr_total = current.get('total', {})
        
        prev_over_line = prev_total.get('over', {}).get('line')
        curr_over_line = curr_total.get('over', {}).get('line')
        
        if prev_over_line != curr_over_line and curr_over_line is not None:
            changes.append({
                'market': 'total',
                'field': 'over_line',
                'old_value': prev_over_line,
                'new_value': curr_over_line
            })
        
        # Check moneyline changes
        prev_ml = previous.get('moneyline', {})
        curr_ml = current.get('moneyline', {})
        
        prev_away_price = prev_ml.get('away', {}).get('price')
        curr_away_price = curr_ml.get('away', {}).get('price')
        
        if prev_away_price != curr_away_price and curr_away_price is not None:
            changes.append({
                'market': 'moneyline',
                'field': 'away_price',
                'old_value': prev_away_price,
                'new_value': curr_away_price
            })
        
        return changes
    
    def _log_changes(
        self,
        game_data: Dict[str, Any],
        changes: List[Dict[str, Any]]
    ) -> None:
        """
        Log changes to CSV file.
        
        Args:
            game_data: Game data
            changes: List of detected changes
        """
        import csv
        
        date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
        csv_path = self.output_dir / f"odds_changes_{date_str}.csv"
        
        teams = game_data.get('teams', {})
        game_str = f"{teams.get('away', 'Unknown')} @ {teams.get('home', 'Unknown')}"
        
        # Check if file exists to determine if we need headers
        file_exists = csv_path.exists()
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'timestamp', 'game_key', 'game', 'market',
                'field', 'old_value', 'new_value'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            timestamp = datetime.now(timezone.utc).isoformat()
            for change in changes:
                writer.writerow({
                    'timestamp': timestamp,
                    'game_key': game_data.get('game_key'),
                    'game': game_str,
                    'market': change['market'],
                    'field': change['field'],
                    'old_value': change['old_value'],
                    'new_value': change['new_value']
                })
    
    def _display_change_alert(
        self,
        game_data: Dict[str, Any],
        changes: List[Dict[str, Any]]
    ) -> None:
        """
        Display colorful alert for odds changes.
        
        Args:
            game_data: Game data
            changes: List of detected changes
        """
        teams = game_data.get('teams', {})
        game_str = f"{teams.get('away', 'Unknown')} @ {teams.get('home', 'Unknown')}"
        
        print(f"\n{Fore.RED}[!] ODDS CHANGE DETECTED{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Game: {game_str}{Style.RESET_ALL}")
        
        for change in changes:
            print(
                f"  {Fore.YELLOW}{change['market']} {change['field']}:{Style.RESET_ALL} "
                f"{change['old_value']} -> {Fore.GREEN}{change['new_value']}{Style.RESET_ALL}"
            )


async def setup_cdp_interception(
    page,
    api_response_handler: Optional[callable] = None
) -> Any:
    """
    Setup CDP network interception on a Playwright page.
    
    Args:
        page: Playwright page object
        api_response_handler: Optional async callback for API responses
        
    Returns:
        CDP session object
    """
    # Create CDP session
    cdp = await page.context.new_cdp_session(page)
    
    # Enable network tracking
    await cdp.send('Network.enable', {
        'maxTotalBufferSize': 100000000,
        'maxResourceBufferSize': 100000000
    })
    
    # Setup response handler if provided
    if api_response_handler:
        async def response_handler(params):
            response = params.get('response', {})
            url = response.get('url', '')
            
            if is_odds_api_response(url):
                request_id = params.get('requestId')
                
                # Log response
                print(
                    f"{Fore.BLUE}[API] Response: "
                    f"{response.get('status')} - {url[:80]}...{Style.RESET_ALL}"
                )
                
                # Try to get response body
                try:
                    # Wait a bit for response to complete
                    await asyncio.sleep(0.1)
                    body_response = await cdp.send(
                        'Network.getResponseBody',
                        {'requestId': request_id}
                    )
                    body = body_response.get('body', '')
                    
                    if body:
                        await api_response_handler(url, body)
                except Exception as e:
                    # Body might not be available for all requests
                    pass
        
        cdp.on('Network.responseReceived', 
               lambda params: asyncio.create_task(response_handler(params)))
    
    return cdp


def save_api_response(url: str, body: str, output_dir: str = "data/overtime_live") -> None:
    """
    Save API response to JSON file.
    
    Args:
        url: Request URL
        body: Response body
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    
    # Extract endpoint name from URL for filename
    endpoint = 'unknown'
    if 'GetSportOffering' in url:
        endpoint = 'sport_offering'
    elif 'GetSports' in url:
        endpoint = 'sports'
    elif 'GetCurrent' in url:
        endpoint = 'current'
    elif 'BetType' in url:
        endpoint = 'bettype'
    
    filename = f"api_response_{endpoint}_{timestamp}.json"
    filepath = output_path / filename
    
    try:
        # Try to parse and pretty-print JSON
        data = json.loads(body)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"{Fore.GREEN}[OK] Saved API response: {filename}{Style.RESET_ALL}")
    except json.JSONDecodeError:
        # Save as-is if not valid JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(body)

