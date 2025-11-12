Document the Chrome DevTools recipe for pulling ESPN’s NCAAF player leaderboards (passing, rushing, receiving, tackles, etc.) so we can feed ResearchEngine with live leader data.

Usage: /espn-player-stats [--season 2025] [--week 12] [--type reg] [--group 80] [--category passingYards]

DevTools steps:
1. Visit https://www.espn.com/college-football/stats (the default “Player” tab), open DevTools → Network, tick **Preserve log**, and filter by `leaders`.
2. When you change the category dropdown (Passing/Rushing/Defense), ESPN reissues a request to the **leaders** endpoint. Capture those by **Copy as fetch**.
3. The response references `sports.core.api.espn.pvt`. Replace `.pvt` with `.com` when replaying outside the browser.

Core endpoint pattern:
```
GET http://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{SEASON}/types/{TYPE}/leaders?lang=en&region=us[&groups=80][&category=passingYards]
```
- `SEASON`: four-digit season year (e.g., 2025).  
- `TYPE`: 1=preseason, 2=regular season, 3=postseason.  
- `groups`: optional (80 FBS, 81 FCS, 55 CFP, etc.).  
- `category`: omit to receive all 13 default categories or set to one (e.g., `rushingTouchdowns`, `totalTackles`).  

Example replay:
```bash
curl -s 'http://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/2025/types/2/leaders?lang=en&region=us&groups=80&category=passingYards' \
  | jq '.categories[0].leaders[:5] | map({player: .athlete.$ref, team: .team.$ref, yards: .value})'
```

Follow-up references:
- `leaders[].athlete.$ref` → `.../seasons/{season}/athletes/{athlete_id}` (basic bio, position, measurements).
- `leaders[].statistics.$ref` → `.../types/{type}/athletes/{athlete_id}/statistics/0` (full stat splits by category, including per-game values).
- `leaders[].team.$ref` → `.../seasons/{season}/teams/{team_id}` (logo, conference, color codes for visualization).

What to deliver:
- CSV/parquet of the top N players per category (include `player_id`, `team_id`, `stat_value`, `category`, `season`, `type`, `capture_time`).
- Enriched JSON for players who intersect with current games so `/analyze` can cite “Top 5 passer” or “Leads FBS in sacks”.
- Optional derived metrics: compute percentile ranks or z-scores and persist them for Betting Edge calculations.

Quality checks:
- Ensure `leaders[].value` is numeric (some defensive categories return strings like `"--"` for empty sets; handle gracefully).
- Watch `kickoffYards` (ESPN sometimes omits leaders—if `leaders` is empty, skip writing to avoid bogus tables).
- When filtering by `week`, ESPN often caches weekly leaders via `?week=N`; include that param if you need snapshot-in-time rather than season aggregate.
