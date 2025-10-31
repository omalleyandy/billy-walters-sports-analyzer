# CLAUDE.md

## Commands
- `wk-card:dry-run` → run card with gates/price checks without placing bets.
- `wk-card:run` → live mode.

### JSON command examples
`/commands/wk-card.dry-run.json`
```json
{ "cmd": "uv run walters-analyzer wk-card --file ./cards/wk-card-2025-10-31.json --dry-run" }
```
`/commands/wk-card.run.json`
```json
{ "cmd": "uv run walters-analyzer wk-card --file ./cards/wk-card-2025-10-31.json" }
```

## Hooks
- `pre-run`: ensure `.env` loaded, confirm injuries/weather/steam gates are true.
- `post-run`: log CLV vs. close and append bias_log.
