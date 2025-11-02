# ESPN College Football URL Reference Table

Quick reference for all ESPN CFB URLs with examples.

---

## 📋 Static URLs (No Wildcards)

| # | Page | URL | Data Available | Update Frequency |
|---|------|-----|----------------|------------------|
| 1 | Homepage | `https://www.espn.com/college-football/` | News, scores, highlights | Hourly |
| 2 | Scoreboard | `https://www.espn.com/college-football/scoreboard` | Live scores, game status | Real-time |
| 3 | Schedule | `https://www.espn.com/college-football/schedule` | Full season schedule | Weekly |
| 4 | SP+ Rankings | `https://www.espn.com/college-football/story/_/id/46128861/...` | SP+ ratings (all 136 teams) | Weekly |
| 5 | FPI Ratings | `https://www.espn.com/college-football/fpi` | FPI scores, win probabilities | Weekly |
| 6 | Standings | `https://www.espn.com/college-football/standings` | Conference standings | Daily |
| 7 | Stats | `https://www.espn.com/college-football/stats` | Statistical leaders | After each game |
| 8 | Team Stats | `https://www.espn.com/college-football/stats/_/view/team` | All team stats | After each game |
| 9 | Teams List | `https://www.espn.com/college-football/teams` | All FBS teams | Seasonal |
| 10 | Odds | `https://www.espn.com/college-football/odds` | Betting lines | Hourly |
| 11 | Rankings | `https://www.espn.com/college-football/rankings` | AP, Coaches, CFP polls | Weekly |

---

## 🔄 Wildcard URLs (Team-Based)

| # | Page Type | URL Pattern | Wildcard | Example (Clemson - ID: 228) |
|---|-----------|-------------|----------|----------------------------|
| 12 | Team Home | `/college-football/team/_/id/*` | Team ID | `/college-football/team/_/id/228` |
| 13 | Team Stats | `/college-football/team/stats/_/id/*` | Team ID | `/college-football/team/stats/_/id/228` |
| 14 | Team Stats (Type) | `/college-football/team/stats/_/type/team/id/*` | Team ID | `/college-football/team/stats/_/type/team/id/228` |
| 15 | Team Roster | `/college-football/team/roster/_/id/*` | Team ID | `/college-football/team/roster/_/id/228` |

**Total Team URLs**: 136 teams × 4 pages = **544 URLs**

---

## 🎮 Wildcard URLs (Game-Based)

| # | Page Type | URL Pattern | Wildcard | Example |
|---|-----------|-------------|----------|---------|
| 16 | Game Details | `/college-football/game/_/gameId/*` | Game ID | `/game/_/gameId/401754577` |

**Total Game URLs**: Varies by season (typically **300-400 games**)

---

## 🏈 Complete FBS Team ID Reference

### ACC (17 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Boston College | 103 | `/team/stats/_/id/103` |
| California | 25 | `/team/stats/_/id/25` |
| Clemson | 228 | `/team/stats/_/id/228` |
| Duke | 150 | `/team/stats/_/id/150` |
| Florida State | 52 | `/team/stats/_/id/52` |
| Georgia Tech | 59 | `/team/stats/_/id/59` |
| Louisville | 97 | `/team/stats/_/id/97` |
| Miami | 2390 | `/team/stats/_/id/2390` |
| NC State | 152 | `/team/stats/_/id/152` |
| North Carolina | 153 | `/team/stats/_/id/153` |
| Pittsburgh | 221 | `/team/stats/_/id/221` |
| SMU | 2567 | `/team/stats/_/id/2567` |
| Stanford | 24 | `/team/stats/_/id/24` |
| Syracuse | 183 | `/team/stats/_/id/183` |
| Virginia | 258 | `/team/stats/_/id/258` |
| Virginia Tech | 259 | `/team/stats/_/id/259` |
| Wake Forest | 154 | `/team/stats/_/id/154` |

### American (14 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Army | 349 | `/team/stats/_/id/349` |
| Charlotte | 2429 | `/team/stats/_/id/2429` |
| East Carolina | 151 | `/team/stats/_/id/151` |
| Florida Atlantic | 2226 | `/team/stats/_/id/2226` |
| Memphis | 235 | `/team/stats/_/id/235` |
| Navy | 2426 | `/team/stats/_/id/2426` |
| North Texas | 249 | `/team/stats/_/id/249` |
| Rice | 242 | `/team/stats/_/id/242` |
| South Florida | 58 | `/team/stats/_/id/58` |
| Temple | 218 | `/team/stats/_/id/218` |
| Tulane | 2655 | `/team/stats/_/id/2655` |
| Tulsa | 202 | `/team/stats/_/id/202` |
| UAB | 5 | `/team/stats/_/id/5` |
| UTSA | 2636 | `/team/stats/_/id/2636` |

