# Extracting URLs from Gzipped Sitemaps

## The Problem

Many websites compress their sitemaps using gzip (.gz) to reduce bandwidth. When you encounter a sitemap index like this:

```xml
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://www.footballdb.com/sitemap_players.xml.gz</loc>
    <lastmod>2025-11-21T03:50:04-05:00</lastmod>
  </sitemap>
  <!-- more .gz sitemaps -->
</sitemapindex>
```

You need to:
1. Parse the index XML
2. Download each .gz file
3. Decompress the gzip content
4. Parse the decompressed XML to extract URLs

## The Solution

### Required Libraries

```bash
uv add httpx lxml
```

- **httpx**: Modern HTTP client (async support, better than requests)
- **lxml**: Fast XML parser with XPath support
- **gzip**: Built-in Python module for decompression

### Core Concepts

#### 1. Parse Sitemap Index (Get .gz URLs)

```python
from lxml import etree

# XML namespace for sitemaps
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# Parse index
root = etree.fromstring(xml_content)
sitemap_urls = root.xpath("//sm:sitemap/sm:loc/text()", namespaces=NS)
# Result: ['https://site.com/sitemap1.xml.gz', 'https://site.com/sitemap2.xml.gz', ...]
```

#### 2. Download and Decompress .gz File

```python
import gzip
import httpx

# Download .gz file
response = httpx.get("https://site.com/sitemap.xml.gz")
gzip_content = response.content  # bytes

# Decompress
xml_content = gzip.decompress(gzip_content)  # decompressed bytes
```

#### 3. Parse Sitemap XML (Extract Page URLs)

```python
# Parse decompressed XML
root = etree.fromstring(xml_content)
page_urls = root.xpath("//sm:url/sm:loc/text()", namespaces=NS)
# Result: ['https://site.com/page1', 'https://site.com/page2', ...]
```

## Quick Start

### Simple Example (examples/sitemap_extraction_example.py)

```bash
uv run python examples/sitemap_extraction_example.py
```

Shows the basic concept in ~80 lines of code.

### Full-Featured Script (scripts/utilities/extract_sitemap_urls.py)

```bash
uv run python scripts/utilities/extract_sitemap_urls.py
```

Features:
- Robust error handling
- Progress tracking
- URL categorization
- Saves to `output/sitemap_urls.txt`
- Summary statistics

## Expected Output

```
======================================================================
FootballDB.com Sitemap URL Extractor
======================================================================

Sitemap Index: https://www.footballdb.com/sitemap_index.xml
Output File: output/sitemap_urls.txt

Fetching: https://www.footballdb.com/sitemap_index.xml
Found 10 sitemaps in index

[1/10] Processing: https://www.footballdb.com/sitemap_players.xml.gz
  Decompressing gzip...
  Extracted 45,231 URLs

[2/10] Processing: https://www.footballdb.com/sitemap_teams.xml.gz
  Decompressing gzip...
  Extracted 1,892 URLs

...

======================================================================
Total unique URLs extracted: 523,841
Saving to: output/sitemap_urls.txt
✅ Saved 523,841 URLs to output/sitemap_urls.txt

======================================================================
Sample URLs (first 10):
----------------------------------------------------------------------
  https://www.footballdb.com/games/boxscore/2024-01-01-chiefs-patriots
  https://www.footballdb.com/players/aaron-rodgers-rodgeaa01
  https://www.footballdb.com/teams/nfl/green-bay-packers
  ... (523,831 more)

======================================================================
URL Categories:
----------------------------------------------------------------------
  /players/: 45,231 URLs
  /games/: 312,456 URLs
  /teams/: 1,892 URLs
  /coaches/: 892 URLs
  ...
```

## Common Issues & Solutions

### 403 Forbidden Error

**Problem**: Website blocks automated requests

**Solutions**:
1. **Add User-Agent header**:
   ```python
   headers = {
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
   }
   ```

2. **Use proxy** (if you have one configured):
   ```python
   proxies = {"http://": "http://user:pass@proxy:port"}
   client = httpx.Client(proxies=proxies)
   ```

3. **Add delays between requests**:
   ```python
   import time
   time.sleep(1)  # Be respectful
   ```

4. **Rotate user agents**:
   ```python
   import random
   user_agents = [...]
   headers = {"User-Agent": random.choice(user_agents)}
   ```

