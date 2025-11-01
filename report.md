# Analysis of Overtime Live Odds Scraper

## Overview

The uploaded project implements a **Scrapy‑based crawler** that uses **Playwright** to fetch live betting data from the “overtime.ag” sports book.  It is organised as a small Scrapy project with the following modules:

* **`items.py`** – defines data classes for `QuoteSide`, `Market` and the top‑level `LiveGameItem`.  These classes capture lines, prices, moneyline odds, teams, the event date (if known) and the time the data was collected.  The `game_key_from()` helper creates a stable hash of the matchup and date bucket, and `iso_now()` returns a UTC timestamp.
* **`pipelines.py`** – implements a `ParquetPipeline` that buffers scraped items and writes them to disk when the spider closes.  It creates both a `.jsonl` file and a **Parquet** snapshot using **PyArrow**, ensuring that each run persists a timestamped snapshot under `data/overtime_live`.  The buffer prevents multiple small writes and makes writing to Parquet straightforward.
* **`selectors.py`** – centralises CSS/XPath selectors and text constants that describe the “College Football” board on overtime.ag.  Keeping selectors in a single file makes it easier to adjust when the site’s markup changes, and the spider falls back to a broad query if the preferred selectors fail.
* **`settings.py`** – contains Scrapy settings.  It disables robots.txt enforcement (leaving compliance decisions to the caller), configures Playwright handlers as the download backend, limits concurrency to two concurrent requests and enables auto‑throttling to be polite to the target site.  It registers the Parquet pipeline at priority 300.
* **`overtime_live_spider.py`** – the heart of the scraper.  It defines an asynchronous Scrapy spider that:
  - Launches a headless Chromium instance via Playwright and navigates to the live betting page.
  - Attempts to query overtime.ag’s internal `.asmx` endpoints via `page.evaluate()` to fetch **JSON** offering data (preferred path).  This is fast and avoids brittle DOM scraping.
  - If no events are returned from the API, it locates the largest iframe, clicks through sport/competition tabs (American Football → NCAAF) and extracts text blocks from DOM rows.  It then parses lines/prices manually by splitting lines and applying regular expressions to identify spreads (`+/-n`), totals (`o/u n`) and moneyline odds.
  - Converts the extracted data into `LiveGameItem` instances and yields them.  The spider keeps track of how many rows were emitted and dumps a text snapshot when nothing is found.

## Output format

The spider yields dictionaries representing `LiveGameItem` objects.  Fields include:

| field         | type                        | description                                                 |
|--------------|-----------------------------|-------------------------------------------------------------|
| `source`      | `str`                       | Always `"overtime.ag"` for this spider.                     |
| `sport`       | `str`                       | Fixed to `"ncaa_football"`.                                  |
| `league`      | `str`                       | Fixed to `"NCAAF"`.                                          |
| `collected_at`| `str` (ISO‑8601)            | UTC timestamp when the data was scraped.                   |
| `game_key`    | `str`                       | Stable SHA‑1 digest of `away@home|date_bucket`.            |
| `event_date`  | `Optional[str]`             | Date of the event when available, else `None`.              |
| `teams`       | `Dict[str,str]`             | Names of away and home teams.                              |
| `state`       | `Dict[str,Any]`             | Live game state (quarter, clock) – currently empty.        |
| `markets`     | `Dict[str,Market]`          | Nested dictionary of `spread`, `total` and `moneyline` markets. |

The Parquet pipeline flattens nested structures into JSON‑encoded string columns (`teams_json`, `state_json`, `markets_json`) so that the tabular format remains simple while preserving all nested data.

## Code quality and design

### Strengths

* **Separation of concerns** – Data definitions, selectors, pipeline logic and spider logic live in separate modules.  This improves maintainability.
* **API‑first strategy** – The spider tries to hit the internal `Offering.asmx` APIs first, which is faster and less prone to break when the site’s HTML changes.  Only if the API yields no events does it fall back to DOM scraping.
* **Headless Playwright** – Using Playwright as the download handler ensures JavaScript rendering and allows direct calls to `page.evaluate()` and `frame.click()`.  The spider is asynchronous and yields its own `start()` method rather than Scrapy’s synchronous `start_requests()`, embracing `asyncio` for Playwright.
* **Configurable via environment** – Many details can be configured without code changes: target URLs (`OVERTIME_LIVE_URL`, `OVERTIME_START_URL`), selected sport/competition (`OVERTIME_SPORT`, `OVERTIME_COMP`) and proxy settings (`OVERTIME_PROXY`/`PROXY_URL` in the commented launch options).  This aligns with the “config‑first” philosophy described in the user’s instructions.
* **Snapshotting** – When fallback scraping fails, the spider saves a full‑page screenshot and the text of `document.body` under `snapshots/`.  This is useful for debugging or for adjusting selectors when the page structure changes.
* **Type hints and dataclasses** – The use of dataclasses with type hints (`QuoteSide`, `Market`, `LiveGameItem`) makes the model explicit and easier to work with.  Helper functions like `to_float`, `_prices_from_text` and `_looks_like_event_block` encapsulate parsing logic.

