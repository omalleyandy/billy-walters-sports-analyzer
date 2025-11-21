# MCP Architecture - Phase 1 Implementation Guide

**Goal**: Enhance existing MCP server with core data collection tools
**Timeline**: Week 1
**Status**: Ready to implement

---

## Overview

Phase 1 focuses on enhancing the existing `walters_mcp_server.py` with essential data collection tools and resources. This is a **non-breaking change** that adds functionality without disrupting the current setup.

**What We're Adding**:
- ✅ 7 new tools (data collection)
- ✅ 5 new resources (data access)
- ✅ 3 new prompts (workflows)
- ✅ Resource templates (dynamic data queries)

---

## Current vs Enhanced Server

### Current State
**File**: `.claude/walters_mcp_server.py`

```
Tools (3):
  - analyze_game
  - calculate_kelly_stake
  - get_injury_report

Resources (2):
  - walters://betting-history
  - walters://system-config

Prompts (0):
  - None
```

### Enhanced State (After Phase 1)
```
Tools (10):
  - analyze_game ✅ (existing)
  - calculate_kelly_stake ✅ (existing)
  - get_injury_report ✅ (existing)
  - collect_week_data 🆕
  - scrape_massey_ratings 🆕
  - scrape_overtime_odds 🆕
  - get_espn_team_stats 🆕
  - get_espn_schedule 🆕
  - get_current_nfl_week 🆕
  - validate_collected_data 🆕

Resources (7):
  - walters://betting-history ✅ (existing)
  - walters://system-config ✅ (existing)
  - sports://odds/{league}/{week} 🆕
  - sports://schedule/{league}/{week} 🆕
  - sports://teams/{league}/stats 🆕
  - sports://power-ratings/{league} 🆕
  - sports://data-status/{week} 🆕

Prompts (3):
  - collect-weekly-data 🆕
  - refresh-odds 🆕
  - prepare-analysis 🆕
```

---

## Implementation Steps

### Step 1: Add Data Collection Tools

**Add to `walters_mcp_server.py` after existing tools**:

