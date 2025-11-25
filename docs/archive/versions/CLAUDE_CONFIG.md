# Billy Walters Sports Analyzer - Claude Configuration
# Location: C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\CLAUDE_CONFIG.md
# Extends: C:\Users\omall\.claude\CLAUDE.md (user-level defaults)

## Project Identity
```json
{
  "project": {
    "name": "Billy Walters Sports Analyzer",
    "short_name": "walters-analyzer",
    "version": "0.1.0",
    "status": "active_development",
    "type": "sports_betting_analytics",
    "domain": "nfl_ncaaf_analytics",
    "inspiration": "Billy Walters professional sports betting methodology",
    "purpose": "Educational and research tool for sports betting analysis",
    "location": "C:\\Users\\omall\\Documents\\python_projects\\billy-walters-sports-analyzer"
  }
}
```

## Project Phase & Status
```json
{
  "development_phase": {
    "current": "Phase 2 - Weather Integration",
    "completed": ["Phase 1 - Line Movement Tracking"],
    "in_progress": ["AccuWeather API Integration", "Real-time Data Collection"],
    "next": ["Phase 3 - Injury Intelligence", "Phase 4 - Sharp Money Detection"],
    "status": {
      "ci_cd": "fully operational - 146 tests passing",
      "code_quality": "automated linting and type checking",
      "security": "automated vulnerability scanning",
      "documentation": "comprehensive (CLAUDE.md + LESSONS_LEARNED.md)",
      "data_collection": "last run: 2025-11-11 (NFL Week 11)"
    }
  }
}
```

## Billy Walters Methodology
```json
{
  "methodology": {
    "core_principles": {
      "power_ratings": "90/10 formula - 90% prior rating + 10% new information",
      "edge_detection": "Identify discrepancies between power ratings and market odds",
      "bet_sizing": "Kelly Criterion with fractional betting",
      "success_metric": "Closing Line Value (CLV), not win percentage"
    },
    "swe_factors": {
      "S": "Situation (home/away, divisional, weather, rest)",
      "W": "Weather (temperature, wind, precipitation)",
      "E": "Emotion (rivalry, motivation, coaching)"
    },
    "edge_thresholds": {
      "max_bet": "7+ points (5% Kelly, 77% win rate)",
      "strong": "4-7 points (3% Kelly, 64% win rate)",
      "moderate": "2-4 points (2% Kelly, 58% win rate)",
      "lean": "1-2 points (1% Kelly, 54% win rate)",
      "no_play": "<1 point"
    },
    "position_injury_values": {
      "qb_elite": "4.5 points",
      "rb_elite": "2.5 points",
      "wr1_elite": "1.8 points",
      "lt_rt_elite": "1.5 points",
      "cb_elite": "1.2 points"
    },
    "weather_impact": {
      "temperature": {
        "under_20f": "-4 points",
        "20_25f": "-3 points",
        "25_32f": "-2 points",
        "32_40f": "-1 point"
      },
      "wind": {
        "over_20mph": "-5 points",
        "15_20mph": "-3 points",
        "10_15mph": "-1 point"
      },
      "precipitation": {
        "snow_over_60pct": "-5 points",
        "rain_over_60pct": "-3 points"
      }
    }
  }
}
```

## Sports Focus
```json
{
  "sports": {
    "primary": ["NFL", "NCAAF"],
    "nfl_specifics": {
      "weeks": "18 regular season weeks + playoffs",
      "bye_weeks": "handle correctly in power ratings",
      "home_field_advantage": "quantify and apply",
      "division_games": "track historical patterns",
      "weather_critical": "outdoor stadiums (Buffalo, Green Bay, Chicago, etc.)"
    },
    "ncaaf_specifics": {
      "conferences": "track conference alignments and changes",
      "bowl_games": "different dynamics than regular season",
      "talent_disparity": "larger skill gaps than NFL",
      "home_field_stronger": "often more significant than NFL",
      "roster_turnover": "high due to graduations/transfers"
    }
  }
}
```

