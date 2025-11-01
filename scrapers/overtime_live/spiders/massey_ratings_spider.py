from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, List
from datetime import datetime

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page, TimeoutError as PWTimeout

# Local modules
from ..items import MasseyRatingsItem, iso_now

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


class MasseyRatingsSpider(scrapy.Spider):
    """
    Comprehensive scraper for Massey Ratings college football data.
    
    Collects:
    1. Team power ratings (offensive, defensive, overall)
    2. Game predictions (spreads, totals, scores)
    3. Matchup analysis (score/margin/total distributions)
    
    This provides a solid foundation for identifying betting edges
    and benchmarking our Billy Walters-based ratings.
    
    Usage:
        scrapy crawl massey_ratings
        scrapy crawl massey_ratings -a data_type=all  # ratings, games, matchups
        scrapy crawl massey_ratings -a data_type=ratings
        scrapy crawl massey_ratings -a data_type=games
    """

    name = "massey_ratings"

    custom_settings = {
        "BOT_NAME": "massey_ratings",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60_000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "CONCURRENT_REQUESTS": 2,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
        # Use custom pipeline for JSONL + Parquet output
        "ITEM_PIPELINES": {
            "scrapers.overtime_live.pipelines.MasseyRatingsPipeline": 300,
        },
    }

    def __init__(self, data_type="all", season="2025", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_type = data_type.lower()  # "all", "ratings", "games", "matchups"
        self.season = season
        
        # Massey Ratings URLs
        self.base_url = "https://masseyratings.com"
        self.urls = {
            "main": f"{self.base_url}/cf/fbs",
            "ratings": f"{self.base_url}/cf/fbs/ratings",
            "games": f"{self.base_url}/cf/fbs/games",
            "scoredist": f"{self.base_url}/scoredist?s=cf{season}&sub=11604&x=s",
        }

    def start_requests(self):
        """Entry point for the spider."""
        self.logger.info(f"Starting Massey Ratings scraper for: {self.data_type}")
        
        # Determine which pages to scrape
        if self.data_type in ("all", "ratings"):
            yield self._create_request(self.urls["ratings"], self.parse_ratings_page)
        
        if self.data_type in ("all", "games"):
            yield self._create_request(self.urls["games"], self.parse_games_page)

    def _create_request(self, url: str, callback):
        """Create a Scrapy request with Playwright."""
        meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "domcontentloaded",
                "timeout": 60_000,
            },
            "playwright_page_methods": [
                PageMethod("wait_for_timeout", 2000),  # Let dynamic content load
            ],
        }

        return scrapy.Request(
            url,
            meta=meta,
            callback=callback,
            errback=self.errback,
        )

    async def errback(self, failure):
        """Handle request failures."""
        self.logger.error("Request failed: %r", failure)
        page = failure.request.meta.get("playwright_page")
        if page:
            os.makedirs("snapshots", exist_ok=True)
            try:
                await page.screenshot(path="snapshots/massey_error.png", full_page=True)
                self.logger.error("Saved error screenshot to snapshots/massey_error.png")
            except Exception:
                self.logger.debug("Could not write error screenshot", exc_info=True)
            try:
                await page.close()
            except Exception:
                pass

    async def parse_ratings_page(self, response: Response):
        """Parse the Massey Ratings power ratings page."""
        page: Page = response.meta["playwright_page"]
        
        # Take a snapshot for debugging
        os.makedirs("snapshots", exist_ok=True)
        try:
            await page.screenshot(path="snapshots/massey_ratings.png", full_page=True)
            self.logger.info("Saved ratings page screenshot")
        except Exception:
            pass

        # Extract ratings data
        ratings = await self._extract_ratings(page)
        
        self.logger.info(f"Extracted {len(ratings)} team ratings")
        
        # Emit items
        for rating_data in ratings:
            item = MasseyRatingsItem(
                source="masseyratings",
                sport="college_football",
                collected_at=iso_now(),
                data_type="rating",
                season=self.season,
                team_name=rating_data.get("team_name"),
                team_abbr=rating_data.get("team_abbr"),
                rank=rating_data.get("rank"),
                rating=rating_data.get("rating"),
                offensive_rating=rating_data.get("offensive_rating"),
                defensive_rating=rating_data.get("defensive_rating"),
                sos=rating_data.get("sos"),
                record=rating_data.get("record"),
                conference=rating_data.get("conference"),
                # Game fields set to None for ratings
                game_date=None,
                game_time=None,
                away_team=None,
                home_team=None,
                away_rank=None,
                home_rank=None,
                predicted_spread=None,
                predicted_total=None,
                predicted_away_score=None,
                predicted_home_score=None,
                confidence=None,
                matchup_id=None,
                score_distribution=None,
                margin_distribution=None,
                total_distribution=None,
                market_spread=None,
                market_total=None,
                spread_edge=None,
                total_edge=None,
                edge_confidence=None,
                notes=None,
                raw_data=rating_data,
            )
            yield json.loads(json.dumps(item, default=lambda o: o.__dict__))

        try:
            await page.close()
        except Exception:
            pass

    async def parse_games_page(self, response: Response):
        """Parse the Massey Ratings games/predictions page."""
        page: Page = response.meta["playwright_page"]
        
        # Take a snapshot for debugging
        os.makedirs("snapshots", exist_ok=True)
        try:
            await page.screenshot(path="snapshots/massey_games.png", full_page=True)
            self.logger.info("Saved games page screenshot")
        except Exception:
            pass

        # Extract games data
        games = await self._extract_games(page)
        
        self.logger.info(f"Extracted {len(games)} game predictions")
        
        # Emit items
        for game_data in games:
            item = MasseyRatingsItem(
                source="masseyratings",
                sport="college_football",
                collected_at=iso_now(),
                data_type="game",
                season=self.season,
                # Team rating fields set to None for games
                team_name=None,
                team_abbr=None,
                rank=None,
                rating=None,
                offensive_rating=None,
                defensive_rating=None,
                sos=None,
                record=None,
                conference=None,
                # Game fields
                game_date=game_data.get("game_date"),
                game_time=game_data.get("game_time"),
                away_team=game_data.get("away_team"),
                home_team=game_data.get("home_team"),
                away_rank=game_data.get("away_rank"),
                home_rank=game_data.get("home_rank"),
                predicted_spread=game_data.get("predicted_spread"),
                predicted_total=game_data.get("predicted_total"),
                predicted_away_score=game_data.get("predicted_away_score"),
                predicted_home_score=game_data.get("predicted_home_score"),
                confidence=game_data.get("confidence"),
                matchup_id=game_data.get("matchup_id"),
                score_distribution=None,
                margin_distribution=None,
                total_distribution=None,
                market_spread=game_data.get("market_spread"),
                market_total=game_data.get("market_total"),
                spread_edge=game_data.get("spread_edge"),
                total_edge=game_data.get("total_edge"),
                edge_confidence=game_data.get("edge_confidence"),
                notes=None,
                raw_data=game_data,
            )
            yield json.loads(json.dumps(item, default=lambda o: o.__dict__))

        try:
            await page.close()
        except Exception:
            pass

    async def _extract_ratings(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract team ratings from the ratings page.
        
        Massey Ratings table structure:
        Team | Record | Δ | Rat | Pwr | Off | Def | HFA | SoS | SSF | EW | EL
        """
        js_code = """
        () => {
            const ratings = [];
            
            // Look for the main ratings table
            const tables = document.querySelectorAll('table');
            
            for (const table of tables) {
                const rows = Array.from(table.querySelectorAll('tbody tr, tr'));
                
                for (const row of rows) {
                    try {
                        const cells = Array.from(row.querySelectorAll('td'));
                        if (cells.length < 8) continue;
                        
                        // Skip header/correlation rows
                        const cellText = cells[0]?.innerText?.trim() || '';
                        if (cellText.includes('Team') || cellText.includes('Correlation')) continue;
                        
                        // Cell 0: Team and Conference
                        // Format: "Ohio St Big 10" where "Ohio St" and "Big 10" are links
                        const teamCell = cells[0];
                        const teamLinks = teamCell ? Array.from(teamCell.querySelectorAll('a')) : [];
                        const teamName = teamLinks[0]?.innerText?.trim();
                        const conference = teamLinks[1]?.innerText?.trim();
                        
                        // Cell 1: Record and Win% (e.g., "7-0 1.000")
                        const recordText = cells[1]?.innerText?.trim() || '';
                        const recordMatch = recordText.match(/(\\d+-\\d+)/);
                        const record = recordMatch ? recordMatch[1] : null;
                        
                        // Cell 2: Rank change (Δ) - skip
                        
                        // Cell 3: Rat (Rank and Rating, e.g., "1 9.36")
                        const ratText = cells[3]?.innerText?.trim() || '';
                        const ratMatch = ratText.match(/(\\d+)\\s+(-?\\d+\\.\\d+)/);
                        const rank = ratMatch ? parseInt(ratMatch[1]) : null;
                        const rating = ratMatch ? parseFloat(ratMatch[2]) : null;
                        
                        // Cell 4: Pwr (Power rating, e.g., "1 84.17")
                        const pwrText = cells[4]?.innerText?.trim() || '';
                        const pwrMatch = pwrText.match(/\\d+\\s+(-?\\d+\\.\\d+)/);
                        const powerRating = pwrMatch ? parseFloat(pwrMatch[1]) : null;
                        
                        // Cell 5: Off (Offensive rating, e.g., "6 66.47")
                        const offText = cells[5]?.innerText?.trim() || '';
                        const offMatch = offText.match(/\\d+\\s+(-?\\d+\\.\\d+)/);
                        const offensiveRating = offMatch ? parseFloat(offMatch[1]) : null;
                        
                        // Cell 6: Def (Defensive rating, e.g., "1 45.50")
                        const defText = cells[6]?.innerText?.trim() || '';
                        const defMatch = defText.match(/\\d+\\s+(-?\\d+\\.\\d+)/);
                        const defensiveRating = defMatch ? parseFloat(defMatch[1]) : null;
                        
                        // Cell 8: SoS (Strength of Schedule, e.g., "51 55.28")
                        const sosText = cells[8]?.innerText?.trim() || '';
                        const sosMatch = sosText.match(/\\d+\\s+(-?\\d+\\.\\d+)/);
                        const sos = sosMatch ? parseFloat(sosMatch[1]) : null;
                        
                        if (teamName && rank !== null && rating !== null) {
                            ratings.push({
                                rank: rank,
                                team_name: teamName,
                                rating: rating,
                                power_rating: powerRating,
                                offensive_rating: offensiveRating,
                                defensive_rating: defensiveRating,
                                sos: sos,
                                record: record,
                                conference: conference,
                            });
                        }
                        
                    } catch (e) {
                        console.error('Error parsing rating row:', e);
                    }
                }
                
                // If we found data in this table, break
                if (ratings.length > 0) break;
            }
            
            return ratings;
        }
        """
        
        try:
            results = await page.evaluate(js_code)
            if isinstance(results, list) and results:
                self.logger.info(f"Extracted {len(results)} ratings from page")
                return self._normalize_ratings(results)
        except Exception:
            self.logger.error("Ratings extraction failed", exc_info=True)
        
        return []

    async def _extract_games(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract game predictions from the games page.
        
        Massey Ratings games page shows:
        Date | Team | Standing | Scr | Pred | Pwin | Margin | Total
        """
        js_code = """
        () => {
            const games = [];
            
            // Find the main games table (typically has header row with "Date", "Team", "Pred", etc.)
            const tables = document.querySelectorAll('table');
            
            for (const table of tables) {
                const rows = Array.from(table.querySelectorAll('tbody tr, tr'));
                
                for (const row of rows) {
                    try {
                        const cells = Array.from(row.querySelectorAll('td'));
                        if (cells.length < 6) continue;
                        
                        // Skip header rows
                        const cellText = cells[0]?.innerText?.trim() || '';
                        if (cellText.includes('Date') || cellText.includes('Team')) continue;
                        
                        // Cell 0: Date/Time
                        const dateTimeText = cells[0]?.innerText?.trim() || '';
                        const dateMatch = dateTimeText.match(/(\\w+)\\s+(\\d{1,2})\\.(\\d{1,2})/);
                        const timeMatch = dateTimeText.match(/(\\d{1,2}:\\d{2}\\.?(AM|PM)(\\.ET)?)/i);
                        const gameDate = dateMatch ? `${dateMatch[2]}/${dateMatch[3]}` : null;
                        const gameTime = timeMatch ? timeMatch[1].replace('.', ' ') : null;
                        
                        // Cell 1: Teams (e.g., "Army @ Air Force")
                        const teamCell = cells[1];
                        const teamLinks = teamCell ? Array.from(teamCell.querySelectorAll('a')) : [];
                        const awayTeam = teamLinks[0]?.innerText?.trim().replace('@', '').trim();
                        const homeTeam = teamLinks[1]?.innerText?.trim().replace('@', '').trim();
                        
                        // Cell 2: Standing (rankings and records, e.g., "# 76 (3-4) # 107 (2-5)")
                        const standingText = cells[2]?.innerText?.trim() || '';
                        const awayRankMatch = standingText.match(/#\\s*(\\d+)/);
                        const homeRankMatch = standingText.match(/#\\s*\\d+[^#]*#\\s*(\\d+)/);
                        const awayRank = awayRankMatch ? parseInt(awayRankMatch[1]) : null;
                        const homeRank = homeRankMatch ? parseInt(homeRankMatch[1]) : null;
                        
                        // Cell 3: Current Scores (skip for upcoming games)
                        // Cell 4: Predicted Scores (e.g., "28 24")
                        const predScoresText = cells[4]?.innerText?.trim() || '';
                        const scoreMatch = predScoresText.match(/(\\d+)\\s+(\\d+)/);
                        const predictedAwayScore = scoreMatch ? parseFloat(scoreMatch[1]) : null;
                        const predictedHomeScore = scoreMatch ? parseFloat(scoreMatch[2]) : null;
                        
                        // Cell 5: Win Probability (e.g., "62 % 38 %")
                        const pwinText = cells[5]?.innerText?.trim() || '';
                        const pwinMatch = pwinText.match(/(\\d+)\\s*%/);
                        const awayWinProb = pwinMatch ? parseInt(pwinMatch[1]) : null;
                        
                        // Cell 6: Predicted Margin/Spread (e.g., "-3.5")
                        const marginText = cells[6]?.innerText?.trim() || '';
                        const spreadMatch = marginText.match(/(-?\\d+\\.?\\d*)/);
                        const predictedSpread = spreadMatch ? parseFloat(spreadMatch[1]) : null;
                        
                        // Cell 7: Predicted Total (e.g., "55.5")
                        const totalText = cells[7]?.innerText?.trim() || '';
                        const totalMatch = totalText.match(/(\\d+\\.?\\d*)/);
                        const predictedTotal = totalMatch ? parseFloat(totalMatch[1]) : null;
                        
                        // Only add if we have valid game data
                        if (awayTeam && homeTeam && predictedAwayScore !== null && predictedHomeScore !== null) {
                            games.push({
                                game_date: gameDate,
                                game_time: gameTime,
                                away_team: awayTeam,
                                home_team: homeTeam,
                                away_rank: awayRank,
                                home_rank: homeRank,
                                predicted_away_score: predictedAwayScore,
                                predicted_home_score: predictedHomeScore,
                                predicted_spread: predictedSpread,
                                predicted_total: predictedTotal,
                                away_win_prob: awayWinProb,
                            });
                        }
                        
                    } catch (e) {
                        console.error('Error parsing game row:', e);
                    }
                }
                
                // If we found data in this table, break
                if (games.length > 0) break;
            }
            
            return games;
        }
        """
        
        try:
            results = await page.evaluate(js_code)
            if isinstance(results, list) and results:
                self.logger.info(f"Extracted {len(results)} games from page")
                return self._normalize_games(results)
        except Exception:
            self.logger.error("Games extraction failed", exc_info=True)
        
        return []

    def _normalize_ratings(self, raw_ratings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize rating data to consistent format.
        """
        normalized = []
        
        for rating in raw_ratings:
            # Clean up team name
            team_name = rating.get("team_name", "").strip()
            if not team_name:
                continue
            
            # Generate team abbreviation (simple approach)
            team_abbr = self._generate_team_abbr(team_name)
            
            normalized.append({
                "rank": rating.get("rank"),
                "team_name": team_name,
                "team_abbr": team_abbr,
                "rating": rating.get("rating"),
                "power_rating": rating.get("power_rating"),
                "offensive_rating": rating.get("offensive_rating"),
                "defensive_rating": rating.get("defensive_rating"),
                "sos": rating.get("sos"),
                "record": rating.get("record"),
                "conference": rating.get("conference"),
            })
        
        return normalized

    def _normalize_games(self, raw_games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize game data to consistent format.
        """
        normalized = []
        
        for game in raw_games:
            # Parse and normalize date
            game_date = self._parse_game_date(game.get("game_date", ""))
            
            # Generate matchup ID
            matchup_id = f"{game.get('away_team', '')}@{game.get('home_team', '')}_{game_date}"
            
            normalized.append({
                "game_date": game_date,
                "game_time": game.get("game_time"),
                "away_team": game.get("away_team", "").strip(),
                "home_team": game.get("home_team", "").strip(),
                "predicted_away_score": game.get("predicted_away_score"),
                "predicted_home_score": game.get("predicted_home_score"),
                "predicted_spread": game.get("predicted_spread"),
                "predicted_total": game.get("predicted_total"),
                "matchup_id": matchup_id,
                "confidence": self._calculate_confidence(game),
            })
        
        return normalized

    def _generate_team_abbr(self, team_name: str) -> str:
        """Generate a team abbreviation from full name."""
        # Simple heuristic: take first letters of words
        words = team_name.split()
        if len(words) == 1:
            return team_name[:3].upper()
        return "".join(w[0] for w in words if w[0].isupper())[:4].upper()

    def _parse_game_date(self, date_str: str) -> Optional[str]:
        """Parse game date to ISO format."""
        if not date_str:
            return None
        
        try:
            # Handle "11/2" format
            if "/" in date_str:
                month, day = date_str.split("/")
                year = datetime.now().year
                dt = datetime(year, int(month), int(day))
                return dt.strftime("%Y-%m-%d")
            
            # Handle "Nov 2" format
            if " " in date_str:
                year = datetime.now().year
                dt = datetime.strptime(f"{date_str} {year}", "%b %d %Y")
                return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
        
        return None

    def _calculate_confidence(self, game_data: Dict[str, Any]) -> str:
        """
        Calculate prediction confidence based on available data.
        
        Billy Walters methodology: Higher confidence with:
        - Clear score predictions
        - Large spreads (blowouts easier to predict)
        - Complete data
        """
        confidence_score = 0
        
        # Has predicted scores
        if game_data.get("predicted_away_score") and game_data.get("predicted_home_score"):
            confidence_score += 30
        
        # Has spread
        if game_data.get("predicted_spread") is not None:
            confidence_score += 20
            
            # Large spreads are more confident
            spread = abs(game_data.get("predicted_spread", 0))
            if spread > 14:
                confidence_score += 20
            elif spread > 7:
                confidence_score += 10
        
        # Has total
        if game_data.get("predicted_total"):
            confidence_score += 20
        
        # Has complete date/time
        if game_data.get("game_date") and game_data.get("game_time"):
            confidence_score += 10
        
        if confidence_score >= 70:
            return "High"
        elif confidence_score >= 40:
            return "Medium"
        else:
            return "Low"

