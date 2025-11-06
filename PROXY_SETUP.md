# Proxy Configuration Guide

This guide covers setting up and using residential proxies with the Billy Walters Sports Analyzer scraping system to improve stealth and bypass Cloudflare protection.

## Overview

Your proxyscrape.com residential proxy provides:
- **10 rotating residential IPs** - Different IP for each request
- **Cloudflare bypass** - Residential IPs avoid bot detection
- **Geographic distribution** - IPs from various US locations
- **Automatic rotation** - No manual IP management needed

## Quick Setup

### 1. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Add your proxy credentials to `.env`:
```bash
# Proxyscrape.com Residential Proxy
PROXY_URL=http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060

# Overtime.ag Login (required)
OV_CUSTOMER_ID=your_customer_id_here
OV_CUSTOMER_PASSWORD=your_password_here
```

**Important:** Never commit `.env` to git - it contains your credentials!

### 2. Test Proxy Connection

Test your proxy with curl:
```bash
curl -x "http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060" "https://ipinfo.io/json"
```

You should see output like:
```json
{
  "ip": "xx.xx.xx.xx",
  "city": "Miami",
  "region": "Florida",
  "country": "US",
  "org": "AS12345 Residential ISP"
}
```

### 3. Run Scrapers with Proxy

The proxy is automatically used by all scrapers:

```powershell
# Pre-game odds scraping with proxy
uv run walters-analyzer scrape-overtime --sport nfl

# Live betting odds with proxy
uv run walters-analyzer scrape-overtime --live

# Injury scraping with proxy
uv run walters-analyzer scrape-injuries --sport nfl
```

## How It Works

### Automatic Proxy Integration

When you set `PROXY_URL` in `.env`, all spiders automatically:

1. **Configure Playwright** to route traffic through the proxy
2. **Verify IP** before scraping (logs the current proxy IP location)
3. **Retry on failures** with exponential backoff
4. **Rotate IPs** automatically (10 different IPs in the pool)

### Proxy Verification Logs

When running a scraper, you'll see:
```
[pregame_odds] INFO: ✓ Using residential proxy: rp.scrapegw.com:6060
[pregame_odds] INFO: Verifying proxy IP...
[pregame_odds] INFO: ✓ Proxy IP verified: 45.67.89.123 (Miami, Florida, US)
```

### Stealth Features Enabled

The scrapers now include:

- ✅ **Latest Chrome User-Agent** (Chrome 131, January 2025)
- ✅ **Residential proxy rotation** (10 IPs)
- ✅ **Realistic viewport/timezone** (1920x1080, US timezones)
- ✅ **Retry with backoff** (5 retries on 403/407/429 errors)
- ✅ **IP verification** before scraping

## Troubleshooting

### Proxy Connection Failed

**Error:** `Could not resolve proxy: rp.scrapegw.com`

**Solutions:**
1. Check your internet connection
2. Verify the proxy URL in `.env` is correct
3. Ensure your proxyscrape.com subscription is active
4. Try testing with curl (see test command above)

### 407 Proxy Authentication Required

**Error:** `407 Proxy Authentication Required`

**Solutions:**
1. Double-check username and password in `PROXY_URL`
2. Ensure no extra spaces in the `.env` file
3. Verify credentials at https://proxyscrape.com dashboard

### Proxy Too Slow

**Issue:** Scraping takes a long time

**Solutions:**
1. This is normal with residential proxies (slower than datacenter)
2. Expected latency: 2-5 seconds per request
3. Adjust timeout if needed:
   ```python
   # In spider custom_settings
   "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 120_000,  # 2 minutes
   ```

### IP Blocked by Cloudflare

**Issue:** Still getting Cloudflare challenges

**Solutions:**
1. Residential proxies should bypass most challenges
2. If persistent, contact proxyscrape.com support
3. Consider adding random delays between requests:
   ```python
   # In settings.py
   AUTOTHROTTLE_START_DELAY = 2.0  # Increase from 1.0
   ```

## Advanced Configuration

