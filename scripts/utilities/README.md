# Utilities Scripts

Helper scripts for data extraction and processing.

## extract_sitemap_urls.py

Extract all URLs from gzipped sitemaps (e.g., footballdb.com).

### Features

- ✅ **Proxy Support**: Auto-uses `PROXY_URL` from `.env` to bypass bot detection
- ✅ **Gzip Decompression**: Handles .gz sitemap files automatically
- ✅ **Retry Logic**: Exponential backoff for 403/407/429 errors (5 retries)
- ✅ **IP Verification**: Confirms proxy is working before starting
- ✅ **Rate Limiting**: 1-second delay between sitemap requests
- ✅ **Progress Tracking**: Shows extraction progress with counts
- ✅ **URL Categorization**: Automatic categorization by path (/games/, /players/, etc.)

### Quick Start

```bash
# Ensure proxy configured in .env
echo 'PROXY_URLhttp://5iwdzupyp3mzyv6-country-us:29eplg6c8ctwjrs@rp.scrapegw.com:6060' >> .env

# Run extractor
uv run python scripts/utilities/extract_sitemap_urls.py

# Results saved to
output/sitemap_urls.txt
```

### Expected Output

```
======================================================================
FootballDB.com Sitemap URL Extractor
======================================================================

[OK] Using proxy: rp.scrapegw.com:6060
Verifying proxy connection...
[OK] Proxy verified: 45.67.89.123 (Miami, Florida, US)

Fetching: https://www.footballdb.com/sitemap_index.xml
Found 10 sitemaps in index

[1/10] Processing: https://www.footballdb.com/sitemap_players.xml.gz
  Decompressing gzip...
  Extracted 45,231 URLs

...

======================================================================
Total unique URLs extracted: 523,841
✅ Saved 523,841 URLs to output/sitemap_urls.txt

======================================================================
URL Categories:
----------------------------------------------------------------------
  /games/: 312,456 URLs
  /players/: 95,231 URLs
  /teams/: 2,392 URLs
  ...
```

### Configuration

Edit script to customize:

```python
# Line 260: Change sitemap URL
SITEMAP_INDEX_URL = "https://www.footballdb.com/sitemap_index.xml"

# Line 261: Change output file
OUTPUT_FILE = Path("output/custom_urls.txt")

# Line 38: Adjust timeout
def __init__(self, ..., timeout: int = 120):  # 2 minutes

# Line 38: Disable proxy
def __init__(self, ..., use_proxy: bool = False):
```

### Filtering Results

```bash
# Extract specific categories
grep "/games/" output/sitemap_urls.txt > output/game_urls.txt
grep "/players/" output/sitemap_urls.txt > output/player_urls.txt

# Filter by year (e.g., 2024 games)
grep "/games/boxscore/2024" output/sitemap_urls.txt > output/2024_games.txt

# Count by category
cut -d'/' -f4 output/sitemap_urls.txt | sort | uniq -c | sort -rn
```

### Troubleshooting

**403 Forbidden Error:**
- Ensure `PROXY_URL` is set in `.env`
- Verify proxy working: `curl -x "http://user:pass@proxy:port" "https://ipinfo.io/json"`
- Check proxyscrape.com dashboard for bandwidth limits

**Timeout Errors:**
- Increase timeout (line 38): `timeout: int = 120`
- Check proxy speed with direct curl test

**Memory Issues:**
- Process one sitemap at a time (edit `SITEMAP_INDEX_URL`)
- Save URLs incrementally instead of all at once

### Documentation

- **Technical Guide**: [docs/guides/extracting_gzipped_sitemaps.md](../../docs/guides/extracting_gzipped_sitemaps.md)
- **FootballDB Guide**: [docs/guides/footballdb_sitemap_extraction.md](../../docs/guides/footballdb_sitemap_extraction.md)
- **Proxy Setup**: See project proxy configuration guide

### Use Cases for Billy Walters Project

1. **Historical Game Data**: Extract all `/games/` URLs for backtesting
2. **Player Statistics**: Get all `/players/` URLs for player analysis
3. **Team Research**: Extract `/teams/` URLs for team historical data
4. **Betting Lines**: Find historical odds and line movement data

### Next Steps

After extraction:
1. Filter URLs by category (games, players, teams)
2. Build scraper for target pages
3. Use proxy for actual scraping
4. Save data to database/CSV/JSON

See `docs/guides/footballdb_sitemap_extraction.md` for complete workflow and examples.
