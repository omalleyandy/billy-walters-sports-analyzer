# Documentation Hub

Every Markdown artifact that used to live in the repository root has been moved into this folder tree.

## Directory Overview

- `guides/` – setup instructions, CLAUDE command references, quick starts, and other reusable runbooks.
- `reports/` – investigations, migration retros, validation write-ups, and day-to-day operation summaries that are still actively referenced.
- `reports/archive/` – historical artifacts kept for posterity; use these when you need the deep dives but don't want them cluttering the primary folder.

## Frequently Used Guides

- [PROXY_SETUP.md](guides/PROXY_SETUP.md) – Residential proxy configuration plus Cloudflare troubleshooting.
- [QUICKSTART.md](guides/QUICKSTART.md) – Minimal steps to get the analyzer running locally.
- [USAGE_GUIDE.md](guides/USAGE_GUIDE.md) – Detailed CLI walkthroughs and sample sessions.
- [CLAUDE.md](guides/CLAUDE.md) – Command catalog and workflow hooks for automation.
- [INJURY_SCRAPER.md](guides/INJURY_SCRAPER.md) – Injury parsing details, position valuations, and gates.

## High-Signal Reports

- [_START_HERE.md](reports/_START_HERE.md) – Executive summary of the latest full investigation.
- [_INVESTIGATION_AND_ORGANIZATION_COMPLETE.md](reports/_INVESTIGATION_AND_ORGANIZATION_COMPLETE.md) – Post-migration audit details.
- [BACKTEST_RESULTS_SUMMARY.md](reports/BACKTEST_RESULTS_SUMMARY.md) – Historical performance snapshot.
- [CHROME_DEVTOOLS_BREAKTHROUGH.md](reports/CHROME_DEVTOOLS_BREAKTHROUGH.md) – Notes from the Cloudflare bypass milestone.
- [DATA_QUALITY_REVIEW.md](reports/DATA_QUALITY_REVIEW.md) – Data validation and QA checkpoints.
- Full historical trail (deployment retros, extra QA packs, etc.) now lives in [reports/archive/](reports/archive); keep contributing to those files, just know they're tucked away to make the top-level docs easier to scan.
- [FEATURE_COVERAGE.md](FEATURE_COVERAGE.md) tracks which features promised in the reports have shipped in code (and flags the gaps).

## Maintenance Workflow

1. Generate docs as usual (session notes, status reports, etc.); they'll temporarily appear in the repo root.
2. Run `python scripts/organize_docs.py` to sweep new Markdown files into the correct folder and automatically archive older reports.
3. Review `git status` to confirm only the intended moves were made before committing.

Keeping the documentation loop here prevents the root directory from ballooning every time a new chat transcript or report is generated.
