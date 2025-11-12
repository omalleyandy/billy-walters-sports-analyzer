# NFL Betting Odds Data

Source: overtime.ag (https://overtime.ag/sports/)

Files in this directory:
- `nfl-odds-YYYYMMDD-HHMMSS.jsonl` - Line-delimited JSON (one game per line)
- `nfl-odds-YYYYMMDD-HHMMSS.json` - Pretty-printed JSON
- `nfl-odds-YYYYMMDD-HHMMSS.csv` - Flattened CSV

Scrape command:
```bash
# Using Chrome DevTools MCP (via agent)
# Manual: python scrape_odds_mcp.py <snapshot_file>
```
