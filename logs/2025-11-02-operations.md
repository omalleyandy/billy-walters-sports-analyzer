# 2025-11-02 Operations Log

## Playwright installation
- Attempted to run `uv run python -m playwright install --with-deps chromium` multiple times.
- Each run failed before syncing dependencies because the resolver could not download packages from PyPI through the proxy (`tunnel error: unsuccessful`).
- Falling back to the system interpreter, `python3 -m playwright install --with-deps chromium` reached the apt dependency installation step but apt returned HTTP 403 errors for all Ubuntu repositories (blocked by proxy).
- A plain `python3 -m playwright install chromium` was also rejected with HTTP 403 responses from the Playwright CDN while trying to download the Chromium bundle.

## Injury scraper
- Ran `python3 -m walters_analyzer.cli scrape-injuries --sport nfl` to reuse the globally installed Scrapy stack.
- Scrapy and Scrapy-Playwright started, but browser launch failed with the "Executable doesn't exist" error because no Chromium binaries were available (previous install steps failed).
- No injury output was produced in `data/injuries/`.

## Card analyzer
- With the CLI importable via the source tree, executed `python3 -m walters_analyzer.cli wk-card --file cards/wk-card-2025-10-31.json --dry-run`.
- Command completed successfully and printed the two configured matchups (dry run only, since data gating is still pending injury/weather refreshes).

## Outstanding follow-ups
- Weather pipeline not rerun (no documented command in repo; blocked until browser install succeeds).
- Power rating refresh command (`walters-analyzer update-power-ratings`) is absent from the current CLI implementation, so no refresh was possible.
- Analyzer edge review deferred until live data ingestion succeeds.
