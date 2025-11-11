"""
Overtime.ag Live Plus Scraper - Get in-play NFL odds

This scraper accesses the Live Plus section for live game betting.
Based on the working pregame scraper pattern.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv('.env', override=True)

async def scrape_live_plus():
    """Scrape live/in-play odds from Overtime.ag Live Plus section"""

    print("=" * 70)
    print("Overtime.ag Live Plus NFL Odds Scraper")
    print("=" * 70)
    print()

    customer_id = os.getenv('OV_CUSTOMER_ID')
    password = os.getenv('OV_PASSWORD')

    if not customer_id or not password:
        print("[ERROR] Missing OV_CUSTOMER_ID or OV_PASSWORD in .env")
        return None

    output_dir = Path("output/overtime/nfl/live")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # Launch browser (headless=False to see what's happening)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # 1. Navigate to Overtime (use hash URL like pregame scraper)
            print("1. Navigating to Overtime.ag...")
            await page.goto('https://overtime.ag/sports#/', wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)

            # 2. Login (use exact same flow as pregame scraper)
            print("2. Logging in...")
            try:
                # Wait for LOGIN button (attached, not necessarily visible)
                await page.wait_for_selector('a.btn-signup', state='attached', timeout=10000)

                # Click LOGIN button using JavaScript (bypasses visibility checks)
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

                if not login_clicked:
                    print("   LOGIN button not found")
                    return None

                await asyncio.sleep(2)

                # Fill customer ID (use placeholder selector like pregame)
                customer_input = await page.query_selector('input[placeholder*="Customer"]')
                if customer_input:
                    await customer_input.fill(customer_id)
                else:
                    print("   Customer ID input not found")
                    return None

                # Fill password (use type selector like pregame)
                password_input = await page.query_selector('input[type="password"]')
                if password_input:
                    await password_input.fill(password)
                else:
                    print("   Password input not found")
                    return None

                # Click login button (look for "LOGIN" text like pregame)
                login_btn = await page.query_selector('button:has-text("LOGIN")')
                if login_btn:
                    await login_btn.click()
                    await asyncio.sleep(5)  # Wait for security checks
                    print("   Login successful!")
                else:
                    print("   Login button not found")
                    return None

            except Exception as e:
                print(f"   Login failed: {e}")
                import traceback
                traceback.print_exc()
                return None

            # 3. Get account info
            print("3. Extracting account information...")
            try:
                balance_elem = await page.query_selector('[href*="dailyFigures"]')
                if balance_elem:
                    balance = await balance_elem.inner_text()
                    print(f"   Balance: {balance}")

                available_elem = await page.query_selector('[href*="openBets"]')
                if available_elem:
                    available = await available_elem.inner_text()
                    print(f"   Available: {available}")
            except:
                pass

            # 4. Navigate to Live Plus
            print("4. Navigating to Live Plus section...")

            # Try multiple selectors for Live Plus
            live_plus_selectors = [
                'a:has-text("LIVE PLUS")',
                '[href*="live"]',
                'text=LIVE PLUS'
            ]

            live_plus_found = False
            for selector in live_plus_selectors:
                try:
                    elem = page.locator(selector).first
                    if await elem.count() > 0:
                        await elem.click()
                        await asyncio.sleep(3)
                        live_plus_found = True
                        print("   Navigated to Live Plus")
                        break
                except:
                    continue

            if not live_plus_found:
                print("   [WARNING] Could not find Live Plus link")
                print("   Trying direct URL...")
                await page.goto('https://overtime.ag/sports#/integrations/liveBetting',
                              wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(5)

            # 5. Extract live games from iframe
            print("5. Extracting live game data...")

            games = []

            # Check for iframes (Live Plus uses iframe)
            frames = page.frames
            print(f"   Found {len(frames)} frames on page")

            # Try to find the live betting frame
            live_frame = None
            for frame in frames:
                try:
                    url = frame.url
                    if 'live' in url.lower() or 'bet' in url.lower():
                        print(f"   Found potential live frame: {url[:80]}...")
                        live_frame = frame
                        break
                except:
                    continue

            if live_frame:
                print("   Extracting from live frame...")

                # Wait for content to load
                await asyncio.sleep(3)

                # Try to extract game data from the frame
                try:
                    # Get all text content
                    content = await live_frame.content()

                    # Look for common betting patterns
                    # Team names, spreads, totals, moneylines
                    lines = content.split('\n')

                    # Try to find structured data (JSON)
                    if '{' in content and '}' in content:
                        # Look for JSON data
                        import re
                        json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
                        for match in json_matches:
                            try:
                                data = json.loads(match)
                                if isinstance(data, dict) and any(k in data for k in ['game', 'team', 'odds', 'spread', 'total']):
                                    games.append(data)
                            except:
                                pass

                    # Also try to get visible text elements
                    text_elements = await live_frame.query_selector_all('div, span, p')
                    print(f"   Found {len(text_elements)} text elements in frame")

                    # Extract visible text that looks like betting lines
                    visible_lines = []
                    for elem in text_elements[:100]:  # Limit to first 100
                        try:
                            text = await elem.inner_text()
                            if text and len(text.strip()) > 3:
                                # Look for patterns like team names, numbers, odds
                                if any(x in text for x in ['Eagles', 'Packers', 'NFL', '+', '-']):
                                    visible_lines.append(text.strip())
                        except:
                            pass

                    if visible_lines:
                        print()
                        print("   VISIBLE BETTING LINES:")
                        print("   " + "-" * 66)
                        for line in visible_lines[:20]:  # Show first 20
                            print(f"   {line}")

                except Exception as e:
                    print(f"   Error extracting from frame: {e}")
            else:
                print("   [WARNING] No live betting frame found")

                # Try extracting from main page
                print("   Trying to extract from main page...")
                all_text = await page.inner_text('body')

                # Look for "Eagles", "Packers", "PHI", "GB"
                if 'Eagles' in all_text or 'Packers' in all_text or 'PHI' in all_text or 'GB' in all_text:
                    print()
                    print("   FOUND GAME TEXT:")
                    print("   " + "-" * 66)
                    lines = all_text.split('\n')
                    for line in lines:
                        if any(x in line for x in ['Eagles', 'Packers', 'PHI', 'GB', 'Philadelphia', 'Green Bay']):
                            print(f"   {line.strip()}")

            # 6. Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"overtime_nfl_live_{timestamp}.json"

            result = {
                'metadata': {
                    'source': 'overtime.ag/live-plus',
                    'scraped_at': datetime.now().isoformat(),
                    'scraper_version': '1.0.0'
                },
                'games': games,
                'raw_data': {
                    'frames_found': len(frames),
                    'live_frame_found': live_frame is not None
                }
            }

            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            print()
            print("6. Saving results...")
            print(f"   Saved to: {output_file}")

            print()
            print("=" * 70)
            print("SCRAPE COMPLETE")
            print("=" * 70)
            print(f"Games extracted: {len(games)}")

            # Keep browser open for manual inspection
            print()
            print("Browser will stay open for 30 seconds for manual inspection...")
            print("Check the Live Plus section manually if needed.")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

        return games

if __name__ == '__main__':
    asyncio.run(scrape_live_plus())
