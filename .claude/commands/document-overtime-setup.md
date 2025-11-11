---
description: Document Overtime.ag scraper setup and learnings
---

Document the Overtime.ag scraper configuration, issues resolved, and best practices.

This command will:
1. Fetch current information from https://overtime.ag/sports#/
2. Review this session's learnings about the scraper
3. Update project documentation with:
   - Scraper configuration details
   - Login flow and element selectors
   - Proxy setup requirements
   - Common issues and solutions
   - When to run for best results
   - Windows compatibility fixes

The documentation will be added to:
- `CLAUDE.md` - Development guidelines section
- `LESSONS_LEARNED.md` - Specific issues and solutions
- `OVERTIME_QUICKSTART.md` - Quick reference updates

Key learnings to document:
- Login button requires JavaScript click (hidden element)
- Unicode characters must be replaced for Windows console
- Proxy configuration needs Playwright native format
- Games only available during specific time windows
- Week 10-11 timing for NFL lines

This ensures future sessions can quickly troubleshoot overtime.ag scraper issues.
