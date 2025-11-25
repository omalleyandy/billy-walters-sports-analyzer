# Action Network Sitemap Scraper Guide

## Overview

Advanced web scraping tool for Action Network that extracts NFL and NCAAF game URLs and content categories from nested sitemaps using Chrome DevTools techniques.

**Key Features:**
- Async/await pattern for high performance
- Regex-based URL categorization
- Nested sitemap crawling (index → general → category-specific)
- Stealth headers and proxy support
- JSONL output format for data pipeline integration
- lxml-based efficient XML parsing
- Intelligent category detection

**Data Extracted:**
- **NFL Games**: Direct game page URLs
- **NCAAF Games**: Direct game page URLs
- **NFL Categories**: futures, odds, strategy, teasers, public betting
- **NCAAF Categories**: futures, odds

---

## Technical Architecture

### URL Patterns

#### Game URLs (Regex)
```python
nfl_game_pattern = re.compile(r"/nfl-game/", re.IGNORECASE)
ncaaf_game_pattern = re.compile(r"/ncaaf-game/", re.IGNORECASE)
```

**Examples:**
- `/nfl-game/chiefs-vs-bills-november-2024`
- `/nfl-game/49ers-vs-cowboys`
- `/ncaaf-game/ohio-state-vs-michigan`

#### Category Patterns (NFL)

| Category | Pattern | Example URLs |
|----------|---------|--------------|
| `futures` | `/nfl/futures` | `/nfl/futures`, `/nfl/super-bowl-futures` |
| `odds` | `/nfl/odds` | `/nfl/odds`, `/nfl/game-odds` |
| `sports-betting-dfs-strategy-nfl-nba-information-news` | `/sports-betting.*nfl` \| `/nfl.*strategy` | `/sports-betting-dfs-strategy-nfl-nba`, `/nfl-betting-strategy` |
| `teasers-nfl-betting-tips-over-under-total` | `/nfl.*teaser` \| `/nfl.*tips` \| `/nfl.*over-under` \| `/nfl.*total` | `/nfl-betting-tips-over-under-total`, `/nfl-teasers` |
| `public-betting` | `/nfl.*public` \| `/nfl.*betting` | `/nfl-public-betting`, `/nfl-betting-insights` |

#### Category Patterns (NCAAF)

| Category | Pattern | Example URLs |
|----------|---------|--------------|
| `futures` | `/ncaaf/futures` | `/ncaaf/futures`, `/ncaaf/playoff-futures` |
| `odds` | `/ncaaf/odds` | `/ncaaf/odds`, `/ncaaf/game-odds` |

### Sitemap Hierarchy

```
sitemap.xml (index)
├── sitemap-general.xml (PRIMARY - processes first)
│   ├── /nfl-game/* (100+ game URLs)
│   ├── /ncaaf-game/* (100+ game URLs)
│   ├── /nfl/odds, /nfl/futures
│   └── /ncaaf/odds, /ncaaf/futures
├── sitemap-nfl.xml
│   ├── /nfl/* category pages
│   └── /nfl-game/* variations
└── sitemap-ncaaf.xml
    ├── /ncaaf/* category pages
    └── /ncaaf-game/* variations
```

**Note:** Processing order matters for efficiency:
1. **General sitemap first** (highest density of game URLs)
2. **Category-specific sitemaps** (catch category pages)

### HTTP Requests Strategy

**Stealth Headers:**
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Accept": "application/xml, text/xml, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}
```

**Proxy Support:**
- Uses `PROXY_URL`, `PROXY_USER`, `PROXY_PASS` from `.env`
- Format: `http://host:port` or `socks5://host:port`
- Credentials injected: `http://user:pass@host:port`

**Timeouts & Rate Limiting:**
- Request timeout: 30 seconds
- Inter-request delay: 0.5 seconds (to avoid rate limiting)
- Automatic redirect following

---

## Installation & Setup

### 1. Install Dependencies

```bash
# Add required packages
uv add httpx lxml

# If proxy authentication needed
# (already in requirements)
```

