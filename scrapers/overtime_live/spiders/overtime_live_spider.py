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
    """Extract price values from a block of event text.

    The previous implementation relied on ``\b`` word boundaries to
    delimit prices.  That approach breaks for odds such as ``-115`` or
    ``+215`` because the leading ``+``/``-`` characters are not word
    characters, meaning ``\b`` does not recognise the transition from
    whitespace to the sign.  As a result no prices were detected and the
    parser concluded that the block did not contain any markets.

    Instead we explicitly ensure that a price token is not preceded by an
    alphanumeric character (to avoid totals like ``O49.5``) and is not
    followed by another digit.  This still captures the usual American odds
    formats while remaining robust to surrounding punctuation.
    """

    pattern = r"(?<![A-Za-z0-9])([+\-]\d{2,4})(?!\d)"
    return [int(x) for x in re.findall(pattern, text)]


def _looks_like_event_block(txt: str) -> bool:
    if not txt:
        return False
    lines = [l for l in txt.splitlines() if l.strip()]
    text_lines = [l for l in lines if re.search(r"[A-Za-z]", l)]
    if len(text_lines) < 2:
        return False
    normalized = txt.replace("½", ".5")
    has_price = bool(_prices_from_text(normalized))
    has_spread = bool(
        re.search(r"(?<![A-Za-z0-9])[+\-]\d{1,2}(?:\.\d+)?", normalized)
    )
    has_total = bool(
        re.search(r"\b[ou]\s*[+\-]?\d{1,2}(?:\.\d+)?", normalized, flags=re.I)
    )
    return has_price or has_spread or has_total


