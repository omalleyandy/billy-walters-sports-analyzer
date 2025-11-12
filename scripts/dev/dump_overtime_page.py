#!/usr/bin/env python3
"""
Simple page dump - just login and see what's there
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(".env", override=True)


async def dump_page():
    """Just login and dump what we see"""

    customer_id = os.getenv("OV_CUSTOMER_ID")
    password = os.getenv("OV_PASSWORD")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate and login (same as working scraper)
            print("Navigating and logging in...")
            await page.goto(
                "https://overtime.ag/sports#/", wait_until="domcontentloaded"
            )
            await page.wait_for_timeout(3000)

            # Login (using JavaScript click like the working scraper)
            await page.evaluate("""
                () => {
                    const loginBtn = document.querySelector('a.btn-signup');
                    if (loginBtn) loginBtn.click();
                }
            """)
            await page.wait_for_timeout(2000)

            customer_input = await page.query_selector('input[placeholder*="Customer"]')
            if customer_input:
                await customer_input.fill(customer_id)

            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(password)

            login_btn = await page.query_selector('button:has-text("LOGIN")')
            if login_btn:
                await login_btn.click()
                await page.wait_for_timeout(5000)

            # Navigate to NFL (using JavaScript like the working scraper)
            print("Navigating to NFL section...")
            await page.evaluate("""
                () => {
                    const nflElement = Array.from(document.querySelectorAll('label'))
                        .find(el => el.textContent.includes('NFL-Game/1H/2H/Qrts'));
                    if (nflElement) {
                        nflElement.click();
                    }
                }
            """)
            await page.wait_for_timeout(5000)  # Wait for games to load

            # Now dump what's on the page
            print("\n" + "=" * 70)
            print("PAGE ANALYSIS")
            print("=" * 70)

            info = await page.evaluate(r"""
                () => {
                    // Get all buttons and their attributes
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const buttonInfo = buttons.map(b => ({
                        text: b.textContent.trim().substring(0, 50),
                        ngClick: b.getAttribute('ng-click'),
                        className: b.className,
                        hasOdds: /[-+]?\d+/.test(b.textContent)
                    }));

                    // Find buttons that look like betting buttons (have odds numbers)
                    const bettingButtons = buttonInfo.filter(b => b.hasOdds);

                    // Get team-like h4 elements (have numbers at start)
                    const h4s = Array.from(document.querySelectorAll('h4'));
                    const teamH4s = h4s.filter(h => /^\d{3,4}/.test(h.textContent.trim()));

                    return {
                        totalButtons: buttons.length,
                        bettingButtons: bettingButtons.slice(0, 20),
                        bettingButtonCount: bettingButtons.length,
                        teamH4s: teamH4s.map(h => h.textContent.trim()).slice(0, 20),
                        teamH4Count: teamH4s.length,
                        sendLineToWagerCount: document.querySelectorAll('button[ng-click*="SendLineToWager"]').length
                    };
                }
            """)

            print(f"\nTotal buttons on page: {info['totalButtons']}")
            print(f"Buttons matching 'SendLineToWager': {info['sendLineToWagerCount']}")
            print(f"Buttons with odds numbers: {info['bettingButtonCount']}")
            print(f"Team H4 elements (with rotation numbers): {info['teamH4Count']}")
            print()

            if info["teamH4s"]:
                print("TEAMS FOUND:")
                for team in info["teamH4s"]:
                    print(f"  - {team}")
                print()

            if info["bettingButtons"]:
                print("BETTING BUTTONS FOUND (first 20):")
                for i, btn in enumerate(info["bettingButtons"][:20], 1):
                    print(f"  {i}. Text: '{btn['text']}'")
                    print(f"      ng-click: {btn['ngClick']}")
                    print(f"      class: {btn['className'][:80]}")
                    print()

            print("=" * 70)
            print(
                f"RESULT: {'GAMES FOUND!' if info['teamH4Count'] > 0 else 'NO GAMES FOUND'}"
            )
            print("=" * 70)

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(dump_page())
