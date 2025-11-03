from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page, Frame, ElementHandle

# Local modules
from ..items import LiveGameItem, Market, QuoteSide, iso_now, game_key_from

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


# ---------- helpers & regex ----------

def to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    try:
        return float(str(s).replace("½", ".5"))
    except Exception:
        try:
            return float(re.sub(r"[^\d\.\-+]", "", str(s)))
        except Exception:
            return None


_PRICE_RE = re.compile(r"(?<![ou])\b([+\-]\d{2,4})\b")
_SPREAD_LINE = re.compile(r"^[+\-]\d+(?:[.]\d)?$")
_TOTAL_TOKEN = re.compile(r"^[ou]\s*[+\-]?\d+(?:[.]\d)?$", re.I)

def _prices_from_text(text: str) -> List[int]:
    return [int(x) for x in _PRICE_RE.findall(text)]

def _looks_like_event_block(txt: str) -> bool:
    if not txt:
        return False
    lines = [l for l in txt.splitlines() if l.strip()]
    text_lines = [l for l in lines if re.search(r"[A-Za-z]", l)]
    if len(text_lines) < 2:
        return False
    has_price = bool(_PRICE_RE.search(txt))
    has_spread = bool(re.search(r"\b[+\-]\d{1,2}(?:[.]\d)?\b", txt.replace("½", ".5")))
    has_total = bool(re.search(r"\b[ou]\s*\d{1,2}(?:[.]\d)?\b", txt.replace("½", ".5"), re.I))
    return has_price or has_spread or has_total

_STATE_RE = re.compile(
    r"\b(\d)(?:st|nd|rd|th)?\s*(?:q(?:uarter)?|qtr)?\s+(\d{1,2}:\d{2})\b",
    re.I,
)

def _parse_state(text: str) -> Dict[str, Any]:
    m = _STATE_RE.search(text)
    if not m:
        return {}
    try:
        return {"quarter": int(m.group(1)), "clock": m.group(2)}
    except Exception:
        return {}


