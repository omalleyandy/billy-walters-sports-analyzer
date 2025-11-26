"""
Debug NFL.com Game Page Structure

Inspects actual page structure to identify correct selectors for:
- Game title/teams
- Stats tables
- Team tabs

Usage:
    uv run python scripts/dev/debug_nfl_page_structure.py
"""

import asyncio
import json
import logging
from pathlib import Path

from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def debug_nfl_game_page():
    """Inspect structure of NFL.com game stats page."""
    # Game URL that failed in previous run
    game_url = "https://www.nfl.com/games/packers-at-lions-2025-reg-13?tab=stats"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )

        try:
            logger.info(f"Loading {game_url}")
            await page.goto(
                game_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await asyncio.sleep(3)

            logger.info("\n[1] Checking for game title using various selectors:")

            # Try all original selectors
            selectors_to_try = [
                "h1",
                "[data-test='game-title']",
                "div.Game__header h1",
                "[class*='game'] [class*='title']",
                "h2",
                "[class*='Game__title']",
                "[class*='matchup']",
                "div[class*='header']",
                "[class*='game'] h1",
            ]

            for selector in selectors_to_try:
                try:
                    element = page.locator(selector).first
                    text = await element.text_content(timeout=2000)
                    if text and text.strip():
                        logger.info(f"  ✓ FOUND with '{selector}': {text}")
                    else:
                        logger.info(f"  - '{selector}': Empty or not found")
                except Exception as e:
                    logger.info(f"  ✗ '{selector}': {type(e).__name__}")

            logger.info("\n[2] Checking page title/meta tags:")
            title = await page.title()
            logger.info(f"  Page title: {title}")

            # Get page content to search for team names
            content = await page.content()
            if "Packers" in content:
                logger.info("  ✓ Page contains 'Packers'")
            if "Lions" in content:
                logger.info("  ✓ Page contains 'Lions'")

            logger.info("\n[3] Checking for stats tables:")
            table_selectors = [
                "table",
                "[role='table']",
                "[data-test*='stats']",
                "[class*='stats']",
                "tbody tr",
                "[class*='table']",
            ]

            for selector in table_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        logger.info(f"  ✓ Found {len(elements)} with '{selector}'")
                        # Show first row content
                        if selector == "tbody tr" and elements:
                            text = await elements[0].text_content()
                            preview = text[:80] if text else ""
                            logger.info(f"    First row preview: {preview}")
                except Exception as e:
                    logger.info(f"  ✗ '{selector}': {type(e).__name__}")

            logger.info("\n[4] Checking for team tabs/buttons:")
            tab_selectors = [
                "button:has-text('PACKERS')",
                "button:has-text('LIONS')",
                "[data-test*='tab']",
                "[role='tab']",
                "[class*='tab']",
                "button",
            ]

            for selector in tab_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        logger.info(f"  ✓ Found {len(elements)} with '{selector}'")
                        # Show button texts
                        if "button" in selector:
                            for i, elem in enumerate(elements[:3]):
                                text = await elem.text_content()
                                if text and text.strip():
                                    logger.info(f"    Button {i}: {text.strip()}")
                except Exception as e:
                    logger.info(f"  ✗ '{selector}': {type(e).__name__}")

            logger.info("\n[5] DOM Structure Analysis:")
            # Get all h1-h3 elements
            for tag in ["h1", "h2", "h3", "h4"]:
                try:
                    elements = await page.locator(tag).all()
                    if elements:
                        logger.info(f"  Found {len(elements)} <{tag}> elements:")
                        for i, elem in enumerate(elements[:3]):
                            text = await elem.text_content()
                            classes = await elem.get_attribute("class")
                            if text and text.strip():
                                logger.info(
                                    f"    {i}: {text.strip()[:50]} (class: {classes})"
                                )
                except Exception:
                    pass

            logger.info("\n[6] Saving page HTML for inspection:")
            # Save HTML for manual inspection
            html = await page.content()
            output_file = Path("output/debug/game_page_structure.html")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"  Saved to {output_file}")

            logger.info("\n[7] Looking for common element patterns:")
            # Check for elements that might contain game info
            patterns = [
                ("[class*='game'] [class*='score']", "Game score"),
                ("[class*='matchup']", "Matchup info"),
                ("[class*='team']", "Team elements"),
                ("[class*='stats']", "Stats elements"),
            ]

            for selector, description in patterns:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        logger.info(
                            f"  ✓ {description}: Found {len(elements)} "
                            f"elements with '{selector}'"
                        )
                except Exception:
                    pass

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_nfl_game_page())
