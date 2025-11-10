---
description: Show the current NFL week and schedule status
---

Check the current NFL season status using the season calendar utility:

```bash
cd src && uv run python -m walters_analyzer.season_calendar
```

Display:
- Today's date
- Current week number
- Season phase (regular season, playoffs, etc.)
- Week date range

This helps ensure all analysis is based on the correct current week.
