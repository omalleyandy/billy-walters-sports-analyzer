"""
Data Extraction Utilities

Helper functions for extracting and parsing data from website responses,
HTML content, and JSON structures. Provides robust parsing with error handling.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that may contain other content.

    Args:
        text: Text that may contain JSON

    Returns:
        Parsed JSON dict or None if not found
    """
    # Try to find JSON object boundaries
    json_patterns = [
        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",  # Simple object
        r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]",  # Simple array
    ]

    for pattern in json_patterns:
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    # Try parsing entire text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    return None


def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extract all numbers from text.

    Args:
        text: Text containing numbers

    Returns:
        List of extracted numbers
    """
    pattern = r"-?\d+\.?\d*"
    matches = re.findall(pattern, text)
    return [float(m) for m in matches]


def parse_datetime(
    date_str: str, formats: Optional[List[str]] = None
) -> Optional[datetime]:
    """
    Parse datetime string with multiple format attempts.

    Args:
        date_str: Date/time string to parse
        formats: List of format strings to try (defaults to common formats)

    Returns:
        Parsed datetime or None
    """
    if formats is None:
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse datetime: {date_str}")
    return None


def extract_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Extract nested value from dict using dot notation.

    Args:
        data: Dictionary to extract from
        path: Dot-separated path (e.g., "user.profile.name")
        default: Default value if path not found

    Returns:
        Extracted value or default
    """
    keys = path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and key.isdigit():
            try:
                current = current[int(key)]
            except (IndexError, ValueError):
                return default
        else:
            return default

        if current is None:
            return default

    return current


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_team_name(text: str) -> Optional[str]:
    """
    Extract team name from text (handles abbreviations, full names).

    Args:
        text: Text containing team name

    Returns:
        Extracted team name or None
    """
    # Common NFL/NCAAF team patterns
    team_patterns = [
        r"\b([A-Z]{2,4})\b",  # Abbreviations (KC, GB, etc.)
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",  # Full names
    ]

    for pattern in team_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]

    return None


def parse_odds_string(odds_str: str) -> Optional[Dict[str, Union[int, float]]]:
    """
    Parse odds string into structured format.

    Handles formats like:
    - "+150" or "-150"
    - "o48.5\n-110\nu48.5\n-110"
    - "+2.5\n-105\n-2.5\n-115"

    Args:
        odds_str: Odds string to parse

    Returns:
        Dict with parsed odds or None
    """
    # Clean the string
    odds_str = clean_text(odds_str)
    lines = [line.strip() for line in odds_str.split("\n") if line.strip()]

    result: Dict[str, Union[int, float]] = {}

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if it's a number (could be spread/total or odds)
        if re.match(r"^[+-]?\d+\.?\d*$", line):
            value = float(line)

            # Check if next line is odds (starts with + or -)
            if i + 1 < len(lines) and re.match(r"^[+-]\d+$", lines[i + 1]):
                odds = int(lines[i + 1])

                # Determine type based on value
                if abs(value) > 50:
                    # Likely a total (over/under)
                    if value > 0:
                        result["over"] = value
                        result["over_odds"] = odds
                    else:
                        result["under"] = abs(value)
                        result["under_odds"] = odds
                else:
                    # Likely a spread
                    if value > 0:
                        result["away_spread"] = value
                        result["away_odds"] = odds
                    else:
                        result["home_spread"] = abs(value)
                        result["home_odds"] = odds

                i += 2
            else:
                # Just a value, no odds
                if "value" not in result:
                    result["value"] = value
                i += 1
        else:
            i += 1

    return result if result else None


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract URLs from text.

    Args:
        text: Text containing URLs

    Returns:
        List of extracted URLs
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches = re.findall(url_pattern, text)
    return matches


def validate_game_data(game: Dict[str, Any]) -> bool:
    """
    Validate that game data has required fields.

    Args:
        game: Game data dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["away_team", "home_team"]
    return all(field in game and game[field] for field in required_fields)


def normalize_team_name(team_name: str) -> str:
    """
    Normalize team name for consistent matching.

    Args:
        team_name: Team name to normalize

    Returns:
        Normalized team name
    """
    # Remove common suffixes
    team_name = re.sub(
        r"\s+(FC|United|City|FC|SC)$", "", team_name, flags=re.IGNORECASE
    )
    # Convert to uppercase for consistency
    team_name = team_name.upper().strip()
    return team_name


def extract_table_data(
    html_content: str, table_selector: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Extract data from HTML table (basic implementation).

    Note: For complex tables, use Playwright or BeautifulSoup.

    Args:
        html_content: HTML content containing table
        table_selector: CSS selector for table (not used in basic version)

    Returns:
        List of row dictionaries
    """
    # This is a basic implementation
    # For production use, integrate with BeautifulSoup or Playwright
    rows = []
    # Simple regex-based extraction (limited)
    row_pattern = r"<tr[^>]*>(.*?)</tr>"
    cell_pattern = r"<t[dh][^>]*>(.*?)</t[dh]>"

    for row_match in re.finditer(row_pattern, html_content, re.DOTALL):
        row_html = row_match.group(1)
        cells = re.findall(cell_pattern, row_html, re.DOTALL)
        if cells:
            # Clean HTML tags from cell content
            clean_cells = [re.sub(r"<[^>]+>", "", cell).strip() for cell in cells]
            rows.append({f"col_{i}": cell for i, cell in enumerate(clean_cells)})

    return rows


def safe_json_parse(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with error handling.

    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"JSON parse error: {e}")
        return default


def extract_api_response_data(
    response_data: Dict[str, Any], data_path: str = "data"
) -> List[Dict[str, Any]]:
    """
    Extract data array from API response structure.

    Handles common API response formats:
    - {"data": [...]}
    - {"results": [...]}
    - {"items": [...]}

    Args:
        response_data: API response dictionary
        data_path: Path to data array (default: "data")

    Returns:
        List of data items
    """
    # Try specified path first
    if data_path in response_data:
        items = response_data[data_path]
        if isinstance(items, list):
            return items

    # Try common alternative paths
    for alt_path in ["results", "items", "games", "events", "matches"]:
        if alt_path in response_data:
            items = response_data[alt_path]
            if isinstance(items, list):
                return items

    return []


def parse_score_string(score_str: str) -> Optional[Dict[str, int]]:
    """
    Parse score string into away/home scores.

    Handles formats like:
    - "24-17"
    - "Away: 24, Home: 17"
    - "24 to 17"

    Args:
        score_str: Score string to parse

    Returns:
        Dict with 'away' and 'home' scores or None
    """
    # Try simple format: "24-17"
    match = re.match(r"(\d+)[\s\-to]+(\d+)", score_str)
    if match:
        return {"away": int(match.group(1)), "home": int(match.group(2))}

    # Try labeled format: "Away: 24, Home: 17"
    away_match = re.search(r"away[:\s]+(\d+)", score_str, re.IGNORECASE)
    home_match = re.search(r"home[:\s]+(\d+)", score_str, re.IGNORECASE)

    if away_match and home_match:
        return {
            "away": int(away_match.group(1)),
            "home": int(home_match.group(1)),
        }

    return None
