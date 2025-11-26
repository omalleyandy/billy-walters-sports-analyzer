"""
Debug stats extraction to see what rows actually contain.

Load game page and inspect table row contents directly.

Usage:
    uv run python scripts/dev/debug_stats_extraction.py
"""

import asyncio
import logging
from pathlib import Path

from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def debug_stats_extraction():
    """Debug what's in the stats table rows."""
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

            logger.info("Clicking PACKERS button to ensure stats are visible")
            await page.click("button:has-text('PACKERS')")
            await asyncio.sleep(2)

            logger.info("\n[1] Checking for all table rows:")
            rows = await page.locator("tr").all()
            logger.info(f"Found {len(rows)} total table rows\n")

            logger.info("[2] Extracting first 20 rows to understand structure:")
            for idx, row in enumerate(rows[:20]):
                cells = await row.locator("th, td").all()
                cell_texts = []
                for cell in cells:
                    try:
                        text = await cell.text_content(timeout=1000)
                        cell_texts.append(text.strip() if text else "[EMPTY]")
                    except Exception:
                        cell_texts.append("[ERROR]")

                # Print first 3 cells of each row
                preview = " | ".join(cell_texts[:3])
                logger.info(f"  Row {idx:2d}: {preview}")

            logger.info("\n[3] Looking for category headers:")
            # Search for rows that might contain category information
            for idx, row in enumerate(rows):
                cells = await row.locator("th, td").all()
                if cells:
                    first_text = (
                        (await cells[0].text_content()).upper().strip() if cells else ""
                    )
                    if any(
                        cat in first_text
                        for cat in [
                            "PASSING",
                            "RUSHING",
                            "RECEIVING",
                            "DEFENSE",
                            "SPECIAL",
                        ]
                    ):
                        # Found a category
                        cell_texts = []
                        for cell in cells[:5]:
                            try:
                                text = await cell.text_content(timeout=1000)
                                cell_texts.append(text.strip() if text else "")
                            except Exception:
                                pass
                        logger.info(f"  Row {idx}: {' | '.join(cell_texts)}")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_stats_extraction())