### Big 12 (16 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Arizona State | 9 | `/team/stats/_/id/9` |
| Arizona | 12 | `/team/stats/_/id/12` |
| BYU | 252 | `/team/stats/_/id/252` |
| Baylor | 239 | `/team/stats/_/id/239` |
| Cincinnati | 2132 | `/team/stats/_/id/2132` |
| Colorado | 38 | `/team/stats/_/id/38` |
| Houston | 248 | `/team/stats/_/id/248` |
| Iowa State | 66 | `/team/stats/_/id/66` |
| Kansas | 2305 | `/team/stats/_/id/2305` |
| Kansas State | 2306 | `/team/stats/_/id/2306` |
| Oklahoma State | 197 | `/team/stats/_/id/197` |
| TCU | 2628 | `/team/stats/_/id/2628` |
| Texas Tech | 2641 | `/team/stats/_/id/2641` |
| UCF | 2116 | `/team/stats/_/id/2116` |
| Utah | 254 | `/team/stats/_/id/254` |
| West Virginia | 277 | `/team/stats/_/id/277` |

### Big Ten (18 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Illinois | 356 | `/team/stats/_/id/356` |
| Indiana | 84 | `/team/stats/_/id/84` |
| Iowa | 2294 | `/team/stats/_/id/2294` |
| Maryland | 120 | `/team/stats/_/id/120` |
| Michigan State | 127 | `/team/stats/_/id/127` |
| Michigan | 130 | `/team/stats/_/id/130` |
| Minnesota | 135 | `/team/stats/_/id/135` |
| Nebraska | 158 | `/team/stats/_/id/158` |
| Northwestern | 77 | `/team/stats/_/id/77` |
| Ohio State | 194 | `/team/stats/_/id/194` |
| Oregon | 2483 | `/team/stats/_/id/2483` |
| Penn State | 213 | `/team/stats/_/id/213` |
| Purdue | 2509 | `/team/stats/_/id/2509` |
| Rutgers | 164 | `/team/stats/_/id/164` |
| UCLA | 26 | `/team/stats/_/id/26` |
| USC | 30 | `/team/stats/_/id/30` |
| Washington | 264 | `/team/stats/_/id/264` |
| Wisconsin | 275 | `/team/stats/_/id/275` |

### Conference USA (12 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Delaware | 48 | `/team/stats/_/id/48` |
| FIU | 2229 | `/team/stats/_/id/2229` |
| Jacksonville State | 55 | `/team/stats/_/id/55` |
| Kennesaw State | 338 | `/team/stats/_/id/338` |
| Liberty | 2335 | `/team/stats/_/id/2335` |
| Louisiana Tech | 2348 | `/team/stats/_/id/2348` |
| Middle Tennessee | 2393 | `/team/stats/_/id/2393` |
| Missouri State | 2623 | `/team/stats/_/id/2623` |
| New Mexico State | 166 | `/team/stats/_/id/166` |
| Sam Houston | 2534 | `/team/stats/_/id/2534` |
| UTEP | 2638 | `/team/stats/_/id/2638` |
| Western Kentucky | 98 | `/team/stats/_/id/98` |

### FBS Independents (2 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Notre Dame | 87 | `/team/stats/_/id/87` |
| UConn | 41 | `/team/stats/_/id/41` |

### MAC (13 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Akron | 2006 | `/team/stats/_/id/2006` |
| Ball State | 2050 | `/team/stats/_/id/2050` |
| Bowling Green | 189 | `/team/stats/_/id/189` |
| Buffalo | 2084 | `/team/stats/_/id/2084` |
| Central Michigan | 2117 | `/team/stats/_/id/2117` |
| Eastern Michigan | 2199 | `/team/stats/_/id/2199` |
| Kent State | 2309 | `/team/stats/_/id/2309` |
| Massachusetts | 113 | `/team/stats/_/id/113` |
| Miami (OH) | 193 | `/team/stats/_/id/193` |
| Northern Illinois | 2459 | `/team/stats/_/id/2459` |
| Ohio | 195 | `/team/stats/_/id/195` |
| Toledo | 2649 | `/team/stats/_/id/2649` |
| Western Michigan | 2711 | `/team/stats/_/id/2711` |

### Mountain West (12 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Air Force | 2005 | `/team/stats/_/id/2005` |
| Boise State | 68 | `/team/stats/_/id/68` |
| Colorado State | 36 | `/team/stats/_/id/36` |
| Fresno State | 278 | `/team/stats/_/id/278` |
| Hawai'i | 62 | `/team/stats/_/id/62` |
| Nevada | 2440 | `/team/stats/_/id/2440` |
| New Mexico | 167 | `/team/stats/_/id/167` |
| San Diego State | 21 | `/team/stats/_/id/21` |
| San José State | 23 | `/team/stats/_/id/23` |
| UNLV | 2439 | `/team/stats/_/id/2439` |
| Utah State | 328 | `/team/stats/_/id/328` |
| Wyoming | 2751 | `/team/stats/_/id/2751` |

### Pac-12 (2 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Oregon State | 204 | `/team/stats/_/id/204` |
| Washington State | 265 | `/team/stats/_/id/265` |

