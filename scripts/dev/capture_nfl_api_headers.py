"""
Capture NFL.com API Request Headers

Uses Playwright to load NFL.com schedule page and capture the exact
HTTP headers used when requesting the weekly-game-details API.
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def capture_headers():
    """Capture headers from NFL API requests"""
    captured_requests = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Capture all API requests
        async def handle_request(route, request):
            if "api.nfl.com" in request.url and "weekly-game-details" in request.url:
                print(f"\n{'=' * 70}")
                print("Found API Request!")
                print(f"{'=' * 70}")
                print(f"URL: {request.url}")
                print("\nHeaders:")
                for key, value in request.headers.items():
                    print(f"  {key}: {value}")

                captured_requests.append(
                    {
                        "url": request.url,
                        "headers": request.headers,
                        "method": request.method,
                    }
                )

            # Continue the request
            await route.continue_()

        # Intercept requests
        await page.route("**/*", handle_request)

        # Navigate to schedule page
        print("\nNavigating to NFL.com schedule...")
        await page.goto(
            "https://www.nfl.com/schedules/2025/REG12", wait_until="networkidle"
        )

        # Wait a bit for API calls to complete
        await asyncio.sleep(5)

        await browser.close()

    # Save captured requests
    if captured_requests:
        output_file = "nfl_api_headers.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(captured_requests, f, indent=2)
        print(f"\n{'=' * 70}")
        print(f"Saved {len(captured_requests)} requests to {output_file}")
        print(f"{'=' * 70}")
    else:
        print("\nNo API requests captured. The endpoint may load via JavaScript.")
        print("Try manually refreshing the page after it loads.")

    return captured_requests


if __name__ == "__main__":
    asyncio.run(capture_headers())
