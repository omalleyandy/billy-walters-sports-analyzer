# Project Operating Rules (Billy Walters Sports Analyzer)

## Tech Stack & Environment
- Python env via **uv**; never touch system Python. Use: `uv run ...`, `uv sync`.
- Scrapers: **Scrapy + Playwright** for prod; **BeautifulSoup4** for quick HTML parsing.
- Headless by default; detect 429/403/CAPTCHA; rotate UAs/proxies; respect crawl cadence.
- Secrets only from `.env`/environment. Never hardcode keys or URLs with creds.

## File Safety & Boundaries
- Modify files **only inside this repo**. Do **not** overwrite: `.env`, `.venv`, `uv.lock`.
- If a change needs secrets, write to `.env.example` and docs, not `.env`.
- Keep outputs reproducible: CSV/JSON/Parquet/Postgres exporters only via config.

## Coding Standards
- Typed functions, modular extractors, structured logging, retries/backoff.
- Config-first: read creds/URLs/flags from `settings.py` or env.
- Include tests/stubs for non-trivial modules; graceful error paths.
- CLI: provide runnable Windows + WSL commands in README updates.

## Approvals (ask before doing these)
- Installing new packages, changing network targets, large refactors, deleting files.

## Done Criteria for New Code
- `uv sync` clean, `pytest -q` (if tests exist) passes, README snippet to run it,
  `.env.example` updated, and export paths verified (CSV/JSON/Parquet/PG).

## Codex CLI Notes
- Codex runs `.codex/preflight.sh`, which executes every script in `hooks/`.
- Use the command helpers in `commands/` (`./commands/bootstrap`, JSON workflows, etc.) rather than ad-hoc one-off scripts.
- See `docs/CODEX_WORKFLOW.md` for the full Codex integration guide.
