import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_NAME = "overtime_live"
SPIDER_MODULES = ["scrapers.overtime_live.spiders"]
NEWSPIDER_MODULE = "scrapers.overtime_live.spiders"

ROBOTSTXT_OBEY = False          # You decide case-by-case.
LOG_LEVEL = "INFO"

# Output via custom pipeline (JSONL + Parquet + CSV snapshots)
ITEM_PIPELINES = {
    "scrapers.overtime_live.pipelines.ParquetPipeline": 300,
    "scrapers.overtime_live.pipelines.CSVPipeline": 310,
}

# Playwright is configured in spider.custom_settings; these here are fallback.
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DOWNLOAD_HANDLERS = {"http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"}

# Respectful cadence
CONCURRENT_REQUESTS = 2
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
DOWNLOAD_TIMEOUT = 60

# Updated User-Agent to latest Chrome (January 2025)
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# ===== Proxy Configuration =====
# Proxyscrape.com residential proxy with 10 rotating IPs
PROXY_URL = os.getenv("PROXY_URL") or os.getenv("OVERTIME_PROXY")

# Playwright launch options with proxy support
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 90_000

# Configure proxy if available
_proxy_config = {}
if PROXY_URL:
    _proxy_config = {"proxy": {"server": PROXY_URL}}
    try:
        print(f"[OK] Proxy configured: {PROXY_URL.split('@')[1] if '@' in PROXY_URL else PROXY_URL}")
    except UnicodeEncodeError:
        print("[OK] Proxy configured")

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    **_proxy_config,
}

# Context options for additional stealth
PLAYWRIGHT_CONTEXT_OPTIONS = {
    "viewport": {"width": 1920, "height": 1080},
    "locale": "en-US",
    "timezone_id": "America/New_York",
}

# Retry configuration for proxy failures
RETRY_TIMES = 5
RETRY_HTTP_CODES = [403, 407, 429, 500, 502, 503, 504]  # 407 = Proxy Auth Required
RETRY_BACKOFF_BASE = 2
RETRY_BACKOFF_MAX = 60
