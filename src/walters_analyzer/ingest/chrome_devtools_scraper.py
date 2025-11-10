"""
Chrome DevTools Scraper for Overtime.ag
Bypasses Cloudflare using MCP chrome-devtools integration
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Any
import json


def parse_fraction(line_str: str) -> float:
    """Convert fraction symbols to decimal (e.g., '6½' -> 6.5)"""
    if '½' in line_str:
        return float(line_str.replace('½', '.5'))
    return float(line_str)


def parse_spread_button(button_text: str) -> Optional[Dict[str, float]]:
    """
    Parse spread button text like '+9 -110' or '-6½ -110'
    Returns: {'line': 9.0, 'price': -110} or None
    """
    if not button_text:
        return None
    
    match = re.match(r'^([+\-][\d½\.]+)\s+([+\-]\d+)$', button_text.strip())
    if match:
        line = parse_fraction(match.group(1))
        price = int(match.group(2))
        return {'line': line, 'price': price}
    return None


def parse_moneyline_button(button_text: str) -> Optional[int]:
    """
    Parse moneyline button text like '+380' or '-515'
    Returns: integer price or None
    """
    if not button_text:
        return None
    
    match = re.match(r'^([+\-]\d{3,4})$', button_text.strip())
    if match:
        return int(match.group(1))
    return None


def parse_total_button(button_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse total button text like 'O 43 -110' or 'U 48 -110'
    Returns: {'side': 'over'/'under', 'line': 43.0, 'price': -110} or None
    """
    if not button_text:
        return None
    
    match = re.match(r'^([OU])\s+([\d½\.]+)\s+([+\-]\d+)$', button_text.strip())
    if match:
        side = 'over' if match.group(1) == 'O' else 'under'
        line = parse_fraction(match.group(2))
        price = int(match.group(3))
        return {'side': side, 'line': line, 'price': price}
    return None


