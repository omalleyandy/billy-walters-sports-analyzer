#!/usr/bin/env python
"""
Utility to keep Markdown artifacts out of the project root.

It moves Markdown files in the repo root (except README/AGENTS) into
either docs/guides or docs/reports based on lightweight heuristics.
Run it after each session to sweep up newly generated briefings.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CATEGORIES = {
    "guides": DOCS / "guides",
    "reports": DOCS / "reports",
}
ARCHIVE_DIR = CATEGORIES["reports"] / "archive"

EXCLUDE = {"README.MD", "AGENTS.MD"}
FORCE_GUIDE = {
    "CLAUDE.MD",
    "BILLY_WALTERS_ANALYTICS_PRD_V1.5.MD",
    "BILLY_WALTERS_METHODOLOGY.MD",
    "CHROME DEVTOOLS MCP INTEGRATION.MD",
    "HTML_DATA_MAPPING.MD",
    "INJURY_SCRAPER.MD",
    "ODDS_QUERY_IMPLEMENTATION.MD",
    "EXAMPLE_OUTPUT.MD",
}
FORCE_REPORT = {
    "_START_HERE.MD",
    "_INVESTIGATION_AND_ORGANIZATION_COMPLETE.MD",
    "_INVESTIGATION_COMPLETE_README.MD",
    "README_INVESTIGATION_COMPLETE.MD",
}

GUIDE_KEYWORDS = (
    "GUIDE",
    "USAGE",
    "QUICK",
    "SETUP",
    "START",
    "REFERENCE",
    "README_",
    "READ_ME",
    "HOWTO",
    "PLAYBOOK",
    "POWER_RATINGS",
    "PROJECT_SETUP",
    "PROXY",
    "WINDOWS",
    "QUICKSTART",
)

ACTIVE_REPORTS = {
    "_START_HERE.MD",
    "_INVESTIGATION_AND_ORGANIZATION_COMPLETE.MD",
    "_INVESTIGATION_COMPLETE_README.MD",
    "BACKTEST_RESULTS_SUMMARY.MD",
    "CHROME_DEVTOOLS_BREAKTHROUGH.MD",
    "DATA_QUALITY_REVIEW.MD",
    "INTEGRATION_ANALYSIS.MD",
    "README_INVESTIGATION_COMPLETE.MD",
}


def categorize(filename: str) -> str | None:
    """Return destination category name or None to skip."""
    upper = filename.upper()
    if upper in EXCLUDE:
        return None
    if upper in FORCE_GUIDE:
        return "guides"
    if upper in FORCE_REPORT:
        return "reports"
    if any(keyword in upper for keyword in GUIDE_KEYWORDS):
        return "guides"
    return "reports"


def move_markdown(dry_run: bool = False) -> None:
    DOCS.mkdir(exist_ok=True)
    for target_dir in CATEGORIES.values():
        target_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(ROOT.glob("*.md")):
        category = categorize(path.name)
        if not category:
            continue
        destination_dir = CATEGORIES[category]
        destination = destination_dir / path.name

        if destination.exists():
            print(f"skip {path.name}: already located at {destination.relative_to(ROOT)}")
            continue

        print(f"{'DRY RUN - would move' if dry_run else 'Moving'} {path.name} -> {destination.relative_to(ROOT)}")
        if not dry_run:
            shutil.move(str(path), destination)


def archive_reports(dry_run: bool = False) -> None:
    """Move less-used reports into docs/reports/archive."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    reports_dir = CATEGORIES["reports"]
    for path in sorted(reports_dir.glob("*.md")):
        if path.name.upper() in ACTIVE_REPORTS:
            continue
        destination = ARCHIVE_DIR / path.name
        if destination.exists():
            continue
        print(f"{'DRY RUN - would archive' if dry_run else 'Archiving'} {path.name} -> {destination.relative_to(ROOT)}")
        if not dry_run:
            shutil.move(str(path), destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize root markdown files under docs/")
    parser.add_argument("--dry-run", action="store_true", help="Show planned moves without touching files")
    parser.add_argument("--skip-archive", action="store_true", help="Do not move reports into docs/reports/archive")
    args = parser.parse_args()
    move_markdown(dry_run=args.dry_run)
    if not args.skip_archive:
        archive_reports(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