## Data Sources & APIs
```json
{
  "data_sources": {
    "weather": {
      "primary": {
        "name": "AccuWeather API",
        "plan": "Starter (free tier)",
        "base_url": "https://dataservice.accuweather.com",
        "capabilities": [
          "Location key lookup",
          "Current conditions",
          "12-hour hourly forecast",
          "5-day daily forecast"
        ],
        "limitations": [
          "12-hour max hourly forecast (not 24 or 72)",
          "MUST use HTTPS (not HTTP)",
          "Games >12 hours away use current conditions (less accurate)"
        ],
        "env_var": "ACCUWEATHER_API_KEY",
        "status": "verified working"
      },
      "backup": {
        "name": "OpenWeather API",
        "use_case": "fallback for long-range forecasts (>12 hours)",
        "env_var": "OPENWEATHER_API_KEY"
      }
    },
    "odds": {
      "primary": {
        "name": "Overtime.ag Hybrid Scraper",
        "type": "Playwright + SignalR WebSocket",
        "implementation": "src/data/overtime_hybrid_scraper.py",
        "script": "scripts/scrapers/scrape_overtime_hybrid.py",
        "capabilities": [
          "Pre-game odds (Playwright authentication + scraping)",
          "Live odds (SignalR WebSocket real-time updates)",
          "Billy Walters standardized format",
          "Line movement tracking"
        ],
        "optimal_timing": "Tuesday-Wednesday (after Monday Night Football)",
        "env_vars": ["OV_CUSTOMER_ID", "OV_PASSWORD"],
        "status": "production-ready",
        "documentation": "docs/OVERTIME_HYBRID_SCRAPER.md"
      },
      "backup": {
        "name": "The Odds API",
        "env_var": "ODDS_API_KEY",
        "limits": "500 requests/month (free tier)"
      }
    },
    "power_ratings": {
      "primary": {
        "name": "Massey Composite Ratings",
        "source": "https://masseyratings.com",
        "systems": "100+ ranking systems",
        "script": "scripts/analysis/weekly_power_rating_update.py"
      },
      "supplemental": {
        "name": "ESPN Stats",
        "api": "ESPN API",
        "data": ["team statistics", "game schedules", "scores"]
      }
    },
    "injuries": {
      "primary": "ESPN API",
      "supplemental": "NFL.com injury reports",
      "tracking": "position-specific impact analysis"
    },
    "sharp_money": {
      "source": "Action Network",
      "env_vars": ["ACTION_USERNAME", "ACTION_PASSWORD"],
      "indicators": ["line movement", "public betting percentages", "sharp action alerts"]
    }
  }
}
```

## Project Structure
```json
{
  "structure": {
    "root": "C:\\Users\\omall\\Documents\\python_projects\\billy-walters-sports-analyzer",
    "directories": {
      "src": {
        "path": "src/",
        "purpose": "Core library code",
        "subdirs": {
          "data": "Data collection (27 scrapers & API clients)",
          "walters_analyzer": "Core analysis system",
          "db": "Database layer"
        }
      },
      "scripts": {
        "path": "scripts/",
        "purpose": "Operational scripts",
        "subdirs": {
          "analysis": "Weekly analysis (8 scripts)",
          "scrapers": "Active data collection (3 scripts)",
          "validation": "Data validation (3 scripts)",
          "backtest": "Backtesting (2 scripts)",
          "utilities": "Helper scripts (5 scripts)",
          "dev": "Development/deployment (14 scripts)",
          "archive": "Legacy code (reference only)"
        }
      },
      "tests": {
        "path": "tests/",
        "purpose": "Test suite (146 tests)",
        "subdirs": {
          "integration": "Integration tests",
          "unit": "Unit tests + pytest suite"
        }
      },
      "docs": {
        "path": "docs/",
        "purpose": "Project documentation",
        "subdirs": {
          "data_sources": "Data schema documentation",
          "features": "Feature documentation",
          "guides": "User guides",
          "reports": "Historical reports and archives"
        }
      },
      "claude": {
        "path": ".claude/",
        "purpose": "Claude Code integration",
        "contents": [
          "walters_mcp_server.py (MCP server)",
          "walters_autonomous_agent.py (autonomous agent)",
          "billy_walters_analytics_prd.md (PRD)",
          "hooks/ (automation hooks)",
          "commands/ (14 custom slash commands)"
        ]
      },
      "data": {
        "path": "data/",
        "purpose": "Data storage",
        "subdirs": {
          "current": "Latest power ratings and schedules",
          "reports": "Generated analysis reports",
          "bets": "Bet tracking data"
        }
      },
      "output": {
        "path": "output/",
        "purpose": "Scraper outputs",
        "subdirs": {
          "overtime": "Overtime.ag odds data",
          "edge_detection": "Edge detection results"
        }
      }
    }
  }
}
```