class OvertimeLiveSpider(scrapy.Spider):
    """
    Live odds scraper for overtime.ag (focus: NCAAF/NFL).
    Strategy:
      1) Prefer site JSON APIs (Offering.asmx) via page.evaluate.
      2) Fallback to DOM/iframe parsing.
    """
    name = "overtime_live"

    _proxy_server = os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")
    custom_settings = {
        "BOT_NAME": "overtime_live",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90_000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            **({"proxy": {"server": _proxy_server}} if _proxy_server else {}),
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [429, 403, 500, 502, 503, 504],
        "RETRY_BACKOFF_BASE": 2,
        "RETRY_BACKOFF_MAX": 60,
    }

    # -------- Scrapy async entry --------
    async def start(self):
        live = os.getenv("OVERTIME_LIVE_URL") or "https://overtime.ag/sports#/integrations/liveBetting"
        start = os.getenv("OVERTIME_START_URL") or "https://overtime.ag"
        target_url = live or start

        proxy_url = os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")
        context_kwargs = {"proxy": {"server": proxy_url}} if proxy_url else None

        goto_kwargs = {"wait_until": "domcontentloaded", "timeout": 60_000, "referer": "https://overtime.ag/"}

        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": goto_kwargs,
            "playwright_page_methods": [
                PageMethod("wait_for_timeout", 500),
            ],
        }
        if context_kwargs:
            meta["playwright_context_kwargs"] = context_kwargs

        yield scrapy.Request(
            target_url,
            meta=meta,
            callback=self.parse_board,
            errback=self.errback,
        )

    async def errback(self, failure):
        self.logger.error("Request failed: %r", failure)
        page = failure.request.meta.get("playwright_page")
        if page:
            os.makedirs("snapshots", exist_ok=True)
            try:
                await page.screenshot(path="snapshots/error.png", full_page=True)
            except Exception:
                pass
            try:
                await page.close()
            except Exception:
                pass

    # -------- helpers --------
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
            btn = await page.query_selector('button:has-text("Login"), button:has-text("LOGIN")')
            if btn:
                await btn.click()
                await page.wait_for_timeout(1500)
            return True
        except Exception:
            return False

    async def _hash_nudge_to_live(self, page: Page):
        try:
            await page.evaluate(
                "() => { const wanted='#/integrations/liveBetting'; if (!location.hash.includes('liveBetting')) { location.hash = wanted; } }"
            )
            await page.wait_for_timeout(500)
        except Exception:
            pass

    async def _find_live_iframe(self, page: Page) -> Optional[Frame]:
        # Prefer frames by URL hint; else pick the largest
        for f in page.frames:
            u = (f.url or "").lower()
            if any(k in u for k in ("live", "digitalsportstech", "ticosports")):
                return f
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
                f = await best.content_frame()
                if f:
                    return f
        except Exception:
            pass
        return None

    async def _try_click_sport_filters(self, root: Page | Frame):
        labels = ["FOOTBALL", "American Football", "Football"]
        comps = ["NCAA", "College", "NCAAF", "College Football"]
        env_sport = os.getenv("OVERTIME_SPORT")
        env_comp = os.getenv("OVERTIME_COMP")
        if env_sport:
            labels.insert(0, env_sport)
        if env_comp:
            comps.insert(0, env_comp)

        for t in labels:
            for sel in (f"text={t}", f"button:has-text('{t}')", f"a:has-text('{t}')", f"[role='tab']:has-text('{t}')"):
                try:
                    await root.click(sel, timeout=1000)
                    await root.wait_for_timeout(200)
                    break
                except Exception:
                    continue

        for t in comps:
            for sel in (f"text={t}", f"button:has-text('{t}')", f"a:has-text('{t}')", f"[role='tab']:has-text('{t}')"):
                try:
                    await root.click(sel, timeout=1000)
                    await root.wait_for_timeout(250)
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

    # ---------- hardened text parser for a single game block ----------
    def _parse_game_block(self, row_text: str) -> Optional[Dict[str, Any]]:
        if not _looks_like_event_block(row_text):
            return None

        all_lines = [l.strip() for l in row_text.splitlines() if l.strip()]
        text_lines = [l for l in all_lines if re.search(r"[A-Za-z]", l)]
        if len(text_lines) < 2:
            return None

        away, home = text_lines[0], text_lines[1]

        # tokenise odds (normalise half)
        norm = row_text.replace("½", ".5")
        toks = re.findall(r"[ou]?\s?[+\-]?\d+\.?\d*|[+\-]\d{2,4}", norm)

        spread = Market()
        total = Market()
        money = Market()

        spread_tokens = [t for t in toks if _SPREAD_LINE.match(t)]
        total_tokens = [t for t in toks if _TOTAL_TOKEN.match(t)]
        prices = _prices_from_text(norm)

        def pull_line_price(ll: List[str], pp: List[int]) -> tuple[Optional[float], Optional[int]]:
            line = to_float(ll.pop(0)) if ll else None
            price = pp.pop(0) if pp else None
            return line, price

        # spreads (away, home)
        if spread_tokens:
            a_ln, a_px = pull_line_price(spread_tokens, prices)
            h_ln, h_px = pull_line_price(spread_tokens, prices)
            spread.away = QuoteSide(a_ln, a_px)
            spread.home = QuoteSide(h_ln, h_px)

        # totals O/U
        if total_tokens:
            def clean(x: str) -> Optional[float]:
                return to_float(x.lstrip("ou").strip())
            o_line = clean(total_tokens.pop(0))
            o_px = prices.pop(0) if prices else None
            u_line = clean(total_tokens.pop(0)) if total_tokens else o_line
            u_px = prices.pop(0) if prices else None
            total.over = QuoteSide(o_line, o_px)
            total.under = QuoteSide(u_line, u_px)

        # moneyline (next two prices if present)
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

        return {
            "away": away,
            "home": home,
            "markets": {"spread": spread, "total": total, "moneyline": money},
        }

    def _normalize_markets(self, markets: Dict[str, Any]) -> Dict[str, Any]:
        for mkt_name, mkt in markets.items():
            if not isinstance(mkt, dict):
                continue
            for side, quote in mkt.items():
                if not isinstance(quote, dict):
                    continue
                line = quote.get("line")
                price = quote.get("price")
                if line is not None:
                    quote["line"] = to_float(line)
                if price is not None:
                    try:
                        quote["price"] = int(price)
                    except Exception:
                        pass
        return markets

    # -------- API path (preferred) --------
    async def _api_pull_events(self, page: Page) -> list[Dict[str, Any]]:
        script = """
        async () => {
          function safeJson(txt) {
            try { return JSON.parse(txt); } catch (e) {
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
          const candidates = ['American Football','Football','US Football','FOOTBALL'];
          const list = sports?.Sports || sports?.Result?.Sports || sports || [];
          for (const s of list) {
            const nm = String(s.Name || s.name || s.description || '').toLowerCase();
            if (candidates.some(c => nm.includes(c.toLowerCase()))) { sportId = s.Id || s.id; break; }
          }
          if (!sportId && list.length && list[0]?.Id) sportId = list[0].Id;

          if (!sportId) return {events: []};
          const offering = await post('/sports/Api/Offering.asmx/GetSportOffering', { SportId: sportId, LangId: 'ENG' });

          const comps = offering?.Competitions || offering?.Result?.Competitions || offering?.competitions || [];
          const out = [];
          for (const c of comps) {
            const evs = c.Events || c.events || [];
            for (const ev of evs) {
              const parts = ev.Participants || ev.participants || ev.teams || [];
              let away = null, home = null;
              for (const p of parts) {
                const role = String(p.Role || p.role || p.side || '').toLowerCase();
                const nm = p.Name || p.name || p.team || '';
                if (!away && (role.includes('away') || role==='visitor')) away = nm;
                if (!home && (role.includes('home') || role==='home')) home = nm;
              }
              if (!away || !home) {
                const names2 = parts.map(p=>p.Name||p.name).filter(Boolean);
                away = away || names2[0] || null;
                home = home || names2[1] || null;
              }

              const mkts = ev.Markets || ev.markets || [];
              const marketOut = {spread:{}, total:{}, moneyline:{}};
              function setSide(m, side, line, price){
                m[side] = { line: (line ?? null), price: (price ?? null) };
              }
              for (const m of mkts) {
                const t = String(m.Type || m.type || m.name || '').toLowerCase();
                const sel = m.Selections || m.selections || m.outcomes || [];
                if (t.includes('spread') || t==='ah' || t==='handicap') {
                  const a = sel.find(x => /(away|visitor|team1)/i.test(x.Name || x.name || '')) || sel[0];
                  const h = sel.find(x => /(home|team2)/i.test(x.Name || x.name || '')) || sel[1];
                  if (a) setSide(marketOut.spread, 'away', a.Points ?? a.line ?? a.hcap ?? null, a.Price ?? a.price ?? null);
                  if (h) setSide(marketOut.spread, 'home', h.Points ?? h.line ?? h.hcap ?? null, h.Price ?? h.price ?? null);
                } else if (t.includes('total') || t.includes('over/under') || t==='ou') {
                  const o = sel.find(x => /over/i.test(x.Name || x.name || '')) || sel[0];
                  const u = sel.find(x => /under/i.test(x.Name || x.name || '')) || sel[1];
                  if (o) setSide(marketOut.total, 'over', o.Points ?? o.total ?? o.line ?? null, o.Price ?? o.price ?? null);
                  if (u) setSide(marketOut.total, 'under', u.Points ?? u.total ?? u.line ?? null, u.Price ?? u.price ?? null);
                } else if (t.includes('money') || t==='ml') {
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
            clean = [e for e in events if e.get("away") and e.get("home")]
            for ev in clean:
                if isinstance(ev.get("markets"), dict):
                    ev["markets"] = self._normalize_markets(ev["markets"])
            return clean
        except Exception:
            return []

    # -------- Scrapy callback --------
    async def parse_board(self, response: Response):
        page: Page = response.meta["playwright_page"]

        await self._perform_login(page)
        await self._hash_nudge_to_live(page)

        os.makedirs("snapshots", exist_ok=True)
        try:
            await page.screenshot(path="snapshots/overtime_live_initial.png", full_page=True)
        except Exception:
            pass

        emitted = 0

        # 1) API preferred
        api_events = await self._api_pull_events(page)
        if api_events:
            for ev in api_events:
                away, home = ev["away"], ev["home"]
                mkts = ev.get("markets", {})
                item = LiveGameItem(
                    source="overtime.ag",
                    sport="college_football",  # adjust if you split by league
                    league="NCAAF",
                    collected_at=iso_now(),
                    game_key=game_key_from(away, home),
                    event_date=None,
                    event_time=None,
                    rotation_number=None,
                    teams={"away": away, "home": home},
                    state={},
                    markets=mkts,
                    is_live=True,
                )
                yield json.loads(json.dumps(item, default=lambda o: o.__dict__))
                emitted += 1

        # 2) DOM/iframe fallback
        if emitted == 0:
            frame = await self._find_live_iframe(page)
            root = frame or page
            await self._try_click_sport_filters(root)
            try:
                await root.wait_for_timeout(900)
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
                state = _parse_state(txt)
                item = LiveGameItem(
                    source="overtime.ag",
                    sport="college_football",
                    league="NCAAF",
                    collected_at=iso_now(),
                    game_key=game_key_from(away, home),
                    event_date=None,
                    event_time=None,
                    rotation_number=None,
                    teams={"away": away, "home": home},
                    state=state,
                    markets=parsed["markets"],
                    is_live=True,
                )
                yield json.loads(json.dumps(item, default=lambda o: o.__dict__))
                emitted += 1

            if emitted == 0:
                try:
                    txt = await (root.evaluate("() => document.body?.innerText || ''"))
                    with open("snapshots/overtime_live_text.txt", "w", encoding="utf-8") as f:
                        f.write(txt[:120000])
                except Exception:
                    pass

        self.logger.info("Emitted %d live rows", emitted)
        try:
            await page.close()
        except Exception:
            pass