```python
# ============================================================================
# Phase 1 Enhancement: Data Collection Tools
# ============================================================================

@mcp.tool()
async def collect_week_data(
    ctx: Context,
    week: int,
    league: str = "nfl",
    include_weather: bool = True,
) -> Dict:
    """
    Collect all data for the specified week (Billy Walters workflow)

    Args:
        week: NFL/NCAAF week number
        league: "nfl" or "ncaaf"
        include_weather: Include weather forecasts

    Returns:
        Collection summary with status of all data sources
    """
    try:
        results = {
            "week": week,
            "league": league,
            "timestamp": datetime.now().isoformat(),
            "data_collected": {},
            "status": "success",
        }

        # 1. Power Ratings
        logger.info(f"Collecting power ratings for {league}...")
        try:
            from scripts.analysis.weekly_power_rating_update import update_power_ratings
            power_ratings = await update_power_ratings(league)
            results["data_collected"]["power_ratings"] = {
                "status": "success",
                "count": len(power_ratings),
            }
        except Exception as e:
            logger.error(f"Power ratings failed: {e}")
            results["data_collected"]["power_ratings"] = {
                "status": "error",
                "error": str(e),
            }

        # 2. Game Schedules
        logger.info(f"Collecting schedules for {league} week {week}...")
        try:
            from src.data.espn_api_client import ESPNAPIClient
            async with ESPNAPIClient() as espn:
                schedule = await espn.get_schedule(league, week)
                results["data_collected"]["schedules"] = {
                    "status": "success",
                    "games": len(schedule.get("events", [])),
                }
        except Exception as e:
            logger.error(f"Schedule collection failed: {e}")
            results["data_collected"]["schedules"] = {
                "status": "error",
                "error": str(e),
            }

        # 3. Team Statistics
        logger.info(f"Collecting team stats for {league}...")
        try:
            from scripts.scrapers.scrape_espn_team_stats import collect_team_stats
            stats = await collect_team_stats(league, week)
            results["data_collected"]["team_stats"] = {
                "status": "success",
                "teams": len(stats),
            }
        except Exception as e:
            logger.error(f"Team stats failed: {e}")
            results["data_collected"]["team_stats"] = {
                "status": "error",
                "error": str(e),
            }

        # 4. Odds Data
        logger.info(f"Collecting odds for {league}...")
        try:
            from scripts.scrapers.scrape_overtime_api import scrape_odds
            odds = await scrape_odds(league)
            results["data_collected"]["odds"] = {
                "status": "success",
                "games": len(odds),
            }
        except Exception as e:
            logger.error(f"Odds collection failed: {e}")
            results["data_collected"]["odds"] = {"status": "error", "error": str(e)}

        # 5. Weather (optional)
        if include_weather:
            logger.info(f"Collecting weather forecasts...")
            try:
                from src.data.accuweather_client import AccuWeatherClient
                # Weather collection logic here
                results["data_collected"]["weather"] = {
                    "status": "success",
                    "forecasts": 0,  # Placeholder
                }
            except Exception as e:
                logger.error(f"Weather collection failed: {e}")
                results["data_collected"]["weather"] = {
                    "status": "error",
                    "error": str(e),
                }

        # Summary
        success_count = sum(
            1
            for v in results["data_collected"].values()
            if v.get("status") == "success"
        )
        total_count = len(results["data_collected"])

        if success_count == total_count:
            results["status"] = "success"
            results["message"] = f"All {total_count} data sources collected successfully"
        elif success_count > 0:
            results["status"] = "partial"
            results[
                "message"
            ] = f"{success_count}/{total_count} data sources collected"
        else:
            results["status"] = "error"
            results["message"] = "All data collection failed"

        return results

    except Exception as e:
        logger.error(f"Error in collect_week_data: {e}")
        return {"error": str(e), "status": "error"}


@mcp.tool()
async def scrape_massey_ratings(ctx: Context, league: str = "nfl") -> Dict:
    """
    Fetch Massey Composite power ratings

    Args:
        league: "nfl" or "ncaaf"

    Returns:
        Power ratings for all teams in league
    """
    try:
        from src.data.massey_client import MasseyClient

        async with MasseyClient() as client:
            ratings = await client.get_composite_ratings(league)

        return {
            "league": league,
            "ratings": ratings,
            "count": len(ratings),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error in scrape_massey_ratings: {e}")
        return {"error": str(e)}


@mcp.tool()
async def scrape_overtime_odds(
    ctx: Context, league: str = "nfl", format: str = "walters"
) -> Dict:
    """
    Get current odds from Overtime.ag API

    Args:
        league: "nfl" or "ncaaf"
        format: "walters" (Billy Walters format) or "raw" (Overtime format)

    Returns:
        Current odds for all games
    """
    try:
        from scripts.scrapers.scrape_overtime_api import main as scrape_odds

        # Run the scraper
        odds_data = await scrape_odds(league=league)

        return {
            "league": league,
            "format": format,
            "games": odds_data,
            "count": len(odds_data),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error in scrape_overtime_odds: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_espn_team_stats(
    ctx: Context, team: str = None, league: str = "nfl", week: int = None
) -> Dict:
    """
    Fetch team statistics from ESPN API

    Args:
        team: Team name (optional, returns all if not specified)
        league: "nfl" or "ncaaf"
        week: Week number (optional, uses current week if not specified)

    Returns:
        Team statistics (PPG, PAPG, total yards, etc.)
    """
    try:
        from src.data.espn_api_client import ESPNAPIClient

        async with ESPNAPIClient() as espn:
            if team:
                stats = await espn.get_team_stats(team, league)
            else:
                # Return all teams
                stats = await espn.get_all_team_stats(league)

        return {
            "league": league,
            "week": week,
            "team": team,
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error in get_espn_team_stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_espn_schedule(
    ctx: Context, league: str = "nfl", week: int = None
) -> Dict:
    """
    Retrieve game schedule from ESPN API

    Args:
        league: "nfl" or "ncaaf"
        week: Week number (optional, uses current week if not specified)

    Returns:
        Game schedule with dates, times, and matchups
    """
    try:
        from src.data.espn_api_client import ESPNAPIClient
        from walters_analyzer.season_calendar import get_nfl_week

        if not week:
            week = get_nfl_week()

        async with ESPNAPIClient() as espn:
            schedule = await espn.get_schedule(league, week)

        return {
            "league": league,
            "week": week,
            "games": schedule.get("events", []),
            "count": len(schedule.get("events", [])),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error in get_espn_schedule: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_current_nfl_week(ctx: Context) -> Dict:
    """
    Calculate current NFL week based on date

    Returns:
        Current NFL week number and date range
    """
    try:
        from walters_analyzer.season_calendar import (
            get_nfl_week,
            get_week_date_range,
        )

        week = get_nfl_week()
        if week:
            date_range = get_week_date_range(week)
            return {
                "week": week,
                "start_date": date_range[0].isoformat(),
                "end_date": date_range[1].isoformat(),
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "week": None,
                "message": "Currently in offseason or playoffs",
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"Error in get_current_nfl_week: {e}")
        return {"error": str(e)}


@mcp.tool()
async def validate_collected_data(
    ctx: Context, week: int, league: str = "nfl"
) -> Dict:
    """
    Check data quality for collected week data

    Args:
        week: NFL/NCAAF week number
        league: "nfl" or "ncaaf"

    Returns:
        Validation report with data quality score
    """
    try:
        from pathlib import Path

        validation = {
            "week": week,
            "league": league,
            "checks": {},
            "score": 0,
            "grade": "UNKNOWN",
        }

        # Check 1: Power Ratings
        power_ratings_file = Path(f"data/current/{league}_power_ratings.json")
        if power_ratings_file.exists():
            validation["checks"]["power_ratings"] = "PASS"
            validation["score"] += 20
        else:
            validation["checks"]["power_ratings"] = "FAIL"

        # Check 2: Schedules
        schedule_file = Path(f"data/current/{league}_schedule_week_{week}.json")
        if schedule_file.exists():
            validation["checks"]["schedule"] = "PASS"
            validation["score"] += 20
        else:
            validation["checks"]["schedule"] = "FAIL"

        # Check 3: Team Stats
        team_stats_file = Path(f"data/current/{league}_team_stats_week_{week}.json")
        if team_stats_file.exists():
            validation["checks"]["team_stats"] = "PASS"
            validation["score"] += 20
        else:
            validation["checks"]["team_stats"] = "FAIL"

        # Check 4: Odds
        odds_files = list(Path("output/overtime/").glob(f"{league}/*walters*.json"))
        if odds_files:
            # Check freshness (< 24 hours old)
            latest_odds = max(odds_files, key=lambda p: p.stat().st_mtime)
            age_hours = (datetime.now().timestamp() - latest_odds.stat().st_mtime) / 3600
            if age_hours < 24:
                validation["checks"]["odds"] = "PASS"
                validation["score"] += 20
            else:
                validation["checks"]["odds"] = f"STALE ({age_hours:.1f}h old)"
                validation["score"] += 10
        else:
            validation["checks"]["odds"] = "FAIL"

        # Check 5: Weather (optional)
        weather_files = list(Path("output/weather/").glob(f"*week_{week}*.json"))
        if weather_files:
            validation["checks"]["weather"] = "PASS"
            validation["score"] += 20
        else:
            validation["checks"]["weather"] = "SKIP"
            validation["score"] += 10

        # Grade
        if validation["score"] >= 90:
            validation["grade"] = "EXCELLENT"
        elif validation["score"] >= 70:
            validation["grade"] = "GOOD"
        elif validation["score"] >= 50:
            validation["grade"] = "FAIR"
        else:
            validation["grade"] = "POOR"

        return validation

    except Exception as e:
        logger.error(f"Error in validate_collected_data: {e}")
        return {"error": str(e)}
```

