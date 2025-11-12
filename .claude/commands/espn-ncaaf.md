Reverse engineer the ESPN NCAAF hub (https://www.espn.com/college-football/) so we can harvest scoreboard, rankings, standings, and headline context straight from the Chrome DevTools network log.

Usage: /espn-ncaaf [--week 12] [--date 20251116] [--group 80]

DevTools workflow:
1. Open Chrome, go to https://www.espn.com/college-football/, hit `F12`, switch to the Network tab, and enable **Preserve log**.
2. Filter network requests by `college-football` or `scoreboard`, then hard‑reload (`Ctrl+Shift+R`) to capture the initial burst of XHRs.
3. Right‑click the JSON/XHR requests listed below, choose **Copy > Copy as fetch**, and paste into Claude so it can replay them via `curl`.
4. If ESPN responds with `sports.core.api.espn.pvt`, replace `.pvt` with `.com` for public access.

Key endpoints to capture:
- **Scoreboard module** – `GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard` with query params such as `week=12`, `dates=20251116`, `groups=80` (FBS), `limit=400`, `lang=en`, `region=us`.  
  ```bash
  curl -s 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?week=12&dates=20251116&groups=80&limit=400&lang=en&region=us' \
    | jq '.events[] | {id,name,status:.competitions[0].status.type.name}'
  ```
- **Rankings carousel** – `GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings`.  
  Follow the `$ref` (e.g., `/seasons/2025/types/2/weeks/12/rankings/1`) to pull the full AP/Coaches/CFP tables with team IDs, poll points, first‑place votes, and trend data.
- **Standings rail** – `GET http://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{season}/types/{type}/groups/{group}/standings/0?lang=en&region=us`.  
  Example for 2025 regular season FBS: `/seasons/2025/types/2/groups/80/standings/0`.
- **Headline/news feed** – `GET https://site.api.espn.com/apis/site/v2/sports/football/college-football/news` for the hero stories, injury blurbs, and video capsules that surface on the hub.

What to save:
- Raw JSON responses (drop under `data/raw/espn/` with timestamps).
- Derived parquet/arrow tables for `events`, `rankings`, and standings entries.
- A short metadata block noting `season`, `week`, `capture_time`, and which modules were present (in case ESPN rearranges sections).

Integration tips:
- Map ESPN `team.id` values to our canonical IDs once, then reuse for all modules.
- Feed scoreboard + rankings into the ResearchEngine so `/analyze` can cite current poll positions and headline context.
- Store standings snapshots alongside Overtime lines; this helps bankroll logic understand conference races and tiebreakers.
