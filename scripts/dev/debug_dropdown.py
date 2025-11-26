"""Debug script to find and analyze the odds type dropdown."""

import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def debug_dropdown():
    """Find the odds type dropdown."""
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
        print("LOOKING FOR SELECT DROPDOWNS")
        print("=" * 60)

        # Find all select elements
        selects = await page.query_selector_all("select")
        print(f"\nFound {len(selects)} SELECT elements")

        for i, select in enumerate(selects):
            select_id = await select.get_attribute("id") or ""
            select_name = await select.get_attribute("name") or ""
            select_class = await select.get_attribute("class") or ""

            # Get options
            options = await select.query_selector_all("option")
            option_texts = []
            for opt in options:
                opt_text = await opt.inner_text()
                opt_value = await opt.get_attribute("value") or ""
                option_texts.append(f"{opt_text} (value={opt_value})")

            print(f"\n  SELECT [{i}]:")
            print(f"    id='{select_id}' name='{select_name}'")
            print(f"    class='{select_class[:50]}'")
            print(f"    Options: {option_texts}")

            # Check if this has Total option
            if any("Total" in t for t in option_texts):
                print("    *** THIS HAS TOTAL OPTION! ***")

        # Look for the option element directly
        print("\n" + "=" * 60)
        print("FINDING PARENT OF 'Total' OPTION")
        print("=" * 60)

        total_option = await page.query_selector("option:has-text('Total')")
        if total_option:
            # Get parent select
            parent_select = await total_option.evaluate("""
                el => {
                    const parent = el.closest('select');
                    return parent ? {
                        id: parent.id,
                        name: parent.name,
                        className: parent.className,
                        currentValue: parent.value
                    } : null;
                }
            """)
            print(f"  Parent SELECT: {parent_select}")

            # Get all options
            if parent_select:
                select_elem = await page.query_selector(
                    f"select#{parent_select['id']}"
                    if parent_select["id"]
                    else "select:has(option:has-text('Total'))"
                )
                if select_elem:
                    current_value = await select_elem.input_value()
                    print(f"  Current value: '{current_value}'")

                    # Try selecting "Total"
                    print("\n  Attempting to select 'Total'...")
                    await select_elem.select_option(label="Total")
                    await asyncio.sleep(2)

                    # Check if table content changed
                    new_value = await select_elem.input_value()
                    print(f"  New value after selection: '{new_value}'")

                    # Get first row data
                    first_cell = await page.query_selector(
                        "div.best-odds__open-container"
                    )
                    if first_cell:
                        cell_text = await first_cell.inner_text()
                        print(f"\n  First odds cell after switching to Total:")
                        print(f"  '{cell_text.replace(chr(10), ' | ')}'")

        await browser.close()
        print("\n" + "=" * 60)
        print("Done!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(debug_dropdown())
