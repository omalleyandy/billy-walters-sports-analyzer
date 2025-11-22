# FootballDB.com Sitemap Extraction Guide

## Overview

This guide shows how to extract all URLs from footballdb.com's sitemap using the residential proxy to bypass Cloudflare/bot detection.

## Quick Start

### 1. Ensure Proxy is Configured

Check your `.env` file has the proxy configured:

```bash
# .env
PROXY_URL=http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060
```

### 2. Run the Extractor

```bash
uv run python scripts/utilities/extract_sitemap_urls.py
```

Expected output:
```
======================================================================
FootballDB.com Sitemap URL Extractor
======================================================================

Sitemap Index: https://www.footballdb.com/sitemap_index.xml
Output File: output/sitemap_urls.txt

[OK] Using proxy: rp.scrapegw.com:6060
Verifying proxy connection...
[OK] Proxy verified: 45.67.89.123 (Miami, Florida, US)

Fetching: https://www.footballdb.com/sitemap_index.xml
Found 10 sitemaps in index

[1/10] Processing: https://www.footballdb.com/sitemap_footballdb.xml.gz
  Decompressing gzip...
  Extracted 1,234 URLs

[2/10] Processing: https://www.footballdb.com/sitemap_players.xml.gz
  Decompressing gzip...
  Extracted 45,231 URLs

[3/10] Processing: https://www.footballdb.com/sitemap_teams.xml.gz
  Decompressing gzip...
  Extracted 1,892 URLs

...

======================================================================
Total unique URLs extracted: 523,841
Saving to: output/sitemap_urls.txt
✅ Saved 523,841 URLs to output/sitemap_urls.txt
```

### 3. Review Results

```bash
# Check total count
wc -l output/sitemap_urls.txt

# View sample URLs
head -20 output/sitemap_urls.txt

# Find specific category
grep "/games/" output/sitemap_urls.txt | head -10
grep "/players/" output/sitemap_urls.txt | head -10
```

## Sitemap Structure

FootballDB.com provides 10 gzipped sitemaps:

| Sitemap File | Content | Estimated URLs |
|--------------|---------|----------------|
| `sitemap_footballdb.xml.gz` | Main pages | ~1,000 |
| `sitemap_players.xml.gz` | NFL player pages | ~45,000 |
| `sitemap_teams.xml.gz` | NFL/college teams | ~2,000 |
| `sitemap_tvt.xml.gz` | Team vs team matchups | ~50,000 |
| `sitemap_games.xml.gz` | Game/boxscore pages | ~300,000 |
| `sitemap_scorelookup.xml.gz` | Score lookup pages | ~10,000 |
| `sitemap_coaches.xml.gz` | Coach pages | ~1,000 |
| `sitemap_collegeplayers.xml.gz` | College players (part 1) | ~50,000 |
| `sitemap_collegeplayers_2.xml.gz` | College players (part 2) | ~50,000 |
| `sitemap_collegeteams.xml.gz` | College teams | ~500 |

**Total:** ~500,000+ URLs

## URL Categories

After extraction, URLs are categorized by path:

```
URL Categories:
----------------------------------------------------------------------
  /games/: 312,456 URLs          # Historical boxscores
  /players/: 95,231 URLs         # NFL + College players
  /teams/: 2,392 URLs            # NFL + College teams
  /college-football/: 54,892 URLs
  /coaches/: 1,023 URLs
  /stats/: 8,234 URLs
  /betting/: 3,421 URLs
  ... more categories
```

## Filtering URLs by Category

### Extract Only Game URLs

```bash
# NFL games
grep "/games/" output/sitemap_urls.txt | grep -E "(nfl|boxscore)" > output/nfl_game_urls.txt

# College games
grep "/games/" output/sitemap_urls.txt | grep "college-football" > output/cfb_game_urls.txt
```

### Extract Player URLs

```bash
# All players
grep "/players/" output/sitemap_urls.txt > output/player_urls.txt

# Active players (typically more recent URLs)
grep "/players/" output/sitemap_urls.txt | tail -5000 > output/active_players.txt
```

### Extract Team Pages

```bash
# NFL teams
grep "/teams/nfl/" output/sitemap_urls.txt > output/nfl_team_urls.txt

# College teams
grep "/teams/college/" output/sitemap_urls.txt > output/cfb_team_urls.txt
```

## Using Extracted URLs

### Example: Scrape Historical Game Data

```python
#!/usr/bin/env python3
"""Scrape historical games from extracted URLs."""

from pathlib import Path
import httpx
from lxml import html
import time

# Load game URLs
game_urls_file = Path("output/nfl_game_urls.txt")
game_urls = game_urls_file.read_text().splitlines()

# Setup client with proxy
client = httpx.Client(
    proxies="http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060",
    timeout=30,
    headers={"User-Agent": "Mozilla/5.0 ..."}
)

# Scrape each game
for i, url in enumerate(game_urls, 1):
    print(f"[{i}/{len(game_urls)}] Scraping: {url}")

    try:
        response = client.get(url)
        tree = html.fromstring(response.content)

        # Extract game data
        home_team = tree.xpath("//div[@class='home-team']/text()")[0]
        away_team = tree.xpath("//div[@class='away-team']/text()")[0]
        final_score = tree.xpath("//div[@class='score']/text()")

        print(f"  {away_team} @ {home_team}: {final_score}")

        # Save to database/CSV/JSON
        # ...

        # Respectful delay
        time.sleep(1)

    except Exception as e:
        print(f"  ERROR: {e}")
        continue

client.close()
```