## Custom Slash Commands (14 Available)
```json
{
  "slash_commands": {
    "workflow_core": {
      "/collect-all-data": "COMPLETE automated 7-step workflow (power ratings → schedules → stats → injuries → weather → odds → analysis)",
      "/power-ratings": "Calculate power ratings using Massey composite (90/10 formula)",
      "/edge-detector": "Detect betting edges using Billy Walters methodology",
      "/betting-card": "Generate weekly betting recommendations (ranked by edge)",
      "/validate-data": "Check data quality and completeness"
    },
    "data_collection": {
      "/scrape-massey": "Scrape Massey Ratings for 100+ ranking systems",
      "/scrape-overtime": "Collect odds from Overtime.ag (Tuesday-Wednesday optimal)",
      "/update-data": "Update all data sources (odds, injuries, weather, schedules)"
    },
    "contextual_analysis": {
      "/weather": "Weather impact analysis (usage: /weather 'Team Name' 'YYYY-MM-DD HH:MM')",
      "/team-stats": "Team statistics and power rating components",
      "/injury-report": "Injury impact with position-specific point values",
      "/analyze-matchup": "Deep dive matchup analysis"
    },
    "tracking": {
      "/clv-tracker": "Track Closing Line Value (CLV) - key success metric",
      "/current-week": "Show current NFL week and schedule status",
      "/odds-analysis": "Analyze current odds and identify value opportunities"
    },
    "documentation": {
      "/document-lesson": "Add entry to LESSONS_LEARNED.md",
      "/lessons": "View lessons learned from previous sessions"
    }
  }
}
```

## Automation Hooks (3 Available)
```json
{
  "automation_hooks": {
    "pre_data_collection": {
      "path": ".claude/hooks/pre_data_collection.py",
      "purpose": "Pre-flight validation before data collection",
      "checks": [
        "Validate environment variables (API keys)",
        "Check output directories exist",
        "Detect current NFL week",
        "Check when data was last collected",
        "Prevent collection with missing credentials"
      ],
      "exit_codes": {
        "0": "proceed with collection",
        "1": "stop - issues found"
      }
    },
    "post_data_collection": {
      "path": ".claude/hooks/post_data_collection.py",
      "purpose": "Post-flight validation after data collection",
      "checks": [
        "Validate collected data completeness (5 required files)",
        "Score data quality: EXCELLENT/GOOD/FAIR/POOR",
        "Check Overtime odds freshness",
        "Generate actionable next steps"
      ],
      "usage": "python .claude/hooks/post_data_collection.py <week_number>",
      "exit_codes": {
        "0": "data quality acceptable",
        "1": "data quality poor - fix issues"
      }
    },
    "auto_edge_detector": {
      "path": ".claude/hooks/auto_edge_detector.py",
      "purpose": "Auto-trigger edge detection on new odds data",
      "logic": [
        "Monitor for new odds data (<5 minutes old)",
        "Check if edge detection already ran",
        "Auto-trigger when conditions met",
        "Prevent redundant processing"
      ],
      "scheduling": "on-demand (manual execution preferred, NOT scheduled)",
      "usage": "python .claude/hooks/auto_edge_detector.py"
    }
  }
}
```

