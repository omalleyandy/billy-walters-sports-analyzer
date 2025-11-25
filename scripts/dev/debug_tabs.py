"""Debug script to analyze tab structure on Action Network odds page."""

import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def debug_tabs():
    """Analyze tab structure."""
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
        await asyncio.sleep(5)

        # Navigate to NFL odds
        print("Navigating to NFL odds...")
        await page.goto("https://www.actionnetwork.com/nfl/odds")
        await asyncio.sleep(3)

        print("\n" + "=" * 60)
        print("TAB ANALYSIS")
        print("=" * 60)

        # Look for tab-like elements
        tab_patterns = [
            "button:has-text('Spread')",
            "button:has-text('Total')",
            "button:has-text('Moneyline')",
            "a:has-text('Spread')",
            "a:has-text('Total')",
            "a:has-text('Moneyline')",
            "[role='tab']",
            "[class*='tab']",
            "[class*='toggle']",
            "div.best-odds__toggle",
            "button[class*='toggle']",
        ]

        for pattern in tab_patterns:
            try:
                elements = await page.query_selector_all(pattern)
                if elements:
                    print(f"\n'{pattern}': {len(elements)} elements")
                    for i, elem in enumerate(elements[:3]):
                        text = await elem.inner_text()
                        tag = await elem.evaluate("el => el.tagName")
                        classes = await elem.get_attribute("class") or ""
                        print(f"  [{i}] <{tag}> class='{classes[:50]}' text='{text[:30]}'")
            except Exception as e:
                print(f"'{pattern}': Error - {e}")

        # Look for specific "Total" or "O/U" text
        print("\n" + "=" * 60)
        print("SEARCHING FOR TOTAL/O-U ELEMENTS")
        print("=" * 60)

        total_searches = [
            "text='Total'",
            "text='TOTAL'",
            "text='O/U'",
            "text='Over/Under'",
            "*:has-text('Total'):not(script):not(style)",
        ]

        for search in total_searches[:3]:
            try:
                elements = await page.query_selector_all(search)
                if elements:
                    print(f"\n'{search}': {len(elements)} elements")
                    for i, elem in enumerate(elements[:5]):
                        text = await elem.inner_text()
                        tag = await elem.evaluate("el => el.tagName")
                        classes = await elem.get_attribute("class") or ""
                        text_preview = text[:40].replace("\n", "|")
                        print(f"  [{i}] <{tag}> class='{classes[:40]}' text='{text_preview}'")
            except Exception as e:
                print(f"'{search}': Error - {e}")

        # Look at the page structure near the table
        print("\n" + "=" * 60)
        print("CHECKING TABLE CONTAINER FOR TABS")
        print("=" * 60)

        table_container = await page.query_selector("div.best-odds__table-container")
        if table_container:
            # Look for siblings or parent elements that might be tabs
            parent = await table_container.query_selector("xpath=..")
            if parent:
                children = await parent.query_selector_all(":scope > *")
                print(f"\nTable container parent has {len(children)} children:")
                for i, child in enumerate(children[:5]):
                    tag = await child.evaluate("el => el.tagName")
                    classes = await child.get_attribute("class") or ""
                    text = await child.inner_text()
                    text_preview = text[:50].replace("\n", "|")
                    print(f"  [{i}] <{tag}> class='{classes[:50]}'")
                    print(f"       text: '{text_preview}'")

        # Check for toggle buttons specifically
        print("\n" + "=" * 60)
        print("LOOKING FOR TOGGLE/TAB BUTTONS")
        print("=" * 60)

        toggles = await page.query_selector_all("[class*='toggle'], [class*='tab'], [class*='pill']")
        print(f"Found {len(toggles)} toggle/tab/pill elements")
        for i, toggle in enumerate(toggles[:10]):
            text = await toggle.inner_text()
            classes = await toggle.get_attribute("class") or ""
            clickable = await toggle.evaluate("el => el.tagName === 'BUTTON' || el.tagName === 'A' || el.onclick !== null")
            text_preview = text[:30].replace("\n", "|")
            print(f"  [{i}] class='{classes[:40]}' text='{text_preview}' clickable={clickable}")

        await browser.close()
        print("\n" + "=" * 60)
        print("Analysis complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(debug_tabs())
