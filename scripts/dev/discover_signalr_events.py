#!/usr/bin/env python3
"""
Discover SignalR Event Names from Overtime.ag

This script reverse engineers the Overtime.ag website to discover
the actual SignalR event names they subscribe to.

Approach:
1. Open Overtime.ag in browser
2. Capture all JavaScript files
3. Search for SignalR hub proxy registrations
4. Extract event names from .on() calls

Usage:
    uv run python scripts/dev/discover_signalr_events.py
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Set

from playwright.async_api import async_playwright


async def discover_signalr_events():
    """Discover SignalR event names from Overtime.ag JavaScript"""

    print("=" * 70)
    print("SignalR Event Discovery - Overtime.ag")
    print("=" * 70)
    print()

    # Store captured JavaScript content
    js_files: Dict[str, str] = {}

    async with async_playwright() as p:
        print("1. Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()

        # Capture all JavaScript responses
        async def handle_response(response):
            if "javascript" in response.headers.get("content-type", ""):
                try:
                    url = response.url
                    content = await response.text()
                    js_files[url] = content
                    print(f"   Captured: {url}")
                except Exception as e:
                    print(f"   [ERROR] Failed to capture {response.url}: {e}")

        page.on("response", handle_response)

        print("2. Loading Overtime.ag...")
        await page.goto("https://overtime.ag", wait_until="networkidle")

        print(f"\n3. Captured {len(js_files)} JavaScript files")

        # Wait a bit for any lazy-loaded scripts
        print("4. Waiting for additional scripts...")
        await asyncio.sleep(3)

        await browser.close()

    print(f"\n5. Analyzing {len(js_files)} JavaScript files for SignalR events...")
    print("-" * 70)

    # Patterns to search for
    patterns = [
        # hubProxy.on('eventName', handler)
        r"\.on\s*\(\s*['\"]([^'\"]+)['\"]",
        # hub.on('eventName', handler)
        r"hub\.on\s*\(\s*['\"]([^'\"]+)['\"]",
        # connection.on('eventName', handler)
        r"connection\.on\s*\(\s*['\"]([^'\"]+)['\"]",
        # .client.eventName = function
        r"\.client\.(\w+)\s*=",
        # hub.client.eventName
        r"hub\.client\.(\w+)",
        # SignalR specific patterns
        r"gbsHub\.on\s*\(\s*['\"]([^'\"]+)['\"]",
        r"proxy\.on\s*\(\s*['\"]([^'\"]+)['\"]",
    ]

    events: Set[str] = set()

    for url, content in js_files.items():
        # Check if this file contains SignalR code
        if "signalr" not in content.lower() and "gbshub" not in content.lower():
            continue

        print(f"\nAnalyzing: {url}")

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    events.add(match)
                    print(f"   Found event: {match}")

    print("\n" + "=" * 70)
    print("DISCOVERED SIGNALR EVENTS")
    print("=" * 70)

    if events:
        sorted_events = sorted(events)
        for i, event in enumerate(sorted_events, 1):
            print(f"{i:2}. {event}")

        # Generate Python code for event subscriptions
        print("\n" + "=" * 70)
        print("PYTHON CODE TO ADD TO SCRAPER")
        print("=" * 70)
        print()
        print("# Add these event subscriptions in overtime_hybrid_scraper.py")
        print("# Around line 395-410")
        print()
        for event in sorted_events:
            print(f'self.signalr_connection.on("{event}", self._on_universal_event)')

        print()
        print("# Update event handlers to match these names")

        # Save to file
        output_file = Path("output/signalr_events_discovered.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "discovered_at": "2025-11-13",
            "source": "overtime.ag",
            "total_events": len(events),
            "events": sorted_events,
            "patterns_used": patterns,
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\nSaved to: {output_file}")

    else:
        print("[WARNING] No SignalR events found!")
        print()
        print("Possible reasons:")
        print("1. SignalR code is dynamically loaded or obfuscated")
        print("2. Events are registered after page load")
        print("3. Need to navigate to specific section (NFL games)")
        print()
        print("Next steps:")
        print("1. Try navigating to NFL section before capturing")
        print("2. Use browser DevTools manually to inspect")
        print("3. Search for 'gbsHub' in Sources tab")

    print("\n" + "=" * 70)
    print("DISCOVERY COMPLETE")
    print("=" * 70)


async def discover_with_login():
    """Enhanced version that logs in and navigates to NFL section"""

    print("=" * 70)
    print("SignalR Event Discovery - With Login & Navigation")
    print("=" * 70)
    print()

    import os
    from dotenv import load_dotenv

    load_dotenv()

    customer_id = os.getenv("OV_CUSTOMER_ID")
    password = os.getenv("OV_PASSWORD")

    if not customer_id or not password:
        print("[ERROR] Missing OV_CUSTOMER_ID or OV_PASSWORD in .env file")
        return

    js_files: Dict[str, str] = {}
    console_logs: List[str] = []

    async with async_playwright() as p:
        print("1. Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()

        # Capture console logs
        page.on("console", lambda msg: console_logs.append(msg.text))

        # Capture JavaScript responses
        async def handle_response(response):
            if "javascript" in response.headers.get("content-type", ""):
                try:
                    url = response.url
                    content = await response.text()
                    js_files[url] = content
                except Exception:
                    pass

        page.on("response", handle_response)

        print("2. Loading Overtime.ag...")
        await page.goto("https://overtime.ag", wait_until="networkidle")

        print("3. Logging in...")
        await page.click('a.btn-signup')
        await asyncio.sleep(1)

        await page.fill('input[ng-model="Username"]', customer_id)
        await page.fill('input[ng-model="Password"]', password)
        await page.click('button[ng-click="Login()"]')
        await asyncio.sleep(3)

        print("4. Navigating to NFL section...")
        nfl_labels = await page.locator('label:has-text("NFL")').all()
        if nfl_labels:
            await nfl_labels[0].click()
            await asyncio.sleep(2)

        print("5. Waiting for SignalR initialization...")
        await asyncio.sleep(5)

        # Try to access SignalR hub from page context
        print("\n6. Checking for SignalR hub in page context...")
        hub_info = await page.evaluate("""() => {
            const results = {
                signalr_exists: typeof $.connection !== 'undefined',
                hub_exists: false,
                hub_name: null,
                events: [],
                connection_state: null
            };

            if ($.connection) {
                results.connection_state = $.connection.hub.state;

                // Look for gbsHub
                if ($.connection.gbsHub) {
                    results.hub_exists = true;
                    results.hub_name = 'gbsHub';

                    // Get all client methods
                    const hub = $.connection.gbsHub;
                    if (hub.client) {
                        results.events = Object.keys(hub.client);
                    }
                }
            }

            return results;
        }""")

        print(f"   SignalR exists: {hub_info['signalr_exists']}")
        print(f"   Hub exists: {hub_info['hub_exists']}")
        print(f"   Hub name: {hub_info['hub_name']}")
        print(f"   Connection state: {hub_info['connection_state']}")

        if hub_info['events']:
            print(f"\n   Found {len(hub_info['events'])} client methods:")
            for event in hub_info['events']:
                print(f"      - {event}")

        print("\n7. Keeping browser open for manual inspection...")
        print("   Press Ctrl+C when done inspecting...")

        try:
            await asyncio.sleep(300)  # Wait 5 minutes for manual inspection
        except KeyboardInterrupt:
            print("\n   User interrupted - closing browser...")

        await browser.close()

    # Analyze collected data
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)

    if hub_info['events']:
        print("\nDiscovered SignalR Client Events:")
        for event in sorted(hub_info['events']):
            print(f"  - {event}")

        print("\n" + "=" * 70)
        print("PYTHON CODE TO ADD TO SCRAPER")
        print("=" * 70)
        print()
        for event in sorted(hub_info['events']):
            print(f'self.signalr_connection.on("{event}", self._on_{event})')

        # Save results
        output_file = Path("output/signalr_events_discovered.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "discovered_at": "2025-11-13",
            "source": "overtime.ag",
            "method": "browser_evaluation",
            "hub_name": hub_info['hub_name'],
            "connection_state": hub_info['connection_state'],
            "total_events": len(hub_info['events']),
            "events": sorted(hub_info['events']),
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--with-login":
        asyncio.run(discover_with_login())
    else:
        print("Usage:")
        print("  Basic discovery:  uv run python scripts/dev/discover_signalr_events.py")
        print("  With login:       uv run python scripts/dev/discover_signalr_events.py --with-login")
        print()
        asyncio.run(discover_with_login())