## Weekly Billy Walters Workflow
```json
{
  "weekly_workflow": {
    "tuesday_wednesday": {
      "timing": "After Monday Night Football - new lines post",
      "steps": [
        "1. Pre-flight validation: python .claude/hooks/pre_data_collection.py",
        "2. Complete data collection: /collect-all-data",
        "3. Validate data quality: /validate-data",
        "4. Edge detection: /edge-detector (or auto-triggered)",
        "5. Generate betting card: /betting-card",
        "6. Review picks: /clv-tracker"
      ],
      "data_collected": [
        "Power Ratings (Massey + ESPN)",
        "Game Schedules (ESPN API)",
        "Team Statistics (ESPN API)",
        "Injury Reports (ESPN + NFL)",
        "Weather Forecasts (game-time only)",
        "Odds Data (Overtime.ag Hybrid Scraper)",
        "Edge Detection Analysis"
      ]
    },
    "thursday": {
      "timing": "Before Thursday Night Football",
      "steps": [
        "Refresh odds: uv run python scripts/scrapers/scrape_overtime_hybrid.py --no-signalr",
        "Re-run edge detection: /edge-detector"
      ]
    },
    "sunday": {
      "timing": "Game day",
      "options": {
        "pre_game_only": "uv run python scripts/scrapers/scrape_overtime_hybrid.py --no-signalr",
        "live_monitoring": "uv run python scripts/scrapers/scrape_overtime_hybrid.py --duration 10800 --headless &"
      },
      "tracking": "/clv-tracker (monitor performance)"
    },
    "individual_game_analysis": {
      "weather": "/weather 'Team Name' 'YYYY-MM-DD HH:MM'",
      "injuries": "/injury-report 'Team Name' 'NFL'",
      "stats": "/team-stats 'Team Name' 'NFL'",
      "matchup": "/analyze-matchup"
    }
  }
}
```

## Development Workflows
```json
{
  "workflows": {
    "adding_new_scraper": {
      "location": "src/data/",
      "naming": "descriptive_source_client.py or descriptive_source_scraper.py",
      "requirements": [
        "Type hints required",
        "Async/await pattern",
        "Comprehensive error handling",
        "Logging throughout",
        "Unit tests in tests/"
      ]
    },
    "adding_analysis_module": {
      "location": "src/walters_analyzer/valuation/",
      "naming": "descriptive_analysis_name.py",
      "requirements": [
        "Follow Billy Walters methodology",
        "Input validation",
        "Output standardization",
        "Documentation of algorithm"
      ]
    },
    "adding_script": {
      "locations": {
        "weekly_analysis": "scripts/analysis/",
        "data_validation": "scripts/validation/",
        "backtesting": "scripts/backtest/",
        "utilities": "scripts/utilities/",
        "development": "scripts/dev/"
      },
      "requirements": [
        "CLI interface using argparse or typer",
        "Proper error handling",
        "Logging to files",
        "Usage examples in docstring"
      ]
    },
    "adding_slash_command": {
      "location": ".claude/commands/",
      "naming": "command-name.md",
      "requirements": [
        "Clear description",
        "Usage examples",
        "Parameters documented",
        "Expected output described"
      ],
      "permissions": "Update .claude/settings.local.json"
    }
  }
}
```

