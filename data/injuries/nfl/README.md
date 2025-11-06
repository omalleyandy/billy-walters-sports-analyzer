# NFL Injury Data

Source: ESPN NFL Injury Reports (https://www.espn.com/nfl/injuries)

Files in this directory:
- `nfl-injuries-YYYYMMDD-HHMMSS.jsonl` - Line-delimited JSON
- `nfl-injuries-YYYYMMDD-HHMMSS.parquet` - Columnar format

Scrape command:
```bash
uv run walters-analyzer scrape-injuries --sport nfl
```
