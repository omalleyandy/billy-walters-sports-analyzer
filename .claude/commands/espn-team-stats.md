Capture the same team-level tables that power https://www.espn.com/college-football/stats/_/view/team so we can compare Billy Walters power ratings against ESPN efficiency splits.

Usage: /espn-team-stats [--season 2025] [--type reg] [--group 80] [--team-id 2]

How to reverse engineer with Chrome DevTools:
1. Open the “Team” tab on ESPN’s stats page, pop DevTools → Network, toggle **Preserve log**, and filter by `teams/` (there are dozens of requests when you scroll).
2. Scroll through the category tabs (Total Offense, Passing, Defense). Each tab fires separate XHRs for the visible teams; copy the request templates via **Copy as fetch**.
3. ESPN uses both `site.api` and `sports.core.api`. If you see `.pvt` in the captured URL, swap it to `.com` before replaying.

Essential endpoints:
- **Team directory** – `GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?groups=80&limit=500`  
  Provides every FBS school with `team.id`, logos, conference, and schedule links (useful for building the iteration list).
- **Team statistics (site API)** – `GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{TEAM_ID}/statistics?season={SEASON}`  
  Responds with `results.stats.categories` (passing, rushing, defense, efficiency) including per-game values already calculated by ESPN.
- **Team statistics (core API)** – `GET http://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{SEASON}/types/{TYPE}/teams/{TEAM_ID}/statistics?lang=en&region=us`  
  Same data model, but split across `$ref`s for deeper drill-down. Useful when we want to stay entirely on the `sports.core` surface.
- **Team leaders** – `GET http://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{SEASON}/types/{TYPE}/teams/{TEAM_ID}/leaders?lang=en&region=us` for quick “who drives the offense” callouts.

Sample extraction:
```bash
TEAM=2026   # App State
curl -s "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/${TEAM}/statistics?season=2025" \
  | jq '.results.stats.categories[] | {group:.name, metrics: map({name, value, perGameValue})}'
```

Batch strategy:
1. Pull the team directory once per session and persist `team_id`, `displayName`, `conferenceId`.
2. Loop over all IDs (respect ESPN’s polite limit ~2 req/sec) and fetch the `statistics` payload; stash raw JSON plus a flattened parquet keyed by `team_id` + `category`.
3. Optionally hit `/leaders` for the same IDs so `/analyze-game --research` can say “Team X’s passing leader averages 312.5 YPG”.

Post-processing ideas:
- Compute offensive and defensive EPA style metrics from ESPN totals (`pointsFor`, `pointsAgainst`, `yardsPerGame`) to validate Billy Walters power ratings.
- Track differential deltas week-over-week by diffing the per-game values from consecutive runs.
- Flag outliers (e.g., top 10 in `thirdDownConvPct` but outside top 50 in `explosivePlays`) for Edge Detector narrative.

Sanity checks:
- Confirm `results.context.displaySeason.year` equals the requested `--season`.
- Some smaller programs lack complete categories; skip missing categories instead of writing null-heavy rows.
- ESPN occasionally reorders stats—key by `stat.name` rather than relying on positional order.
