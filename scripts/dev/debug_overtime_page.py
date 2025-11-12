#!/usr/bin/env python3
"""
Debug script to investigate Overtime.ag page structure when games are visible
"""

import asyncio
import os
import sys
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
    print("OVERTIME.AG PAGE DEBUGGER")
    print("=" * 70)
    print()

    async with async_playwright() as p:
        # Launch visible browser to see what's happening
        browser = await p.chromium.launch(headless=False)
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
            await page.click('label:has-text("NFL-Game/1H/2H/Qrts")')
            await page.wait_for_timeout(3000)

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

                        // Check for team names
                        h4Elements: document.querySelectorAll('h4').length,
                        h4Texts: Array.from(document.querySelectorAll('h4')).slice(0, 20).map(h => h.textContent.trim()),

                        // Check for rotation numbers (usually prefix team names)
                        rotationNumbers: Array.from(document.querySelectorAll('h4'))
                            .filter(h => /^\d{3,4}\s+/.test(h.textContent))
                            .map(h => h.textContent.trim())
                            .slice(0, 10),

                        // Check button classes
                        buttonClasses: Array.from(document.querySelectorAll('button'))
                            .map(b => b.className)
                            .filter((v, i, a) => a.indexOf(v) === i)
                            .slice(0, 10),

                        // Check ng-click patterns
                        ngClickPatterns: Array.from(document.querySelectorAll('button[ng-click]'))
                            .map(b => b.getAttribute('ng-click'))
                            .filter((v, i, a) => a.indexOf(v) === i)
                            .slice(0, 10),

                        // Check if games container exists
                        hasGamesContainer: !!document.querySelector('.games, .games-list, [class*="game"]'),

                        // Current URL hash
                        currentHash: window.location.hash,
                    };

                    return results;
                }
            """)

            print(
                f"Original selector (SendLineToWager): {debug_info['sendLineToWager']} buttons"
            )
            print(f"Total buttons on page: {debug_info['allButtons']}")
            print(f"Buttons with ng-click: {debug_info['buttonsWithNgClick']}")
            print(f"H4 elements (team names): {debug_info['h4Elements']}")
            print(f"Has games container: {debug_info['hasGamesContainer']}")
            print(f"Current hash: {debug_info['currentHash']}")
            print()

            print("First 20 H4 texts (looking for team names):")
            for i, text in enumerate(debug_info["h4Texts"], 1):
                print(f"  {i}. {text}")
            print()

            if debug_info["rotationNumbers"]:
                print("Found rotation numbers (these are games!):")
                for rot in debug_info["rotationNumbers"]:
                    print(f"  - {rot}")
                print()
            else:
                print("No rotation numbers found (no games with rotation numbers)")
                print()

            print("Button classes (sample):")
            for cls in debug_info["buttonClasses"]:
                print(f"  - {cls}")
            print()

            print("ng-click patterns (sample):")
            for pattern in debug_info["ngClickPatterns"]:
                print(f"  - {pattern}")
            print()

            # 5. Take screenshot
            screenshot_file = "output/overtime_debug_screenshot.png"
            await page.screenshot(path=screenshot_file, full_page=True)
            print(f"Screenshot saved to: {screenshot_file}")
            print()

            # 6. Save page HTML
            html_file = "output/overtime_debug_page.html"
            html = await page.content()
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Page HTML saved to: {html_file}")
            print()

            print("=" * 70)
            print("ANALYSIS COMPLETE")
            print("=" * 70)
            print()
            print("Next steps:")
            print(
                "1. Check if rotation numbers were found (indicates games are visible)"
            )
            print("2. Check ng-click patterns to see if selector needs updating")
            print("3. Review screenshot to see what's actually on page")
            print("4. Review HTML file to understand page structure")
            print()

            # Wait for user to inspect
            input("Press Enter to close browser...")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_overtime())