### 2. Configure Environment

Create `.env` file (never commit):

```bash
# Proxy configuration (optional)
PROXY_URL=http://proxy-host:port
PROXY_USER=proxy_username
PROXY_PASS=proxy_password

# Or use SOCKS5
PROXY_URL=socks5://proxy-host:port
```

### 3. Verify Setup

```bash
# Check imports
uv run python -c "from src.data.action_network_sitemap_scraper import ActionNetworkSitemapScraper; print('[OK] Scraper imported successfully')"
```

---

## Usage

### Basic Usage

```bash
# Run scraper with defaults (saves to output/action_network/)
uv run python scripts/scrapers/scrape_action_network_sitemap.py
```

### Programmatic Usage

```python
import asyncio
from src.data.action_network_sitemap_scraper import ActionNetworkSitemapScraper

async def main():
    scraper = ActionNetworkSitemapScraper(
        output_base="data/my_output"
    )
    await scraper.run()

asyncio.run(main())
```

### Advanced Options

```python
# Custom output directory
scraper = ActionNetworkSitemapScraper(
    output_base="custom/path"
)

# Scraper automatically:
# - Fetches sitemap index
# - Parses nested sitemaps
# - Categorizes URLs
# - Saves JSONL files
# - Generates summary report
```

---

## Output Format

### Directory Structure

```
output/action_network/
├── nfl/
│   ├── games_20241115_143022.jsonl          # All NFL game URLs
│   ├── futures_20241115_143022.jsonl        # NFL futures pages
│   ├── odds_20241115_143022.jsonl           # NFL odds pages
│   ├── sports-betting-dfs-strategy-nfl-...  # NFL strategy pages
│   └── teasers-nfl-betting-tips-...         # NFL teaser/tips pages
├── ncaaf/
│   ├── games_20241115_143022.jsonl          # All NCAAF game URLs
│   ├── futures_20241115_143022.jsonl        # NCAAF futures pages
│   └── odds_20241115_143022.jsonl           # NCAAF odds pages
└── scrape_summary_20241115_143022.json      # Summary statistics
```

### JSONL Record Format

**Game Record:**
```json
{
  "url": "https://www.actionnetwork.com/nfl-game/chiefs-vs-bills-november-28-2024",
  "league": "nfl",
  "content_type": "game",
  "category": null,
  "path": "/nfl-game/chiefs-vs-bills-november-28-2024",
  "path_parts": ["nfl-game", "chiefs-vs-bills-november-28-2024"],
  "slug": "chiefs-vs-bills-november-28-2024",
  "scraped_at": "2024-11-15T14:30:22.123456",
  "domain": "www.actionnetwork.com"
}
```

**Category Record:**
```json
{
  "url": "https://www.actionnetwork.com/nfl/odds",
  "league": "nfl",
  "content_type": "category",
  "category": "odds",
  "path": "/nfl/odds",
  "path_parts": ["nfl", "odds"],
  "slug": "odds",
  "scraped_at": "2024-11-15T14:30:22.123456",
  "domain": "www.actionnetwork.com"
}
```

### Summary Report

**scrape_summary_*.json:**
```json
{
  "timestamp": "2024-11-15T14:30:22.123456",
  "nfl_games": 145,
  "ncaaf_games": 287,
  "nfl_categories": {
    "odds": 1,
    "futures": 1,
    "sports-betting-dfs-strategy-nfl-nba-information-news": 8,
    "teasers-nfl-betting-tips-over-under-total": 12,
    "public-betting": 5
  },
  "ncaaf_categories": {
    "odds": 1,
    "futures": 1
  }
}
```

---

## Integration with Data Pipeline

### 1. Load JSONL Files

```python
import json

# Load game URLs
nfl_games = []
with open("output/action_network/nfl/games_*.jsonl") as f:
    for line in f:
        nfl_games.append(json.loads(line))

print(f"Loaded {len(nfl_games)} NFL games")
```

### 2. Extract Metadata

