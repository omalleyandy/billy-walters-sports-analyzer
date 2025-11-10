#!/usr/bin/env python3
"""
Overtime.ag CDP Scraper with Proxy Support
Uses Chrome DevTools Protocol to launch Chrome with proxy authentication
"""

import os
import json
import asyncio
from typing import List, Dict
from datetime import datetime
from playwright.async_api import async_playwright

# Import your existing parser
from walters_analyzer.ingest.chrome_devtools_scraper import ChromeDevToolsOddsExtractor


async def scrape_overtime_with_cdp_proxy() -> List[Dict]:
    """
    Scrape overtime.ag using CDP with proxy support via Chrome command-line args.

    Chrome handles proxy authentication natively via --proxy-server flag,
    which works better than Playwright's proxy config.

    Returns:
        List of game dictionaries in Billy Walters format
    """
    # Get proxy from environment
    proxy_url = os.getenv("PROXY_URL")
    ov_customer_id = os.getenv("OV_CUSTOMER_ID")
    ov_password = os.getenv("OV_PASSWORD")

    if not proxy_url:
        print("WARNING: No PROXY_URL found in environment")
        return []

    print(f"Using proxy: {proxy_url}")
    print(f"OV Customer ID: {ov_customer_id}")

    async with async_playwright() as p:
        # Launch Chrome with CDP and proxy via command-line args
        # Chrome's --proxy-server handles authentication from URL automatically
        browser = await p.chromium.launch(
            headless=False,  # Visible for debugging
            args=[
                f'--proxy-server={proxy_url}',  # Chrome parses credentials from URL
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        try:
            # Create context
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                locale='en-US'
            )

            page = await context.new_page()

            # Navigate to overtime.ag
            print("Navigating to overtime.ag...")
            await page.goto("https://overtime.ag", wait_until='domcontentloaded', timeout=60000)

            # Wait for page to load
            await page.wait_for_timeout(3000)

            # Check if login is needed
            if ov_customer_id and ov_password:
                print("Checking for login...")
                try:
                    # Try to find login button or form
                    login_indicator = await page.query_selector('text="LOGIN"')
                    if login_indicator:
                        print("Login required, attempting to log in...")
                        # Navigate to login page
                        await page.evaluate('location.hash = "#/login"')
                        await page.wait_for_timeout(2000)

                        # Fill credentials
                        customer_input = await page.query_selector('input[placeholder*="Customer"], input[name*="customer"]')
                        if customer_input:
                            await customer_input.fill(ov_customer_id)

                        password_input = await page.query_selector('input[type="password"]')
                        if password_input:
                            await password_input.fill(ov_password)

                        # Click login
                        login_btn = await page.query_selector('button:has-text("LOGIN")')
                        if login_btn:
                            await login_btn.click()
                            await page.wait_for_timeout(3000)
                            print("Login successful!")
                except Exception as e:
                    print(f"Login attempt failed: {e}")

            # Navigate to live betting page
            print("Navigating to live betting page...")
            await page.goto("https://overtime.ag/sports#/integrations/liveBetting",
                          wait_until='domcontentloaded', timeout=60000)

            await page.wait_for_timeout(5000)  # Wait for odds to load

            # Get accessibility snapshot
            print("Capturing accessibility snapshot...")
            cdp = await page.context.new_cdp_session(page)
            snapshot = await cdp.send('Accessibility.getFullAXTree')

            # Convert to text format for parser
            snapshot_text = accessibility_tree_to_text(snapshot)

            # Save snapshot for debugging
            with open('overtime_snapshot.txt', 'w', encoding='utf-8') as f:
                f.write(snapshot_text)
            print("Snapshot saved to overtime_snapshot.txt")

            # Extract games using existing parser
            extractor = ChromeDevToolsOddsExtractor()
            games = extractor.extract_games_from_snapshot(snapshot_text)

            print(f"Extracted {len(games)} games")

            # Save games to JSON
            output_file = 'output/overtime_cdp_odds.json'
            os.makedirs('output', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(games, f, indent=2)
            print(f"Games saved to {output_file}")

            return games

        finally:
            await browser.close()


def accessibility_tree_to_text(ax_tree: dict) -> str:
    """Convert accessibility tree to text format for parser"""
    lines = []

    def traverse(node, depth=0):
        """Recursively traverse accessibility tree"""
        if not isinstance(node, dict):
            return

        # Get node properties
        role = node.get('role', {}).get('value', '')
        name = node.get('name', {}).get('value', '')
        node_id = node.get('nodeId', '')

        # Format line similar to accessibility snapshot format
        if name:
            lines.append(f'uid={node_id} {role} "{name}"')

        # Traverse children
        children = node.get('children', [])
        for child in children:
            traverse(child, depth + 1)

    # Start traversal
    nodes = ax_tree.get('nodes', [])
    for node in nodes:
        traverse(node)

    return '\n'.join(lines)


async def main():
    """Main entry point"""
    print("=" * 60)
    print("Overtime.ag CDP Scraper with Proxy Support")
    print("=" * 60)

    games = await scrape_overtime_with_cdp_proxy()

    if games:
        print(f"\n✓ Successfully scraped {len(games)} games!")
        print("\nSample game:")
        print(json.dumps(games[0], indent=2))
    else:
        print("\n✗ No games extracted")
        print("This is normal if no games are currently live")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
