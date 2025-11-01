# CLAUDE.md

## Commands
- `wk-card:dry-run` → run card with gates/price checks without placing bets.
- `wk-card:run` → live mode.
- `massey-scrape` → scrape Massey Ratings (all data: ratings + games).
- `massey-games` → scrape Massey game predictions only.
- `massey-ratings` → scrape Massey team power ratings only.
- `massey-analyze` → analyze Massey predictions vs. market odds for edges.

### JSON command examples
`/commands/wk-card.dry-run.json`
```json
{ "cmd": "uv run walters-analyzer wk-card --file ./cards/wk-card-2025-10-31.json --dry-run" }
```
`/commands/wk-card.run.json`
```json
{ "cmd": "uv run walters-analyzer wk-card --file ./cards/wk-card-2025-10-31.json" }
```
`/commands/massey-scrape.json`
```json
{ "cmd": "uv run walters-analyzer scrape-massey --data-type all" }
```
`/commands/massey-games.json`
```json
{ "cmd": "uv run walters-analyzer scrape-massey --data-type games" }
```
`/commands/massey-ratings.json`
```json
{ "cmd": "uv run walters-analyzer scrape-massey --data-type ratings" }
```
`/commands/massey-analyze.json`
```json
{ "cmd": "uv run python scripts/analyze_massey_edges.py --min-edge 2.0" }
```

## Hooks
- `pre-run`: ensure `.env` loaded, confirm injuries/weather/steam gates are true.
- `post-run`: log CLV vs. close and append bias_log.
- `pre-scrape`: optionally update Massey ratings before running wk-card analysis.

## Massey Ratings Integration
- `pre-bet-analysis`: scrape Massey for latest predictions, compare to market.
- `edge-detection`: identify 2+ point spread or 3+ point total discrepancies.
- `model-validation`: benchmark your ratings against Massey's proven system.