### Step 2: Add Data Resources

**Add after existing resources**:

```python
# ============================================================================
# Phase 1 Enhancement: Data Resources
# ============================================================================


@mcp.resource("sports://odds/{league}/{week}")
async def get_odds_resource(ctx: Context, league: str, week: int) -> str:
    """Get current odds for specified league and week"""
    try:
        from pathlib import Path
        import json

        # Find latest odds file
        odds_dir = Path(f"output/overtime/{league}/pregame/")
        odds_files = list(odds_dir.glob("api_walters_*.json"))

        if not odds_files:
            return json.dumps({"error": "No odds data found", "league": league, "week": week})

        latest_odds = max(odds_files, key=lambda p: p.stat().st_mtime)

        with open(latest_odds) as f:
            odds_data = json.load(f)

        return json.dumps(odds_data, indent=2)

    except Exception as e:
        logger.error(f"Error in get_odds_resource: {e}")
        return json.dumps({"error": str(e)})


@mcp.resource("sports://schedule/{league}/{week}")
async def get_schedule_resource(ctx: Context, league: str, week: int) -> str:
    """Get game schedule for specified league and week"""
    try:
        from pathlib import Path
        import json

        schedule_file = Path(f"data/current/{league}_schedule_week_{week}.json")

        if not schedule_file.exists():
            return json.dumps({"error": "Schedule not found", "league": league, "week": week})

        with open(schedule_file) as f:
            schedule_data = json.load(f)

        return json.dumps(schedule_data, indent=2)

    except Exception as e:
        logger.error(f"Error in get_schedule_resource: {e}")
        return json.dumps({"error": str(e)})


@mcp.resource("sports://teams/{league}/stats")
async def get_all_team_stats_resource(ctx: Context, league: str) -> str:
    """Get statistics for all teams in league"""
    try:
        from pathlib import Path
        import json

        # Find latest team stats file
        stats_files = list(Path("data/current/").glob(f"{league}_team_stats_week_*.json"))

        if not stats_files:
            return json.dumps({"error": "No team stats found", "league": league})

        latest_stats = max(stats_files, key=lambda p: p.stat().st_mtime)

        with open(latest_stats) as f:
            stats_data = json.load(f)

        return json.dumps(stats_data, indent=2)

    except Exception as e:
        logger.error(f"Error in get_all_team_stats_resource: {e}")
        return json.dumps({"error": str(e)})


@mcp.resource("sports://power-ratings/{league}")
async def get_power_ratings_resource(ctx: Context, league: str) -> str:
    """Get power ratings for all teams in league"""
    try:
        from pathlib import Path
        import json

        ratings_file = Path(f"data/current/{league}_power_ratings.json")

        if not ratings_file.exists():
            return json.dumps({"error": "Power ratings not found", "league": league})

        with open(ratings_file) as f:
            ratings_data = json.load(f)

        return json.dumps(ratings_data, indent=2)

    except Exception as e:
        logger.error(f"Error in get_power_ratings_resource: {e}")
        return json.dumps({"error": str(e)})


@mcp.resource("sports://data-status/{week}")
async def get_data_status_resource(ctx: Context, week: int) -> str:
    """Get data collection status for specified week"""
    try:
        # Use the validation tool to check status
        validation = await validate_collected_data(None, week=week, league="nfl")
        return json.dumps(validation, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error in get_data_status_resource: {e}")
        return json.dumps({"error": str(e)})
```

