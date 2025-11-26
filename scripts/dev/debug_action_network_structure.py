"""
Debug script to understand Action Network page structure.
"""

import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def debug_page_structure():
    """Debug the page structure after login."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Login
        print("Logging in...")
        await page.goto("https://www.actionnetwork.com/login")
        await page.wait_for_selector("input[placeholder='Email']")
        await page.fill("input[placeholder='Email']", os.getenv("ACTION_USERNAME"))
        await page.fill("input[placeholder='Password']", os.getenv("ACTION_PASSWORD"))
        await page.click("button[type='submit']")
        await asyncio.sleep(5)  # Wait for redirect
        print(f"Login successful - current URL: {page.url}")

        # Navigate to NFL odds
        print("\nNavigating to NFL odds...")
        await page.goto("https://www.actionnetwork.com/nfl/odds")
        await asyncio.sleep(3)  # Wait for dynamic content

        # Check what selectors find elements
        print("\n=== DEBUG: Selector Analysis ===")

        selectors_to_test = [
            # Game containers
            "div.best-odds__game-info",
            "div[class*='best-odds__game']",
            "div[class*='game-info']",
            # Team names
            "div.game-info__teams",
            ".game-info__teams",
            # Tables
            "table",
            "table[class*='css-']",
            # Rows
            "tr",
            "tbody tr",
        ]

        for selector in selectors_to_test:
            try:
                elements = await page.query_selector_all(selector)
                print(f"  '{selector}': {len(elements)} elements")
                if elements and len(elements) <= 5:
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.inner_text()
                            text_preview = text[:80].replace("\n", " ").strip()
                            print(f"    [{i}]: {text_preview}...")
                        except Exception:
                            pass
            except Exception as e:
                print(f"  '{selector}': ERROR - {e}")

        # Look for parent containers
        print("\n=== DEBUG: Game Wrapper Search ===")
        wrappers = await page.query_selector_all("div[class*='game']")
        print(f"  Found {len(wrappers)} div[class*='game'] elements")

        # Check the specific structure
        print("\n=== DEBUG: Checking Best Odds Structure ===")
        game_info = await page.query_selector_all("div.best-odds__game-info")
        print(f"  Found {len(game_info)} best-odds__game-info divs")

        for i, info in enumerate(game_info[:3]):
            print(f"\n  Game {i + 1}:")
            text = await info.inner_text()
            print(f"    Text: {text}")

            # Check parent
            parent = await info.query_selector("xpath=..")
            if parent:
                parent_class = await parent.get_attribute("class")
                print(f"    Parent class: {parent_class}")

                # Check siblings (might have odds table)
                sibling = await parent.query_selector("table")
                if sibling:
                    print(f"    Has sibling table: YES")
                else:
                    print(f"    Has sibling table: NO")

        # Save a snapshot of the HTML
        print("\n=== Saving HTML snapshot ===")
        html = await page.content()

        output_dir = "output/debug"
        os.makedirs(output_dir, exist_ok=True)
        with open(
            f"{output_dir}/action_network_nfl_odds.html", "w", encoding="utf-8"
        ) as f:
            f.write(html)
        print(f"  Saved to {output_dir}/action_network_nfl_odds.html")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_page_structure())
