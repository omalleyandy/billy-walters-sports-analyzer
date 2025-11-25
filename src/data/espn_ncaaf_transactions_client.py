"""
ESPN NCAAF Transactions Client

Fetches NCAAF (college football) team roster transactions, transfers, and
coaching changes from ESPN. Scrapes the team transactions page and extracts
structured transaction data.

Usage:
    client = ESPNNCAAFTransactionsClient()

    # Get transactions for a team
    transactions = await client.get_team_transactions("alabama")

    # Get all FBS teams' transactions
    all_transactions = await client.get_all_ncaaf_transactions()

Transaction Types:
    - Transfer In: Player transferred to program
    - Transfer Out: Player transferred from program
    - Signed: Player signed
    - Coaching: Coaching staff changes
    - Recruiting: Recruiting-related updates
    - Eligibility: Eligibility status changes
    - Injury: Injury-related news

ESPN URL Pattern:
    - Team: https://www.espn.com/college-football/team/transactions/_/id/{team_id}/{team_name}
    - Example: https://www.espn.com/college-football/team/transactions/_/id/25/alabama-crimson-tide
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


# Major NCAAF FBS teams mapping (subset - can be expanded)
# Format: abbreviation -> {"id": ESPN_TEAM_ID, "name": url_slug, "full_name": display_name}
NCAAF_TEAMS = {
    "alabama": {
        "id": "25",
        "name": "alabama-crimson-tide",
        "full_name": "Alabama Crimson Tide",
    },
    "lsu": {"id": "84", "name": "lsu-tigers", "full_name": "LSU Tigers"},
    "ohiostate": {
        "id": "25",
        "name": "ohio-state-buckeyes",
        "full_name": "Ohio State Buckeyes",
    },
    "clemson": {"id": "25", "name": "clemson-tigers", "full_name": "Clemson Tigers"},
    "georgia": {
        "id": "61",
        "name": "georgia-bulldogs",
        "full_name": "Georgia Bulldogs",
    },
    "texas": {"id": "251", "name": "texas-longhorns", "full_name": "Texas Longhorns"},
    "oklahoma": {
        "id": "84",
        "name": "oklahoma-sooners",
        "full_name": "Oklahoma Sooners",
    },
    "usc": {"id": "30", "name": "usc-trojans", "full_name": "USC Trojans"},
    "florida": {
        "id": "57",
        "name": "florida-gators",
        "full_name": "Florida Gators",
    },
    "texas-am": {
        "id": "245",
        "name": "texas-am-aggies",
        "full_name": "Texas A&M Aggies",
    },
    "nebraska": {
        "id": "25",
        "name": "nebraska-cornhuskers",
        "full_name": "Nebraska Cornhuskers",
    },
    "michigan": {
        "id": "130",
        "name": "michigan-wolverines",
        "full_name": "Michigan Wolverines",
    },
    "penn-state": {
        "id": "25",
        "name": "penn-state-nittany-lions",
        "full_name": "Penn State Nittany Lions",
    },
}


class ESPNNCAAFTransactionsClient:
    """
    ESPN NCAAF Transactions API client.

    Fetches college football team roster transactions via web scraping since
    no dedicated API endpoint exists. Extracts player names, transaction types,
    dates, and transfer information.
    """

    BASE_URL = "https://www.espn.com/college-football/team/transactions"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize ESPN NCAAF Transactions client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
            rate_limit_delay: Delay between requests (seconds) - 1s default for
                            politeness
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
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    ),
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
        Get transactions for a specific NCAAF team.

        Args:
            team_abbr: Team abbreviation (e.g., 'alabama')

        Returns:
            Dictionary with team info and transactions list
        """
        team_abbr_lower = team_abbr.lower()

        if team_abbr_lower not in NCAAF_TEAMS:
            raise ValueError(f"Unknown team abbreviation: {team_abbr}")

        team_info = NCAAF_TEAMS[team_abbr_lower]
        url = f"{self.BASE_URL}/_/id/{team_info['id']}/{team_info['name']}"

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

        # NCAAF transactions are rendered as continuous text with date separators
        page_text = soup.get_text()
        return self._extract_transactions_from_text(page_text, team_abbr)

    def _extract_transactions_from_text(self, text: str, team_abbr: str) -> list[dict]:
        """
        Extract transactions from page text.

        Args:
            text: Full page text
            team_abbr: Team abbreviation

        Returns:
            List of transactions
        """
        import re

        transactions = []

        # Clean HTML artifacts
        text = re.sub(r"DATETRANSACTION", "", text)

        # Pattern for dates: "Month Day, Year"
        date_pattern = (
            r"((?:January|February|March|April|May|June|July|August|September|"
            r"October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|"
            r"Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})"
        )

        # Find all dates with positions
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
            content_start = end
            content_end = (
                dates_with_pos[i + 1][1] if i + 1 < len(dates_with_pos) else len(text)
            )

            content = text[content_start:content_end].strip()

            if not content:
                continue

            # Split by punctuation
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

        # College-specific transaction types
        patterns = [
            ("transfer in", "Transfer In"),
            ("transfer out", "Transfer Out"),
            ("transfer portal", "Transfer Portal"),
            ("coaching", "Coaching"),
            ("recruiting", "Recruiting"),
            ("eligibility", "Eligibility"),
            ("injury", "Injury"),
            ("signed", "Signed"),
            ("committed", "Committed"),
            ("decommitted", "Decommitted"),
        ]

        for pattern, label in patterns:
            if pattern in text_lower:
                return label

        return None

    @staticmethod
    def _extract_player_name(text: str) -> Optional[str]:
        """Extract player name from transaction text."""
        words = text.split()

        skip_words = {
            "transfer",
            "portal",
            "coaching",
            "recruiting",
            "signed",
            "committed",
            "decommitted",
            "injury",
            "eligible",
            "ineligible",
            "coaching",
            "staff",
            "hire",
            "fire",
            "promote",
            "demote",
            "off",
            "to",
            "from",
            "as",
            "with",
            "on",
            "ncaa",
            "team",
            "reserve",
            "injury",
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
        }

        for i, word in enumerate(words):
            clean_word = word.strip("-|/.").lower()
            if clean_word not in skip_words and len(word) > 1:
                name_parts = []
                for j in range(i, min(i + 3, len(words))):
                    w = words[j].strip("-|/.")
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
        import re

        # Pattern: MM/DD/YYYY
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

    async def get_all_ncaaf_transactions(self) -> dict:
        """
        Get transactions for all major FBS teams.

        Returns:
            Dictionary with all teams' transactions
        """
        all_transactions = {}

        for team_abbr in sorted(NCAAF_TEAMS.keys()):
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
        filename = f"transactions_ncaaf_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(transactions_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved transactions: {filepath}")
        return filepath