```python
# Extract slugs for content scraping
game_slugs = [record["slug"] for record in nfl_games]

# Extract categories
odd_pages = [
    record["url"] for record in
    json.loads(line)
    for line in open("output/action_network/nfl/odds_*.jsonl")
]
```

### 3. Filter by Date/Week

```python
import re
from datetime import datetime

# Extract date from slug
def extract_date(slug):
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", slug)
    if match:
        return datetime(*map(int, match.groups()))
    return None

# Filter Week 11 games (Nov 10-17)
week_11_games = [
    record for record in nfl_games
    if extract_date(record["slug"]) and
    datetime(2024, 11, 10) <= extract_date(record["slug"]) <= datetime(2024, 11, 17)
]
```

---

## Regex Pattern Reference

### Building Custom Patterns

```python
import re

# Case-insensitive matching
pattern = re.compile(r"/nfl-game/", re.IGNORECASE)

# Match multiple patterns
pattern = re.compile(
    r"/nfl/futures|/nfl-future|/futures-nfl",
    re.IGNORECASE
)

# Match with variations
pattern = re.compile(
    r"/nfl.*teaser|/nfl.*tips|/teasers.*nfl",
    re.IGNORECASE
)

# Negative lookahead (exclude)
pattern = re.compile(
    r"/nfl(?!-game)/",  # Match /nfl/ but not /nfl-game/
    re.IGNORECASE
)
```

### Testing Patterns

```python
# Test your pattern
test_urls = [
    "/nfl-game/test",
    "/NCAAF-GAME/test",
    "/nfl/odds",
    "/nfl/futures"
]

pattern = re.compile(r"/nfl-game/", re.IGNORECASE)

for url in test_urls:
    if pattern.search(url):
        print(f"[MATCH] {url}")
    else:
        print(f"[NO MATCH] {url}")
```

---

## Troubleshooting

### Issue: "Failed to fetch sitemap"

**Symptoms:**
```
[ERROR] HTTP Error fetching https://www.actionnetwork.com/sitemap.xml: [Errno -2] Name or service not known
```

**Solutions:**
1. Check internet connectivity: `ping www.actionnetwork.com`
2. Verify proxy settings (if configured)
3. Check firewall/antivirus blocking Action Network
4. Try without proxy first: Remove `PROXY_URL` from `.env`

### Issue: "No sitemaps found in index"

**Symptoms:**
```
[ERROR] No sitemaps found in index
```

**Solutions:**
1. Check XML parsing: Action Network may have changed sitemap structure
2. Verify namespace: `http://www.sitemaps.org/schemas/sitemap/0.9`
3. Test manually: `curl https://www.actionnetwork.com/sitemap.xml`
4. Check if robots.txt blocks sitemaps: `curl https://www.actionnetwork.com/robots.txt`

### Issue: "Timeouts or slow collection"

**Symptoms:**
```
[WARNING] Failed to fetch: https://www.actionnetwork.com/sitemap-nfl.xml (timeout)
```

**Solutions:**
1. Increase timeout: Edit line in scraper `timeout=60` (seconds)
2. Reduce concurrent requests: Adjust delay between requests
3. Use proxy if IP throttled: Configure `PROXY_URL` in `.env`
4. Check network: `tracert www.actionnetwork.com`

### Issue: "Regex patterns not matching expected URLs"

**Solutions:**
1. Test pattern independently:
   ```python
   import re
   pattern = re.compile(r"/nfl-game/", re.IGNORECASE)
   assert pattern.search("/NFL-GAME/test")
   ```
2. Check URL encoding (spaces → `%20`)
3. Verify pattern case sensitivity
4. Review captured sitemaps for actual URL structure

### Issue: "JSONL files empty"

**Symptoms:**
```
Saved 0 NFL games to output/action_network/nfl/games_*.jsonl
```

**Solutions:**
1. Verify URLs were captured: Check scraper output logs
2. Check regex patterns: URLs might not match categorization
3. Verify XML parsing: Sitemaps might be empty
4. Check file permissions: Can write to output directory?

