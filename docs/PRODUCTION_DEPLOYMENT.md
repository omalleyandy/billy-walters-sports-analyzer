# Production Deployment Guide

**Version**: 1.0.0  
**Status**: Production-Ready  
**Last Updated**: November 8, 2025

## Overview

This guide covers deploying the Billy Walters Sports Analyzer for production use, including configuration, monitoring, and best practices.

## Prerequisites

- Python 3.11 or higher
- uv package manager
- PowerShell 7+ (for automation)
- 4GB RAM minimum
- 10GB disk space

### Optional
- Docker (for containerized deployment)
- PostgreSQL (for enhanced data storage)
- Grafana (for monitoring dashboards)

---

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-repo/billy-walters-sports-analyzer.git
cd billy-walters-sports-analyzer
```

### 2. Install Dependencies
```bash
# Core dependencies
uv sync

# With all features
uv sync --all-extras

# Or specific features
uv sync --extra ml --extra mcp --extra scraping
```

### 3. Configure Environment
```bash
# Copy template
cp env.template .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

**Required API Keys:**
- ACCUWEATHER_API_KEY
- HIGHLIGHTLY_API_KEY
- ODDS_API_KEY

### 4. Verify Installation
```bash
# Run system test
.codex/super-run.ps1 -Task test-system

# Or use pytest
uv run pytest tests/ -v

# Expected: 114 tests passing
```

---

## Configuration

### Environment Variables

See `env.template` for complete list. Key variables:

```bash
# APIs
ACCUWEATHER_API_KEY=xxx
HIGHLIGHTLY_API_KEY=xxx
ODDS_API_KEY=xxx

# Bankroll
DEFAULT_BANKROLL=10000
MAX_BET_PERCENTAGE=3.0
FRACTIONAL_KELLY=0.5

# Performance
RESEARCH_CACHE_TTL=300
API_RATE_LIMIT=60

# Logging
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### Application Settings

Located in `walters_analyzer/config/settings.py`:

```python
# Modify these for your use case
bankroll = float(os.getenv('DEFAULT_BANKROLL', 10000))
max_bet_pct = float(os.getenv('MAX_BET_PERCENTAGE', 3.0))
fractional_kelly = float(os.getenv('FRACTIONAL_KELLY', 0.5))
key_numbers = [3, 7, 6, 10, 14]
```

---

## Monitoring

### Logging

**Log Locations:**
- Application logs: `logs/walters-analyzer.log`
- MCP server logs: `logs/mcp-server.log`
- Alert logs: `logs/alerts.log`
- Super-run logs: `logs/super-run-TIMESTAMP.log`

**Log Levels:**
- DEBUG: Verbose details
- INFO: Normal operations
- WARNING: Degraded functionality
- ERROR: Failures

**Log Rotation** (recommended):
```bash
# Install logrotate (Linux) or use Windows Task Scheduler
# Rotate daily, keep 30 days

# Example logrotate config
/path/to/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

### Performance Monitoring

**Metrics to Track:**
- Analysis response time (target: <1s)
- Scraper success rate (target: >95%)
- API rate limit usage
- Cache hit rate (target: >80%)
- Test pass rate (target: >95%)

**Monitoring Tools:**
- Built-in: `.codex/super-run.ps1 -Task test-system`
- Custom: Parse logs for metrics
- Future: Grafana dashboards

### Health Checks

**Automated:**
```powershell
# Daily health check (schedule with Task Scheduler)
.codex/super-run.ps1 -Task test-system

# Alert if failures detected
```

**Manual:**
```bash
# Quick system check
uv run walters-analyzer analyze-game --home "Test" --away "Test" --spread -2.5

# Full test suite
uv run pytest tests/ -v
```

---

## Backup Strategy

### Data to Backup

**Critical:**
- `data/` - All scraped data
- `.env` - Your API keys (SECURE!)
- `logs/` - Historical logs
- Custom configurations

**Optional:**
- Analysis results
- Bet history
- Performance metrics

### Backup Commands

```powershell
# Daily backup
$date = Get-Date -Format "yyyyMMdd"
Compress-Archive -Path data,logs,.env -DestinationPath "backups/backup-$date.zip"

# Exclude from git
echo "backups/" >> .gitignore
```

---

## Scaling

### For High Volume