## Testing Strategy
```json
{
  "testing": {
    "framework": "pytest",
    "coverage_target": "80%+",
    "test_data": {
      "nfl": "Use realistic NFL game scenarios and edge cases",
      "ncaaf": "Use realistic NCAAF data with conference variety",
      "weather": "Test extreme conditions (Buffalo snowstorm, Miami heat)",
      "odds": "Test line movements and edge detection thresholds"
    },
    "ci_platforms": ["Ubuntu", "Windows"],
    "ci_python_versions": ["3.11", "3.12"],
    "running_tests": {
      "all": "uv run pytest tests/ -v",
      "with_coverage": "uv run pytest tests/ -v --cov=. --cov-report=term",
      "specific_file": "uv run pytest tests/test_file.py -v",
      "pattern_match": "uv run pytest tests/ -k 'test_pattern' -v"
    }
  }
}
```

## Environment Variables (Required)
```json
{
  "environment": {
    "file": ".env (NEVER commit to git)",
    "template": ".env.example",
    "required": {
      "weather": {
        "ACCUWEATHER_API_KEY": "required",
        "OPENWEATHER_API_KEY": "optional (backup)"
      },
      "odds": {
        "OV_CUSTOMER_ID": "required (Overtime.ag)",
        "OV_PASSWORD": "required (Overtime.ag)",
        "ODDS_API_KEY": "optional (backup)"
      },
      "ai_services": {
        "ANTHROPIC_API_KEY": "required for MCP server",
        "OPENAI_API_KEY": "optional"
      },
      "sharp_money": {
        "ACTION_USERNAME": "optional (Action Network)",
        "ACTION_PASSWORD": "optional (Action Network)"
      },
      "proxy": {
        "PROXY_URL": "optional (for scraping)",
        "PROXY_USER": "optional",
        "PROXY_PASS": "optional"
      }
    }
  }
}
```

## CI/CD Pipeline
```json
{
  "ci_cd": {
    "platform": "GitHub Actions",
    "workflow_file": ".github/workflows/ci.yml",
    "triggers": ["push", "pull_request"],
    "checks": {
      "format": "ruff format --check .",
      "lint": "ruff check .",
      "type_check": "pyright",
      "tests": "pytest tests/ -v --cov=. --cov-report=xml",
      "security": ["pip-audit", "TruffleHog secret detection"]
    },
    "branch_protection": {
      "branch": "main",
      "requirements": [
        "All CI checks must pass",
        "Pull request review required (if team)",
        "Cannot force push"
      ]
    },
    "local_validation": {
      "before_push": [
        "uv run ruff format .",
        "uv run ruff format --check .",
        "uv run ruff check .",
        "uv run pyright",
        "uv run pytest tests/ -v --cov=."
      ]
    }
  }
}
```

## Legacy Code Management
```json
{
  "legacy": {
    "philosophy": "Pragmatic - don't block on legacy, improve incrementally",
    "approach": {
      "new_code": "Must pass strict linting and type checking",
      "modified_code": "Fix issues in files you're editing",
      "untouched_code": "Leave alone unless it breaks"
    },
    "configuration": {
      "ruff_ignores": [
        "E722 (bare except)",
        "F401 (unused imports in __init__.py)",
        "F821 (undefined name)",
        "F841 (unused local variable)"
      ],
      "pyright_mode": "basic (lenient for now, will increase strictness)"
    },
    "tracking": "Monitor error counts quarterly, remove ignores as code improves"
  }
}
```

## Documentation Files
```json
{
  "documentation": {
    "primary": {
      "CLAUDE.md": "Development guidelines (current file - narrative guide)",
      "CLAUDE_CONFIG.md": "Claude configuration (this file - JSON settings)",
      "LESSONS_LEARNED.md": "Troubleshooting and session learnings",
      "README.md": "Project overview and quick start"
    },
    "ci_cd": {
      ".github/CI_CD.md": "CI/CD technical documentation",
      ".github/BRANCH_PROTECTION_SETUP.md": "Branch protection setup guide",
      ".github/GIT_WORKFLOW_GUIDE.md": "Complete git workflow"
    },
    "features": {
      "docs/OVERTIME_HYBRID_SCRAPER.md": "Hybrid scraper implementation",
      "docs/OVERTIME_DIRECTORY_STRUCTURE.md": "Output organization",
      "docs/_INDEX.md": "Complete documentation index"
    },
    "data_sources": {
      "docs/data_sources/": "Schema documentation for all data sources"
    },
    "commands": {
      ".claude/commands/README.md": "Complete slash command reference"
    }
  }
}
```