### gzip.BadGzipFile: Not a gzipped file

**Problem**: File extension is .gz but content isn't gzipped

**Solution**: Handle both cases
```python
if sitemap_url.endswith(".gz"):
    try:
        xml_content = gzip.decompress(response.content)
    except gzip.BadGzipFile:
        # Not actually gzipped, use as-is
        xml_content = response.content
else:
    xml_content = response.content
```

### Memory Issues with Large Sitemaps

**Problem**: Sitemap has millions of URLs, runs out of memory

**Solution**: Process incrementally
```python
def save_urls_streaming(sitemap_url: str, output_file: Path) -> None:
    """Save URLs one at a time instead of loading all into memory."""
    with output_file.open("a") as f:  # Append mode
        for url in parse_sitemap_streaming(sitemap_url):
            f.write(f"{url}\n")
```

### XML Parsing Errors

**Problem**: Invalid XML or encoding issues

**Solution**: Use error recovery
```python
from lxml import etree

parser = etree.XMLParser(recover=True, encoding='utf-8')
root = etree.fromstring(xml_content, parser=parser)
```

## Integration with Billy Walters Project

### Use Cases

1. **Historical Game Data**: Extract all `/games/` URLs for backtesting
2. **Player Statistics**: Scrape all `/players/` URLs for player data
3. **Team History**: Get all `/teams/` URLs for team analytics
4. **Coach Analysis**: Collect `/coaches/` URLs for coaching impact

### Example: Extract Only Game URLs

```python
def extract_game_urls(all_urls: set[str]) -> list[str]:
    """Filter for game URLs only."""
    return [url for url in all_urls if "/games/" in url]

# Usage
extractor = SitemapExtractor("https://www.footballdb.com/sitemap_index.xml")
all_urls = extractor.extract_all_urls()
game_urls = extract_game_urls(all_urls)

# Save for scraping
with open("output/game_urls_to_scrape.txt", "w") as f:
    for url in game_urls:
        f.write(f"{url}\n")
```

### Next Steps After Extraction

1. **Prioritize URLs**: Filter by date, team, league
2. **Rate Limiting**: Space out requests (e.g., 1 request/second)
3. **Data Storage**: Save to database as you scrape
4. **Error Handling**: Skip and log failed URLs
5. **Progress Tracking**: Resume from last successful URL

## Best Practices

1. **Respect robots.txt**: Check allowed paths and crawl delay
2. **Use appropriate User-Agent**: Identify your bot clearly
3. **Add delays**: Don't hammer the server
4. **Handle errors gracefully**: Skip and log, don't crash
5. **Save progress**: Write URLs incrementally, not all at end
6. **Dedup**: Use set() to avoid duplicate URLs
7. **Validate**: Check URL patterns before scraping

## References

- [Sitemap Protocol](https://www.sitemaps.org/protocol.html)
- [lxml Documentation](https://lxml.de/)
- [httpx Documentation](https://www.python-httpx.org/)
- [Python gzip Module](https://docs.python.org/3/library/gzip.html)

## Files Created

- **examples/sitemap_extraction_example.py**: Simple 80-line example
- **scripts/utilities/extract_sitemap_urls.py**: Production-ready script
- **docs/guides/extracting_gzipped_sitemaps.md**: This guide

## Summary

**The workflow**:
```
Sitemap Index XML
    ↓ (parse with lxml)
List of .gz sitemap URLs
    ↓ (download with httpx)
Gzipped content
    ↓ (decompress with gzip)
Sitemap XML
    ↓ (parse with lxml)
List of page URLs
    ↓ (save to file)
output/sitemap_urls.txt
```

**Key libraries**:
- `lxml` for XML parsing with XPath
- `httpx` for HTTP requests
- `gzip` for decompression (built-in)

**Common pattern**:
```python
import gzip, httpx
from lxml import etree

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# 1. Get index
index = httpx.get(index_url).content
sitemaps = etree.fromstring(index).xpath("//sm:sitemap/sm:loc/text()", namespaces=NS)

# 2. Process each .gz sitemap
for sitemap_url in sitemaps:
    content = httpx.get(sitemap_url).content
    xml = gzip.decompress(content)  # if .gz
    urls = etree.fromstring(xml).xpath("//sm:url/sm:loc/text()", namespaces=NS)
    # Save urls...
```

Done! 🎯
