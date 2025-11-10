# NCAA Football Betting Odds Data

Source: overtime.ag (https://overtime.ag/sports/)

Files in this directory:
- `ncaaf-odds-YYYYMMDD-HHMMSS.jsonl` - Line-delimited JSON (one game per line)
- `ncaaf-odds-YYYYMMDD-HHMMSS.json` - Pretty-printed JSON
- `ncaaf-odds-YYYYMMDD-HHMMSS.csv` - Flattened CSV

Scrape command:
```bash
# Using Chrome DevTools MCP (via agent)
# Manual: python scrape_odds_mcp.py <snapshot_file>
```
