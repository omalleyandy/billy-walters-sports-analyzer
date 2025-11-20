#!/usr/bin/env python3
"""
Simple Overtime.ag Live Betting Scraper

Directly scrapes the live betting page (overtime.ag/sports#/integrations/liveBetting)
without using SignalR. Just periodically refreshes and captures odds.

This is simpler and more reliable than WebSocket monitoring.

Usage:
    # Monitor for 30 minutes, check every 30 seconds
    uv run python scripts/scrapers/scrape_overtime_live_simple.py --duration 1800 --interval 30

    # Quick test (5 minutes, check every 15 seconds)
    uv run python scripts/scrapers/scrape_overtime_live_simple.py --duration 300 --interval 15

Author: Billy Walters Sports Analyzer
Created: 2025-11-14
"""

import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import Page, async_playwright


class SimpleLiveBettingScraper:
    """Simple live betting scraper - no SignalR, just periodic page scraping"""

    def __init__(
        self,
        duration: int = 1800,
        interval: int = 30,
        headless: bool = False,
        output_dir: str = "output/overtime/live",
    ):
        """
        Initialize scraper.

        Args:
            duration: How long to monitor (seconds)
            interval: How often to check for updates (seconds)
            headless: Run browser in headless mode
            output_dir: Output directory
        """
        self.duration = duration
        self.interval = interval
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.customer_id = os.getenv("OV_CUSTOMER_ID")
        self.password = os.getenv("OV_PASSWORD")

        # Data storage
        self.snapshots: List[Dict[str, Any]] = []
        self.line_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    async def run(self):
        """Run the scraper"""
        print("=" * 70)
        print("Simple Live Betting Scraper")
        print("=" * 70)
        print()
        print(f"Duration: {self.duration}s ({self.duration / 60:.1f} minutes)")
        print(f"Check interval: {self.interval}s")
        print(f"Expected checks: {self.duration // self.interval}")
        print()

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )

            try:
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                )
                page = await context.new_page()

                # Login
                print("1. Logging in...")
                await self._login(page)

                # Navigate to Live Betting
                print("2. Navigating to Live Betting page...")
                await page.goto(
                    "https://overtime.ag/sports#/integrations/liveBetting",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                await page.wait_for_timeout(5000)  # Let page fully load

                print("3. Starting monitoring...")
                print()

                start_time = asyncio.get_event_loop().time()
                check_num = 1

                while (asyncio.get_event_loop().time() - start_time) < self.duration:
                    print(f"[Check #{check_num}] {datetime.now().strftime('%H:%M:%S')}")

                    # Extract games
                    games = await self._extract_live_games(page)
                    print(f"  Found {len(games)} live games")

                    if games:
                        for game in games:
                            print(f"    - {game.get('matchup', 'Unknown')}")

                    # Store snapshot
                    snapshot = {
                        "timestamp": datetime.now().isoformat(),
                        "check_number": check_num,
                        "games": games,
                    }
                    self.snapshots.append(snapshot)

                    # Track line movements
                    for game in games:
                        game_id = game.get("game_id", f"game_{check_num}")
                        self.line_history[game_id].append(game)

                    # Wait for next check
                    if (asyncio.get_event_loop().time() - start_time) < self.duration:
                        print(f"  Next check in {self.interval}s...")
                        print()
                        await asyncio.sleep(self.interval)

                    check_num += 1

                print()
                print("4. Monitoring complete!")

            finally:
                await browser.close()

        # Save results
        self._save_results()

    async def _login(self, page: Page):
        """Login to Overtime.ag"""
        await page.goto("https://overtime.ag/sports#/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # Click login button
        await page.evaluate("""
            () => {
                const loginBtn = document.querySelector('a.btn-signup');
                if (loginBtn) loginBtn.click();
            }
        """)
        await page.wait_for_timeout(2000)

        # Fill credentials
        customer_input = await page.query_selector('input[placeholder*="Customer"]')
        if customer_input:
            await customer_input.fill(self.customer_id)

        password_input = await page.query_selector('input[type="password"]')
        if password_input:
            await password_input.fill(self.password)

        # Submit
        login_btn = await page.query_selector('button:has-text("LOGIN")')
        if login_btn:
            await login_btn.click()
            await page.wait_for_timeout(5000)
            print("   Login successful")

    async def _extract_live_games(self, page: Page) -> List[Dict[str, Any]]:
        """Extract live games from the page"""
        try:
            games_data = await page.evaluate("""
                () => {
                    const games = [];

                    // Find all game containers
                    const gameElements = document.querySelectorAll('[data-game-id], .game-row, .live-game');

                    // If no specific containers, try to find team names and odds
                    const teamElements = document.querySelectorAll('h4, .team-name');
                    const oddsButtons = document.querySelectorAll('button[ng-click*="Wager"], .odds-button, button:contains("-"), button:contains("+")');

                    // Simple extraction: look for any visible game data
                    const allText = document.body.innerText;

                    return {
                        game_elements: gameElements.length,
                        team_elements: teamElements.length,
                        odds_buttons: oddsButtons.length,
                        page_text_sample: allText.substring(0, 1000),
                    };
                }
            """)

            # For now, return diagnostic info
            return [{
                "game_id": "diagnostic",
                "matchup": "Diagnostic Data",
                "data": games_data,
                "timestamp": datetime.now().isoformat(),
            }]

        except Exception as e:
            print(f"  [ERROR] Extraction failed: {e}")
            return []

    def _save_results(self):
        """Save all results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save full snapshots
        snapshots_file = self.output_dir / f"live_snapshots_{timestamp}.json"
        with open(snapshots_file, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "duration_seconds": self.duration,
                    "interval_seconds": self.interval,
                    "total_checks": len(self.snapshots),
                },
                "snapshots": self.snapshots,
            }, f, indent=2, default=str)

        print(f"\n[OK] Saved snapshots: {snapshots_file}")
        print(f"Total checks: {len(self.snapshots)}")


def parse_args():
    parser = argparse.ArgumentParser(description="Simple Live Betting Scraper")
    parser.add_argument(
        "--duration",
        type=int,
        default=1800,
        help="How long to monitor (seconds, default: 1800 = 30 min)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="How often to check (seconds, default: 30)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    scraper = SimpleLiveBettingScraper(
        duration=args.duration,
        interval=args.interval,
        headless=args.headless,
    )

    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
