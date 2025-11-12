#!/usr/bin/env python3
"""
Open Overtime.ag with Chrome DevTools for manual inspection

This script will:
1. Open a visible Chrome browser
2. Navigate to Overtime.ag
3. Log in automatically
4. Navigate to NFL section
5. Pause so you can use Chrome DevTools to inspect the page

Instructions:
- Once browser opens and navigates to NFL section, press F12 to open DevTools
- Use DevTools to inspect the page structure
- Look for betting buttons, team names, etc.
- Note the exact HTML structure and selectors
- Press Enter in terminal when done to close browser
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(".env", override=True)


async def inspect_with_devtools():
    """Open browser for manual DevTools inspection"""

    customer_id = os.getenv("OV_CUSTOMER_ID")
    password = os.getenv("OV_PASSWORD")

    if not customer_id or not password:
        print("[ERROR] Missing OV_CUSTOMER_ID or OV_PASSWORD in .env")
        return

    print("=" * 70)
    print("OVERTIME.AG CHROME DEVTOOLS INSPECTOR")
    print("=" * 70)
    print()
    print("This will open a Chrome browser and navigate to Overtime.ag")
    print("You can then use Chrome DevTools (F12) to inspect the page")
    print()
    print("Instructions:")
    print("1. Browser will open and automatically log in")
    print("2. Browser will navigate to NFL section")
    print("3. Press F12 to open Chrome DevTools")
    print("4. Inspect the page structure:")
    print("   - Look for betting buttons with odds")
    print("   - Look for team names (usually in <h4> tags)")
    print("   - Check ng-click attributes on buttons")
    print("   - Note any selectors that would identify game lines")
    print("5. Press Enter in this terminal when done")
    print()
    print("=" * 70)
    print()

    async with async_playwright() as p:
        # Launch visible Chrome with DevTools
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome",  # Use Chrome instead of Chromium
            args=[
                "--auto-open-devtools-for-tabs",  # Auto-open DevTools
            ],
        )

        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        try:
            # 1. Navigate
            print("Step 1: Navigating to Overtime.ag...")
            await page.goto(
                "https://overtime.ag/sports#/", wait_until="domcontentloaded"
            )
            await page.wait_for_timeout(3000)
            print("   [OK] Page loaded")
            print()

            # 2. Login
            print("Step 2: Logging in...")
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
                    print("   [OK] Logged in successfully")
                    print()

            # 3. Navigate to NFL section
            print("Step 3: Navigating to NFL section...")
            await page.evaluate("""
                () => {
                    const nflElement = Array.from(document.querySelectorAll('label'))
                        .find(el => el.textContent.includes('NFL-Game/1H/2H/Qrts'));
                    if (nflElement) {
                        nflElement.click();
                        return true;
                    }
                    return false;
                }
            """)
            await page.wait_for_timeout(5000)
            print("   [OK] NFL section opened")
            print()

            # 4. Show what we can detect
            print("Step 4: Quick page analysis...")
            info = await page.evaluate("""
                () => {
                    return {
                        totalButtons: document.querySelectorAll('button').length,
                        h4Count: document.querySelectorAll('h4').length,
                        h4Texts: Array.from(document.querySelectorAll('h4'))
                            .map(h => h.textContent.trim())
                            .slice(0, 30)
                    };
                }
            """)

            print(f"   Total buttons: {info['totalButtons']}")
            print(f"   H4 elements: {info['h4Count']}")
            print()

            if info["h4Texts"]:
                print("   First 30 H4 texts:")
                for text in info["h4Texts"]:
                    if text:
                        print(f"      - {text}")
                print()

            # 5. Instructions for manual inspection
            print("=" * 70)
            print("READY FOR MANUAL INSPECTION")
            print("=" * 70)
            print()
            print("The browser is now ready for inspection.")
            print()
            print("Chrome DevTools should be open (if not, press F12)")
            print()
            print("Things to check in DevTools:")
            print("  1. Are there game lines visible on the page?")
            print("  2. What HTML elements contain team names?")
            print("  3. What HTML elements contain betting buttons?")
            print("  4. What are the ng-click attributes on betting buttons?")
            print("  5. Are games loading dynamically (check Network tab)?")
            print()
            print("In DevTools Console, you can run queries like:")
            print("  document.querySelectorAll('h4')")
            print("  document.querySelectorAll('button')")
            print("  document.querySelectorAll('button[ng-click*=\"SendLine\"]')")
            print()
            print("=" * 70)
            print()

            # Wait for user to finish inspection
            input("Press Enter when you're done inspecting...")

        finally:
            await browser.close()
            print()
            print("Browser closed. Done!")


if __name__ == "__main__":
    asyncio.run(inspect_with_devtools())
