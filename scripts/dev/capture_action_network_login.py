#!/usr/bin/env python
"""
Capture Action Network login steps manually.

Opens a visible browser, navigates to login, and pauses for manual interaction.
After you login manually, press 'Resume' in the Playwright Inspector to continue.
The script will then capture the current page state including cookies and selectors.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


async def main():
    """Open browser and capture login steps."""
    output_dir = Path("output/debug")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("ACTION NETWORK LOGIN CAPTURE")
    print("=" * 70)
    print("\nThis tool will:")
    print("  1. Open a visible browser window")
    print("  2. Navigate to Action Network login page")
    print("  3. PAUSE so you can log in manually")
    print("  4. Capture cookies and page state after you resume")
    print("\nInstructions:")
    print("  - A Playwright Inspector window will open")
    print("  - Log in to Action Network in the browser window")
    print("  - After successful login, click 'Resume' in the Inspector")
    print("  - The script will capture your session data")
    print("=" * 70 + "\n")

    async with async_playwright() as p:
        # Launch visible browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("[*] Navigating to Action Network login...")
        try:
            # Use domcontentloaded instead of networkidle for faster load
            await page.goto(
                "https://www.actionnetwork.com/login",
                wait_until="domcontentloaded",
                timeout=60000
            )
        except Exception as e:
            print(f"[!] Initial navigation warning: {e}")
            print("[*] Continuing anyway - page may still be loading...")

        print("\n" + "=" * 70)
        print("BROWSER IS OPEN - LOG IN MANUALLY NOW")
        print("=" * 70)
        print("\nSteps:")
        print("  1. In the browser window, enter your credentials and log in")
        print("  2. Wait until you see the logged-in state (account icon, etc)")
        print("  3. Click 'Resume' (green play button) in the Playwright Inspector")
        print("=" * 70 + "\n")

        # Pause for manual login
        await page.pause()

        print("\n[*] Resuming after manual login...")
        print("[*] Capturing session state...\n")

        # Capture current URL
        current_url = page.url
        print(f"Current URL: {current_url}")

        # Capture cookies
        cookies = await context.cookies()

        # Check for login indicators
        login_indicators = {
            "email_input": await page.query_selector('input[placeholder="Email"]'),
            "account_link": await page.query_selector('a[href*="/account"]'),
            "profile_link": await page.query_selector('a[href*="/profile"]'),
            "logout_button": await page.query_selector('button:has-text("Log out")'),
            "user_avatar": await page.query_selector('img[alt*="avatar"]'),
        }

        logged_in = any([
            login_indicators["account_link"],
            login_indicators["profile_link"],
            login_indicators["logout_button"],
            login_indicators["user_avatar"],
        ]) and not login_indicators["email_input"]

        print(f"\nLogin detected: {logged_in}")
        print("\nLogin indicators found:")
        for name, element in login_indicators.items():
            status = "[OK]" if (element if name != "email_input" else not element) else "[ ]"
            print(f"  {status} {name}: {'found' if element else 'not found'}")

        # Capture visible elements for debugging
        print("\n[*] Capturing page elements for selector debugging...")

        # Get all buttons
        buttons = await page.query_selector_all("button")
        print(f"\nFound {len(buttons)} buttons:")
        for i, btn in enumerate(buttons[:10]):  # First 10
            text = await btn.inner_text()
            classes = await btn.get_attribute("class") or ""
            if text.strip():
                print(f"  {i+1}. '{text.strip()[:40]}' class='{classes[:50]}'")

        # Get all links
        links = await page.query_selector_all("a[href]")
        print(f"\nFound {len(links)} links, checking for account-related:")
        for link in links:
            href = await link.get_attribute("href") or ""
            if any(x in href.lower() for x in ["account", "profile", "user", "settings", "logout"]):
                text = await link.inner_text()
                print(f"  - '{text.strip()[:30]}' -> {href}")

        # Save session data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = output_dir / f"action_network_session_{timestamp}.json"

        session_data = {
            "timestamp": datetime.now().isoformat(),
            "current_url": current_url,
            "logged_in": logged_in,
            "cookies": [
                {
                    "name": c["name"],
                    "domain": c["domain"],
                    "secure": c.get("secure", False),
                    "httpOnly": c.get("httpOnly", False),
                }
                for c in cookies
            ],
            "login_indicators": {k: bool(v) for k, v in login_indicators.items()},
        }

        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        print(f"\n[OK] Session data saved to: {session_file}")
        print(f"[*] Found {len(cookies)} cookies")

        # Take screenshot
        screenshot_file = output_dir / f"action_network_state_{timestamp}.png"
        await page.screenshot(path=str(screenshot_file))
        print(f"[OK] Screenshot saved to: {screenshot_file}")

        # Give time to review
        print("\n[*] Browser will close in 5 seconds...")
        await asyncio.sleep(5)

        await browser.close()

        print("\n" + "=" * 70)
        print("CAPTURE COMPLETE")
        print("=" * 70)
        if logged_in:
            print("[OK] Login appears successful!")
            print("\nNext steps:")
            print("  1. Review the captured session data")
            print("  2. Check if we need to update selectors")
            print("  3. Run the scraper again")
        else:
            print("[!] Login may have failed or selectors need updating")
            print("\nCheck the screenshot and session JSON for clues")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
