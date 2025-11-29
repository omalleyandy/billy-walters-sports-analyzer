Scrape X (Twitter) for NFL and NCAAF news, injury updates, and breaking information from official sources.

Usage: /scrape-x-news [options]

Examples:
- /scrape-x-news (all sources, both leagues)
- /scrape-x-news --nfl (NFL sources only)
- /scrape-x-news --ncaaf (NCAAF sources only)
- /scrape-x-news --source @AdamSchefter (specific source)

**Pre-Flight Validation (Automatic)**
Before scraping begins, automatic validation ensures:
- Environment variables set (X_BEARER_TOKEN if using API)
- Output directories exist
- Rate limiting checks (5 calls/day free tier)
- Exit code 0 = Safe to proceed
- Exit code 1 = Rate limit exceeded or missing credentials

This command scrapes X (Twitter) for sports news:

**Official Sources Monitored:**
- @NFL - Official NFL account
- @AdamSchefter - ESPN NFL insider
- @FieldYates - ESPN NFL reporter
- @ESPNCollegeFB - ESPN College Football
- @RapSheet - NFL Network insider
- @JosinaAnderson - CBS Sports NFL

**Data Collected:**
- Breaking injury news
- Game-day inactive lists
- Trade and roster moves
- Weather updates for outdoor games
- Coach and player statements

**Integration with E-Factor System:**
- Automatic injury extraction and classification
- Real-time integration with RealDataIntegrator
- E-Factor adjustment calculations
- Confidence scoring based on source reliability

**Rate Limits (Free Tier):**
- 5 API calls per day
- 24-hour caching to maximize efficiency
- Smart scheduling: Runs best Wednesday-Saturday

**Output:**
- `output/x_news/integrated/x_news_YYYYMMDD_HHMMSS.json`
- Structured data with source, timestamp, relevance score
- Automatic deduplication

**Script:**
```bash
uv run python scripts/scrapers/scrape_x_news_integrated.py --all
```

**When to Run:**
- Wednesday: Initial injury news collection
- Friday: Final injury updates before weekend
- Saturday morning: Last-minute scratches and news
- Avoid: Sunday (rate limits needed for live updates)

**Post-Collection:**
- Auto-triggers post_data_collection_validator.py
- Validates data quality
- Integrates with edge detection pipeline
