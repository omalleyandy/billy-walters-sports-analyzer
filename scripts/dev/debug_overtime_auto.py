#!/usr/bin/env python3
"""
Automated debug script for Overtime.ag - no user input needed
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(".env", override=True)


async def debug_overtime():
    """Debug what's actually on the Overtime.ag page"""

    customer_id = os.getenv("OV_CUSTOMER_ID")
    password = os.getenv("OV_PASSWORD")

    if not customer_id or not password:
        print("[ERROR] Missing OV_CUSTOMER_ID or OV_PASSWORD in .env")
        return

    print("=" * 70)
    print("OVERTIME.AG AUTOMATED PAGE DEBUGGER")
    print("=" * 70)
    print()

    async with async_playwright() as p:
        # Launch headless for automation
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        try:
            # 1. Navigate
            print("1. Navigating to Overtime.ag...")
            await page.goto(
                "https://overtime.ag/sports#/",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await page.wait_for_timeout(3000)

            # 2. Login
            print("2. Logging in...")
            login_clicked = await page.evaluate("""
                () => {
                    const loginBtn = document.querySelector('a.btn-signup');
                    if (loginBtn) {
                        loginBtn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if login_clicked:
                await page.wait_for_timeout(2000)

                customer_input = await page.query_selector(
                    'input[placeholder*="Customer"]'
                )
                if customer_input:
                    await customer_input.fill(customer_id)

                password_input = await page.query_selector('input[type="password"]')
                if password_input:
                    await password_input.fill(password)

                login_btn = await page.query_selector('button:has-text("LOGIN")')
                if login_btn:
                    await login_btn.click()
                    await page.wait_for_timeout(5000)
                    print("   Login successful!")

            # 3. Click NFL section
            print("3. Clicking NFL section...")
            nfl_label = await page.query_selector(
                'label:has-text("NFL-Game/1H/2H/Qrts")'
            )
            if nfl_label:
                await nfl_label.click()
                await page.wait_for_timeout(5000)  # Wait longer for games to load
                print("   NFL section clicked")

            # 4. Debug page structure
            print("\n4. Analyzing page structure...")
            print("=" * 70)

            debug_info = await page.evaluate("""
                () => {
                    // Check various button selectors
                    const results = {
                        // Original selector
                        sendLineToWager: document.querySelectorAll('button[ng-click*="SendLineToWager"]').length,

                        // Alternative selectors
                        allButtons: document.querySelectorAll('button').length,
                        buttonsWithNgClick: document.querySelectorAll('button[ng-click]').length,

                        // Check for team names (h4 with rotation numbers)
                        h4Elements: document.querySelectorAll('h4').length,
                        h4Texts: Array.from(document.querySelectorAll('h4')).slice(0, 30).map(h => h.textContent.trim()),

                        // Check button text content
                        buttonTexts: Array.from(document.querySelectorAll('button'))
                            .map(b => b.textContent.trim())
                            .filter(t => t && t.length > 0 && t.length < 50)
                            .slice(0, 50),

                        // Check button classes
                        buttonClasses: Array.from(new Set(
                            Array.from(document.querySelectorAll('button'))
                                .map(b => b.className)
                                .filter(c => c)
                        )).slice(0, 20),

                        // Check ng-click patterns
                        ngClickPatterns: Array.from(new Set(
                            Array.from(document.querySelectorAll('button[ng-click]'))
                                .map(b => b.getAttribute('ng-click'))
                                .filter(c => c)
                        )).slice(0, 20),

                        // Current URL hash
                        currentHash: window.location.hash,

                        // Check page content for game indicators
                        pageText: document.body.textContent.substring(0, 5000),
                    };

                    return results;
                }
            """)

            print(f"\nButton Analysis:")
            print(
                f"  Original selector (SendLineToWager): {debug_info['sendLineToWager']} buttons"
            )
            print(f"  Total buttons: {debug_info['allButtons']}")
            print(f"  Buttons with ng-click: {debug_info['buttonsWithNgClick']}")
            print(f"  H4 elements: {debug_info['h4Elements']}")
            print(f"  Current hash: {debug_info['currentHash']}")
            print()

            print("H4 Texts (first 30 - looking for team names):")
            for i, text in enumerate(debug_info["h4Texts"], 1):
                print(f"  {i}. {text}")
            print()

            print("Button Texts (first 50 - looking for odds):")
            for i, text in enumerate(debug_info["buttonTexts"], 1):
                print(f"  {i}. {text}")
            print()

            print("Button Classes (unique):")
            for cls in debug_info["buttonClasses"]:
                print(f"  - {cls}")
            print()

            print("ng-click Patterns (unique):")
            for pattern in debug_info["ngClickPatterns"]:
                print(f"  - {pattern}")
            print()

            # Check if we can find game-like patterns in text
            page_text = debug_info["pageText"]
            if any(
                team in page_text
                for team in ["Chiefs", "Bills", "Packers", "Eagles", "Cowboys"]
            ):
                print("[OK] Found NFL team names in page text!")
            else:
                print("[WARNING] No common NFL team names found in page text")

            # 5. Save debug info to file
            debug_file = "output/overtime_debug_info.json"
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(debug_info, f, indent=2)
            print(f"\nFull debug info saved to: {debug_file}")

            # 6. Take screenshot
            screenshot_file = "output/overtime_debug_screenshot.png"
            await page.screenshot(path=screenshot_file, full_page=True)
            print(f"Screenshot saved to: {screenshot_file}")

            print()
            print("=" * 70)
            print("ANALYSIS COMPLETE")
            print("=" * 70)

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_overtime())