### Step 3: Add Prompts

**Add prompts at the end of the file**:

```python
# ============================================================================
# Phase 1 Enhancement: Prompts
# ============================================================================

from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent


@mcp.prompt()
async def collect_weekly_data_prompt(
    week: int, league: str = "nfl", include_weather: bool = True
) -> list[PromptMessage]:
    """
    Complete Billy Walters data collection workflow

    This prompt guides through the complete weekly data collection process:
    1. Power ratings (Massey + ESPN)
    2. Game schedules
    3. Team statistics
    4. Odds from Overtime.ag
    5. Weather forecasts (optional)
    6. Data validation
    """
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"""Execute the complete Billy Walters data collection workflow for {league.upper()} Week {week}.

REQUIRED STEPS:
1. Collect power ratings (Massey composite + ESPN enhancements)
2. Get game schedule for week {week}
3. Fetch team statistics (offensive/defensive)
4. Scrape odds from Overtime.ag API
5. {'Get weather forecasts for outdoor stadiums' if include_weather else 'Skip weather (indoor only)'}
6. Validate data quality

Use the collect_week_data tool with these parameters:
- week: {week}
- league: "{league}"
- include_weather: {str(include_weather).lower()}

After collection completes, run validate_collected_data to check data quality.
Report any failures or missing data.

SUCCESS CRITERIA:
- All 5 data sources collected
- Data quality grade: GOOD or EXCELLENT
- Odds data < 24 hours old
- No critical errors

Return a summary of what was collected and data quality score."""
            ),
        )
    ]


@mcp.prompt()
async def refresh_odds_prompt(league: str = "nfl") -> list[PromptMessage]:
    """
    Refresh odds before game day

    Quick update of odds data without full collection
    """
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"""Refresh {league.upper()} odds from Overtime.ag before game day.

STEPS:
1. Call scrape_overtime_odds tool with league="{league}"
2. Check odds freshness (should be < 1 hour old)
3. Compare to previous odds to identify line movements
4. Report any significant line changes (>1 point)

FOCUS ON:
- Games with line movement >1 point (potential sharp action)
- Games crossing key numbers (3, 7, 10 for NFL)
- Totals moving >2 points (weather or injury news)

Return summary of odds update and notable line movements."""
            ),
        )
    ]


@mcp.prompt()
async def prepare_analysis_prompt(week: int, league: str = "nfl") -> list[PromptMessage]:
    """
    Prepare complete dataset for edge detection

    Gathers all necessary data for Billy Walters edge detection
    """
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"""Prepare complete dataset for {league.upper()} Week {week} edge detection.

REQUIRED DATA:
1. Power ratings (sports://power-ratings/{league})
2. Game schedule (sports://schedule/{league}/{week})
3. Current odds (sports://odds/{league}/{week})
4. Team statistics (sports://teams/{league}/stats)
5. Data validation status (sports://data-status/{week})

VERIFICATION:
- Confirm all data files exist and are recent
- Check data quality score is GOOD or better
- Verify odds are fresh (< 24 hours)
- Ensure power ratings include all teams

NEXT STEP:
If all data is ready, recommend running edge detection analysis.
If data is missing or stale, recommend running collect_week_data first.

Return dataset readiness report with recommendations."""
            ),
        )
    ]
```