---

## Performance Metrics

### Typical Execution

| Phase | Duration | Items |
|-------|----------|-------|
| Fetch sitemap index | ~2 sec | 1 index |
| Fetch general sitemap | ~3 sec | 400+ URLs |
| Fetch category sitemaps | ~10 sec | 3-5 sitemaps |
| Parse & categorize | ~1 sec | 500+ URLs |
| Write JSONL files | <1 sec | 500+ records |
| **Total** | **~16 sec** | **500+ records** |

### Resource Usage

| Metric | Value |
|--------|-------|
| Memory | ~50-100 MB |
| Network | ~2-5 MB |
| Disk I/O | ~500 KB |
| CPU | Low (mostly I/O wait) |

### Optimization Tips

1. **Parallel Sitemap Fetching**: Modify to fetch multiple sitemaps concurrently
   ```python
   tasks = [self.fetch_xml(url) for url in sitemap_urls]
   await asyncio.gather(*tasks)
   ```

2. **Streaming JSONL Output**: Write records as they're processed (already implemented)

3. **Proxy Connection Pooling**: Reuse proxy connections across requests (httpx handles automatically)

---

## Advanced Usage

### Custom Output Handler

```python
class CustomActionNetworkScraper(ActionNetworkSitemapScraper):
    async def process_game_url(self, url: str) -> None:
        """Custom handler for each game URL."""
        # Extract metadata
        slug = url.split('/')[-1]

        # Store in database
        await self.db.insert({
            'url': url,
            'slug': slug,
            'source': 'action_network_sitemap'
        })

scraper = CustomActionNetworkScraper()
await scraper.run()
```

### Filtering During Collection

```python
def process_urls(self, urls: List[str]) -> None:
    """Override to filter URLs."""
    for url in urls:
        # Skip certain categories
        if "outdated" in url:
            continue

        # Only collect recent games
        if datetime.now().year in url:
            super().process_urls([url])
```

### Incremental Updates

```python
import os
from pathlib import Path

# Load existing URLs
existing_urls = set()
for file in Path("output/action_network").glob("**/games_*.jsonl"):
    with open(file) as f:
        for line in f:
            existing_urls.add(json.loads(line)["url"])

# Skip already collected
def process_urls(self, urls):
    new_urls = [u for u in urls if u not in existing_urls]
    super().process_urls(new_urls)
```

---

## DevTools Techniques Used

### 1. Stealth Headers
- Realistic User-Agent
- Browser-standard headers
- Accept-Encoding for compression

### 2. Rate Limiting
- Inter-request delays (0.5 sec)
- Timeout handling
- Connection pooling

### 3. Robust Parsing
- Namespace-aware XML parsing (lxml)
- Fallback patterns
- Error handling

### 4. Async/Await
- Non-blocking I/O
- Efficient resource usage
- Scalable architecture

### 5. Regex Mastery
- Case-insensitive matching
- Pattern alternatives
- Nested path support

---

## Related Documentation

- **API Integration**: `docs/api/requirements_action_network.txt`
- **Billy Walters Edge Detection**: `docs/billy_walters_edge_detection.md`
- **Data Pipeline**: `src/data/data_orchestrator.py`
- **MCP Server**: `.claude/walters_mcp_server.py`

---

## Support & Issues

For issues or improvements:

1. Check `LESSONS_LEARNED.md` for similar problems
2. Review test suite: `tests/test_action_network_sitemap_scraper.py`
3. Enable debug logging: Set `logging.level=DEBUG`
4. Report with: URL, error message, traceback

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-11-15 | Initial release with NFL/NCAAF game URL extraction |
| | | Async/await pattern for performance |
| | | Regex-based categorization |
| | | JSONL output format |
| | | Proxy & stealth support |

---

## License & Attribution

Part of Billy Walters Sports Analyzer project.
Uses lxml, httpx, and async/await patterns.
Designed for educational sports analytics purposes.
