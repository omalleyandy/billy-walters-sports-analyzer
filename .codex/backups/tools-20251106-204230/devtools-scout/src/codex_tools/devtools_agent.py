from __future__ import annotations
import re
from typing import Dict, Optional
from playwright.sync_api import sync_playwright, Response
from .utils import to_curl, to_fetch

JSON_CT = re.compile(r"(application/(json|ld\+json))|(text/csv)", re.I)


class NetworkCapture:
    def __init__(
        self,
        url: str,
        method: str,
        status: int,
        headers: Dict[str, str],
        body: bytes | None,
    ):
        self.url = url
        self.method = method
        self.status = status
        self.headers = headers
        self.body = body

    def as_curl(self) -> str:
        return to_curl(self.method, self.url, self.headers, self.body)

    def as_fetch(self) -> str:
        return to_fetch(self.method, self.url, self.headers, self.body)


def _match(resp: Response, domain_hint: Optional[str]) -> bool:
    try:
        if resp.status != 200:
            return False
        if domain_hint and domain_hint not in resp.url:
            return False
        ct = resp.headers.get("content-type", "")
        return bool(JSON_CT.search(ct))
    except Exception:
        return False


def capture_first_json(url: str, domain_hint: Optional[str] = None) -> NetworkCapture:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        resp = page.wait_for_response(lambda r: _match(r, domain_hint), timeout=45000)
        headers = {k.lower(): v for k, v in resp.headers.items()}
        try:
            body = resp.body()
        except Exception:
            body = None
        cap = NetworkCapture(resp.url, resp.request.method, resp.status, headers, body)
        browser.close()
        return cap