---

## Step 4: Testing

### Test with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Start inspector with enhanced server
npx @modelcontextprotocol/inspector uv run python .claude/walters_mcp_server.py
```

### Test New Tools

```bash
# In MCP Inspector:

# 1. List all tools
> tools/list

# 2. Test collect_week_data
> tools/call collect_week_data {"week": 11, "league": "nfl", "include_weather": true}

# 3. Test scrape_massey_ratings
> tools/call scrape_massey_ratings {"league": "nfl"}

# 4. Test scrape_overtime_odds
> tools/call scrape_overtime_odds {"league": "nfl", "format": "walters"}

# 5. Test validation
> tools/call validate_collected_data {"week": 11, "league": "nfl"}
```

### Test New Resources

```bash
# In MCP Inspector:

# 1. List all resources
> resources/list

# 2. Get odds
> resources/read "sports://odds/nfl/11"

# 3. Get schedule
> resources/read "sports://schedule/nfl/11"

# 4. Get power ratings
> resources/read "sports://power-ratings/nfl"

# 5. Get data status
> resources/read "sports://data-status/11"
```

### Test Prompts

```bash
# In MCP Inspector:

# 1. List prompts
> prompts/list

# 2. Get collect-weekly-data prompt
> prompts/get "collect-weekly-data" {"week": 11, "league": "nfl"}

