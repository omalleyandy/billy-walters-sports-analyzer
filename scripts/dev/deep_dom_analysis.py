"""
Deep DOM Analysis for Action Network Odds Page.

Analyzes the structure to understand how game info relates to odds values.
"""

import asyncio
import os
import re

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def analyze_dom():
    """Deep DOM analysis to understand odds structure."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Login
        print("=" * 70)
        print("DEEP DOM ANALYSIS - Action Network Odds")
        print("=" * 70)
        print("\n[1] Logging in...")
        await page.goto("https://www.actionnetwork.com/login")
        await page.wait_for_selector("input[placeholder='Email']")
        await page.fill("input[placeholder='Email']", os.getenv("ACTION_USERNAME"))
        await page.fill("input[placeholder='Password']", os.getenv("ACTION_PASSWORD"))
        await page.click("button[type='submit']")
        await asyncio.sleep(5)
        print(f"    Login complete - URL: {page.url}")

        # Navigate to NFL odds
        print("\n[2] Navigating to NFL odds...")
        await page.goto("https://www.actionnetwork.com/nfl/odds")
        await asyncio.sleep(3)

        # Step 1: Find all game info containers and their parents
        print("\n[3] Analyzing game info container hierarchy...")
        game_infos = await page.query_selector_all("div.best-odds__game-info")
        print(f"    Found {len(game_infos)} game info containers")

        if game_infos:
            first_game = game_infos[0]

            # Get the text of first game
            game_text = await first_game.inner_text()
            print(f"\n    First game text: {game_text.replace(chr(10), ' | ')}")

            # Walk up the tree to find container structure
            print("\n[4] Walking up DOM tree from first game...")
            current = first_game
            depth = 0
            ancestors = []
            while current and depth < 10:
                tag = await current.evaluate("el => el.tagName")
                classes = await current.get_attribute("class") or ""
                class_preview = classes[:60] + "..." if len(classes) > 60 else classes

                # Get sibling count
                sibling_count = await current.evaluate(
                    "el => el.parentElement ? el.parentElement.children.length : 0"
                )

                ancestors.append(
                    {
                        "depth": depth,
                        "tag": tag,
                        "class": class_preview,
                        "siblings": sibling_count,
                    }
                )

                print(
                    f"    [{depth}] <{tag}> class='{class_preview}' (siblings: {sibling_count})"
                )

                # Move to parent
                parent = await current.evaluate("el => el.parentElement")
                if parent:
                    current = await current.query_selector("xpath=..")
                else:
                    break
                depth += 1

        # Step 2: Find elements containing betting lines
        print("\n[5] Searching for betting line patterns...")

        # Look for elements containing spread-like values
        spread_patterns = [
            "+2.5",
            "-2.5",
            "+3",
            "-3",
            "+7",
            "-7",
            "-110",
            "-105",
            "+100",
        ]

        for pattern in spread_patterns[:3]:
            elements = await page.query_selector_all(f"text='{pattern}'")
            if elements:
                print(f"\n    Found '{pattern}' in {len(elements)} elements")
                for i, elem in enumerate(elements[:2]):
                    tag = await elem.evaluate("el => el.tagName")
                    classes = await elem.get_attribute("class") or ""
                    parent_tag = await elem.evaluate(
                        "el => el.parentElement?.tagName || 'none'"
                    )
                    parent_class = await elem.evaluate(
                        "el => el.parentElement?.className || ''"
                    )

                    print(f"      [{i}] <{tag}> class='{classes[:40]}'")
                    print(
                        f"          Parent: <{parent_tag}> class='{parent_class[:40]}'"
                    )

        # Step 3: Look at table structure
        print("\n[6] Analyzing table structure...")
        tables = await page.query_selector_all("table")
        print(f"    Found {len(tables)} tables")

        for i, table in enumerate(tables[:3]):
            table_class = await table.get_attribute("class") or ""
            rows = await table.query_selector_all("tr")
            cols = await table.query_selector_all("th, td")

            print(f"\n    Table {i + 1}: class='{table_class[:50]}'")
            print(f"      Rows: {len(rows)}, Cells: {len(cols)}")

            # Get first row content
            if rows:
                first_row = rows[0]
                row_text = await first_row.inner_text()
                row_preview = row_text[:100].replace("\n", " | ")
                print(f"      First row: {row_preview}...")

        # Step 4: Find the odds table associated with first game
        print("\n[7] Finding odds associated with first game...")

        if game_infos:
            first_game = game_infos[0]

            # Try to find nearby table (sibling or child of parent)
            # Method 1: Check if there's a table as a sibling
            sibling_table = await first_game.query_selector(
                "xpath=following-sibling::table"
            )
            if sibling_table:
                print("    Found table as following sibling!")
                table_text = await sibling_table.inner_text()
                print(
                    f"    Table preview: {table_text[:200].replace(chr(10), ' | ')}..."
                )
            else:
                print("    No direct sibling table")

            # Method 2: Go up to parent and look for table
            parent = await first_game.query_selector("xpath=..")
            if parent:
                parent_class = await parent.get_attribute("class") or ""
                print(f"\n    Parent class: {parent_class}")

                # Look for table in parent
                parent_table = await parent.query_selector("table")
                if parent_table:
                    print("    Found table in parent!")
                    table_text = await parent_table.inner_text()
                    print(
                        f"    Table preview: {table_text[:200].replace(chr(10), ' | ')}..."
                    )

                # Look for sibling divs with odds
                siblings = await parent.query_selector_all(":scope > div")
                print(f"\n    Parent has {len(siblings)} direct div children")

                for j, sib in enumerate(siblings[:5]):
                    sib_class = await sib.get_attribute("class") or ""
                    sib_text = await sib.inner_text()
                    sib_preview = sib_text[:60].replace("\n", " | ")
                    print(f"      [{j}] class='{sib_class[:40]}' text='{sib_preview}'")

        # Step 5: Look for specific odds-related classes
        print("\n[8] Searching for odds-specific classes...")
        odds_class_patterns = [
            "[class*='spread']",
            "[class*='total']",
            "[class*='moneyline']",
            "[class*='odds']",
            "[class*='line']",
            "[class*='cell']",
            "[class*='book']",
        ]

        for pattern in odds_class_patterns:
            elements = await page.query_selector_all(pattern)
            if elements:
                print(f"\n    '{pattern}': {len(elements)} elements")
                # Sample first element
                if elements:
                    elem = elements[0]
                    tag = await elem.evaluate("el => el.tagName")
                    full_class = await elem.get_attribute("class") or ""
                    text = await elem.inner_text()
                    text_preview = text[:80].replace("\n", " | ")
                    print(f"      First: <{tag}> class='{full_class[:50]}'")
                    print(f"      Text: {text_preview}")

        # Step 6: Look at the structure around betting values
        print("\n[9] Analyzing structure around actual betting values...")

        # Find elements with spread-like text
        spread_elem = await page.query_selector("text=/[+-]\\d+\\.?\\d*/")
        if spread_elem:
            text = await spread_elem.inner_text()
            print(f"    Found spread value: {text}")

            # Walk up 5 levels
            current = spread_elem
            for level in range(5):
                if current:
                    tag = await current.evaluate("el => el.tagName")
                    classes = await current.get_attribute("class") or ""
                    current_text = await current.inner_text()
                    text_preview = current_text[:40].replace("\n", "|")
                    print(
                        f"      L{level}: <{tag}> class='{classes[:30]}' text='{text_preview}'"
                    )
                    current = await current.query_selector("xpath=..")

        # Step 7: Full page evaluation for odds patterns
        print("\n[10] Evaluating page for complete game+odds structure...")

        result = await page.evaluate("""
            () => {
                const gameInfos = document.querySelectorAll('div.best-odds__game-info');
                const results = [];

                for (let i = 0; i < Math.min(gameInfos.length, 2); i++) {
                    const info = gameInfos[i];
                    const gameText = info.innerText.trim().replace(/\\n/g, ' | ');

                    // Get parent structure
                    let parent = info.parentElement;
                    let parentInfo = [];
                    let depth = 0;

                    while (parent && depth < 5) {
                        parentInfo.push({
                            tag: parent.tagName,
                            class: parent.className?.substring(0, 50) || '',
                            childCount: parent.children.length
                        });
                        parent = parent.parentElement;
                        depth++;
                    }

                    // Look for betting values near this game
                    const container = info.closest('[class*="game"]') || info.parentElement;
                    const allText = container ? container.innerText : '';

                    // Find spread patterns
                    const spreadMatch = allText.match(/[+-]\\d+\\.?\\d*\\s*[+-]?\\d*/g);

                    results.push({
                        gameText: gameText.substring(0, 50),
                        parents: parentInfo,
                        containerClass: container?.className?.substring(0, 60) || '',
                        spreadMatches: spreadMatch ? spreadMatch.slice(0, 5) : [],
                        containerTextLength: allText.length
                    });
                }

                return results;
            }
        """)

        print("\n    Game-Container Analysis:")
        for i, r in enumerate(result):
            print(f"\n    Game {i + 1}: {r['gameText']}")
            print(f"      Container class: {r['containerClass']}")
            print(f"      Container text length: {r['containerTextLength']}")
            print(f"      Spread matches: {r['spreadMatches']}")
            print("      Parent chain:")
            for p in r["parents"][:3]:
                print(
                    f"        <{p['tag']}> class='{p['class']}' children={p['childCount']}"
                )

        await browser.close()
        print("\n" + "=" * 70)
        print("Analysis complete!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(analyze_dom())
