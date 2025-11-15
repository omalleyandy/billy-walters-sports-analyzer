# Chrome DevTools Integration Guide

## Overview

This guide explains how to use Chrome DevTools Protocol (CDP) for scraper debugging, performance monitoring, and network request analysis.

## Components

### ChromeDevToolsMonitor (`src/data/chrome_devtools_monitor.py`)

Monitors Playwright pages for network activity and performance metrics.

**Features:**
- Network request/response tracking
- Performance metrics collection
- Resource loading analysis
- WebSocket connection monitoring

**Usage:**
```python
from data.chrome_devtools_monitor import ChromeDevToolsMonitor
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    
    # Start monitoring
    monitor = ChromeDevToolsMonitor(page)
    await monitor.start_monitoring()
    
    # Do your scraping
    await page.goto("https://example.com")
    # ... scraping code ...
    
    # Stop monitoring and get metrics
    metrics = await monitor.stop_monitoring()
    
    # Save metrics
    monitor.save_metrics("output/performance.json")
    
    # Get summary
    summary = monitor.get_summary()
    print(f"Total requests: {summary['total_requests']}")
```

### NetworkAnalyzer (`src/data/network_analyzer.py`)

Analyzes network data collected by ChromeDevToolsMonitor.

**Features:**
- API endpoint identification
- Rate limit detection
- Performance bottleneck detection
- Request pattern analysis

**Usage:**
```python
from data.network_analyzer import NetworkAnalyzer
import json

# Load metrics from monitor
with open("output/performance.json") as f:
    metrics = json.load(f)

# Analyze network data
analyzer = NetworkAnalyzer(metrics)

# Find API endpoints
api_endpoints = analyzer.find_api_endpoints()
print(f"Found {len(api_endpoints)} API endpoints")

# Find rate limits
rate_limits = analyzer.find_rate_limits()
if rate_limits:
    print("Rate limiting detected!")

# Find bottlenecks
bottlenecks = analyzer.find_bottlenecks()
if bottlenecks:
    print("Performance bottlenecks found")

# Generate comprehensive report
analyzer.generate_report("output/network_analysis.json")

# Print summary to console
analyzer.print_summary()
```

## Integration Examples

### Example 1: Monitor Massey Ratings Scraper

```python
from data.massey_ratings_scraper import MasseyRatingsScraper
from data.chrome_devtools_monitor import ChromeDevToolsMonitor
from playwright.async_api import async_playwright

async def scrape_with_monitoring():
    scraper = MasseyRatingsScraper()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Start monitoring
        monitor = ChromeDevToolsMonitor(page)
        await monitor.start_monitoring()
        
        # Do scraping (would need to modify scraper to accept page)
        # For now, monitor after scraping
        await scraper.scrape_nfl_ratings()
        
        # Get metrics
        metrics = await monitor.stop_monitoring()
        monitor.save_metrics("output/massey_performance.json")
        
        # Analyze
        from data.network_analyzer import NetworkAnalyzer
        analyzer = NetworkAnalyzer(metrics)
        analyzer.generate_report("output/massey_network_analysis.json")
        
        await browser.close()
```

### Example 2: Monitor Overtime Hybrid Scraper

```python
from data.overtime_hybrid_scraper import OvertimeHybridScraper
from data.chrome_devtools_monitor import ChromeDevToolsMonitor

async def scrape_overtime_with_monitoring():
    scraper = OvertimeHybridScraper(headless=True)
    
    # The scraper uses Playwright internally
    # We can monitor by modifying the scraper to expose the page
    # Or integrate monitoring directly into the scraper
    
    result = await scraper.scrape()
    
    # Monitor SignalR WebSocket connections
    # (would need to integrate monitoring into scraper)
```

## Best Practices

### Performance Monitoring

1. **Enable monitoring early**: Start monitoring before navigation
2. **Monitor complete workflows**: Include all scraping steps
3. **Save metrics regularly**: Save metrics after each major step
4. **Analyze bottlenecks**: Use NetworkAnalyzer to identify issues

### Network Analysis

1. **Identify API endpoints**: Use `find_api_endpoints()` to discover APIs
2. **Watch for rate limits**: Monitor for 429 responses and retry-after headers
3. **Track large responses**: Identify large files that slow down scraping
4. **Analyze request patterns**: Understand request frequency and timing

### Debugging Tips

1. **Check failed requests**: Look for failed requests in metrics
2. **Monitor WebSocket connections**: Track SignalR or other WebSocket connections
3. **Identify slow domains**: Find domains with slow response times
4. **Track redirects**: Monitor redirect chains that might affect scraping

## Output Structure

### Performance Metrics
```
output/performance/
├── massey_performance.json
├── overtime_performance.json
└── network_analysis/
    ├── massey_network_analysis.json
    └── overtime_network_analysis.json
```

### Metrics Format

**Performance Metrics:**
```json
{
  "start_time": "2025-11-13T14:30:00",
  "end_time": "2025-11-13T14:35:00",
  "duration_seconds": 300.0,
  "network": {
    "total_requests": 150,
    "total_bytes": 5242880,
    "request_count": 150,
    "response_count": 150,
    "requests_by_type": {
      "xhr": 20,
      "document": 1,
      "stylesheet": 5,
      "script": 10
    }
  },
  "performance": {
    "metrics": [...]
  }
}
```

**Network Analysis:**
```json
{
  "summary": {
    "total_requests": 150,
    "total_responses": 150,
    "duration_seconds": 300.0,
    "total_bytes": 5242880
  },
  "api_endpoints": [
    {
      "url": "https://api.example.com/endpoint",
      "method": "GET",
      "domain": "api.example.com",
      "path": "/endpoint"
    }
  ],
  "rate_limits": [],
  "bottlenecks": [],
  "patterns": {
    "request_methods": {"GET": 140, "POST": 10},
    "resource_types": {"xhr": 20, "document": 1},
    "status_codes": {200: 145, 404: 5}
  }
}
```

## Troubleshooting

### Monitoring Not Starting

**Issue**: Monitor doesn't collect data

**Solution**: 
- Ensure monitoring is started before navigation
- Check that page is from Playwright browser context
- Verify CDP session is properly initialized

### Missing Performance Metrics

**Issue**: Performance metrics are empty

**Solution**:
- Ensure `enable_performance=True` when creating monitor
- Check that browser supports CDP (Chromium-based browsers)
- Verify tracing is enabled in browser context

### Network Analysis Returns Empty Results

**Issue**: No API endpoints or patterns found

**Solution**:
- Verify metrics contain request/response data
- Check that requests were made during monitoring period
- Ensure responses include status codes and headers

## Resources

- [Chrome DevTools Protocol Documentation](https://chromedevtools.github.io/devtools-protocol/)
- [Playwright CDP Documentation](https://playwright.dev/python/docs/api/class-browsercontext#browser-context-new-cdp-session)
- [Network Analysis Best Practices](https://developer.mozilla.org/en-US/docs/Web/Performance/Network_basics)
