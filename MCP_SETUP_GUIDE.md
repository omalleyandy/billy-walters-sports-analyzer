# MCP Server Setup Guide for Claude Desktop

## Overview

This guide helps you set up the Billy Walters Sports Analyzer to work with Claude Desktop using the Model Context Protocol (MCP). This allows Claude to autonomously scrape odds data and run analysis.

## What You've Built

Your system has three key components:

1. **Chrome DevTools Scraper** (`scrape_odds_mcp.py`): Bypasses Cloudflare to extract NFL betting odds
2. **Billy Walters Valuation System** (`walters_analyzer/`): Analyzes injuries and odds for betting signals
3. **MCP Integration**: Allows Claude to autonomously navigate browsers and extract data

## Prerequisites

- Claude Desktop installed (download from https://claude.ai/download)
- Chrome browser installed
- This repository set up with `uv sync` completed

## Step 1: Install MCP Server for Chrome DevTools

The Chrome DevTools MCP server allows Claude to control a browser and extract data.

### Install via npm:

```bash
npm install -g @modelcontextprotocol/server-chrome-devtools
```

### Or use npx (no installation required):

```bash
# This will be configured in Claude Desktop config
npx -y @modelcontextprotocol/server-chrome-devtools
```

## Step 2: Configure Claude Desktop

Claude Desktop reads its MCP configuration from a JSON file. The location depends on your OS:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Configuration File:

Create or edit the file with this configuration:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-chrome-devtools"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/user/billy-walters-sports-analyzer"
      ]
    }
  }
}
```

**Note:** Replace `/home/user/billy-walters-sports-analyzer` with your actual repository path.

### What This Does:

- **chrome-devtools**: Enables browser automation for odds scraping
- **filesystem**: Allows Claude to read/write files in your project directory

## Step 3: Restart Claude Desktop

After saving the configuration:

1. **Quit Claude Desktop completely** (not just close the window)
2. **Restart Claude Desktop**
3. **Look for MCP indicators** - You should see icons showing MCP servers are connected

## Step 4: Test the MCP Connection

In Claude Desktop, try this prompt:

```
Navigate to https://overtime.ag/sports/ and take a snapshot of the page.
```

Claude should:
1. Use the chrome-devtools MCP to open Chrome
2. Navigate to the overtime.ag sports page
3. Extract the accessibility tree snapshot
4. Show you the data it found

## Step 5: Test the Autonomous Odds Scraper

Now try the full workflow:

```
Use the chrome-devtools MCP to:
1. Navigate to https://overtime.ag/sports/
2. Take a snapshot
3. Save the snapshot to ./snapshots/current_odds.txt
4. Run: uv run python scrape_odds_mcp.py ./snapshots/current_odds.txt
5. Show me the results
```

Claude should:
- Navigate to overtime.ag
- Extract the snapshot
- Pass it to your scraper
- Parse all NFL games
- Save odds data to `data/odds/nfl/`
- Display a summary

## Step 6: Test the Billy Walters Analysis

With odds data collected, run the analysis:

```
Run the Billy Walters injury analysis:
1. uv run python analyze_games_with_injuries.py
2. Show me the top betting signals with edge > 2 points
```

This combines:
- Scraped odds data
- ESPN injury data
- Billy Walters valuation methodology
- Outputs betting recommendations

## Using the Autonomous Agent

### Create a Custom Prompt for Claude Desktop:

Save this as a bookmark or quick command in Claude Desktop:

```markdown
# Autonomous Odds Analysis Agent

Please perform a complete odds analysis:

1. **Scrape Current Odds**:
   - Navigate to https://overtime.ag/sports/
   - Extract all NFL games
   - Save to data/odds/nfl/

2. **Analyze with Billy Walters System**:
   - Run analyze_games_with_injuries.py
   - Identify games with edge > 2 points
   - Show injury impacts and market inefficiencies

3. **Generate Report**:
   - List top 5 betting opportunities
   - Show spread adjustments
   - Calculate Kelly bet sizes
   - Display confidence levels

Please work autonomously and show me the final results.
```

### Expected Output:

```
🏈 BILLY WALTERS BETTING SIGNALS - Nov 7, 2025

TOP OPPORTUNITIES:

1. Browns @ Jets (1:00 PM ET)
   Market Line: CLE -2.5 (-106)
   Billy Walters Adjusted: CLE -5.2
   Edge: 2.7 points
   Reasoning:
   - Jets QB injury (hamstring, 70% capacity): -1.8 pts
   - Jets WR1 out: -1.5 pts
   - Market underreaction: +0.6 pts
   Recommendation: BET Browns -2.5
   Kelly Size: 1.8% of bankroll
   Win Rate: 62%

2. Falcons @ Colts (9:30 AM ET)
   ...
```

## Troubleshooting

### MCP Server Not Connecting

1. Check Claude Desktop logs:
   - **macOS**: `~/Library/Logs/Claude/`
   - **Windows**: `%APPDATA%/Claude/logs/`
   - **Linux**: `~/.config/Claude/logs/`

2. Verify the MCP server is installed:
   ```bash
   npx @modelcontextprotocol/server-chrome-devtools --help
   ```

3. Test manually:
   ```bash
   npx @modelcontextprotocol/server-chrome-devtools
   ```

### Chrome Not Launching

- Ensure Chrome is installed and accessible
- On Linux, you may need: `export CHROME_BIN=/usr/bin/google-chrome`
- Try opening Chrome manually first to verify it works

### Scraper Not Finding Data

- Check that you're on the correct page: https://overtime.ag/sports/
- Verify the snapshot contains data: `cat snapshots/current_odds.txt`
- The page should show NFL games (check the schedule)

### No Games Found

- NFL games may not be visible outside of game weeks
- Check the overtime.ag website manually to see if games are listed
- Try during NFL season (September - February)

## Advanced Usage

### Scheduled Scraping

Create a cron job or scheduled task to run daily:

```bash
# Run every day at 9 AM
0 9 * * * cd /home/user/billy-walters-sports-analyzer && uv run python scrape_odds_mcp.py
```

### Multiple Sportsbooks

Extend the scraper to other sportsbooks:

```python
# Add to scrape_odds_mcp.py
SPORTSBOOKS = [
    "https://overtime.ag/sports/",
    "https://www.bovada.lv/sports/football",
    # Add more...
]
```

### Injury Data Integration

Keep injury data up to date:

```bash
# Run daily before odds scraping
uv run walters-analyzer scrape-injuries --sport nfl
uv run python analyze_games_with_injuries.py
```

## What's Next

1. **Paper Trading**: Track your signals vs. actual outcomes
2. **Backtest**: Validate the Billy Walters methodology with historical data
3. **Optimize**: Tune injury multipliers and position values
4. **Automate**: Set up daily scraping and analysis pipeline

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Chrome DevTools MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/chrome-devtools)
- [Billy Walters Methodology](./BILLY_WALTERS_METHODOLOGY.md)
- [Chrome DevTools Breakthrough Report](./CHROME_DEVTOOLS_BREAKTHROUGH.md)

## Support

For issues:
1. Check logs in `logs/` directory
2. Review `CHROME_DEVTOOLS_BREAKTHROUGH.md` for technical details
3. Test components individually (MCP, scraper, analyzer)
4. File issues in the repository

---

**Status**: Ready for testing with Claude Desktop
**Last Updated**: 2025-11-07
