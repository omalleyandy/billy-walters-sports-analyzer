#!/usr/bin/env python
"""
Capture Action Network odds page selectors.

Logs in and pauses so you can navigate to the NFL odds page.
Then captures the page structure for selector debugging.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def main():
    """Login and capture odds page selectors."""
    output_dir = Path("output/debug")
    output_dir.mkdir(parents=True, exist_ok=True)

    username = os.getenv("ACTION_USERNAME", "")
    password = os.getenv("ACTION_PASSWORD", "")

    print("\n" + "=" * 70)
    print("ACTION NETWORK ODDS PAGE CAPTURE")
    print("=" * 70)
    print("\nThis tool will:")
    print("  1. Log in automatically")
    print("  2. PAUSE so you can navigate to NFL odds page")
    print("  3. Capture the page structure for debugging")
    print("=" * 70 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print("[*] Navigating to login page...")
        await page.goto(
            "https://www.actionnetwork.com/login",
            wait_until="domcontentloaded",
            timeout=60000
        )
        await page.wait_for_load_state("load")

        print("[*] Logging in...")
        try:
            await page.get_by_placeholder("Email").click(timeout=10000)
            await page.get_by_role("textbox", name="Email").fill(username)
            await page.get_by_role("textbox", name="Password").click(timeout=5000)
            await page.get_by_role("textbox", name="Password").fill(password)
            await page.get_by_role("button", name="Sign In", exact=True).click(timeout=5000)
            await page.wait_for_load_state("load")
            await page.wait_for_timeout(2000)
            print("[OK] Login successful!")
        except Exception as e:
            print(f"[!] Login issue: {e}")

        print("\n" + "=" * 70)
        print("LOGGED IN - NOW NAVIGATE TO NFL ODDS")
        print("=" * 70)
        print("\nSteps:")
        print("  1. Click on 'NFL' or navigate to the NFL odds page")
        print("  2. Wait for the odds/games table to load")
        print("  3. When you see the games listed, click 'Resume' in Inspector")
        print("=" * 70 + "\n")

        # Pause for navigation
        await page.pause()

        print("\n[*] Capturing page structure...\n")

        current_url = page.url
        print(f"Current URL: {current_url}")

        # Capture all tables
        tables = await page.query_selector_all("table")
        print(f"\nFound {len(tables)} tables:")
        for i, table in enumerate(tables):
            classes = await table.get_attribute("class") or ""
            id_attr = await table.get_attribute("id") or ""
            print(f"  {i+1}. class='{classes}' id='{id_attr}'")

        # Capture divs with game-related classes
        print("\n[*] Looking for game-related containers...")
        game_patterns = ["game", "matchup", "odds", "event", "contest", "bet"]
        for pattern in game_patterns:
            elements = await page.query_selector_all(f"div[class*='{pattern}']")
            if elements:
                print(f"\n  div[class*='{pattern}']: {len(elements)} found")
                for i, el in enumerate(elements[:3]):  # Show first 3
                    classes = await el.get_attribute("class") or ""
                    text = (await el.inner_text())[:50].replace("\n", " ")
                    print(f"    - '{classes[:60]}': '{text}...'")

        # Look for links with NFL/sports
        print("\n[*] Looking for navigation links...")
        nav_links = await page.query_selector_all("a[href*='nfl'], a[href*='odds']")
        print(f"Found {len(nav_links)} NFL/odds links:")
        for i, link in enumerate(nav_links[:10]):
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()[:30]
            print(f"  {i+1}. '{text}' -> {href}")

        # Look for article elements (common for game cards)
        articles = await page.query_selector_all("article")
        print(f"\nFound {len(articles)} article elements")

        # Look for specific odds-related elements
        odds_selectors = [
            "table.odds-table",
            "div[class*='odds']",
            "div[class*='spread']",
            "div[class*='moneyline']",
            "div[class*='game-card']",
            "[data-testid*='game']",
            "[data-testid*='odds']",
        ]

        print("\n[*] Testing known odds selectors...")
        for selector in odds_selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"  [OK] {selector}: {count} found")
            except Exception:
                pass

        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_file = output_dir / f"action_network_odds_{timestamp}.png"
        await page.screenshot(path=str(screenshot_file), full_page=True)
        print(f"\n[OK] Screenshot saved: {screenshot_file}")

        # Save page HTML for offline analysis
        html_file = output_dir / f"action_network_odds_{timestamp}.html"
        html_content = await page.content()
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[OK] HTML saved: {html_file}")

        # Give time to review
        print("\n[*] Browser will close in 10 seconds...")
        await page.wait_for_timeout(10000)

        await browser.close()

        print("\n" + "=" * 70)
        print("CAPTURE COMPLETE")
        print("=" * 70)
        print(f"\nReview the files in: {output_dir}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
