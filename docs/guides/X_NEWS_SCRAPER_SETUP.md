# X (Twitter) News & Injury Scraper Setup Guide

**Status**: Ready for production
**Date**: 2025-11-28
**Purpose**: Real-time news and injury updates for E-Factor integration

---

## Quick Summary

The X News Scraper monitors official NFL and NCAAF accounts on X (formerly Twitter) to pull:
- **Injury announcements** from @NFL, @AdamSchefter, @FieldYates
- **Breaking news** on trades, signings, coaching changes
- **Team updates** directly from team X accounts
- **Game status** and weather alerts

This data feeds into the E-Factor system to adjust betting edges when material news breaks.

---

## Setup (5 minutes)

### Step 1: Get X API Credentials

Visit [https://developer.twitter.com/](https://developer.twitter.com/):

1. Click "Sign in"
2. Log in with your X account (or create one)
3. Click "Create project" or go to existing project
4. Go to **Keys & tokens** section
5. Generate:
   - **API Key** (keep safe)
   - **API Secret** (keep safe)
   - **Access Token** (keep safe)
   - **Access Token Secret** (keep safe)

### Step 2: Add to Environment

Add to your `.env` file:

```bash
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

**OR** set as environment variables:

```bash
# PowerShell
$env:X_API_KEY = "your_key"
$env:X_API_SECRET = "your_secret"
$env:X_ACCESS_TOKEN = "your_token"
$env:X_ACCESS_TOKEN_SECRET = "your_token_secret"

# Or in Command Prompt
set X_API_KEY=your_key
```

### Step 3: Test the Scraper

```bash
# Test with NFL injuries
uv run python scripts/scrapers/scrape_x_news.py --league nfl --type injury

# Test with NCAAF news
uv run python scripts/scrapers/scrape_x_news.py --league ncaaf --type news

# Test team-specific posts
uv run python scripts/scrapers/scrape_x_news.py --league nfl --team KC
```

---

## Usage Examples

### Get Recent NFL Injuries

```bash
uv run python scripts/scrapers/scrape_x_news.py \
  --league nfl \
  --type injury \
  --days 7 \
  --export
```

**Output**: JSON file with recent injury posts from official sources

### Get NCAAF News

```bash
uv run python scripts/scrapers/scrape_x_news.py \
  --league ncaaf \
  --type news \
  --days 7
```

### Monitor Specific Team

```bash
# Kansas City Chiefs
uv run python scripts/scrapers/scrape_x_news.py \
  --league nfl \
  --team KC \
  --days 3

# LSU Tigers
uv run python scripts/scrapers/scrape_x_news.py \
  --league ncaaf \
  --team LSU \
  --days 5
```

### Python Code Usage

```python
import asyncio
from walters_analyzer.data_integration.x_news_scraper import XNewsScraper

async def main():
    scraper = XNewsScraper()
    await scraper.initialize()

    # Get NFL injuries
    injuries = await scraper.get_league_news(
        "nfl",
        source_type="injury",
        days=7
    )

    for post in injuries:
        print(f"{post.author}: {post.text}")
        print(f"  Relevance: {post.relevance_score:.0%}")

    # Export results
    await scraper.export_posts(injuries, "nfl", "injuries")

    await scraper.close()

asyncio.run(main())
```

---

## Official Sources Monitored

### NFL

**Injury Sources**:
- @NFL (official league)
- @AdamSchefter (ESPN's top NFL insider)
- @FieldYates (ESPN injury expert)
- @NFL_Motive (NFL injury analytics)
- @nflhealth (official health/injury info)

**News Sources**:
- @NFL
- @nflofficial
- @ESPN
- @NFL_Motive
- @ProFootballTalk (NBC's breaking news)

**Team Accounts** (sample):
- @KansasCity (Chiefs)
- @dallascowboys (Cowboys)
- @packers (Packers)
- @patriots (Patriots)
- @49ers (49ers)
- And 27 more NFL team accounts

### NCAAF

**Injury Sources**:
- @ESPNCollegeFB
- @FieldYates
- @Brett_McMurphy (College Football Insider)
- @Jeff_Schnitt (College sports analyst)

**News Sources**:
- @ESPNCollegeFB
- @ESPN
- @Brett_McMurphy
- @Jeff_Schnitt
- @RedditCFB (community insights)

**Team Accounts** (sample):
- @LSUfootball
- @AlabamaFTBL
- @AggieFootball
- @OU_Football
- And more...

---

## Output Format

Each post includes:

```json
{
  "post_id": "1234567890123456789",
  "author": "Adam Schefter",
  "author_handle": "AdamSchefter",
  "text": "Patrick Mahomes dealing with ankle injury, status for Sunday game TBD",
  "created_at": "2025-11-28T10:30:00",
  "likes": 1250,
  "retweets": 450,
  "source_type": "injury",
  "league": "nfl",
  "team": "KC",
  "relevance_score": 0.95,
  "url": "https://x.com/AdamSchefter/status/1234567890123456789"
}
```

### Post Types

- **injury**: Player injury announcements, status updates
- **news**: Trades, signings, coaching changes, suspensions
- **team_update**: Official team announcements

### Relevance Score

0.0 - 1.0 score based on keyword matching:
- 0.8+ = High relevance
- 0.5-0.8 = Moderate relevance
- <0.5 = Low relevance

---

## Integration with E-Factor

The X News Scraper feeds into the E-Factor system:

```
X News Scraper
    ↓
RealDataIntegrator (gets posts)
    ↓
NewsDecayFunction (applies time decay)
    ↓
IntegratedEdgeCalculator (adjusts betting edges)
    ↓
Record predictions with E-Factor impact
```

Example: If we scrape "Patrick Mahomes out for Week 13", the E-Factor system would:
1. Detect it's a breaking injury post (high relevance)
2. Apply decay based on timing (fresh = full impact, old = reduced impact)
3. Adjust KC's betting edge downward by 4-8 points
4. Record the adjusted edge with E-Factor sources

---

## Troubleshooting

### "X API credentials not found"

**Fix**: Set environment variables
```bash
# Check if set
echo $env:X_API_KEY  # PowerShell
echo %X_API_KEY%     # CMD

# If not set, add to .env file
X_API_KEY=your_key_here
```

### "API rate limit exceeded"

**Info**: X API has rate limits (450 requests/15 min)
**Fix**: Tweepy automatically waits (`wait_on_rate_limit=True`). Scraper will pause and retry automatically.

### "No posts found"

**Possible causes**:
- No recent posts matching keywords
- Search term too specific
- API project needs elevated access tier

**Solution**: Check X/Twitter directly for posts from @AdamSchefter, @NFL, etc.

### "Connection timeout"

**Fix**: Run again, network issue was temporary

```bash
# Retry after 30 seconds
uv run python scripts/scrapers/scrape_x_news.py --league nfl --type injury
```

---

## API Tier Requirements

**Free Tier (Essential)**: Limited to 1 request/second
- Works for small-scale scraping
- May hit rate limits during peak hours
- Good for development/testing

**Elevated Tier**: Higher rate limits
- Recommended for production
- Request via [https://developer.twitter.com/](https://developer.twitter.com/)

**Academic Tier**: Free, very high rate limits
- Available for research/academic use
- Request via API dashboard

---

## Commands Reference

```bash
# NFL injuries
uv run python scripts/scrapers/scrape_x_news.py --league nfl --type injury

# NFL news
uv run python scripts/scrapers/scrape_x_news.py --league nfl --type news

# NCAAF injuries
uv run python scripts/scrapers/scrape_x_news.py --league ncaaf --type injury

# NCAAF news
uv run python scripts/scrapers/scrape_x_news.py --league ncaaf --type news

# Specific team
uv run python scripts/scrapers/scrape_x_news.py --league nfl --team KC

# Past 3 days
uv run python scripts/scrapers/scrape_x_news.py --league nfl --days 3

# Export to JSON
uv run python scripts/scrapers/scrape_x_news.py --league nfl --type injury --export
```

---

## Next Steps

1. **Get API credentials** (5 min)
2. **Add to .env file** (1 min)
3. **Test the scraper** (1 min)
4. **Integrate with data collection** (add to `/collect-all-data`)
5. **Monitor real game weeks** (production use)

---

## Security Notes

- **Never commit API keys** to git
- Use `.env` file (git-ignored)
- Rotate keys periodically
- Monitor for unauthorized access on X dashboard

---

**Resources**:
- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [Tweepy Documentation](https://docs.tweepy.org/)
- [X API Rate Limits](https://developer.twitter.com/en/docs/twitter-api/rate-limits)
