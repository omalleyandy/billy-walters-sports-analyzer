"""
ESPN College Football Schedule Weather Link Scraper

Extracts AccuWeather location keys from ESPN's college football schedule.
ESPN embeds direct links to AccuWeather in the schedule HTML:
  http://www.accuweather.com/en/us/michigan-stadium-mi/48104/hourly-weather-forecast/53592_poi

The location key (53592_poi) can be used directly with AccuWeather API.
"""

import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ESPNWeatherLinkScraper:
    """Scrapes AccuWeather location keys from ESPN schedule pages."""

    ESPN_CFB_SCHEDULE_URL = "https://www.espn.com/college-football/schedule"
    ESPN_NFL_SCHEDULE_URL = "https://www.espn.com/nfl/schedule"

    @staticmethod
    async def fetch_schedule_html(sport: str = "cfb") -> Optional[str]:
        """
        Fetch the ESPN schedule page HTML.

        Args:
            sport: 'cfb' for college football or 'nfl' for NFL

        Returns:
            HTML content or None if fetch fails
        """
        url = (
            ESPNWeatherLinkScraper.ESPN_CFB_SCHEDULE_URL
            if sport == "cfb"
            else ESPNWeatherLinkScraper.ESPN_NFL_SCHEDULE_URL
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36"
                        )
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Failed to fetch ESPN schedule: {e}")
            return None

    @staticmethod
    def extract_accuweather_links(html: str) -> dict[str, str]:
        """
        Extract AccuWeather location keys from ESPN schedule HTML.

        Looks for links like:
        http://www.accuweather.com/en/us/michigan-stadium-mi/48104/
        hourly-weather-forecast/53592_poi?day=1&hbhhour=12

        Args:
            html: HTML content from ESPN schedule

        Returns:
            Dictionary mapping stadium names to location keys
            Example: {'Michigan Stadium, Ann Arbor, MI': '53592_poi'}
        """
        soup = BeautifulSoup(html, "html.parser")
        locations = {}

        # Find all AccuWeather links
        for link in soup.find_all("a", href=re.compile(r"accuweather\.com")):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Extract location key from URL
            # Pattern: /hourly-weather-forecast/53592_poi?...
            match = re.search(r"/hourly-weather-forecast/([a-z0-9_]+)", href)
            if match and text:
                location_key = match.group(1)
                locations[text] = location_key
                logger.debug(
                    f"Found stadium: {text} -> {location_key}"
                )

        return locations

    @staticmethod
    async def get_location_keys(
        sport: str = "cfb",
    ) -> dict[str, str]:
        """
        Get AccuWeather location keys for all stadiums in ESPN schedule.

        Args:
            sport: 'cfb' for college football or 'nfl' for NFL

        Returns:
            Dictionary mapping stadium names to AccuWeather location keys
        """
        html = await ESPNWeatherLinkScraper.fetch_schedule_html(
            sport
        )
        if not html:
            logger.warning(
                f"Could not fetch ESPN {sport} schedule"
            )
            return {}

        return ESPNWeatherLinkScraper.extract_accuweather_links(html)


if __name__ == "__main__":
    # Test the scraper
    import asyncio

    async def test():
        """Test ESPN weather link scraper."""
        locations = await ESPNWeatherLinkScraper.get_location_keys(
            "cfb"
        )
        print(f"\nFound {len(locations)} stadiums:")
        for stadium, key in sorted(locations.items())[:10]:
            print(f"  {stadium}: {key}")

    asyncio.run(test())
