from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, List

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page, Frame, ElementHandle, TimeoutError as PWTimeout

# Local modules
from ..items import LiveGameItem, Market, QuoteSide, iso_now, game_key_from

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


def to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    try:
        return float(s.replace("½", ".5"))
    except Exception:
        try:
            return float(re.sub(r"[^\d\.\-+]", "", s))
        except Exception:
            return None


def _prices_from_text(text: str) -> list[int]:
    return [int(x) for x in re.findall(r"(?<![ou])\b([+\-]\d{2,4})\b", text)]


def _looks_like_event_block(txt: str) -> bool:
    if not txt:
        return False
    lines = [l for l in txt.splitlines() if l.strip()]
    text_lines = [l for l in lines if re.search(r"[A-Za-z]", l)]
    if len(text_lines) < 2:
        return False
    has_price = bool(re.search(r"(?<![ou])\b[+\-]\d{2,4}\b", txt))
    has_spread = bool(re.search(r"\b[+\-]\d{1,2}(?:\.\d)?\b", txt))
    has_total = bool(re.search(r"\b[ou]\s*\d{1,2}(?:\.\d)?\b", txt, flags=re.I))
    return has_price or has_spread or has_total


class OvertimeLiveSpider(scrapy.Spider):
    """
    Live odds scraper for overtime.ag (focus: NCAAF).
    Strategy:
      1) Try site JSON APIs (Offering.asmx) via page.evaluate -> robust & fast.
      2) Fallback to DOM/iframe parsing with best-effort sport selection.
    """

    name = "overtime_live"

    custom_settings = {
        "BOT_NAME": "overtime_live",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90_000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            # "proxy": {"server": os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")}
        },
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "CONCURRENT_REQUESTS": 2,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
    }

    # -------- Scrapy async entry --------
    async def start(self):
        live = os.getenv("OVERTIME_LIVE_URL") or "https://overtime.ag/sports#/integrations/liveBetting"
        start = os.getenv("OVERTIME_START_URL") or "https://overtime.ag/sports"

        target_url = live or start

        yield scrapy.Request(
            target_url,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded"),
                    PageMethod("wait_for_load_state", "networkidle"),
                ],
            },
            callback=self.parse_board,
        )

    # -------- Helpers --------
    async def _hash_nudge_to_live(self, page: Page):
        try:
            await page.evaluate(
                "() => { const wanted='#/integrations/liveBetting'; if (!location.hash.includes('liveBetting')) { location.hash = wanted; } }"
            )
            await page.wait_for_timeout(800)
        except Exception:
            pass

    async def _find_live_iframe(self, page: Page) -> Optional[Frame]:
        try:
            await page.wait_for_timeout(400)
        except Exception:
            pass

        # Prefer frames with these patterns
        for f in page.frames:
            u = (f.url or "").lower()
            if any(k in u for k in ("live", "digitalsportstech", "ticosports")):
                return f

        # Otherwise pick the largest iframe
        try:
            handles: List[ElementHandle] = await page.query_selector_all("iframe")
            best = None
            area = 0.0
            for el in handles:
                try:
                    box = await el.bounding_box()
                    if box:
                        a = box["width"] * box["height"]
                        if a > area:
                            best, area = el, a
                except Exception:
                    continue
            if best:
                os.makedirs("snapshots", exist_ok=True)
                try:
                    await best.screenshot(path="snapshots/overtime_live_iframe.png")
                except Exception:
                    pass
                f = await best.content_frame()
                if f:
                    return f
        except Exception:
            pass
        return None

    async def _try_click_sport_filters(self, root: Page | Frame):
        """Attempt to click Football -> NCAA/College inside the widget."""
        labels = [
            "FOOTBALL",
            "American Football",
            "Football",
        ]
        comps = [
            "NCAA",
            "College",
            "NCAAF",
            "College Football",
        ]
        # Env overrides
        env_sport = os.getenv("OVERTIME_SPORT")
        env_comp = os.getenv("OVERTIME_COMP")
        if env_sport:
            labels.insert(0, env_sport)
        if env_comp:
            comps.insert(0, env_comp)

        # Try a few common UI text buttons/anchors
        for t in labels:
            for sel in (f"text={t}", f"button:has-text('{t}')", f"a:has-text('{t}')", f"[role='tab']:has-text('{t}')"):
                try:
                    await root.click(sel, timeout=1200)
                    await root.wait_for_timeout(250)
                    break
                except Exception:
                    continue

        for t in comps:
            for sel in (f"text={t}", f"button:has-text('{t}')", f"a:has-text('{t}')", f"[role='tab']:has-text('{t}')"):
                try:
                    await root.click(sel, timeout=1200)
                    await root.wait_for_timeout(350)
                    break
                except Exception:
                    continue

    async def _extract_rows_js(self, root: Page | Frame) -> list[Dict[str, Any]]:
        js = """
        () => {
          const nodes = Array.from(document.querySelectorAll(
            '[class*="event"], [class*="match"], [class*="row"], [role="row"], .market, .fixture, li, tr'
          ));
          const out = [];
          for (const n of nodes) {
            const txt = (n.innerText || '').trim();
            if (!txt) continue;
            out.push({ text: txt.slice(0, 6000) });
          }
          if (!out.length) {
            const bodyTxt = (document.body?.innerText || '').trim();
            if (bodyTxt) out.push({ text: bodyTxt.slice(0, 16000) });
          }
          return out.slice(0, 2000);
        }
        """
        try:
            rows = await root.evaluate(js)
            if isinstance(rows, list):
                return rows
        except Exception:
            pass
        return []

    def _parse_game_block(self, row_text: str) -> Optional[Dict[str, Any]]:
        if not _looks_like_event_block(row_text):
            return None

        all_lines = [l.strip() for l in row_text.splitlines() if l.strip()]
        text_lines = [l for l in all_lines if re.search(r"[A-Za-z]", l)]
        if len(text_lines) < 2:
            return None

        away, home = text_lines[0], text_lines[1]

        toks = re.findall(r"[ou]?\s?[+\-]?\d+\.?\d*|[+\-]\d{2,4}", row_text.replace("½", ".5"))
        spread = Market()
        total = Market()
        money = Market()

        spread_lines = [t for t in toks if re.match(r"^[+\-]\d+(\.\d+)?$", t)]
        total_lines = [t for t in toks if re.match(r"^[ou]\s*[+\-]?\d+(\.\d+)?$", t, flags=re.I)]
        prices = _prices_from_text(row_text)

        def pull_line_price(ll: list[str], pp: list[int]) -> tuple[Optional[float], Optional[int]]:
            line = to_float(ll.pop(0)) if ll else None
            price = pp.pop(0) if pp else None
            return line, price

        if spread_lines:
            a_ln, a_px = pull_line_price(spread_lines, prices)
            h_ln, h_px = pull_line_price(spread_lines, prices)
            spread.away = QuoteSide(a_ln, a_px)
            spread.home = QuoteSide(h_ln, h_px)

        if total_lines:
            def clean(x: str) -> Optional[float]:
                return to_float(x.lstrip("ou").strip())
            o_line = clean(total_lines.pop(0))
            o_px = prices.pop(0) if prices else None
            u_line = clean(total_lines.pop(0)) if total_lines else o_line
            u_px = prices.pop(0) if prices else None
            total.over = QuoteSide(o_line, o_px)
            total.under = QuoteSide(u_line, u_px)

        if prices:
            a_ml = prices.pop(0) if prices else None
            h_ml = prices.pop(0) if prices else None
            money.away = QuoteSide(None, a_ml)
            money.home = QuoteSide(None, h_ml)

        has_any = any([
            getattr(spread, "away", None) or getattr(spread, "home", None),
            getattr(total, "over", None) or getattr(total, "under", None),
            getattr(money, "away", None) or getattr(money, "home", None),
        ])
        if not has_any:
            return None

        return {"away": away, "home": home, "markets": {"spread": spread, "total": total, "moneyline": money}}

    # -------- API path (preferred) --------
    async def _api_pull_events(self, page: Page) -> list[Dict[str, Any]]:
        """
        Use in-page fetch to call site APIs with current cookies.
        Returns a normalized list of {away, home, markets{...}} dicts.
        """
        script = """
        async () => {
          function safeJson(txt) {
            try { return JSON.parse(txt); } catch (e) {
              // some ASP.NET services wrap JSON in a "d" field or as a stringified JSON
              try { const obj = JSON.parse(txt); if (obj && obj.d) {
                  try { return JSON.parse(obj.d); } catch (e2) { return obj.d; }
              } } catch(e3) {}
              return null;
            }
          }
          async function post(path, body) {
            const res = await fetch(path, {
              method: 'POST',
              headers: {'content-type':'application/json; charset=UTF-8'},
              body: JSON.stringify(body || {})
            });
            const t = await res.text();
            return safeJson(t) ?? {};
          }

          const sports = await post('/sports/Api/Offering.asmx/GetSports', {});
          let sportId = null;
          const names = ['American Football','Football','FOOTBALL','US Football'];
          function norm(x){return String(x||'').toLowerCase();}
          const list = sports?.Sports || sports?.Result?.Sports || sports || [];
          for (const s of list) {
            const nm = norm(s.Name || s.name || s.description);
            if (names.some(n => nm.includes(n.toLowerCase()))) { sportId = s.Id || s.id; break; }
          }
          if (!sportId && list.length && list[0].Id) { sportId = list[0].Id; }

          if (!sportId) return {events: []};

          const offering = await post('/sports/Api/Offering.asmx/GetSportOffering', { SportId: sportId, LangId: 'ENG' });

          // Try to collect live competitions/events
          const comps = offering?.Competitions
                        || offering?.Result?.Competitions
                        || offering?.competitions
                        || [];
          const out = [];
          for (const c of comps) {
            const evs = c.Events || c.events || [];
            for (const ev of evs) {
              // participants / teams
              const parts = ev.Participants || ev.participants || ev.teams || [];
              let away = null, home = null;
              for (const p of parts) {
                const role = (p.Role || p.role || p.side || '').toLowerCase();
                const nm = p.Name || p.name || p.team || '';
                if (!away and (role.includes('away') or role=='visitor')) away = nm;
                if (!home and (role.includes('home') or role=='home')) home = nm;
              }
              if (!away or !home) {
                // fallback: first two names
                const names2 = parts.map(p=>p.Name||p.name).filter(Boolean);
                away = away || names2[0] || null;
                home = home || names2[1] || null;
              }

              // markets
              const mkts = ev.Markets || ev.markets || [];
              const marketOut = {spread:{}, total:{}, moneyline:{}};

              function setSide(m, side, line, price){
                if (line===undefined || line===null) line = null;
                if (price===undefined || price===null) price = null;
                m[side] = { line, price };
              }

              for (const m of mkts) {
                const t = String(m.Type || m.type || m.name || '').toLowerCase();
                const sel = m.Selections || m.selections || m.outcomes || [];
                if (t.includes('spread') || t=='ah' || t=='handicap') {
                  // try to map two sides
                  const a = sel.find(x => /(away|visitor|team1)/i.test(x.Name || x.name || '')) || sel[0];
                  const h = sel.find(x => /(home|team2)/i.test(x.Name || x.name || '')) || sel[1];
                  if (a) setSide(marketOut.spread, 'away', a.Points ?? a.line ?? a.hcap ?? null, a.Price ?? a.price ?? null);
                  if (h) setSide(marketOut.spread, 'home', h.Points ?? h.line ?? h.hcap ?? null, h.Price ?? h.price ?? null);
                } else if (t.includes('total') or t.includes('over/under') or t=='ou') {
                  const o = sel.find(x => /over/i.test(x.Name || x.name || '')) || sel[0];
                  const u = sel.find(x => /under/i.test(x.Name || x.name || '')) || sel[1];
                  if (o) setSide(marketOut.total, 'over', o.Points ?? o.total ?? o.line ?? null, o.Price ?? o.price ?? null);
                  if (u) setSide(marketOut.total, 'under', u.Points ?? u.total ?? u.line ?? None);
                } else if (t.includes('money') or t=='ml') {
                  const a = sel.find(x => /(away|visitor|team1)/i.test(x.Name || x.name || '')) || sel[0];
                  const h = sel.find(x => /(home|team2)/i.test(x.Name || x.name || '')) || sel[1];
                  if (a) setSide(marketOut.moneyline, 'away', null, a.Price ?? a.price ?? null);
                  if (h) setSide(marketOut.moneyline, 'home', null, h.Price ?? h.price ?? null);
                }
              }

              out.push({ away, home, markets: marketOut });
            }
          }
          return { events: out };
        }
        """
        try:
            data = await page.evaluate(script)
            events = data.get("events", []) if isinstance(data, dict) else []
            # filter to sane rows
            clean = [e for e in events if e.get("away") and e.get("home")]
            return clean
        except Exception:
            return []

    # -------- Scrapy callback --------
    async def parse_board(self, response: Response):
        page: Page = response.meta["playwright_page"]
        await self._hash_nudge_to_live(page)

        os.makedirs("snapshots", exist_ok=True)
        try:
            await page.screenshot(path="snapshots/overtime_live_initial.png", full_page=True)
        except Exception:
            pass

        emitted = 0

        # 1) Preferred: API pull
        api_events = await self._api_pull_events(page)
        if api_events:
            for ev in api_events:
                away, home = ev["away"], ev["home"]
                mkts = ev.get("markets", {})
                item = LiveGameItem(
                    source="overtime.ag",
                    sport="ncaa_football",
                    league="NCAAF",
                    collected_at=iso_now(),
                    game_key=game_key_from(away, home),
                    event_date=None,
                    teams={"away": away, "home": home},
                    state={},
                    markets=mkts,
                )
                yield json.loads(json.dumps(item, default=lambda o: o.__dict__))
                emitted += 1

        # 2) Fallback: DOM/iframe parse if API yielded nothing
        if emitted == 0:
            frame = await self._find_live_iframe(page)
            root = frame or page

            # try clicking filters to reveal NCAAF
            await self._try_click_sport_filters(root)
            try:
                await root.wait_for_timeout(1200)
            except Exception:
                pass

            rows = await self._extract_rows_js(root)
            for r in rows:
                txt = r.get("text", "")
                if not _looks_like_event_block(txt):
                    continue
                parsed = self._parse_game_block(txt)
                if not parsed:
                    continue

                away, home = parsed["away"], parsed["home"]
                item = LiveGameItem(
                    source="overtime.ag",
                    sport="ncaa_football",
                    league="NCAAF",
                    collected_at=iso_now(),
                    game_key=game_key_from(away, home),
                    event_date=None,
                    teams={"away": away, "home": home},
                    state={},
                    markets=parsed["markets"],
                )
                yield json.loads(json.dumps(item, default=lambda o: o.__dict__))
                emitted += 1

            # dump a text snapshot if still nothing
            if emitted == 0:
                try:
                    txt = await (root.evaluate("() => document.body?.innerText || ''"))
                    with open("snapshots/overtime_live_text.txt", "w", encoding="utf-8") as f:
                        f.write(txt[:120000])
                except Exception:
                    pass

        self.logger.info("Emitted %d college football rows", emitted)

        try:
            await page.close()
        except Exception:
            pass