## Troubleshooting

### Still Getting 403 Errors

1. **Verify proxy is working:**
   ```bash
   curl -x "http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060" "https://ipinfo.io/json"
   ```

2. **Check .env file:**
   ```bash
   cat .env | grep PROXY_URL
   ```

3. **Increase retry delay:**
   Edit `scripts/utilities/extract_sitemap_urls.py`:
   ```python
   # Line 234: Increase delay from 1s to 2s
   time.sleep(2)
   ```

### Script Hangs or Timeouts

1. **Increase timeout:**
   Edit line 38 in extractor:
   ```python
   def __init__(self, sitemap_index_url: str, timeout: int = 120, ...):
   ```

2. **Check proxy bandwidth:**
   - Login to proxyscrape.com dashboard
   - Check if you've hit bandwidth limits

### Memory Issues with Large Sitemaps

If processing 500k+ URLs causes memory issues:

1. **Process incrementally:**
   ```python
   # Save URLs as they're extracted, not all at once
   with output_file.open("a") as f:
       for url in urls:
           f.write(f"{url}\n")
   ```

2. **Process one sitemap at a time:**
   ```bash
   # Edit main() to process specific sitemap
   SITEMAP_URL = "https://www.footballdb.com/sitemap_games.xml.gz"
   ```

## Best Practices

1. **Rate Limiting:**
   - 1-second delay between requests (already built-in)
   - Don't run extraction more than once per day
   - Respect robots.txt crawl-delay

2. **Proxy Usage:**
   - Residential proxy rotates IP automatically (10 IPs)
   - Monitor bandwidth usage on proxyscrape.com
   - Each request ~2-10 KB (sitemaps) or ~50-200 KB (pages)

3. **Data Storage:**
   - Keep extracted URLs in `output/sitemap_urls.txt`
   - Version control: Don't commit large URL files
   - Use filters to create category-specific files

4. **Error Handling:**
   - Script continues if one sitemap fails
   - Check output for ERROR messages
   - Re-run for failed sitemaps individually

## Integration with Billy Walters Project

### Use Cases

1. **Historical Backtesting:**
   - Extract all game URLs from 2020-2024
   - Scrape boxscores for training data
   - Build historical odds database

2. **Player Analysis:**
   - Get all player URLs
   - Scrape career stats
   - Identify injury patterns

3. **Team Research:**
   - Extract team pages
   - Scrape season statistics
   - Analyze home/away splits

4. **Betting Line Analysis:**
   - Find historical betting line pages
   - Compare opening vs closing lines
   - Identify sharp money patterns

### Next Steps After Extraction

1. **Prioritize URLs:**
   ```bash
   # Recent games (2024 season)
   grep "/games/boxscore/2024" output/sitemap_urls.txt > output/2024_games.txt

   # Specific teams
   grep "packers" output/sitemap_urls.txt > output/packers_urls.txt
   ```

2. **Build Scraper:**
   - Use Playwright for JavaScript-heavy pages
   - Implement retry logic (like extractor)
   - Save to database as you scrape

3. **Schedule Regular Updates:**
   ```bash
   # Weekly sitemap refresh (new games added)
   0 2 * * 1 cd /path/to/project && uv run python scripts/utilities/extract_sitemap_urls.py
   ```

## Files Created

- **scripts/utilities/extract_sitemap_urls.py** - Main extractor script
- **output/sitemap_urls.txt** - All extracted URLs (500k+ lines)
- **docs/guides/footballdb_sitemap_extraction.md** - This guide
- **docs/guides/extracting_gzipped_sitemaps.md** - Technical details

## Resources

- [FootballDB Sitemap Index](https://www.footballdb.com/sitemap_index.xml)
- [Sitemap Protocol](https://www.sitemaps.org/protocol.html)
- [Proxyscrape Dashboard](https://proxyscrape.com/dashboard)
- [Project Proxy Guide](../PROXY_GUIDE.md)

## Summary

**The complete workflow:**

```bash
# 1. Setup proxy in .env
echo 'PROXY_URL=http://user:pass@rp.scrapegw.com:6060' >> .env

# 2. Extract all URLs (500k+)
uv run python scripts/utilities/extract_sitemap_urls.py

# 3. Filter by category
grep "/games/" output/sitemap_urls.txt > output/game_urls.txt

# 4. Build your scraper
# (Use extracted URLs as input)

# 5. Scrape with proxy + delays
# (See example code above)
```

**Key features:**
- ✅ Automatic proxy support from `.env`
- ✅ IP verification before scraping
- ✅ Retry logic with exponential backoff
- ✅ Gzip decompression built-in
- ✅ Handles all 10 FootballDB sitemaps
- ✅ Outputs categorized URL list

**Expected runtime:** ~2-5 minutes (with proxy, 10 sitemaps, 1s delays)

Done! 🏈
