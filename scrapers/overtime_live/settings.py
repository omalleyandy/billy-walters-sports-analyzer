BOT_NAME = "overtime_live"
SPIDER_MODULES = ["scrapers.overtime_live.spiders"]
NEWSPIDER_MODULE = "scrapers.overtime_live.spiders"

ROBOTSTXT_OBEY = False          # You decide case-by-case.
LOG_LEVEL = "INFO"

# Output via custom pipeline (JSONL + Parquet snapshots)
ITEM_PIPELINES = {
    "scrapers.overtime_live.pipelines.ParquetPipeline": 300,
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