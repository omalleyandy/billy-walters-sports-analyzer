#!/usr/bin/env python3
"""Test if Firefox works better with the proxy"""

import asyncio
from playwright.async_api import async_playwright

# Stealth mode
try:
    try:
        from playwright_stealth import Stealth
        stealth_async = lambda page: Stealth().apply_stealth_async(page)
        STEALTH_AVAILABLE = True
    except (ImportError, AttributeError):
        from playwright_stealth import stealth_async
        STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

async def test():
    print("Testing Firefox internet access...")
    async with async_playwright() as p:
        print("Launching Firefox...")
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        if STEALTH_AVAILABLE:
            print("Applying stealth...")
            await stealth_async(page)

        print("Navigating to overtime.ag/sports/...")
        try:
            await page.goto("https://overtime.ag/sports/", wait_until="domcontentloaded", timeout=60000)
            print("✓ Page loaded!")
            print(f"Title: {await page.title()}")

            # Check if logged in
            content = await page.content()
            if "Customer Id" in content:
                print("⚠ Login form detected")
            else:
                print("✓ Page content loaded")

        except Exception as e:
            print(f"❌ Failed: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
