Update all sports data sources for the current NFL week.

Usage: /update-data [optional: source]

This command will:
1. Detect current NFL week automatically
2. Fetch latest game schedules and scores
3. Update odds from Action Network
4. Refresh weather forecasts
5. Update team statistics
6. Check for roster changes and injuries

Before updating, check current week:
```bash
cd src && uv run python -m walters_analyzer.season_calendar
```

Sources:
- overtime (Overtime API)
- action (Action Network)
- weather (AccuWeather + OpenWeather)
- all (default - updates everything)
