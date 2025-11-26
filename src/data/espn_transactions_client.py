"""
ESPN Transactions Client

Fetches NFL team roster transactions (trades, signings, releases, etc.) from ESPN.
Scrapes the team transactions page and extracts structured transaction data.

Usage:
    client = ESPNTransactionsClient()

    # Get transactions for a team
    transactions = await client.get_team_transactions("buf")

    # Get all NFL teams' transactions
    all_transactions = await client.get_all_nfl_transactions()

Transaction Types:
    - Signed: Player signed to roster
    - Traded: Player acquired via trade
    - Released: Player removed from roster
    - Waived: Player waived for potential claim by other teams
    - Claimed off waivers: Player claimed from waivers
    - Injured Reserve: Player placed on injured reserve
    - Activated: Player activated from injured reserve or suspension
    - Re-signed: Previously released player re-signed
    - Assigned: Practice squad assignment
    - Signed to practice squad: Practice squad signing

ESPN URL Pattern:
    - Team: https://www.espn.com/nfl/team/transactions/_/name/{team_abbr}/{team_name}
    - Example: https://www.espn.com/nfl/team/transactions/_/name/buf/buffalo-bills
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# NFL team ID and abbreviation mapping
NFL_TEAMS = {
    "atl": {"name": "atlanta-falcons", "full_name": "Atlanta Falcons"},
    "buf": {"name": "buffalo-bills", "full_name": "Buffalo Bills"},
    "chi": {"name": "chicago-bears", "full_name": "Chicago Bears"},
    "cin": {"name": "cincinnati-bengals", "full_name": "Cincinnati Bengals"},
    "cle": {"name": "cleveland-browns", "full_name": "Cleveland Browns"},
    "dal": {"name": "dallas-cowboys", "full_name": "Dallas Cowboys"},
    "den": {"name": "denver-broncos", "full_name": "Denver Broncos"},
    "det": {"name": "detroit-lions", "full_name": "Detroit Lions"},
    "gb": {"name": "green-bay-packers", "full_name": "Green Bay Packers"},
    "hou": {"name": "houston-texans", "full_name": "Houston Texans"},
    "ind": {"name": "indianapolis-colts", "full_name": "Indianapolis Colts"},
    "jax": {"name": "jacksonville-jaguars", "full_name": "Jacksonville Jaguars"},
    "kc": {"name": "kansas-city-chiefs", "full_name": "Kansas City Chiefs"},
    "lar": {"name": "los-angeles-rams", "full_name": "Los Angeles Rams"},
    "lac": {"name": "los-angeles-chargers", "full_name": "Los Angeles Chargers"},
    "lv": {"name": "las-vegas-raiders", "full_name": "Las Vegas Raiders"},
    "mia": {"name": "miami-dolphins", "full_name": "Miami Dolphins"},
    "min": {"name": "minnesota-vikings", "full_name": "Minnesota Vikings"},
    "ne": {"name": "new-england-patriots", "full_name": "New England Patriots"},
    "no": {"name": "new-orleans-saints", "full_name": "New Orleans Saints"},
    "nyg": {"name": "new-york-giants", "full_name": "New York Giants"},
    "nyj": {"name": "new-york-jets", "full_name": "New York Jets"},
    "phi": {"name": "philadelphia-eagles", "full_name": "Philadelphia Eagles"},
    "pit": {"name": "pittsburgh-steelers", "full_name": "Pittsburgh Steelers"},
    "sf": {"name": "san-francisco-49ers", "full_name": "San Francisco 49ers"},
    "sea": {"name": "seattle-seahawks", "full_name": "Seattle Seahawks"},
    "tb": {"name": "tampa-bay-buccaneers", "full_name": "Tampa Bay Buccaneers"},
    "ten": {"name": "tennessee-titans", "full_name": "Tennessee Titans"},
    "was": {"name": "washington-commanders", "full_name": "Washington Commanders"},
}


class ESPNTransactionsClient:
    """
    ESPN Transactions API client.

    Fetches NFL team roster transactions via web scraping since no dedicated
    API endpoint exists. Extracts player names, transaction types, dates, and
    transaction details.
    """

    BASE_URL = "https://www.espn.com/nfl/team/transactions"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize ESPN Transactions client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
            rate_limit_delay: Delay between requests (seconds) - 1s default for politeness
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Initialize HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def _make_request(self, url: str) -> str:
        """
        Make HTTP request with retry logic.

        Args:
            url: Full URL to fetch

        Returns:
            HTML content

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url)
                response.raise_for_status()

                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)

                return response.text

            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

        raise RuntimeError("Request failed after all retries")

    async def get_team_transactions(self, team_abbr: str) -> dict:
        """
        Get transactions for a specific NFL team.

        Args:
            team_abbr: Team abbreviation (e.g., 'buf' for Buffalo Bills)

        Returns:
            Dictionary with team info and transactions list
        """
        team_abbr_lower = team_abbr.lower()

        if team_abbr_lower not in NFL_TEAMS:
            raise ValueError(f"Unknown team abbreviation: {team_abbr}")

        team_info = NFL_TEAMS[team_abbr_lower]
        url = f"{self.BASE_URL}/_/name/{team_abbr_lower}/{team_info['name']}"

        logger.info(f"Fetching transactions for {team_info['full_name']}")

        html = await self._make_request(url)
        transactions = self._parse_transactions_html(html, team_abbr_lower)

        return {
            "team_abbr": team_abbr_lower,
            "team_name": team_info["full_name"],
            "transactions": transactions,
            "transaction_count": len(transactions),
            "fetched_at": datetime.now().isoformat(),
        }

    def _parse_transactions_html(self, html: str, team_abbr: str) -> list[dict]:
        """
        Parse transaction data from ESPN team transactions page HTML.

        Args:
            html: Page HTML content
            team_abbr: Team abbreviation (for context)

        Returns:
            List of transaction dictionaries
        """
        soup = BeautifulSoup(html, "html.parser")
        transactions = []

        # ESPN transactions are rendered as continuous text with month/date separators
        # No semantic HTML structure; extract all text and parse by date patterns
        page_text = soup.get_text()
        return self._extract_transactions_from_text(page_text, team_abbr)

    def _parse_transaction_element(self, element, team_abbr: str) -> Optional[dict]:
        """
        Parse a single transaction element.

        Args:
            element: BeautifulSoup element
            team_abbr: Team abbreviation

        Returns:
            Transaction dictionary or None if unable to parse
        """
        # Extract text from element
        text = element.get_text(strip=True)

        if not text:
            return None

        # Common transaction patterns:
        # "PlayerName - Transaction Type - Date"
        # "Date | PlayerName | Transaction Type"
        # etc.

        # Try to identify transaction type
        trans_type = self._identify_transaction_type(text)
        if not trans_type:
            return None

        # Extract player name (usually first capitalized word)
        player_name = self._extract_player_name(text)

        # Extract date if present
        trans_date = self._extract_date(text)

        return {
            "team_abbr": team_abbr,
            "player_name": player_name,
            "transaction_type": trans_type,
            "date": trans_date,
            "raw_text": text,
        }

    def _extract_transactions_from_text(self, text: str, team_abbr: str) -> list[dict]:
        """
        Extract transactions from page text as fallback.

        Args:
            text: Full page text
            team_abbr: Team abbreviation

        Returns:
            List of transactions
        """
        import re

        transactions = []

        # Clean HTML artifacts from text (e.g., "DATETRANSACTIONNovember")
        text = re.sub(r"DATETRANSACTION", "", text)

        # Pattern for dates: "Month Day, Year" or "Month Day Year"
        # Matches: "November 20, 2025", "Jan 1, 2025", "December 25 2025"
        date_pattern = (
            r"((?:January|February|March|April|May|June|July|August|September|"
            r"October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|"
            r"Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})"
        )

        # Find all dates in the text with their positions
        dates_with_pos = [
            (m.group(1), m.start(), m.end()) for m in re.finditer(date_pattern, text)
        ]

        if not dates_with_pos:
            # Fallback: process line by line
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue

                trans_type = self._identify_transaction_type(line)
                if not trans_type:
                    continue

                player_name = self._extract_player_name(line)
                if not player_name:
                    continue

                trans_date = self._extract_date(line)

                transactions.append(
                    {
                        "team_abbr": team_abbr,
                        "player_name": player_name,
                        "transaction_type": trans_type,
                        "date": trans_date,
                        "raw_text": line,
                    }
                )
            return transactions

        # Process transactions between dates
        for i, (date_str, start, end) in enumerate(dates_with_pos):
            # Get content from after this date until the next date
            content_start = end
            content_end = (
                dates_with_pos[i + 1][1] if i + 1 < len(dates_with_pos) else len(text)
            )

            content = text[content_start:content_end].strip()

            if not content:
                continue

            # Split content by periods to get individual transactions
            # Each transaction typically ends with a period
            trans_items = [
                item.strip()
                for item in re.split(r"(?<=[.:])\s+(?=[A-Z])", content)
                if item.strip()
            ]

            for trans_item in trans_items:
                if len(trans_item) < 5:
                    continue

                trans_type = self._identify_transaction_type(trans_item)
                if not trans_type:
                    continue

                player_name = self._extract_player_name(trans_item)
                if not player_name:
                    continue

                transactions.append(
                    {
                        "team_abbr": team_abbr,
                        "player_name": player_name,
                        "transaction_type": trans_type,
                        "date": date_str,
                        "raw_text": trans_item,
                    }
                )

        return transactions

    @staticmethod
    def _identify_transaction_type(text: str) -> Optional[str]:
        """Identify transaction type from text."""
        text_lower = text.lower()

        # Order matters - check more specific patterns first
        patterns = [
            ("injured reserve", "Injured Reserve"),
            ("claimed off waivers", "Claimed off Waivers"),
            ("signed to practice squad", "Signed to Practice Squad"),
            ("activated from", "Activated"),
            ("activated off", "Activated"),
            ("waived", "Waived"),
            ("released", "Released"),
            ("traded", "Traded"),
            ("re-signed", "Re-signed"),
            ("signed", "Signed"),
        ]

        for pattern, label in patterns:
            if pattern in text_lower:
                return label

        return None

    @staticmethod
    def _extract_player_name(text: str) -> Optional[str]:
        """Extract player name from transaction text."""
        # Player names are usually capitalized words, often with position prefix
        # Examples: "WR Mecole Hardman", "DT Phidarian Mathis", "CB Maxwell Hairston"
        words = text.split()

        # Skip common keywords, positions, and action verbs
        skip_words = {
            "signed",
            "traded",
            "released",
            "waived",
            "claimed",
            "acquired",
            "placed",
            "designated",
            "activated",
            "promoted",
            "reverted",
            "elevated",
            "hired",
            "announced",
            "retired",
            "off",
            "to",
            "from",
            "as",
            "with",
            "on",
            "nfl",
            "team",
            "pup",
            "nfi",
            "reserve",
            "injured",
            "return",
            "-",
            "/",
            "|",
            "and",
            "the",
            "a",
            "an",
            "in",
            "of",
            "for",
            "by",
            # Position abbreviations
            "qb",
            "rb",
            "wr",
            "te",
            "ol",
            "dl",
            "lb",
            "cb",
            "s",
            "p",
            "k",
            "ole",
            "olg",
            "c",
            "ot",
            "og",
            "de",
            "dt",
            "ilb",
            "olb",
            "fs",
            "ss",
            "db",
            "dil",
            "iolb",
            "fb",
            "ls",
            "h",
            "ps",
            "swr",
            "no",
            "wr",
        }

        for i, word in enumerate(words):
            clean_word = word.strip("-|/.").lower()  # Also strip periods/dots
            if clean_word not in skip_words and len(word) > 1:
                # Likely start of name - try to get first and last name
                name_parts = []
                for j in range(i, min(i + 3, len(words))):
                    w = words[j].strip("-|/.")  # Also strip trailing periods
                    if not w:
                        continue
                    w_lower = w.lower()
                    if w_lower not in skip_words and w[0].isupper() and len(w) > 1:
                        name_parts.append(w)
                    elif w_lower in skip_words:
                        break

                if name_parts:
                    return " ".join(name_parts)

        return None

    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        """Extract date from transaction text."""
        # Look for common date patterns
        import re

        # Pattern: MM/DD/YYYY or M/D/YYYY
        date_pattern = r"\d{1,2}/\d{1,2}/\d{4}"
        matches = re.findall(date_pattern, text)

        if matches:
            return matches[0]

        # Pattern: Month DD, YYYY
        month_pattern = (
            r"(January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{1,2},?\s+\d{4}"
        )
        matches = re.findall(month_pattern, text, re.IGNORECASE)

        if matches:
            return matches[0]

        return None

    async def get_all_nfl_transactions(self) -> dict:
        """
        Get transactions for all 32 NFL teams.

        Returns:
            Dictionary with all teams' transactions
        """
        all_transactions = {}

        for team_abbr in sorted(NFL_TEAMS.keys()):
            try:
                result = await self.get_team_transactions(team_abbr)
                all_transactions[team_abbr] = result
            except Exception as e:
                logger.error(f"Error fetching transactions for {team_abbr}: {e}")
                all_transactions[team_abbr] = {
                    "error": str(e),
                    "transactions": [],
                }

        return all_transactions

    async def save_transactions_json(
        self,
        transactions_data: dict,
        output_dir: Path,
    ) -> Path:
        """
        Save raw transactions data to JSON file.

        Args:
            transactions_data: Transactions dictionary
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transactions_nfl_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(transactions_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved transactions: {filepath}")
        return filepath
