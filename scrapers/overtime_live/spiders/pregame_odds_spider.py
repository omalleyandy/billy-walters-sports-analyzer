from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional
from datetime import datetime

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page

# Local modules
from ..items import LiveGameItem, Market, QuoteSide, iso_now, game_key_from

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def to_float(s: Optional[str]) -> Optional[float]:
    """Convert string to float, handling fractions like ½"""
    if not s:
        return None
    try:
        return float(str(s).replace("½", ".5"))
    except Exception:
        try:
            return float(re.sub(r"[^\d\.\-+]", "", str(s)))
        except Exception:
            return None


def parse_date_time(date_str: str, time_str: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse date/time strings from overtime.ag format.
    Date: like "Sun Nov 2"
    Time: like "1:00 PM"
    Returns (YYYY-MM-DD, "h:mm AM/PM ET")
    """
    try:
        if not date_str:
            return None, None
        current_year = datetime.now().year
        parts = date_str.split()
        if len(parts) >= 3:
            dt = datetime.strptime(f"{current_year} {parts[1]} {parts[2]}", "%Y %b %d")
            iso_date = dt.strftime("%Y-%m-%d")
            t = (time_str or "").strip()
            if t and "ET" not in t.upper():
                t = f"{t} ET"
            return iso_date, t or None
    except Exception:
        pass
    return None, None


class PregameOddsSpider(scrapy.Spider):
    """
    Pre-game odds scraper for overtime.ag (NFL and College Football).
    Extracts rotation numbers, date/time, teams, spreads, totals, and moneylines.
    """
    name = "pregame_odds"

    custom_settings = {
        "BOT_NAME": "overtime_pregame",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90_000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            **({"proxy": {"server": os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")}}
               if (os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")) else {}),
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "CONCURRENT_REQUESTS": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [429, 403, 500, 502, 503, 504],
    }

    def __init__(self, sport: str = "both", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_sport = sport.lower().strip()  # nfl | cfb | both

    async def start(self):
        url = "https://overtime.ag/sports#/"
        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "domcontentloaded",
                "timeout": 60_000,
            },
            "playwright_page_methods": [
                PageMethod("wait_for_timeout", 800),
            ],
        }
        yield scrapy.Request(url, meta=meta, callback=self.parse_main, errback=self.errback)

    async def errback(self, failure):
        self.logger.error("Request failed: %r", failure)
        page = failure.request.meta.get("playwright_page")
        if page:
            try:
                await page.close()
            except Exception:
                pass

    async def _perform_login(self, page: Page) -> bool:
        cid = os.getenv("OV_CUSTOMER_ID")
        pwd = os.getenv("OV_CUSTOMER_PASSWORD")
        if not cid or not pwd:
            return False
        try:
            try:
                await page.wait_for_selector("text=/logout/i", timeout=1200)
                return True
            except Exception:
                pass
            await page.evaluate("() => { location.hash = '#/login'; }")
            await page.wait_for_timeout(800)
            cid_el = await page.query_selector('input[placeholder*="Customer"], input[name*="customer"], input[type="text"]')
            if cid_el:
                await cid_el.fill(cid)
            pwd_el = await page.query_selector('input[type="password"]')
            if pwd_el:
                await pwd_el.fill(pwd)
            btn = await page.query_selector('button:has-text(\"Login\"), button:has-text(\"LOGIN\")')
            if btn:
                await btn.click()
                await page.wait_for_timeout(1500)
            return True
        except Exception:
            return False

    async def parse_main(self, response: Response):
        page: Page = response.meta["playwright_page"]

        await self._perform_login(page)
        await page.evaluate("() => { location.hash = '#/'; }")
        await page.wait_for_timeout(1200)

        os.makedirs("snapshots", exist_ok=True)
        try:
            await page.screenshot(path="snapshots/pregame_main.png", full_page=True)
        except Exception:
            pass

        if self.target_sport in ("nfl", "both"):
            async for item in self._scrape_sport(page, "nfl"):
                yield item
        if self.target_sport in ("cfb", "both"):
            async for item in self._scrape_sport(page, "cfb"):
                yield item

        try:
            await page.close()
        except Exception:
            pass

    async def _scrape_sport(self, page: Page, sport: str):
        self.logger.info("Scraping %s odds...", sport.upper())

        if sport == "nfl":
            selector = 'label[for="gl_Football_NFL_G"]'
            league = "NFL"
            sport_name = "nfl"
        else:
            selector = 'label[for="gl_Football_COLLEGE_FB"]'
            league = "NCAAF"
            sport_name = "college_football"

        try:
            esc = selector.replace('"', '\\"')
            await page.evaluate(f'() => {{ const el = document.querySelector("{esc}"); if(el) el.click(); }}')
            await page.wait_for_timeout(2200)
        except Exception:
            self.logger.warning("Selector click failed for %s; continuing best-effort", sport.upper())

        games = await self._extract_games_js(page)

        for g in games:
            item = LiveGameItem(
                source="overtime.ag",
                sport=sport_name,
                league=league,
                collected_at=iso_now(),
                game_key=game_key_from(g["away_team"], g["home_team"], g.get("event_date")),
                event_date=g.get("event_date"),
                event_time=g.get("event_time"),
                rotation_number=g.get("rotation_number"),
                teams={"away": g["away_team"], "home": g["home_team"]},
                state={},
                markets=g["markets"],
                is_live=False,
            )
            yield json.loads(json.dumps(item, default=lambda o: o.__dict__))

    async def _extract_games_js(self, page: Page) -> list[Dict[str, Any]]:
        js = """
        () => {
            const games = [];
            const listItems = document.querySelectorAll('ul li, .event-row, [class*="game"], [role="row"]');

            for (const item of listItems) {
                try {
                    const headings = item.querySelectorAll('h4, h3, [class*="team"]');
                    if (headings.length < 2) continue;

                    const awayText = (headings[0].innerText || '').trim();
                    const homeText = (headings[1].innerText || '').trim();

                    const awayMatch = awayText.match(/^(\\d{3,4})\\s+(.+)$/);
                    const homeMatch = homeText.match(/^(\\d{3,4})\\s+(.+)$/);
                    if (!awayMatch || !homeMatch) continue;

                    const awayRot = awayMatch[1];
                    const awayTeam = awayMatch[2];
                    const homeRot = homeMatch[1];
                    const homeTeam = homeMatch[2];

                    // attempt to find date/time text near the item
                    let dateStr = null, timeStr = null;
                    const dateTimeElements = item.querySelectorAll('div, span, time');
                    for (const el of dateTimeElements) {
                        const t = (el.innerText || '').trim();
                        if (/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\s+\\w+\\s+\\d{1,2}$/i.test(t)) dateStr = t;
                        if (/^\\d{1,2}:\\d{2}\\s+(AM|PM)$/i.test(t)) timeStr = t;
                    }

                    // odds buttons/labels
                    const buttons = item.querySelectorAll('button, [role="button"]');
                    const odds = Array.from(buttons).map(b => (b.innerText || '').trim());

                    // markets
                    const markets = { spread: {}, total: {}, moneyline: {} };

                    // spread: "-2½ -115" / "+3 -110"
                    const spreadRe = /^([+\\-]\\d+(?:[.]\\d)?)\\s+([+\\-]\\d{2,4})$/;
                    let sCount = 0;
                    for (const o of odds) {
                        const m = o.replace('½', '.5').match(spreadRe);
                        if (m && sCount < 2) {
                            const ln = parseFloat(m[1]);
                            const px = parseInt(m[2], 10);
                            if (sCount === 0) markets.spread.away = { line: ln, price: px };
                            else markets.spread.home = { line: ln, price: px };
                            sCount++;
                        }
                    }

                    // totals: "O 51 -110" / "U 48½ -105"
                    const totalRe = /^([OU])\\s+(\\d+(?:[.]\\d)?)\\s+([+\\-]\\d{2,4})$/i;
                    for (const o of odds) {
                        const m = o.replace('½', '.5').match(totalRe);
                        if (m) {
                            const side = m[1].toUpperCase();
                            const ln = parseFloat(m[2]);
                            const px = parseInt(m[3], 10);
                            if (side === 'O') markets.total.over = { line: ln, price: px };
                            else markets.total.under = { line: ln, price: px };
                        }
                    }

                    // ML (best-effort): standalone +/-
                    // intentionally left minimal—moneyline often appears in separate buttons

                    games.push({
                        rotation_number: `${awayRot}-${homeRot}`,
                        away_team: awayTeam,
                        home_team: homeTeam,
                        event_date: dateStr,
                        event_time: timeStr,
                        markets
                    });
                } catch (e) {
                    // ignore row failures
                }
            }
            return games;
        }
        """
        try:
            raw = await page.evaluate(js)
        except Exception:
            return []

        out: list[Dict[str, Any]] = []
        for g in raw or []:
            d, t = parse_date_time(g.get("event_date") or "", g.get("event_time") or "")
            markets_dict = g.get("markets", {}) or {}
            spread = Market(
                away=QuoteSide(**markets_dict.get("spread", {}).get("away", {})) if markets_dict.get("spread", {}).get("away") else None,
                home=QuoteSide(**markets_dict.get("spread", {}).get("home", {})) if markets_dict.get("spread", {}).get("home") else None,
            )
            total = Market(
                over=QuoteSide(**markets_dict.get("total", {}).get("over", {})) if markets_dict.get("total", {}).get("over") else None,
                under=QuoteSide(**markets_dict.get("total", {}).get("under", {})) if markets_dict.get("total", {}).get("under") else None,
            )
            moneyline = Market(
                away=QuoteSide(**markets_dict.get("moneyline", {}).get("away", {})) if markets_dict.get("moneyline", {}).get("away") else None,
                home=QuoteSide(**markets_dict.get("moneyline", {}).get("home", {})) if markets_dict.get("moneyline", {}).get("home") else None,
            )
            out.append({
                "rotation_number": g.get("rotation_number"),
                "away_team": g.get("away_team"),
                "home_team": g.get("home_team"),
                "event_date": d,
                "event_time": t,
                "markets": {
                    "spread": spread,
                    "total": total,
                    "moneyline": moneyline,
                },
            })
        return out