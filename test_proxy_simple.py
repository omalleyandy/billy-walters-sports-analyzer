#!/usr/bin/env python3
"""
Simple proxy test using requests library (faster than Playwright)
This helps isolate whether the issue is proxy or browser-specific.

Usage:
    uv run python test_proxy_simple.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_proxy_simple():
    """Test proxy with simple HTTP requests (no browser)"""
    print("=" * 60)
    print("SIMPLE PROXY TEST (requests library)")
    print("=" * 60)

    # Get proxy from environment
    proxy_url = os.getenv("PROXY_URL") or os.getenv("OVERTIME_PROXY")

    if not proxy_url:
        print("\n❌ No proxy configured in .env file")
        print("   Set PROXY_URL in .env to test proxy")
        return

    # Parse proxy URL
    proxy_display = proxy_url.split('@')[1] if '@' in proxy_url else proxy_url
    print(f"\n🔗 Testing proxy: {proxy_display}")

    # Configure proxies for requests
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    # Test 1: IP check
    print("\n1️⃣ Testing IP verification...")
    try:
        response = requests.get(
            "http://ip-api.com/json",
            proxies=proxies,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Proxy IP: {data.get('query')}")
            print(f"   ✓ Location: {data.get('city')}, {data.get('regionName')}, {data.get('country')}")
            print(f"   ✓ ISP: {data.get('isp')}")
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ IP check failed: {e}")

    # Test 2: Alternative IP check
    print("\n2️⃣ Testing with ipinfo.io...")
    try:
        response = requests.get(
            "https://ipinfo.io/json",
            proxies=proxies,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Proxy IP: {data.get('ip')}")
            print(f"   ✓ Location: {data.get('city')}, {data.get('region')}, {data.get('country')}")
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 3: Test overtime.ag access
    print("\n3️⃣ Testing overtime.ag access (HTTP only)...")
    try:
        import time
        start = time.time()
        response = requests.get(
            "https://overtime.ag/sports/",
            proxies=proxies,
            timeout=60,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }
        )
        load_time = time.time() - start

        if response.status_code == 200:
            print(f"   ✓ Page loaded in {load_time:.1f}s (HTTP {response.status_code})")
            print(f"   ✓ Content length: {len(response.content)} bytes")

            # Check for blocks
            content = response.text.lower()
            if "cloudflare" in content and "challenge" in content:
                print("   ⚠️ Cloudflare challenge detected")
            elif "access denied" in content:
                print("   ❌ Access denied detected")
            else:
                print("   ✓ No obvious blocking detected")
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ overtime.ag test failed: {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nℹ️  If this test passes but Playwright fails:")
    print("   - Playwright/browser is being blocked by Cloudflare")
    print("   - Try running: uv run python test_proxy.py")
    print("   - Compare results to see if it's a browser issue")


if __name__ == "__main__":
    test_proxy_simple()