### Disable Proxy Temporarily

To scrape without the proxy (testing purposes):

```bash
# Comment out in .env
# PROXY_URL=http://...
```

Or set to empty:
```bash
PROXY_URL=
```

### Proxy Statistics

The proxy pool provides:
- **10 rotating IPs** per subscription
- **Geographic coverage:** US-based residential IPs
- **Rotation method:** Automatic per-request
- **Concurrent connections:** Depends on your proxyscrape.com plan

### Custom Proxy Settings

If you have multiple proxies, you can use `OVERTIME_PROXY` as an alternative:

```bash
# Primary proxy
PROXY_URL=http://user1:pass1@proxy1.com:6060

# Alternative for overtime.ag specifically
OVERTIME_PROXY=http://user2:pass2@proxy2.com:8080
```

The spiders check both variables (OVERTIME_PROXY takes precedence for overtime.ag spiders).

## Monitoring Proxy Usage

### Check IP Rotation

Run the scraper multiple times and check the logs:

```bash
uv run walters-analyzer scrape-overtime --sport nfl
# Look for: "Proxy IP verified: 45.67.89.123 (Miami, FL, US)"

# Run again
uv run walters-analyzer scrape-overtime --sport nfl
# Should show different IP: "Proxy IP verified: 67.89.123.45 (Dallas, TX, US)"
```

### Proxy Health Check

Test proxy directly:
```bash
# Check IP info
curl -x "http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060" "https://ipinfo.io/json"

# Check if proxy is residential
curl -x "http://5iwdzupyp3mzyv6:9cz69tojhtqot8f@rp.scrapegw.com:6060" "https://ipinfo.io/json" | grep "org"
# Should show residential ISP, NOT "AS15169 Google" or datacenter
```

## Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore`, but double-check
2. **Rotate credentials periodically** - Update proxy password monthly
3. **Monitor usage** - Check proxyscrape.com dashboard for bandwidth
4. **Use HTTPS** - Proxy URL uses `http://` but target sites use HTTPS (end-to-end encryption)
5. **Separate accounts** - Consider different credentials for dev/prod

## Cost Optimization

Your proxyscrape.com plan likely includes:
- **Bandwidth limits** - Monitor usage in dashboard
- **Concurrent connections** - Check your plan limits
- **IP pool size** - 10 rotating IPs (confirm in dashboard)

To reduce costs:
1. Scrape less frequently (e.g., once per hour vs. every 5 minutes)
2. Enable longer `AUTOTHROTTLE_START_DELAY` (reduces requests)
3. Scrape only specific sports (not "both" NFL + CFB every time)
4. Use dry-run mode for testing (doesn't hit target sites)

## Proxy Comparison

| Feature | Your Proxyscrape Setup | Direct Connection |
|---------|----------------------|-------------------|
| IP Rotation | ✅ 10 IPs | ❌ Single IP |
| Cloudflare Bypass | ✅ Residential | ❌ Often blocked |
| Detection Risk | ✅ Low | ❌ High |
| Speed | ⚠️ 2-5s latency | ✅ <1s latency |
| Cost | 💰 ~$50/month | ✅ Free |
| Reliability | ✅ 99.9% uptime | ⚠️ IP bans common |

## Support

- **Proxyscrape.com Dashboard:** https://proxyscrape.com/dashboard
- **Test Proxy:** `curl -x "http://user:pass@rp.scrapegw.com:6060" "https://ipinfo.io/json"`
- **Check Logs:** Look for "Proxy IP verified" messages
- **Scraper Issues:** Check `snapshots/` directory for debug screenshots

## Next Steps

After setting up your proxy:

1. ✅ Test with curl (see above)
2. ✅ Run a test scrape: `uv run walters-analyzer scrape-overtime --sport nfl`
3. ✅ Verify IP rotation by running multiple times
4. ✅ Check `data/overtime_live/` for output files
5. ✅ Monitor proxyscrape.com dashboard for bandwidth usage

For additional stealth improvements, see the recommendations in the main codebase documentation.