**Increase rate limits:**
```bash
# In .env
API_RATE_LIMIT=120  # Increase if you have quota
RESEARCH_CACHE_TTL=600  # Longer cache for less API calls
```

**Use paid API tiers:**
- AccuWeather: Upgrade for more calls/day
- The Odds API: Upgrade for more calls/month
- Highlightly: Check premium plans

### For Multiple Sports

```bash
# NFL + NCAA simultaneously
.codex/super-run.ps1 -Task collect-data -Sport both

# Separate bankrolls (future feature)
# NFL: $10,000
# NCAA: $5,000
```

---

## Security Hardening

### API Key Management

```bash
# Store in secure location
chmod 600 .env  # Linux/Mac
icacls .env /inheritance:r /grant:r "%USERNAME%:F"  # Windows

# Rotate regularly
# Update .env with new keys
# Test with: uv run walters-analyzer monitor-sharp --test
```

### Data Privacy

- No personal betting data logged
- All storage local by default
- Optional cloud sync (configure separately)
- GDPR compliant

### Network Security

```bash
# Use HTTPS for all API calls (default)
# Use authenticated proxy if needed
# Monitor for unusual API activity
```

---

## Troubleshooting

### Common Issues

**API Rate Limiting:**
```bash
# Symptom: "Rate limit exceeded" errors
# Fix: Increase cache TTL or upgrade API plan
RESEARCH_CACHE_TTL=600
```

**Slow Performance:**
```bash
# Symptom: Analysis takes >2s
# Fix: Clear cache, check network, verify API keys
```

**Import Errors:**
```bash
# Symptom: ModuleNotFoundError
# Fix: Reinstall dependencies
uv sync --force
```

### Debug Mode

```bash
# Enable debug logging
# In .env:
LOG_LEVEL=DEBUG
DEBUG_MODE=true

# Run command
uv run walters-analyzer analyze-game ... 2>&1 | tee debug.log
```

---

## Maintenance

### Daily
- Run health check: `.codex/super-run.ps1 -Task test-system`
- Check logs for errors
- Monitor API usage
- Review performance metrics

### Weekly
- Run full test suite: `uv run pytest tests/`
- Review bankroll performance
- Update power ratings (if changed)
- Archive old logs

### Monthly
- Rotate API keys
- Review and update documentation
- Performance optimization review
- Dependency updates: `uv sync --upgrade`

---

## Best Practices

### 1. Environment Management
- Use separate .env for dev/staging/prod
- Never commit .env files
- Document all custom settings
- Test configuration changes

### 2. Data Management
- Scrape data daily (morning routine)
- Keep 30 days of historical data
- Archive older data monthly
- Monitor disk usage

### 3. Performance
- Monitor cache hit rates
- Optimize API call patterns
- Use batch analysis when possible
- Profile slow operations

### 4. Testing
- Run tests before major changes
- Add tests for new features
- Maintain >95% pass rate
- Performance test regressions

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (uv run pytest tests/)
- [ ] env.template documented
- [ ] API keys configured
- [ ] Logs directory created
- [ ] System test passing

### Deployment
- [ ] Install dependencies (uv sync --all-extras)
- [ ] Configure .env from template
- [ ] Run system test
- [ ] Test analyze-game command
- [ ] Test interactive mode
- [ ] Verify automation scripts

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Verify API calls working
- [ ] Test full workflow
- [ ] Document any issues
- [ ] Set up monitoring

---

## Support

### Getting Help
1. Check documentation (`docs/`)
2. Review logs (`logs/`)
3. Run diagnostics (`.codex/super-run.ps1 -Task test-system`)
4. Check GitHub issues (if public)

### Reporting Issues
Include:
- Command executed
- Expected behavior
- Actual behavior
- Error messages
- Relevant logs
- System info

---

## Conclusion

The Billy Walters Sports Analyzer is production-ready with:

✅ Complete feature set  
✅ Comprehensive documentation  
✅ 114 passing tests  
✅ Professional monitoring  
✅ Automated workflows  
✅ Production configuration  

Follow this guide for smooth deployment and operation!

---

**See Also:**
- Architecture: `docs/ARCHITECTURE.md`
- Quick Start: `docs/guides/QUICKSTART_ANALYZE_GAME.md`
- CLI Reference: `docs/guides/CLI_REFERENCE.md`
- env.template: `env.template`