### Areas for improvement

1. **Environment and dependency management** – The repository does not include a `pyproject.toml` or a `requirements.txt`.  Adopting **uv** or `poetry` to manage dependencies would make installation reproducible.  The dependencies include `scrapy`, `scrapy‑playwright`, `playwright`, `orjson`, `pyarrow`, `python‑dotenv` and possibly `dotenv`.  Providing a `pyproject.toml` with pinned versions and a lock file (`uv.lock`) would ease installation.  An `.env.example` describing environment variables should accompany the code.

2. **Error handling and logging** – While there are many `try/except` blocks, most exceptions are silently ignored (`pass`).  Swallowing exceptions can hide issues.  Consider logging exceptions at the `DEBUG` level to aid troubleshooting.  For example, catching `PWTimeout` when waiting for elements and logging the timeout reason helps identify broken selectors.

3. **Testing** – There are no unit or integration tests.  You can add pytest fixtures to test `_parse_game_block()` with sample texts.  Create a fixtures directory with sample JSON responses from the API and sample DOM snippets.  Then write tests to ensure that lines and prices are parsed correctly.  Automated tests help catch regressions when updating selectors or parsing logic.

4. **Respectful crawling** – Even though the settings limit concurrency and enable auto‑throttle, there is no handling for server blocks (HTTP 429/403).  Adding retry middleware with exponential back‑off and rotating user agents/proxies would make the scraper more robust.  Scrapy’s [`RetryMiddleware`](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#retrymiddleware) can be tuned, or you can implement custom middleware to detect rate‑limit pages and sleep accordingly.  Include `PLAYWRIGHT_LAUNCH_OPTIONS["proxy"]` in `custom_settings` and rotate proxies via environment variables if necessary.

5. **Data normalisation** – Some numeric fields remain strings.  The API branch uses `Points` and `Price` from the JSON but does not convert them to floats/ints.  Converting values to the appropriate type before serialising to JSON/Parquet will simplify downstream analytics.  Similarly, including an `event_date` when available (most APIs expose a scheduled start time) would improve historical analysis.

6. **Output structure** – The `to_dict()` method on `LiveGameItem` currently flattens dataclasses without performing any transformation; it iterates through markets but does nothing.  Either remove the method or complete the flattening logic.  Alternatively, rely on `orjson.dumps(item, default=lambda o: o.__dict__)` as used in the spider.

7. **Repository contents** – The user referenced a GitHub repository (`omalleyandy/billy‑walters‑sports‑analyzer`).  Our GitHub connector could not find or access this repository, so the review is limited to the provided files.  If the repository is private, ensure the GitHub app has access to it.  Including CI/CD configuration (GitHub Actions or similar) in the repository could automate scraping runs and validate the environment.

8. **State extraction** – The `state` field in `LiveGameItem` is always empty.  The live widget includes quarter and game clock information.  Extending the API extraction to include `CurrentPeriod`, `TimeRemaining` or similar fields would make the dataset more informative.  In the fallback DOM scrape, you could parse lines like “3rd Q 05:32” and store them in the `state` dictionary.

9. **CLI and documentation** – A short **README.md** should describe how to set up the environment, run the spider and interpret the outputs.  It should note that the spider uses Playwright and requires a headless Chromium browser (`playwright install`) and that the script writes snapshots and Parquet files.  Providing example commands both for Windows and Unix/WSL (e.g., `uv venv .venv && uv pip install -r requirements.txt && scrapy crawl overtime_live`) helps users reproduce results.

10. **Robots.txt compliance** – The settings disable `ROBOTSTXT_OBEY`.  While this may be acceptable in some contexts (e.g., for internal use), you should verify and respect the target site’s robots.txt and Terms of Service.  Document your decision so that others understand the ethical implications.

## Summary

The overtime live odds scraper is a well‑structured, asynchronous Scrapy spider that leverages Playwright to pull live betting markets from overtime.ag.  It tries an API call first, falls back to DOM parsing, and writes results to JSONL and Parquet for further analysis.  To improve reliability and maintainability, consider formalising dependency management, adding logging and tests, respecting rate limits, normalising data types and documenting the project.  Providing access to the referenced GitHub repository would allow a more thorough code review, including CI configuration and any additional modules not included here.

