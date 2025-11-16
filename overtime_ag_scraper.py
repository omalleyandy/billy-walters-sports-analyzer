#!/usr/bin/env python3
"""
Overtime.ag Scraper - Get betting lines for NFL and NCAAF
Uses Playwright to bypass CloudFlare and handle dynamic JavaScript content

SETUP INSTRUCTIONS:
1. Install Playwright browsers: `uv run playwright install chromium`
2. Set environment variables in .env:
   - OV_CUSTOMER_ID=your_customer_id
   - OV_CUSTOMER_PASSWORD=your_password
3. Run: `python overtime_ag_scraper.py`
"""

import asyncio
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class BettingLine:
    """Represents a betting line from overtime.ag"""

    game_id: str
    sport: str  # 'nfl' or 'ncaaf'
    away_team: str
    home_team: str
    game_time: str

    # Spread
    spread: Optional[float] = None
    spread_away_price: Optional[int] = None  # e.g., -110
    spread_home_price: Optional[int] = None

    # Total
    total: Optional[float] = None
    over_price: Optional[int] = None
    under_price: Optional[int] = None

    # Moneyline
    away_ml: Optional[int] = None
    home_ml: Optional[int] = None

    # Metadata
    timestamp: str = None
    source: str = "overtime.ag"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class OvertimeAgScraper:
    """
    Scraper for overtime.ag betting lines

    Uses Playwright with stealth settings to bypass CloudFlare protection
    and handle dynamic JavaScript content rendering.
    """

    BASE_URL = "https://overtime.ag/sports"

    def __init__(self, headless: bool = True, timeout: int = 60000):
        """
        Initialize scraper

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize(self):
        """Initialize Playwright browser with stealth settings"""
        print("🚀 Initializing browser...")
        playwright = await async_playwright().start()

        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )

        # Create context with realistic browser fingerprint
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Create page
        self.page = await self.context.new_page()

        # Add stealth scripts
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        print("✅ Browser initialized")

    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def navigate_to_sports(self) -> bool:
        """
        Navigate to overtime.ag/sports and wait for content to load

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n🌐 Navigating to {self.BASE_URL}...")

            # Navigate to sports page
            response = await self.page.goto(
                self.BASE_URL, wait_until="domcontentloaded", timeout=self.timeout
            )

            if response is None or response.status != 200:
                print(
                    f"❌ Failed to load page: {response.status if response else 'No response'}"
                )
                return False

            print("✅ Page loaded")

            # Wait for Angular to initialize
            await asyncio.sleep(5)

            # Take screenshot for debugging
            await self.page.screenshot(path="overtime_screenshot.png")
            print("📸 Screenshot saved to overtime_screenshot.png")

            return True

        except Exception as e:
            print(f"❌ Error navigating: {e}")
            return False

    async def save_debug_files(self, sport: str):
        """Save HTML and text for debugging"""
        try:
            content = await self.page.content()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save HTML
            html_file = f"overtime_debug_{sport}_{timestamp}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"💾 Debug HTML saved to: {html_file}")

            # Save text
            page_text = await self.page.inner_text("body")
            text_file = f"overtime_text_{sport}_{timestamp}.txt"
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(page_text)
            print(f"💾 Page text saved to: {text_file}")

        except Exception as e:
            print(f"⚠️  Could not save debug files: {e}")

    async def scrape_betting_lines(self, sport: str = "nfl") -> List[BettingLine]:
        """
        Scrape betting lines for specified sport

        Args:
            sport: 'nfl' or 'ncaaf'

        Returns:
            List of BettingLine objects
        """
        lines = []

        try:
            print(f"\n🔍 Scraping {sport.upper()} betting lines...")

            # Save debug files
            await self.save_debug_files(sport)

            # TODO: Implement actual parsing based on HTML structure
            # For now, this is a placeholder that saves debug files

            print(f"\n⚠️  NEXT STEPS:")
            print(f"1. Review the debug HTML file to understand page structure")
            print(f"2. Implement parsing logic based on actual HTML elements")
            print(f"3. Look for patterns like game containers, team names, odds")
            print(f"4. Update this scrape_betting_lines() method with parsing code")

            return lines

        except Exception as e:
            print(f"❌ Error scraping betting lines: {e}")
            return lines

    async def scrape_nfl(self) -> List[BettingLine]:
        """Scrape NFL betting lines"""
        print("\n" + "=" * 60)
        print("🏈 SCRAPING NFL LINES FROM OVERTIME.AG")
        print("=" * 60)

        if not await self.navigate_to_sports():
            return []

        lines = await self.scrape_betting_lines("nfl")

        print(f"\n✅ Scraping complete: {len(lines)} NFL betting lines found")
        return lines

    async def scrape_ncaaf(self) -> List[BettingLine]:
        """Scrape NCAA Football betting lines"""
        print("\n" + "=" * 60)
        print("🏈 SCRAPING NCAAF LINES FROM OVERTIME.AG")
        print("=" * 60)

        if not await self.navigate_to_sports():
            return []

        lines = await self.scrape_betting_lines("ncaaf")

        print(f"\n✅ Scraping complete: {len(lines)} NCAAF betting lines found")
        return lines

    async def scrape_all_football(self) -> Dict[str, List[BettingLine]]:
        """
        Scrape both NFL and NCAAF betting lines

        Returns:
            Dictionary with 'nfl' and 'ncaaf' keys containing lists of BettingLine objects
        """
        print("\n" + "=" * 60)
        print("🏈 SCRAPING ALL FOOTBALL LINES FROM OVERTIME.AG")
        print("=" * 60)

        results = {"nfl": [], "ncaaf": []}

        # Scrape NFL
        results["nfl"] = await self.scrape_nfl()

        # Navigate back to main sports page
        await self.navigate_to_sports()

        # Scrape NCAAF
        results["ncaaf"] = await self.scrape_ncaaf()

        # Save results
        await self.save_results(results)

        return results

    async def save_results(self, results: Dict[str, List[BettingLine]]):
        """Save scraping results to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("data/odds")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / f"overtime_lines_{timestamp}.json"

            # Convert to serializable format
            serializable = {
                sport: [line.to_dict() for line in lines]
                for sport, lines in results.items()
            }

            with open(output_file, "w") as f:
                json.dump(serializable, f, indent=2, default=str)

            print(f"\n💾 Results saved to: {output_file}")

        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


async def main():
    """Test the scraper"""
    scraper = OvertimeAgScraper(
        headless=True
    )  # Set to False to see browser (Windows only)

    try:
        await scraper.initialize()

        # Test NFL scraping
        nfl_lines = await scraper.scrape_nfl()

        print("\n" + "=" * 60)
        print(f"📊 RESULTS: {len(nfl_lines)} NFL betting lines")
        print("=" * 60)

        if nfl_lines:
            for line in nfl_lines[:5]:  # Show first 5
                print(f"\n{line.away_team} @ {line.home_team}")
                if line.spread:
                    print(
                        f"  Spread: {line.spread:+.1f} ({line.spread_away_price}/{line.spread_home_price})"
                    )
                if line.total:
                    print(
                        f"  Total: {line.total:.1f} (O: {line.over_price} / U: {line.under_price})"
                    )
                if line.away_ml:
                    print(f"  ML: {line.away_ml} / {line.home_ml}")
        else:
            print(
                "\n⚠️  No betting lines found yet - parsing logic needs to be implemented"
            )
            print(
                "📁 Check the debug files (HTML and text) to understand page structure"
            )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await scraper.close()
        print("\n✅ Browser closed")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("OVERTIME.AG SCRAPER - SETUP PHASE")
    print("=" * 60)
    print("\nThis scraper will:")
    print("  1. Navigate to overtime.ag/sports")
    print("  2. Save debug files (HTML, text, screenshot)")
    print("  3. Show you what needs to be parsed")
    print("\nNext steps after running:")
    print("  1. Review debug files to see HTML structure")
    print("  2. Implement parsing logic for betting lines")
    print("  3. Test with real data")
    print("\n" + "=" * 60 + "\n")

    asyncio.run(main())
