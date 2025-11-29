"""
ESPN College Football Schedule Weather Link Scraper

Extracts zipcode from AccuWeather links in ESPN's college football schedule.
ESPN embeds direct links to AccuWeather in the schedule HTML:
  https://www.accuweather.com/en/us/brooks-stadium/29526/hourly-weather-forecast/209212_poi

From the URL we extract the ZIPCODE (29526), which is used to look up the
correct AccuWeather location key. This is more reliable than using POI keys.
"""

import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ESPNWeatherLinkScraper:
    """Scrapes zipcode from AccuWeather links in ESPN schedule pages."""

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
    def extract_stadium_zipcodes(html: str) -> dict[str, str]:
        """
        Extract stadium zipcodes from AccuWeather links in ESPN schedule.

        Looks for links like:
        https://www.accuweather.com/en/us/brooks-stadium/29526/
        hourly-weather-forecast/209212_poi?day=1&lang=en-us&partner=espn_gc

        Extracts the ZIPCODE (29526) from the URL path, which is authoritative
        and can be used to look up the correct AccuWeather location key.

        Args:
            html: HTML content from ESPN schedule

        Returns:
            Dictionary mapping stadium names to zipcodes
            Example: {'Brooks Stadium, South Carolina': '29526'}
        """
        soup = BeautifulSoup(html, "html.parser")
        locations = {}

        # Find all AccuWeather links
        for link in soup.find_all("a", href=re.compile(r"accuweather\.com")):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Extract zipcode from URL
            # Pattern: /en/us/stadium-name/ZIPCODE/hourly-weather-forecast/
            match = re.search(r"/en/us/[^/]+/(\d{5})/hourly-weather-forecast", href)
            if match and text:
                zipcode = match.group(1)
                locations[text] = zipcode
                logger.debug(f"Found stadium: {text} -> Zipcode {zipcode}")

        return locations

    @staticmethod
    async def get_stadium_zipcodes(
        sport: str = "cfb",
    ) -> dict[str, str]:
        """
        Get stadium zipcodes from ESPN schedule.

        Args:
            sport: 'cfb' for college football or 'nfl' for NFL

        Returns:
            Dictionary mapping stadium names to zipcodes
            Example: {'Delaware Stadium, Newark, DE': '19711'}
        """
        html = await ESPNWeatherLinkScraper.fetch_schedule_html(sport)
        if not html:
            logger.warning(f"Could not fetch ESPN {sport} schedule")
            return {}

        return ESPNWeatherLinkScraper.extract_stadium_zipcodes(html)


if __name__ == "__main__":
    # Test the scraper
    import asyncio

    async def test():
        """Test ESPN weather link scraper."""
        zipcodes = await ESPNWeatherLinkScraper.get_stadium_zipcodes("cfb")
        print(f"\nFound {len(zipcodes)} stadiums:")
        for stadium, zipcode in sorted(zipcodes.items())[:10]:
            print(f"  {stadium}: {zipcode}")

    asyncio.run(test())