### SEC (16 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| Alabama | 333 | `/team/stats/_/id/333` |
| Arkansas | 8 | `/team/stats/_/id/8` |
| Auburn | 2 | `/team/stats/_/id/2` |
| Florida | 57 | `/team/stats/_/id/57` |
| Georgia | 61 | `/team/stats/_/id/61` |
| Kentucky | 96 | `/team/stats/_/id/96` |
| LSU | 99 | `/team/stats/_/id/99` |
| Mississippi State | 344 | `/team/stats/_/id/344` |
| Missouri | 142 | `/team/stats/_/id/142` |
| Oklahoma | 201 | `/team/stats/_/id/201` |
| Ole Miss | 145 | `/team/stats/_/id/145` |
| South Carolina | 2579 | `/team/stats/_/id/2579` |
| Tennessee | 2633 | `/team/stats/_/id/2633` |
| Texas A&M | 245 | `/team/stats/_/id/245` |
| Texas | 251 | `/team/stats/_/id/251` |
| Vanderbilt | 238 | `/team/stats/_/id/238` |

### Sun Belt (14 teams)
| Team | ID | Team Stats URL |
|------|----|----|
| App State | 2026 | `/team/stats/_/id/2026` |
| Arkansas State | 2032 | `/team/stats/_/id/2032` |
| Coastal Carolina | 324 | `/team/stats/_/id/324` |
| Georgia Southern | 290 | `/team/stats/_/id/290` |
| Georgia State | 2247 | `/team/stats/_/id/2247` |
| James Madison | 256 | `/team/stats/_/id/256` |
| Louisiana | 309 | `/team/stats/_/id/309` |
| Marshall | 276 | `/team/stats/_/id/276` |
| Old Dominion | 295 | `/team/stats/_/id/295` |
| South Alabama | 6 | `/team/stats/_/id/6` |
| Southern Miss | 2572 | `/team/stats/_/id/2572` |
| Texas State | 326 | `/team/stats/_/id/326` |
| Troy | 2653 | `/team/stats/_/id/2653` |
| UL Monroe | 2433 | `/team/stats/_/id/2433` |

---

## 🎯 Quick Lookup

### Popular Teams
| Team | ID | Full URL |
|------|----|----|
| Alabama | 333 | `https://www.espn.com/college-football/team/_/id/333` |
| Clemson | 228 | `https://www.espn.com/college-football/team/_/id/228` |
| Georgia | 61 | `https://www.espn.com/college-football/team/_/id/61` |
| Michigan | 130 | `https://www.espn.com/college-football/team/_/id/130` |
| Notre Dame | 87 | `https://www.espn.com/college-football/team/_/id/87` |
| Ohio State | 194 | `https://www.espn.com/college-football/team/_/id/194` |
| Oklahoma | 201 | `https://www.espn.com/college-football/team/_/id/201` |
| Texas | 251 | `https://www.espn.com/college-football/team/_/id/251` |
| USC | 30 | `https://www.espn.com/college-football/team/_/id/30` |

---

## 📊 URL Pattern Templates

### For Teams
```
Home Page:      https://www.espn.com/college-football/team/_/id/{TEAM_ID}
Stats:          https://www.espn.com/college-football/team/stats/_/id/{TEAM_ID}
Advanced Stats: https://www.espn.com/college-football/team/stats/_/type/team/id/{TEAM_ID}
Roster:         https://www.espn.com/college-football/team/roster/_/id/{TEAM_ID}
```

### For Games
```
Game Details:   https://www.espn.com/college-football/game/_/gameId/{GAME_ID}
```

---

## 🔢 Summary Statistics

| Category | Count |
|----------|-------|
| **Total FBS Teams** | 136 |
| **Conferences** | 11 |
| **Static URLs** | 11 |
| **Team URL Patterns** | 4 |
| **Total Team URLs** | 544 (136 × 4) |
| **Game URL Patterns** | 1 |
| **Typical Game URLs per Season** | 300-400 |
| **Total URLs (approximate)** | 855-955 |

---

## 💡 Usage Examples

### Get Stats for Georgia
```bash
curl https://www.espn.com/college-football/team/stats/_/id/61
```

### Get Roster for Alabama
```bash
curl https://www.espn.com/college-football/team/roster/_/id/333
```

### Get Odds
```bash
curl https://www.espn.com/college-football/odds
```

### Python Example
```python
team_ids = [333, 228, 61, 130, 194]  # Top 5 teams

for team_id in team_ids:
    stats_url = f"https://www.espn.com/college-football/team/stats/_/id/{team_id}"
    roster_url = f"https://www.espn.com/college-football/team/roster/_/id/{team_id}"
    
    # Scrape stats and roster
    scrape(stats_url)
    scrape(roster_url)
```

---

**Last Updated**: November 1, 2025  
**Total Teams**: 136  
**Total URL Patterns**: 16  
**Expanded URLs**: 555+

