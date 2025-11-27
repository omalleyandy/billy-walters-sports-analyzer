# Billy Walters CLI - Command Reference

## Overview

The new `walters` CLI provides a clean, organized command structure using Typer.
All commands follow a consistent pattern: `walters <group> <command> [options]`.

## Quick Start

```bash
# Run complete weekly workflow
walters quickstart --sport nfl --week 13

# Check system status
walters status --verbose

# Find betting edges
walters analyze edges --sport nfl --min-edge 5.5

# Record a bet for CLV tracking
walters clv record "DET @ CHI" "DET -3.5" -3.5 --stake 200

# View help
walters --help
walters analyze --help
```

## Command Groups

### `walters analyze` - Analysis Commands

| Command | Description | Example |
|---------|-------------|---------|
| `edges` | Find betting edges | `walters analyze edges --sport nfl --week 13` |
| `game` | Analyze single game | `walters analyze game "Bears" "Lions" --spread -6.5` |
| `injuries` | Injury impact analysis | `walters analyze injuries --sport nfl --team Lions` |
| `weather` | Weather impact analysis | `walters analyze weather --sport nfl --week 13` |
| `divergence` | Sharp/public divergence | `walters analyze divergence --threshold 5` |

### `walters scrape` - Data Collection

| Command | Description | Example |
|---------|-------------|---------|
| `overtime` | Scrape Overtime.ag odds | `walters scrape overtime --sport nfl` |
| `espn` | Scrape ESPN data | `walters scrape espn injuries --sport nfl` |
| `massey` | Scrape Massey ratings | `walters scrape massey --sport nfl` |
| `action-network` | Sharp signals | `walters scrape action-network --sport nfl` |
| `all` | Run all scrapers | `walters scrape all --sport nfl --parallel` |

### `walters clv` - CLV Tracking

| Command | Description | Example |
|---------|-------------|---------|
| `record` | Record new bet | `walters clv record "DET @ CHI" "DET -3.5" -3.5 --stake 200` |
| `update` | Update closing line | `walters clv update <ID> --closing-line -6.5 --result win` |
| `report` | CLV performance report | `walters clv report --sport nfl --detailed` |
| `list` | List tracked bets | `walters clv list --status pending` |
| `analyze` | Analyze CLV trends | `walters clv analyze --by week` |

### `walters power-ratings` - Power Ratings

| Command | Description | Example |
|---------|-------------|---------|
| `update` | Weekly 90/10 update | `walters power-ratings update --sport nfl --week 13` |
| `view` | View current ratings | `walters power-ratings view --sport nfl --top 10` |
| `compare` | Compare to sources | `walters power-ratings compare --sources massey,espn` |
| `history` | Team rating history | `walters power-ratings history "Lions" --weeks 10` |

### `walters db` - Database Operations

| Command | Description | Example |
|---------|-------------|---------|
| `migrate` | Run migrations | `walters db migrate up` |
| `backup` | Backup database | `walters db backup --output backup.sql.gz` |
| `load` | Load data files | `walters db load odds data/odds/nfl/` |
| `query` | Run SQL query | `walters db query "SELECT * FROM games"` |
| `status` | Check DB status | `walters db status` |

### `walters monitor` - Line Monitoring

| Command | Description | Example |
|---------|-------------|---------|
| `start` | Start monitoring | `walters monitor start --sport nfl --interval 30` |
| `alerts` | View recent alerts | `walters monitor alerts --hours 12` |
| `game` | Monitor single game | `walters monitor game "DET @ CHI"` |
| `config` | View/edit config | `walters monitor config --show` |

### Root Commands

| Command | Description | Example |
|---------|-------------|---------|
| `status` | System health check | `walters status --verbose` |
| `version` | Show version | `walters version` |
| `quickstart` | Weekly workflow | `walters quickstart --sport nfl` |

## Global Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |
| `--help` | Show help message |

## Common Workflows

### Weekly Analysis (Tuesday-Saturday)

```bash
# 1. Check system health
walters status --verbose

# 2. Collect fresh data
walters scrape all --sport nfl

# 3. Update power ratings
walters power-ratings update --sport nfl --week 13

# 4. Find opportunities
walters analyze edges --sport nfl --min-edge 5.5 --verbose

# 5. Record bets as placed
walters clv record "DET @ CHI" "DET -6.5" -6.5 --stake 200 --edge 7.2
```

### Pre-Kickoff (Saturday/Sunday)

```bash
# 1. Update closing lines
walters clv update all --auto

# 2. Start line monitoring
walters monitor start --sport nfl --sms
```

### Post-Game (Monday)

```bash
# 1. Update results
walters clv update <ID> --result win

# 2. Generate CLV report
walters clv report --sport nfl --detailed

# 3. Update power ratings with results
walters power-ratings update --sport nfl --week 13
```

## Migration from Old CLI

The legacy `walters-analyzer` command is still available for backward compatibility:

```bash
# Old way (still works)
walters-analyzer analyze-game --home Bears --away Lions --spread -6.5

# New way
walters analyze game "Bears" "Lions" --spread -6.5
```

## Files Location

- CLI main: `src/walters_analyzer/cli/main.py`
- Command groups: `src/walters_analyzer/cli/commands/`
- Legacy CLI: `src/walters_analyzer/cli.py`