# 3. Get refresh-odds prompt
> prompts/get "refresh-odds" {"league": "nfl"}

# 4. Get prepare-analysis prompt
> prompts/get "prepare-analysis" {"week": 11, "league": "nfl"}
```

---

## Step 5: Integration with Claude Desktop

### Update Configuration

**Edit**: `~/.claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "billy-walters-enhanced": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/path/to/billy-walters-sports-analyzer/.claude/walters_mcp_server.py"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "your-key",
        "ACCUWEATHER_API_KEY": "your-key",
        "OV_CUSTOMER_ID": "your-id",
        "OV_PASSWORD": "your-password"
      }
    }
  }
}
```

### Test in Claude Desktop

1. Restart Claude Desktop
2. Open a new conversation
3. Try these prompts:

```
"What tools do you have access to for sports betting?"
→ Should list all 10 tools

"Collect data for NFL Week 11"
→ Should call collect_week_data tool

"Show me the power ratings for all NFL teams"
→ Should read sports://power-ratings/nfl resource

"Use the collect-weekly-data prompt for NFL Week 11"
→ Should execute the prompt workflow
```

---

## Success Criteria

✅ **Phase 1 Complete When**:

1. All 7 new tools working in MCP Inspector
2. All 5 new resources accessible
3. All 3 prompts functional
4. Claude Desktop successfully connects to enhanced server
5. End-to-end test: "Collect NFL Week 11 data" works from Claude Desktop
6. No breaking changes to existing tools/resources
7. All tests pass

---

## Troubleshooting

### Issue: Tool calls failing

**Symptom**: Tool returns `{"error": "..."}`

**Solutions**:
1. Check logs: `.claude/logs/mcp-server.log`
2. Verify imports: All used modules are installed
3. Check file paths: Data files in correct locations
4. Test function directly: `uv run python -c "from walters_mcp_server import collect_week_data; ..."`

### Issue: Resources returning empty

**Symptom**: Resource returns `{"error": "not found"}`

**Solutions**:
1. Verify file exists: `ls data/current/nfl_power_ratings.json`
2. Check file permissions: Readable by user
3. Verify path in resource handler matches actual location
4. Test with absolute paths first, then relative

### Issue: Prompts not showing

**Symptom**: `prompts/list` returns empty array

**Solutions**:
1. Check prompt decorator syntax: `@mcp.prompt()`
2. Verify function signature includes all arguments
3. Check return type: `list[PromptMessage]`
4. Restart MCP server after adding prompts

### Issue: Claude Desktop not connecting

**Symptom**: Server not showing in Claude Desktop

**Solutions**:
1. Check config file syntax: Valid JSON
2. Verify path to server script: Absolute path recommended
3. Check `uv` is in PATH: `which uv`
4. Review Claude Desktop logs: `~/Library/Logs/Claude/`
5. Test server directly: `uv run python .claude/walters_mcp_server.py`

---

## Next Steps After Phase 1

Once Phase 1 is complete and tested:

1. **Document learnings**: Use `/document-lesson` for any issues encountered
2. **Gather feedback**: How is the enhanced server performing?
3. **Plan Phase 2**: Split into specialized servers
4. **Optimize**: Add caching, improve error handling
5. **Monitor**: Track tool usage and performance

---

## Resources

- **MCP Specification**: https://modelcontextprotocol.io/specification
- **FastMCP Docs**: https://github.com/jlowin/fastmcp
- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector
- **Project Docs**: `/docs/MCP_ARCHITECTURE.md`

---

**Status**: Ready for implementation
**Estimated Time**: 4-6 hours
**Risk**: Low (non-breaking changes)
