"""Debug script to see contents of each cell in the odds table."""

import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def debug_cells():
    """Debug cell contents."""
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

        # Find the table
        table = await page.query_selector("table:has(div.best-odds__game-info)")
        if not table:
            print("Table not found!")
            return

        # Get first game row (skip header)
        rows = await table.query_selector_all("tbody tr")
        print(f"\nFound {len(rows)} rows")

        # Analyze first game row
        for row_idx in [0, 1]:  # First two game rows
            row = rows[row_idx]
            cells = await row.query_selector_all("td")

            print(f"\n{'='*60}")
            print(f"ROW {row_idx + 1}: {len(cells)} cells")
            print(f"{'='*60}")

            for i, cell in enumerate(cells[:8]):  # First 8 cells
                cell_text = await cell.inner_text()
                cell_html = await cell.inner_html()

                # Check for specific classes
                has_game_info = await cell.query_selector("div.best-odds__game-info")
                has_open_container = await cell.query_selector("div.best-odds__open-container")
                has_book_cell = await cell.query_selector("div.book-cell__odds")

                text_preview = cell_text[:50].replace("\n", "|")

                print(f"\n  Cell {i}:")
                print(f"    Text: '{text_preview}'")
                print(f"    Has game-info: {bool(has_game_info)}")
                print(f"    Has open-container: {bool(has_open_container)}")
                print(f"    Has book-cell__odds: {bool(has_book_cell)}")

                # Check for numbers that could be totals
                lines = cell_text.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and "." in line:
                        try:
                            val = float(line.replace("O", "").replace("U", ""))
                            if 30 < val < 80:
                                print(f"    POTENTIAL TOTAL: {val}")
                        except ValueError:
                            pass

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_cells())
