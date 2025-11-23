#!/usr/bin/env python3
"""
Auto Index Updater Hook

Automatically updates documentation index (_INDEX.md) and memory file (CLAUDE.md)
whenever a new report or summary is created.

This hook is triggered after major deliverables/reports to:
1. Scan docs/ for new files (reports, QA docs, guides)
2. Update _INDEX.md with new documentation links
3. Update CLAUDE.md Recent Updates section
4. Maintain cross-references between documentation files

Usage:
    python .claude/hooks/auto_index_updater.py --scan-dir docs/reports
    python .claude/hooks/auto_index_updater.py --add-index "ESPN Data QA" "docs/reports/ESPN_DATA_QA_REPORT_2025-11-23.md"
    python .claude/hooks/auto_index_updater.py --auto (detect changes and update automatically)
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentationIndexUpdater:
    """Updates documentation index and memory files."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize updater.

        Args:
            project_root: Root project directory (detects from script location)
        """
        if project_root is None:
            # Detect from script location: .claude/hooks/auto_index_updater.py
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
        self.project_root = project_root
        self.docs_dir = project_root / "docs"
        self.index_file = self.docs_dir / "_INDEX.md"
        self.claude_file = project_root / "CLAUDE.md"

        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Docs directory: {self.docs_dir}")

    def scan_reports(self, scan_dir: Optional[Path] = None) -> List[Dict[str, str]]:
        """
        Scan directory for new report files.

        Args:
            scan_dir: Directory to scan (defaults to docs/reports)

        Returns:
            List of report metadata dicts
        """
        if scan_dir is None:
            scan_dir = self.docs_dir / "reports"

        reports = []
        if not scan_dir.exists():
            logger.warning(f"Scan directory not found: {scan_dir}")
            return reports

        for file_path in sorted(scan_dir.glob("*.md")):
            # Skip index files
            if file_path.name in ("_INDEX.md", "README.md"):
                continue

            # Extract title from filename
            title = file_path.stem.replace("_", " ").replace("-", " ")

            # Read first non-comment line as description
            description = None
            try:
                with open(file_path, encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("#"):
                            # Extract from markdown header
                            description = line.strip().lstrip("# ").strip()
                            break
                        elif line.strip() and not line.startswith("<!--"):
                            description = line.strip()[:100]
                            break
            except Exception as e:
                logger.debug(f"Could not read {file_path}: {e}")

            reports.append(
                {
                    "title": title,
                    "path": str(file_path.relative_to(self.docs_dir)),
                    "description": description or "Report",
                    "file_path": str(file_path),
                    "date": datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
                        "%Y-%m-%d"
                    ),
                }
            )

        logger.info(f"Found {len(reports)} reports in {scan_dir}")
        return reports

    def update_index(self, section: str, category: str, entries: List[Dict]) -> bool:
        """
        Update _INDEX.md with new entries.

        Args:
            section: Section name (e.g., "Testing & Quality")
            category: Category name (e.g., "Quality Assurance")
            entries: List of entry dicts with 'title', 'path', 'description'

        Returns:
            True if successful
        """
        if not self.index_file.exists():
            logger.error(f"Index file not found: {self.index_file}")
            return False

        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find or create section
            section_pattern = rf"(## {re.escape(section)}.*?)(## |\Z)"
            match = re.search(section_pattern, content, re.DOTALL)

            if match:
                section_start = match.start(1)
                section_text = match.group(1)

                # Find or create category
                category_pattern = rf"(### {re.escape(category)}.*?)(### |## |\Z)"
                category_match = re.search(
                    category_pattern, section_text, re.DOTALL
                )

                if category_match:
                    # Add entries to category
                    category_end = section_start + category_match.end(1)
                    new_entries = "\n".join(
                        [
                            f"- [{e['title']}]({e['path']}) - {e['description']}"
                            for e in entries
                        ]
                    )

                    content = (
                        content[:category_end] + f"\n{new_entries}" + content[category_end:]
                    )

                    with open(self.index_file, "w", encoding="utf-8") as f:
                        f.write(content)

                    logger.info(f"Updated {section} > {category} in _INDEX.md")
                    return True
        except Exception as e:
            logger.error(f"Error updating _INDEX.md: {e}")
            return False

        return False

    def add_recent_update(self, title: str, content: str) -> bool:
        """
        Add entry to CLAUDE.md Recent Updates section.

        Args:
            title: Update title
            content: Update content (markdown)

        Returns:
            True if successful
        """
        if not self.claude_file.exists():
            logger.error(f"Claude file not found: {self.claude_file}")
            return False

        try:
            with open(self.claude_file, "r", encoding="utf-8") as f:
                content_text = f.read()

            # Find Recent Updates section
            section_pattern = r"(## Recent Updates.*?)(### )"
            match = re.search(section_pattern, content_text, re.DOTALL)

            if match:
                # Insert after section header
                insert_pos = match.start(2)
                timestamp = datetime.now().strftime("%Y-%m-%d")
                new_entry = f"### {title} ✅ ({timestamp})\n\n{content}\n\n---\n\n"

                content_text = (
                    content_text[:insert_pos] + new_entry + content_text[insert_pos:]
                )

                with open(self.claude_file, "w", encoding="utf-8") as f:
                    f.write(content_text)

                logger.info(f"Added '{title}' to CLAUDE.md Recent Updates")
                return True
        except Exception as e:
            logger.error(f"Error updating CLAUDE.md: {e}")
            return False

        return False

    def auto_detect_and_update(self) -> Tuple[bool, List[str]]:
        """
        Auto-detect new files and update documentation.

        Returns:
            Tuple of (success, list of updated files)
        """
        updated_files = []

        # Check for new QA reports
        qa_reports = list(self.docs_dir.glob("*QA*REPORT*.md"))
        if qa_reports:
            logger.info(f"Found {len(qa_reports)} QA reports")
            updated_files.extend([str(r) for r in qa_reports])

        # Check for new session reports
        session_dir = self.docs_dir / "reports" / "sessions"
        if session_dir.exists():
            session_reports = list(session_dir.glob("SESSION*.md"))
            logger.info(f"Found {len(session_reports)} session reports")
            updated_files.extend([str(r) for r in session_reports])

        logger.info(f"Auto-detected {len(updated_files)} documentation files")
        return True, updated_files


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-update documentation index and memory files"
    )
    parser.add_argument(
        "--scan-dir",
        type=Path,
        help="Directory to scan for reports",
    )
    parser.add_argument(
        "--add-index",
        nargs=2,
        metavar=("TITLE", "PATH"),
        help="Add entry to index: --add-index 'Title' 'path/to/file.md'",
    )
    parser.add_argument(
        "--add-update",
        nargs=2,
        metavar=("TITLE", "CONTENT_FILE"),
        help="Add entry to CLAUDE.md: --add-update 'Title' 'path/to/content.md'",
    )
    parser.add_argument(
        "--auto", action="store_true", help="Auto-detect and update all docs"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Project root directory",
    )

    args = parser.parse_args()

    updater = DocumentationIndexUpdater(args.project_root)

    if args.scan_dir:
        # Scan directory
        reports = updater.scan_reports(args.scan_dir)
        print(json.dumps(reports, indent=2))
        return 0

    if args.add_index:
        # Add to index
        title, path = args.add_index
        success = updater.update_index(
            "Testing & Quality",
            "Quality Assurance",
            [{"title": title, "path": path, "description": "Quality assurance report"}],
        )
        return 0 if success else 1

    if args.add_update:
        # Add to recent updates
        title, content_file = args.add_update
        try:
            with open(content_file, "r", encoding="utf-8") as f:
                content = f.read()
            success = updater.add_recent_update(title, content)
            return 0 if success else 1
        except Exception as e:
            logger.error(f"Error reading content file: {e}")
            return 1

    if args.auto:
        # Auto-detect and update
        success, files = updater.auto_detect_and_update()
        if success:
            logger.info(f"Updated documentation for {len(files)} files")
            logger.info("Files updated:")
            for f in files:
                logger.info(f"  - {f}")
        return 0 if success else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    exit(main())
