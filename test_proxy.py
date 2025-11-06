#!/usr/bin/env python3
"""
Quick proxy test script to diagnose connection issues.

Usage:
    uv run python test_proxy.py
"""

import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()


async def test_proxy():
    """Test proxy connection and response time"""
    proxy_url = os.getenv("PROXY_URL") or os.getenv("OVERTIME_PROXY")

    print("=" * 60)
    print("PROXY CONNECTION TEST")
    print("=" * 60)

    if not proxy_url:
        print("❌ No proxy configured in .env file")
        print("   Set PROXY_URL in .env to test proxy")
        return

    proxy_display = proxy_url.split('@')[1] if '@' in proxy_url else proxy_url
    print(f"\n🔗 Testing proxy: {proxy_display}")

    async with async_playwright() as p:
        print("\n1️⃣ Launching browser with proxy...")
        try:
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": proxy_url}
            )
            print("   ✓ Browser launched")
        except Exception as e:
            print(f"   ❌ Failed to launch browser: {e}")
            return

        try:
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
            )
            page = await context.new_page()

            # Test 1: IP check
            print("\n2️⃣ Checking proxy IP...")
            try:
                await page.goto("https://ipinfo.io/json", timeout=30000)
                ip_info = await page.evaluate("""
                    () => {
                        try {
                            const pre = document.querySelector('pre');
                            if (pre) {
                                return JSON.parse(pre.innerText);
                            }
                        } catch (e) {
                            return null;
                        }
                        return null;
                    }
                """)

                if ip_info:
                    print(f"   ✓ Proxy IP: {ip_info.get('ip')}")
                    print(f"   ✓ Location: {ip_info.get('city')}, {ip_info.get('region')}, {ip_info.get('country')}")
                    print(f"   ✓ ISP: {ip_info.get('org', 'Unknown')}")
                else:
                    print("   ⚠ Could not parse IP info")
            except Exception as e:
                print(f"   ❌ IP check failed: {e}")

            # Test 2: Load overtime.ag
            print("\n3️⃣ Testing overtime.ag access...")
            try:
                import time
                start = time.time()
                await page.goto("https://overtime.ag/sports#/", timeout=120000)
                load_time = time.time() - start

                print(f"   ✓ Page loaded in {load_time:.1f}s")

                # Wait for content
                await page.wait_for_timeout(2000)

                # Check for Cloudflare
                title = await page.title()
                print(f"   ✓ Page title: {title}")

                # Check if blocked
                content = await page.content()
                if "cloudflare" in content.lower() and "challenge" in content.lower():
                    print("   ⚠ Cloudflare challenge detected")
                elif "access denied" in content.lower():
                    print("   ❌ Access denied detected")
                else:
                    print("   ✓ No blocking detected")

                # Save screenshot
                await page.screenshot(path="proxy_test.png")
                print("   ✓ Screenshot saved: proxy_test.png")

            except Exception as e:
                print(f"   ❌ overtime.ag test failed: {e}")

        finally:
            await browser.close()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_proxy())