def parse_date_time(date_str: str, time_str: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse date/time from overtime.ag format
    Date: 'Thu Nov 6' or 'Sun Nov 9'
    Time: '8:15 PM' or '1:00 PM'
    Returns: (ISO date, time with timezone)
    """
    try:
        current_year = datetime.now().year
        # Parse "Thu Nov 6" -> "2025-11-06"
        parts = date_str.split()
        if len(parts) >= 3:
            month_str = parts[1]
            day_str = parts[2]
            dt = datetime.strptime(f"{current_year} {month_str} {day_str}", "%Y %b %d")
            iso_date = dt.strftime("%Y-%m-%d")
            time_with_tz = f"{time_str} ET" if time_str and "ET" not in time_str else time_str
            return iso_date, time_with_tz
    except Exception:
        pass
    return None, None


class ChromeDevToolsOddsExtractor:
    """Extract betting odds from Chrome DevTools accessibility snapshot"""
    
    def __init__(self):
        self.current_date = None
        self.current_time = None
    
    def extract_games_from_snapshot(self, snapshot_text: str) -> List[Dict]:
        """
        Parse accessibility snapshot text to extract all games
        
        Snapshot structure pattern:
        uid=X StaticText "Thu Nov 6"        <- Date
        uid=Y StaticText "8:15 PM"          <- Time
        uid=Z StaticText "109"              <- Away rotation
        uid=A StaticText " "                <- Spacer
        uid=B StaticText "Las Vegas Raiders" <- Away team
        uid=C button "+9 -110"              <- Away spread
        uid=D button "+380"                 <- Away ML
        uid=E button "O 43 -110"            <- Away total (over)
        uid=F StaticText "110"              <- Home rotation
        uid=G StaticText " "                <- Spacer
        uid=H StaticText "Denver Broncos"   <- Home team
        uid=I button "-9 -110"              <- Home spread
        uid=J button "-515"                 <- Home ML
        uid=K button "U 43 -110"            <- Home total (under)
        
        Args:
            snapshot_text: Raw accessibility tree snapshot text
        
        Returns:
            List of game dictionaries in Billy Walters format
        """
        games = []
        lines = [l.strip() for l in snapshot_text.split('\n') if l.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for date header (Thu Nov 6, Sun Nov 9, etc.)
            date_match = re.search(r'StaticText "((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+\s+\d+)"', line)
            if date_match:
                self.current_date = date_match.group(1)
                i += 1
                continue
            
            # Check for time (8:15 PM, 1:00 PM, etc.)
            time_match = re.search(r'StaticText "(\d{1,2}:\d{2}\s+(?:AM|PM))"', line)
            if time_match:
                self.current_time = time_match.group(1)
                i += 1
                continue
            
            # Check for rotation number (3 digits) - indicates start of team
            rotation_match = re.search(r'StaticText "(\d{3})"', line)
            if rotation_match:
                # Try to extract full game pair (away + home)
                game = self._extract_game_pair(lines, i)
                if game:
                    games.append(game)
                    # Skip past both teams (typically 13-14 lines)
                    i += 13
                else:
                    i += 1
            else:
                i += 1
        
        return games
    
    def _extract_game_pair(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Extract a complete game (away + home team) starting at start_idx"""
        try:
            # Extract away team
            away_data = self._extract_team_data(lines, start_idx)
            if not away_data:
                return None
            
            # Extract home team (should be 6 lines after away rotation number)
            # Pattern: rotation(0) + space(1) + team(2) + spread(3) + ML(4) + total(5) + home_rotation(6)
            home_data = self._extract_team_data(lines, start_idx + 6)
            if not home_data:
                return None
            
            # Build game object
            iso_date, time_with_tz = parse_date_time(self.current_date or "", self.current_time or "")
            
            game = {
                'source': 'overtime.ag',
                'sport': 'nfl',
                'league': 'NFL',
                'collected_at': datetime.utcnow().isoformat() + 'Z',
                'rotation_number': f"{away_data['rotation']}-{home_data['rotation']}",
                'event_date': iso_date,
                'event_time': time_with_tz,
                'teams': {
                    'away': away_data['team'],
                    'home': home_data['team']
                },
                'markets': {
                    'spread': {
                        'away': away_data['spread'],
                        'home': home_data['spread']
                    },
                    'total': {
                        'over': away_data['total'],
                        'under': home_data['total']
                    },
                    'moneyline': {
                        'away': {'line': None, 'price': away_data['moneyline']},
                        'home': {'line': None, 'price': home_data['moneyline']}
                    }
                },
                'state': {},
                'is_live': False
            }
            
            # Generate game_key for uniqueness
            game['game_key'] = self._generate_game_key(
                away_data['team'], 
                home_data['team'], 
                iso_date
            )
            
            return game
            
        except Exception as e:
            return None
    
    def _extract_team_data(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """
        Extract single team data starting at rotation number line
        Expected structure:
        - Line 0: uid=X StaticText "109"
        - Line 1: uid=Y StaticText " "
        - Line 2: uid=Z StaticText "Las Vegas Raiders"
        - Line 3: uid=A button "+9 -110"
        - Line 4: uid=B button "+380"
        - Line 5: uid=C button "O 43 -110" (or "U 43 -110")
        """
        try:
            if start_idx >= len(lines):
                return None
            
            # Rotation number
            rotation_line = lines[start_idx]
            rotation_match = re.search(r'StaticText "(\d{3})"', rotation_line)
            if not rotation_match:
                return None
            rotation = rotation_match.group(1)
            
            # Team name (2 lines after rotation)
            if start_idx + 2 >= len(lines):
                return None
            team_line = lines[start_idx + 2]
            team_match = re.search(r'StaticText "([^"]+)"', team_line)
            if not team_match:
                return None
            team = team_match.group(1).strip()
            
            # Skip if it's just a space or empty
            if team == " " or not team:
                return None
            
            # Validate team name (no emojis, reasonable length)
            if len(team) < 3 or not re.match(r'^[A-Za-z\s\-\.&\']+$', team):
                return None
            
            # Spread button (3 lines after rotation)
            spread = None
            if start_idx + 3 < len(lines):
                spread_line = lines[start_idx + 3]
                spread_match = re.search(r'button "([^"]+)"', spread_line)
                if spread_match:
                    spread = parse_spread_button(spread_match.group(1))
            
            # Moneyline button (4 lines after rotation)
            moneyline = None
            if start_idx + 4 < len(lines):
                ml_line = lines[start_idx + 4]
                ml_match = re.search(r'button "([^"]+)"', ml_line)
                if ml_match:
                    moneyline = parse_moneyline_button(ml_match.group(1))
            
            # Total button (5 lines after rotation)
            total = None
            if start_idx + 5 < len(lines):
                total_line = lines[start_idx + 5]
                total_match = re.search(r'button "([^"]+)"', total_line)
                if total_match:
                    total = parse_total_button(total_match.group(1))
            
            return {
                'rotation': rotation,
                'team': team,
                'spread': spread,
                'moneyline': moneyline,
                'total': total
            }
            
        except (IndexError, AttributeError) as e:
            return None
    
    def _generate_game_key(self, away_team: str, home_team: str, date: Optional[str]) -> str:
        """Generate unique game key"""
        import hashlib
        key_string = f"{away_team}_{home_team}_{date or 'unknown'}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]


def scrape_overtime_odds_chrome_devtools() -> List[Dict]:
    """
    Main function to scrape odds using Chrome DevTools
    
    Returns:
        List of game dictionaries in Billy Walters format
    """
    # This will be called from a script that has access to MCP chrome-devtools
    # For now, return empty list as placeholder
    # The actual implementation will use MCP tools
    return []


def format_for_billy_walters(games: List[Dict]) -> List[Dict]:
    """
    Ensure games are in exact Billy Walters format
    
    Expected format:
    {
        "source": "overtime.ag",
        "sport": "nfl",
        "league": "NFL",
        "collected_at": "2025-11-06T13:00:00Z",
        "game_key": "abc123",
        "rotation_number": "109-110",
        "event_date": "2025-11-06",
        "event_time": "8:15 PM ET",
        "teams": {
            "away": "Las Vegas Raiders",
            "home": "Denver Broncos"
        },
        "markets": {
            "spread": {
                "away": {"line": 9.0, "price": -110},
                "home": {"line": -9.0, "price": -110}
            },
            "total": {
                "over": {"line": 43.0, "price": -110},
                "under": {"line": 43.0, "price": -110}
            },
            "moneyline": {
                "away": {"line": null, "price": 380},
                "home": {"line": null, "price": -515}
            }
        },
        "state": {},
        "is_live": false
    }
    """
    # Games are already in correct format from extract_games_from_snapshot
    # This function can add any final validation or formatting
    return games


if __name__ == "__main__":
    # Test the parser with sample snapshot data
    sample_snapshot = """
uid=1_73 StaticText "109"
uid=1_74 StaticText " "
uid=1_75 StaticText "Las Vegas Raiders"
uid=1_76 button "+9 -110"
uid=1_77 button "+380"
uid=1_78 button "O 43 -110"
uid=1_79 StaticText "110"
uid=1_80 StaticText " "
uid=1_81 StaticText "Denver Broncos"
uid=1_82 button "-9 -110"
uid=1_83 button "-515"
uid=1_84 button "U 43 -110"
    """
    
    extractor = ChromeDevToolsOddsExtractor()
    extractor.current_date = "Thu Nov 6"
    extractor.current_time = "8:15 PM"
    
    games = extractor.extract_games_from_snapshot(sample_snapshot)
    
    if games:
        print(f"Extracted {len(games)} games")
        print(json.dumps(games[0], indent=2))
    else:
        print("No games extracted - check parser logic")