## Troubleshooting Quick Reference
```json
{
  "common_issues": {
    "accuweather_403": {
      "symptoms": "HTTP 403 Forbidden or 301 redirect",
      "fixes": [
        "Verify HTTPS (not HTTP) in BASE_URL",
        "Check API key validity",
        "Remember 12-hour hourly forecast limit"
      ],
      "test": "python src/data/accuweather_client.py"
    },
    "unicode_errors_windows": {
      "symptoms": "Console encoding errors, emoji display issues",
      "fix": "Use ASCII characters: [OK], [ERROR], [WARNING], -> (not ✓, ✗, ⚠, →)",
      "file": "Any console output scripts"
    },
    "module_not_found": {
      "symptoms": "ModuleNotFoundError when running scripts",
      "fixes": [
        "uv sync --all-extras --dev",
        "cd src && uv run python -m walters_analyzer.module",
        "uv pip install -e ."
      ]
    },
    "ci_type_check_failing": {
      "check": "pyproject.toml pyright configuration",
      "local_test": "uv run pyright",
      "note": "Most errors suppressed for legacy code"
    },
    "edge_detection_not_triggering": {
      "check": "ls -lt output/overtime_nfl_walters_*.json | head -1",
      "requirement": "Odds must be <5 minutes old",
      "manual": "python .claude/hooks/auto_edge_detector.py",
      "optimal": "Tuesday-Wednesday after new lines post"
    }
  }
}
```

## Recent Major Updates
```json
{
  "recent_updates": {
    "2025_11_11": {
      "feature": "Overtime.ag Hybrid Scraper - PRODUCTION READY",
      "changes": [
        "Built hybrid scraper combining Playwright + SignalR WebSocket",
        "Tested against live Overtime.ag site",
        "Completed NFL Week 11 data collection",
        "Created comprehensive documentation",
        "Integrated into /collect-all-data workflow"
      ],
      "files_added": [
        "src/data/overtime_hybrid_scraper.py (574 lines)",
        "src/data/overtime_signalr_parser.py (369 lines)",
        "scripts/scrapers/scrape_overtime_hybrid.py (181 lines)",
        "docs/OVERTIME_HYBRID_SCRAPER.md (737 lines)"
      ],
      "status": "Production-ready, fully tested"
    },
    "codebase_cleanup": {
      "deleted": "9 obsolete files",
      "archived": "5 legacy overtime scrapers",
      "reorganized": "scripts/ directory structure",
      "moved": "7 test scripts to proper locations",
      "consolidated": "Documentation to docs/ with index",
      "improvement": "70% reduction in root clutter"
    }
  }
}
```

## Notes for Claude
> **Project Context**: This is Andy's side project implementing Billy Walters' professional
> sports betting methodology for NFL and NCAAF. Focus is on edge detection, power ratings,
> and Closing Line Value (CLV) tracking - NOT win/loss percentage.
> 
> **Data Collection Timing**: Optimal Tuesday-Wednesday after Monday Night Football when
> new lines are posted. Sunday scraping gets live odds but pre-game lines are down.
> 
> **Success Metric**: Closing Line Value (CLV) is the key metric, not win rate. Professional
> target is +1.5 CLV average, elite target is +2.0 CLV average.
> 
> **Automation Philosophy**: 100% on-demand execution - no scheduled automation. Andy runs
> /collect-all-data when ready, hooks validate automatically, edge detection auto-triggers
> on new odds data (<5 minutes old).
> 
> **Development State**: Production-ready with 146 passing tests, comprehensive CI/CD,
> automated data collection workflow, and thorough documentation. Legacy code exists but
> managed pragmatically with incremental improvements.
