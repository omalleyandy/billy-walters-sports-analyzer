# NCAA Football Injury Data

Source: ESPN College Football Injury Reports (https://www.espn.com/college-football/injuries)

Files in this directory:
- `ncaaf-injuries-YYYYMMDD-HHMMSS.jsonl` - Line-delimited JSON
- `ncaaf-injuries-YYYYMMDD-HHMMSS.parquet` - Columnar format

Scrape command:
```bash
uv run walters-analyzer scrape-injuries --sport cfb
```