class OvertimeLiveSpider(scrapy.Spider):
    """
    Live odds scraper for overtime.ag (focus: NCAAF).
    Strategy:
      1) Try site JSON APIs (Offering.asmx) via page.evaluate -> robust & fast.
      2) Fallback to DOM/iframe parsing with best-effort sport selection.
    """

    name = "overtime_live"

    # Custom settings allow this spider to be self‑contained.  See the README for
    # instructions on overriding these values via a settings file or the
    # command line.  In addition to the original settings we enable
    # retry/backoff for 429/403 responses and optionally configure a proxy
    # server via environment variables.  If OVERTIME_PROXY or PROXY_URL is
    # defined the proxy dict will be passed to Playwright.  Otherwise the
    # proxy entry is omitted.
    custom_settings = {
        "BOT_NAME": "overtime_live",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90_000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,
            # Proxy will be configured per-request in start() method
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        },
        "PLAYWRIGHT_CONTEXT_OPTIONS": {
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone_id": "America/New_York",
        },
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        # Concurrency and throttling – keep the load reasonable and avoid
        # overwhelming the target.  AutoThrottle will dynamically adjust
        # delays based on observed latencies.
        "CONCURRENT_REQUESTS": 2,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
        # Retry configuration – back off on 429/403/407 and other transient
        # errors.  407 = Proxy Authentication Required (common with rotating proxies)
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [403, 407, 429, 500, 502, 503, 504],
        "RETRY_BACKOFF_BASE": 2,
        "RETRY_BACKOFF_MAX": 60,
    }

    # -------- Scrapy async entry --------
    async def start(self):
        live = os.getenv("OVERTIME_LIVE_URL") or "https://overtime.ag/sports#/integrations/liveBetting"
        start = os.getenv("OVERTIME_START_URL") or "https://overtime.ag"
        # Always start with main page, login will happen in parse_board callback
        target_url = start

        # Per-request proxy (fixes 407 when you set OVERTIME_PROXY / PROXY_URL)
        # Try keeping credentials in URL for residential proxies that don't support HTTP auth
        proxy_url = os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")
        context_kwargs = None
        if proxy_url:
            # Some residential proxies require credentials in URL, not as separate fields
            context_kwargs = {"proxy": {"server": proxy_url}}

        # Hash routes rarely fire "load" → use domcontentloaded; fail faster on blocks
        goto_kwargs = {"wait_until": "domcontentloaded", "timeout": 60_000, "referer": "https://overtime.ag/"}

        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": goto_kwargs,
            "playwright_page_methods": [
                # small beat for SPA hydration; prefer a selector if you have one
                PageMethod("wait_for_timeout", 500),
                # Example (if you find a stable element on the live board):
                # PageMethod("wait_for_selector", "text=/Live|College Football/i", timeout=5000),
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
                self.logger.error("Saved error screenshot to snapshots/error.png")
            except Exception:
                self.logger.debug("Could not write error screenshot", exc_info=True)
            try:
                await page.close()
            except Exception:
                pass

    # -------- Helpers --------
    async def _verify_proxy_ip(self, page: Page) -> bool:
        """
        Verify the proxy is working by checking the external IP.
        Returns True if proxy verification successful, False otherwise.
        """
        proxy_url = os.getenv("OVERTIME_PROXY") or os.getenv("PROXY_URL")
        if not proxy_url:
            return True  # No proxy configured, skip verification

        try:
            self.logger.info("Verifying proxy IP...")
            await page.goto("https://ipinfo.io/json", timeout=15_000)

            # Extract IP info from the page
            ip_info = await page.evaluate("""
                () => {
                    try {
                        const pre = document.querySelector('pre');
                        if (pre) {
                            const data = JSON.parse(pre.innerText);
                            return {
                                ip: data.ip,
                                city: data.city,
                                region: data.region,
                                country: data.country,
                                org: data.org
                            };
                        }
                    } catch (e) {
                        return null;
                    }
                    return null;
                }
            """)

            if ip_info:
                self.logger.info(
                    f"✓ Proxy IP verified: {ip_info.get('ip')} "
                    f"({ip_info.get('city')}, {ip_info.get('region')}, {ip_info.get('country')})"
                )
                return True
            else:
                self.logger.warning("⚠ Could not parse IP info")
                return False

        except Exception as e:
            self.logger.error(f"✗ Proxy verification failed: {e}")
            return False

    async def _perform_login(self, page: Page) -> bool:
        """
        Perform login to overtime.ag if credentials are available.
        Returns True if login successful or already logged in, False otherwise.
        """
        customer_id = os.getenv("OV_CUSTOMER_ID")
        password = os.getenv("OV_PASSWORD") or os.getenv("OV_CUSTOMER_PASSWORD")

        if not customer_id or not password:
            self.logger.warning("No login credentials found in environment (OV_CUSTOMER_ID, OV_PASSWORD)")
            return False

        try:
            # Check if already logged in by looking for logout indicator
            try:
                await page.wait_for_selector("text=/logout/i", timeout=2000)
                self.logger.info("Already logged in")
                return True
            except Exception:
                pass

            # Navigate to login page
            self.logger.info("Navigating to login page...")
            await page.evaluate("() => { location.hash = '#/login'; }")
            await page.wait_for_timeout(1500)

            # Fill in credentials
            self.logger.info("Filling login credentials...")
            customer_id_input = await page.query_selector('input[placeholder*="Customer"], input[name*="customer"], input[type="text"]')
            if customer_id_input:
                await customer_id_input.fill(customer_id)
            
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(password)
            
            # Click login button
            login_btn = await page.query_selector('button:has-text("LOGIN"), button:has-text("Login")')
            if login_btn:
                await login_btn.click()
                await page.wait_for_timeout(3000)
                
                # Check for successful login
                current_hash = await page.evaluate("() => location.hash")
                if "#/login" not in current_hash:
                    self.logger.info("Login successful")
                    return True
                else:
                    self.logger.error("Login failed - still on login page")
                    return False
            else:
                self.logger.error("Login button not found")
                return False

        except Exception as e:
            self.logger.error(f"Login error: {e}", exc_info=True)
            return False

    async def _hash_nudge_to_live(self, page: Page):
        try:
            await page.evaluate(
                "() => { const wanted='#/integrations/liveBetting'; if (!location.hash.includes('liveBetting')) { location.hash = wanted; } }"
            )
            await page.wait_for_timeout(800)
        except Exception:
            # Log but don't crash if we cannot adjust the hash.  The page may
            # already be on the live betting route or the site may have
            # changed its routing mechanism.
            self.logger.debug("Could not nudge to liveBetting hash", exc_info=True)

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
            self.logger.debug("Error while locating live iframe", exc_info=True)
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
                    # Clicking a particular filter may fail if it is not
                    # present; ignore and continue but log at debug level.
                    self.logger.debug("Failed to click sport filter %s", sel, exc_info=True)

        for t in comps:
            for sel in (f"text={t}", f"button:has-text('{t}')", f"a:has-text('{t}')", f"[role='tab']:has-text('{t}')"):
                try:
                    await root.click(sel, timeout=1200)
                    await root.wait_for_timeout(350)
                    break
                except Exception:
                    self.logger.debug("Failed to click competition filter %s", sel, exc_info=True)

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
            self.logger.debug("JS extraction failed", exc_info=True)
        return []

    def _parse_game_block(self, row_text: str) -> Optional[Dict[str, Any]]:
        if not _looks_like_event_block(row_text):
            return None

        all_lines = [l.strip() for l in row_text.splitlines() if l.strip()]
        text_lines = [l for l in all_lines if re.search(r"[A-Za-z]", l)]
        if len(text_lines) < 2:
            return None

        away, home = text_lines[0], text_lines[1]

        toks = [
            t.strip()
            for t in re.findall(
                r"[ou]?\s?[+\-]?\d+\.?\d*|[+\-]\d{2,4}", row_text.replace("½", ".5")
            )
            if t.strip()
        ]
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

    def _normalize_markets(self, markets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert line/price values within the market dictionary to the appropriate
        types (float for line, int for price) if possible.  This helper will
        tolerate missing keys and values gracefully.

        :param markets: nested dictionary of markets as returned by the API or
                        DOM parser (e.g. {"spread": {"away": {"line": "-6.5", "price": "-110"}, ...}})
        :return: the same dictionary with numeric values converted when safe
        """
        for mkt_name, mkt in markets.items():
            if not isinstance(mkt, dict):
                continue
            for side, quote in mkt.items():
                if not isinstance(quote, dict):
                    continue
                line = quote.get("line")
                price = quote.get("price")
                # normalise line
                if line is not None:
                    try:
                        # accept strings or numbers and convert halves
                        quote["line"] = to_float(str(line))
                    except Exception:
                        self.logger.debug("Failed to normalise line %s", line, exc_info=True)
                # normalise price
                if price is not None:
                    try:
                        quote["price"] = int(price)
                    except Exception:
                        self.logger.debug("Failed to normalise price %s", price, exc_info=True)
        return markets

    def _parse_state(self, text: str) -> Dict[str, Any]:
        """
        Attempt to extract game state (quarter and clock) from a block of text.

        Many betting boards display live state as "3rd Q 05:32" or similar.
        This function uses a simple regular expression to look for an ordinal
        quarter number followed by a clock in mm:ss format.  If found, it
        returns a dictionary with integer `quarter` and string `clock` keys.

        :param text: raw text from a game row
        :return: dict with state information or empty dict if none found
        """
        state: Dict[str, Any] = {}
        # Look for patterns like "3rd Q 05:32" or "4th Quarter 1:23"
        m = re.search(r"\b(\d)(?:st|nd|rd|th)?\s*(?:q(?:uarter)?|qtr)?\s*(\d{1,2}:\d{2})", text, re.IGNORECASE)
        if m:
            try:
                state["quarter"] = int(m.group(1))
                state["clock"] = m.group(2)
            except Exception:
                self.logger.debug("Failed to parse state from %s", m.group(0), exc_info=True)
        return state

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
                if (!away && (role.includes('away') || role=='visitor')) away = nm;
                if (!home && (role.includes('home') || role=='home')) home = nm;
              }
              if (!away || !home) {
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
                } else if (t.includes('total') || t.includes('over/under') || t=='ou') {
                  const o = sel.find(x => /over/i.test(x.Name || x.name || '')) || sel[0];
                  const u = sel.find(x => /under/i.test(x.Name || x.name || '')) || sel[1];
                  if (o) setSide(marketOut.total, 'over', o.Points ?? o.total ?? o.line ?? null, o.Price ?? o.price ?? null);
                  if (u) setSide(marketOut.total, 'under', u.Points ?? u.total ?? u.line ?? null, u.Price ?? u.price ?? null);
                } else if (t.includes('money') || t=='ml') {
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
            # Normalise numeric types within markets
            for ev in clean:
                mkts = ev.get("markets")
                if isinstance(mkts, dict):
                    ev["markets"] = self._normalize_markets(mkts)
            return clean
        except Exception:
            self.logger.debug("API evaluation failed", exc_info=True)
            return []

    # -------- Scrapy callback --------
    async def parse_board(self, response: Response):
        page: Page = response.meta["playwright_page"]

        # Verify proxy IP if configured
        await self._verify_proxy_ip(page)

        # Navigate to overtime.ag after IP check
        await page.goto("https://overtime.ag", timeout=60_000)
        await page.wait_for_timeout(1000)

        # Attempt login first
        await self._perform_login(page)
        
        # Navigate to live betting
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
                    sport="college_football",
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
                # Derive state (quarter/clock) from the free‑text block
                state = self._parse_state(txt)
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