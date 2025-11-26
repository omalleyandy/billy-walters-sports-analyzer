#!/usr/bin/env python
"""
Debug Action Network page structure.

Logs in, navigates to NFL odds, takes screenshots and saves HTML.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def main():
    """Login, navigate to NFL odds, capture page structure."""
    output_dir = Path("output/debug")
    output_dir.mkdir(parents=True, exist_ok=True)

    username = os.getenv("ACTION_USERNAME", "")
    password = os.getenv("ACTION_PASSWORD", "")

    print("\n[*] Starting debug capture...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = await context.new_page()

        # Login
        print("[*] Logging in...")
        await page.goto(
            "https://www.actionnetwork.com/login",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        await page.wait_for_load_state("load")

        await page.get_by_placeholder("Email").click(timeout=10000)
        await page.get_by_role("textbox", name="Email").fill(username)
        await page.fill("input[placeholder='Password']", password, timeout=5000)
        await page.get_by_role("button", name="Sign In", exact=True).click(timeout=5000)
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(5000)
        print(f"[OK] Logged in, URL: {page.url}")

        # Navigate to NFL odds
        print("[*] Navigating to NFL odds...")
        await page.goto(
            "https://www.actionnetwork.com/nfl/odds",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(5000)  # Wait for dynamic content
        print(f"[OK] On NFL odds page, URL: {page.url}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Take screenshot
        screenshot_file = output_dir / f"nfl_odds_{timestamp}.png"
        await page.screenshot(path=str(screenshot_file), full_page=True)
        print(f"[OK] Screenshot: {screenshot_file}")

        # Save HTML
        html_file = output_dir / f"nfl_odds_{timestamp}.html"
        html_content = await page.content()
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[OK] HTML: {html_file}")

        # Analyze page structure
        print("\n[*] Analyzing page structure...\n")

        # Find all tables
        tables = await page.query_selector_all("table")
        print(f"Tables found: {len(tables)}")
        for i, table in enumerate(tables[:5]):
            classes = await table.get_attribute("class") or ""
            print(f"  Table {i + 1}: class='{classes}'")

        # Look for common game container patterns
        patterns = [
            "article",
            "div[class*='game']",
            "div[class*='matchup']",
            "div[class*='event']",
            "div[class*='odds']",
            "div[class*='card']",
            "section[class*='game']",
            "[data-testid]",
        ]

        for pattern in patterns:
            try:
                elements = await page.query_selector_all(pattern)
                if elements:
                    print(f"\n{pattern}: {len(elements)} found")
                    # Show first 2
                    for i, el in enumerate(elements[:2]):
                        classes = await el.get_attribute("class") or ""
                        text = (await el.inner_text())[:80].replace("\n", " ")
                        print(f"  {i + 1}. class='{classes[:60]}' text='{text}...'")
            except Exception as e:
                print(f"  Error checking {pattern}: {e}")

        # Check for spread/moneyline text
        print("\n[*] Looking for betting lines...")
        page_text = await page.inner_text("body")
        lines = page_text.split("\n")
        betting_patterns = []
        for line in lines:
            line = line.strip()
            # Look for spreads like "-3.5" or "+7"
            if any(
                c in line
                for c in ["-1", "+1", "-2", "+2", "-3", "+3", "-4", "-5", "-6", "-7"]
            ):
                if len(line) < 50:  # Short lines likely to be odds
                    betting_patterns.append(line)
        print(f"Potential betting lines found: {len(betting_patterns)}")
        for line in betting_patterns[:10]:
            print(f"  '{line}'")

        print("\n[*] Keeping browser open for 30 seconds for manual inspection...")
        await page.wait_for_timeout(30000)

        await browser.close()

        print("\n[OK] Debug capture complete!")
        print(f"    Check: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
