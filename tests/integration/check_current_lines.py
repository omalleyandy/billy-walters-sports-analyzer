"""Check current NFL lines from Overtime.ag (including live games)"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(".env", override=True)


async def check_current_lines():
    print("=" * 70)
    print("CHECKING CURRENT NFL LINES (Overtime.ag)")
    print("=" * 70)
    print()

    customer_id = os.getenv("OV_CUSTOMER_ID")
    password = os.getenv("OV_PASSWORD")

    if not customer_id or not password:
        print("[ERROR] Missing OV_CUSTOMER_ID or OV_PASSWORD")
        return

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to Overtime
            print("1. Navigating to Overtime.ag...")
            await page.goto(
                "https://overtime.ag/sports",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await asyncio.sleep(2)

            # Login
            print("2. Logging in...")
            login_button = page.locator("a.btn-signup")
            await login_button.evaluate("el => el.click()")
            await asyncio.sleep(1)

            await page.fill('input[name="customerId"]', customer_id)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(3)

            # Get account info
            print("3. Checking account...")
            balance_elem = await page.query_selector('[href*="dailyFigures"]')
            if balance_elem:
                balance_text = await balance_elem.inner_text()
                print(f"   Balance: {balance_text}")

            print()
            print("4. Checking for NFL games...")
            print("-" * 70)

            # Click NFL section
            nfl_label = page.locator('label:has-text("NFL-Game/1H/2H/Qrts")')
            if await nfl_label.count() > 0:
                await nfl_label.click()
                await asyncio.sleep(2)

            # Get all game containers
            game_containers = await page.query_selector_all(
                'div.event-container, div.game-container, div[class*="event"], div[class*="game"]'
            )

            print(f"Found {len(game_containers)} potential game elements")
            print()

            # Try to extract game info
            games_found = []

            # Look for team names and lines
            h4_elements = await page.query_selector_all("h4")
            for h4 in h4_elements:
                text = await h4.inner_text()
                # Skip headers
                if any(
                    x in text.upper()
                    for x in ["FOOTBALL", "BASKETBALL", "BASEBALL", "NFL", "NCAAF"]
                ):
                    continue

                # Team names typically have rotation numbers like "501 Team Name"
                if text and len(text) > 5:
                    print(f"Team/Game: {text}")

            print()

            # Look for betting buttons with lines
            buttons = await page.query_selector_all(
                'button[ng-click*="SendLineToWager"]'
            )
            print(f"Found {len(buttons)} betting buttons")

            if len(buttons) > 0:
                print()
                print("AVAILABLE LINES:")
                print("-" * 70)

                for i, button in enumerate(buttons[:20]):  # Limit to first 20
                    try:
                        text = await button.inner_text()
                        if text:
                            print(f"  {text}")
                    except:
                        pass

            # Check if there are any games at all
            if len(buttons) == 0:
                print()
                print("[INFO] No active betting lines found")
                print()
                print("This could mean:")
                print("  - All games have started (lines taken down)")
                print("  - No games scheduled for betting")
                print("  - Need to check LIVE PLUS section for in-play odds")
                print()

                # Try to navigate to Live Plus
                print("5. Checking LIVE PLUS section...")
                print("-" * 70)

                # Look for Live Plus link
                live_plus_link = page.locator('a:has-text("LIVE PLUS"), [href*="live"]')
                if await live_plus_link.count() > 0:
                    print("   Found LIVE PLUS link, navigating...")
                    await live_plus_link.first.click()
                    await asyncio.sleep(3)

                    # Check for iframe with live games
                    frames = page.frames
                    print(f"   Found {len(frames)} frames on page")

                    for frame in frames:
                        try:
                            frame_url = frame.url
                            if "live" in frame_url.lower():
                                print(f"   Live frame URL: {frame_url}")

                                # Try to get content from live frame
                                live_buttons = await frame.query_selector_all(
                                    'button, [class*="bet"], [class*="odd"]'
                                )
                                print(
                                    f"   Found {len(live_buttons)} potential betting elements in live frame"
                                )
                        except:
                            pass
                else:
                    print("   Could not find LIVE PLUS link")

            print()
            print("=" * 70)

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback

            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(check_current_lines())
