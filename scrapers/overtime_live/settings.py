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

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
