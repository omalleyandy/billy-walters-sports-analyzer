from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime
import os, orjson, pyarrow as pa, pyarrow.parquet as pq, csv

class ParquetPipeline:
    def __init__(self, out_dir: str = "data/overtime_live"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
        self._buffer: List[Dict[str, Any]] = []

    @classmethod
    def from_crawler(cls, crawler):
        out_dir = crawler.settings.get("OVERTIME_OUT_DIR", "data/overtime_live")
        return cls(out_dir)

    def process_item(self, item, spider):
        self._buffer.append(item)
        return item

    def close_spider(self, spider):
        if not self._buffer:
            return
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        jsonl_path = os.path.join(self.out_dir, f"overtime-live-{ts}.jsonl")
        with open(jsonl_path, "wb") as f:
            for row in self._buffer:
                f.write(orjson.dumps(row))
                f.write(b"\n")

        table = pa.table({
            "source": [r.get("source") for r in self._buffer],
            "league": [r.get("league") for r in self._buffer],
            "sport":  [r.get("sport")  for r in self._buffer],
            "game_key": [r.get("game_key") for r in self._buffer],
            "collected_at": [r.get("collected_at") for r in self._buffer],
            "event_date": [r.get("event_date") for r in self._buffer],
            "event_time": [r.get("event_time") for r in self._buffer],
            "rotation_number": [r.get("rotation_number") for r in self._buffer],
            "is_live": [r.get("is_live", False) for r in self._buffer],
            "teams_json":   [orjson.dumps(r.get("teams")).decode() for r in self._buffer],
            "state_json":   [orjson.dumps(r.get("state")).decode() for r in self._buffer],
            "markets_json": [orjson.dumps(r.get("markets")).decode() for r in self._buffer],
        })
        pq_path = os.path.join(self.out_dir, f"overtime-live-{ts}.parquet")
        pq.write_table(table, pq_path)


class CSVPipeline:
    """
    Export scraped items to CSV with flattened market data.
    Each game gets one row with columns for spread/total/moneyline fields.
    """
    def __init__(self, out_dir: str = "data/overtime_live"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
        self._buffer: List[Dict[str, Any]] = []

    @classmethod
    def from_crawler(cls, crawler):
        out_dir = crawler.settings.get("OVERTIME_OUT_DIR", "data/overtime_live")
        return cls(out_dir)

    def process_item(self, item, spider):
        self._buffer.append(item)
        return item

    def close_spider(self, spider):
        if not self._buffer:
            return
        
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        csv_path = os.path.join(self.out_dir, f"overtime-live-{ts}.csv")
        
        # Flatten the nested structure for CSV
        flattened_rows = []
        for row in self._buffer:
            flat = {
                "source": row.get("source"),
                "sport": row.get("sport"),
                "league": row.get("league"),
                "collected_at": row.get("collected_at"),
                "event_date": row.get("event_date"),
                "event_time": row.get("event_time"),
                "rotation_number": row.get("rotation_number"),
                "is_live": row.get("is_live", False),
                "game_key": row.get("game_key"),
                "away_team": row.get("teams", {}).get("away"),
                "home_team": row.get("teams", {}).get("home"),
            }
            
            # Extract market data
            markets = row.get("markets", {})
            
            # Spread market
            spread = markets.get("spread", {})
            flat["spread_away_line"] = spread.get("away", {}).get("line") if isinstance(spread.get("away"), dict) else None
            flat["spread_away_price"] = spread.get("away", {}).get("price") if isinstance(spread.get("away"), dict) else None
            flat["spread_home_line"] = spread.get("home", {}).get("line") if isinstance(spread.get("home"), dict) else None
            flat["spread_home_price"] = spread.get("home", {}).get("price") if isinstance(spread.get("home"), dict) else None
            
            # Total market
            total = markets.get("total", {})
            flat["total_over_line"] = total.get("over", {}).get("line") if isinstance(total.get("over"), dict) else None
            flat["total_over_price"] = total.get("over", {}).get("price") if isinstance(total.get("over"), dict) else None
            flat["total_under_line"] = total.get("under", {}).get("line") if isinstance(total.get("under"), dict) else None
            flat["total_under_price"] = total.get("under", {}).get("price") if isinstance(total.get("under"), dict) else None
            
            # Moneyline market
            moneyline = markets.get("moneyline", {})
            flat["moneyline_away_price"] = moneyline.get("away", {}).get("price") if isinstance(moneyline.get("away"), dict) else None
            flat["moneyline_home_price"] = moneyline.get("home", {}).get("price") if isinstance(moneyline.get("home"), dict) else None
            
            # Game state (for live betting)
            state = row.get("state", {})
            flat["quarter"] = state.get("quarter")
            flat["clock"] = state.get("clock")
            
            flattened_rows.append(flat)
        
        # Write CSV
        if flattened_rows:
            fieldnames = list(flattened_rows[0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_rows)


class InjuryPipeline:
    """
    Export injury report items to both JSONL and Parquet formats.
    Handles the InjuryReportItem structure.
    """
    def __init__(self, out_dir: str = "data/injuries"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
        self._buffer: List[Dict[str, Any]] = []

    @classmethod
    def from_crawler(cls, crawler):
        out_dir = crawler.settings.get("INJURY_OUT_DIR", "data/injuries")
        return cls(out_dir)

    def process_item(self, item, spider):
        self._buffer.append(item)
        return item

    def close_spider(self, spider):
        if not self._buffer:
            spider.logger.warning("No injury data collected")
            return
        
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        
        # Write JSONL
        jsonl_path = os.path.join(self.out_dir, f"injuries-{ts}.jsonl")
        with open(jsonl_path, "wb") as f:
            for row in self._buffer:
                f.write(orjson.dumps(row))
                f.write(b"\n")
        spider.logger.info(f"Wrote {len(self._buffer)} injuries to {jsonl_path}")

        # Write Parquet
        table = pa.table({
            "source": [r.get("source") for r in self._buffer],
            "sport": [r.get("sport") for r in self._buffer],
            "league": [r.get("league") for r in self._buffer],
            "collected_at": [r.get("collected_at") for r in self._buffer],
            "team": [r.get("team") for r in self._buffer],
            "team_abbr": [r.get("team_abbr") for r in self._buffer],
            "player_name": [r.get("player_name") for r in self._buffer],
            "position": [r.get("position") for r in self._buffer],
            "injury_status": [r.get("injury_status") for r in self._buffer],
            "injury_type": [r.get("injury_type") for r in self._buffer],
            "date_reported": [r.get("date_reported") for r in self._buffer],
            "game_date": [r.get("game_date") for r in self._buffer],
            "opponent": [r.get("opponent") for r in self._buffer],
            "notes": [r.get("notes") for r in self._buffer],
        })
        pq_path = os.path.join(self.out_dir, f"injuries-{ts}.parquet")
        pq.write_table(table, pq_path)
        spider.logger.info(f"Wrote {len(self._buffer)} injuries to {pq_path}")


class MasseyRatingsPipeline:
    """
    Export Massey Ratings data to JSONL, Parquet, and CSV formats.
    Handles team ratings, game predictions, and matchup analysis.
    """
    def __init__(self, out_dir: str = "data/massey_ratings"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
        self._buffer: List[Dict[str, Any]] = []

    @classmethod
    def from_crawler(cls, crawler):
        out_dir = crawler.settings.get("MASSEY_OUT_DIR", "data/massey_ratings")
        return cls(out_dir)

    def process_item(self, item, spider):
        self._buffer.append(item)
        return item

    def close_spider(self, spider):
        if not self._buffer:
            spider.logger.warning("No Massey Ratings data collected")
            return
        
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        
        # Separate items by type for better organization
        ratings_items = [r for r in self._buffer if r.get("data_type") == "rating"]
        games_items = [r for r in self._buffer if r.get("data_type") == "game"]
        matchup_items = [r for r in self._buffer if r.get("data_type") == "matchup"]
        
        # Write JSONL (all data combined)
        jsonl_path = os.path.join(self.out_dir, f"massey-{ts}.jsonl")
        with open(jsonl_path, "wb") as f:
            for row in self._buffer:
                f.write(orjson.dumps(row))
                f.write(b"\n")
        spider.logger.info(f"Wrote {len(self._buffer)} items to {jsonl_path}")
        
        # Write separate Parquet files by type
        if ratings_items:
            self._write_ratings_parquet(ratings_items, ts, spider)
        
        if games_items:
            self._write_games_parquet(games_items, ts, spider)
        
        if matchup_items:
            self._write_matchups_parquet(matchup_items, ts, spider)
        
        # Write CSV for easy analysis
        if games_items:
            self._write_games_csv(games_items, ts, spider)

    def _write_ratings_parquet(self, items: List[Dict[str, Any]], timestamp: str, spider):
        """Write team ratings to Parquet."""
        try:
            table = pa.table({
                "source": [r.get("source") for r in items],
                "sport": [r.get("sport") for r in items],
                "collected_at": [r.get("collected_at") for r in items],
                "season": [r.get("season") for r in items],
                "rank": [r.get("rank") for r in items],
                "team_name": [r.get("team_name") for r in items],
                "team_abbr": [r.get("team_abbr") for r in items],
                "rating": [r.get("rating") for r in items],
                "offensive_rating": [r.get("offensive_rating") for r in items],
                "defensive_rating": [r.get("defensive_rating") for r in items],
                "sos": [r.get("sos") for r in items],
                "record": [r.get("record") for r in items],
                "conference": [r.get("conference") for r in items],
            })
            pq_path = os.path.join(self.out_dir, f"massey-ratings-{timestamp}.parquet")
            pq.write_table(table, pq_path)
            spider.logger.info(f"Wrote {len(items)} team ratings to {pq_path}")
        except Exception as e:
            spider.logger.error(f"Failed to write ratings parquet: {e}")

    def _write_games_parquet(self, items: List[Dict[str, Any]], timestamp: str, spider):
        """Write game predictions to Parquet."""
        try:
            table = pa.table({
                "source": [r.get("source") for r in items],
                "sport": [r.get("sport") for r in items],
                "collected_at": [r.get("collected_at") for r in items],
                "season": [r.get("season") for r in items],
                "game_date": [r.get("game_date") for r in items],
                "game_time": [r.get("game_time") for r in items],
                "away_team": [r.get("away_team") for r in items],
                "home_team": [r.get("home_team") for r in items],
                "away_rank": [r.get("away_rank") for r in items],
                "home_rank": [r.get("home_rank") for r in items],
                "predicted_spread": [r.get("predicted_spread") for r in items],
                "predicted_total": [r.get("predicted_total") for r in items],
                "predicted_away_score": [r.get("predicted_away_score") for r in items],
                "predicted_home_score": [r.get("predicted_home_score") for r in items],
                "confidence": [r.get("confidence") for r in items],
                "matchup_id": [r.get("matchup_id") for r in items],
                "market_spread": [r.get("market_spread") for r in items],
                "market_total": [r.get("market_total") for r in items],
                "spread_edge": [r.get("spread_edge") for r in items],
                "total_edge": [r.get("total_edge") for r in items],
                "edge_confidence": [r.get("edge_confidence") for r in items],
            })
            pq_path = os.path.join(self.out_dir, f"massey-games-{timestamp}.parquet")
            pq.write_table(table, pq_path)
            spider.logger.info(f"Wrote {len(items)} game predictions to {pq_path}")
        except Exception as e:
            spider.logger.error(f"Failed to write games parquet: {e}")

    def _write_matchups_parquet(self, items: List[Dict[str, Any]], timestamp: str, spider):
        """Write matchup analysis to Parquet."""
        try:
            table = pa.table({
                "source": [r.get("source") for r in items],
                "sport": [r.get("sport") for r in items],
                "collected_at": [r.get("collected_at") for r in items],
                "season": [r.get("season") for r in items],
                "matchup_id": [r.get("matchup_id") for r in items],
                "away_team": [r.get("away_team") for r in items],
                "home_team": [r.get("home_team") for r in items],
                "score_distribution_json": [orjson.dumps(r.get("score_distribution") or {}).decode() for r in items],
                "margin_distribution_json": [orjson.dumps(r.get("margin_distribution") or {}).decode() for r in items],
                "total_distribution_json": [orjson.dumps(r.get("total_distribution") or {}).decode() for r in items],
            })
            pq_path = os.path.join(self.out_dir, f"massey-matchups-{timestamp}.parquet")
            pq.write_table(table, pq_path)
            spider.logger.info(f"Wrote {len(items)} matchup analyses to {pq_path}")
        except Exception as e:
            spider.logger.error(f"Failed to write matchups parquet: {e}")

    def _write_games_csv(self, items: List[Dict[str, Any]], timestamp: str, spider):
        """Write game predictions to CSV for easy viewing."""
        try:
            csv_path = os.path.join(self.out_dir, f"massey-games-{timestamp}.csv")
            
            # Flatten for CSV
            flattened_rows = []
            for row in items:
                flat = {
                    "date": row.get("game_date"),
                    "time": row.get("game_time"),
                    "away_team": row.get("away_team"),
                    "home_team": row.get("home_team"),
                    "predicted_away_score": row.get("predicted_away_score"),
                    "predicted_home_score": row.get("predicted_home_score"),
                    "predicted_spread": row.get("predicted_spread"),
                    "predicted_total": row.get("predicted_total"),
                    "confidence": row.get("confidence"),
                    "market_spread": row.get("market_spread"),
                    "market_total": row.get("market_total"),
                    "spread_edge": row.get("spread_edge"),
                    "total_edge": row.get("total_edge"),
                    "edge_confidence": row.get("edge_confidence"),
                }
                flattened_rows.append(flat)
            
            # Write CSV
            if flattened_rows:
                fieldnames = list(flattened_rows[0].keys())
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_rows)
                spider.logger.info(f"Wrote {len(flattened_rows)} games to {csv_path}")
        except Exception as e:
            spider.logger.error(f"Failed to write games CSV: {e}")


class OddsChangeTrackerPipeline:
    """
    Track odds changes and log them in real-time.
    
    Uses SQLite by default, with optional Redis support for distributed tracking.
    Detects changes in spread, total, and moneyline markets.
    """
    
    def __init__(self, out_dir: str = "data/overtime_live", use_redis: bool = False):
        """
        Initialize odds change tracker.
        
        Args:
            out_dir: Output directory for change logs
            use_redis: Whether to use Redis (falls back to SQLite if unavailable)
        """
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
        
        # Import helper classes
        from .cdp_helpers import (
            OddsChangeDetector,
            SQLiteOddsStorage,
            RedisOddsStorage
        )
        
        # Setup storage backend
        if use_redis:
            redis_storage = RedisOddsStorage()
            if redis_storage.available:
                self.storage = redis_storage
                self.storage_type = "Redis"
            else:
                # Fallback to SQLite
                self.storage = SQLiteOddsStorage(
                    os.path.join(out_dir, "odds_changes.db")
                )
                self.storage_type = "SQLite"
        else:
            self.storage = SQLiteOddsStorage(
                os.path.join(out_dir, "odds_changes.db")
            )
            self.storage_type = "SQLite"
        
        # Create change detector
        self.detector = OddsChangeDetector(self.storage, out_dir)
    
    @classmethod
    def from_crawler(cls, crawler):
        """
        Create pipeline from Scrapy crawler.
        
        Args:
            crawler: Scrapy crawler instance
            
        Returns:
            OddsChangeTrackerPipeline instance
        """
        out_dir = crawler.settings.get("OVERTIME_OUT_DIR", "data/overtime_live")
        use_redis = crawler.settings.get("USE_REDIS_ODDS_TRACKING", False)
        return cls(out_dir, use_redis)
    
    def open_spider(self, spider):
        """Log pipeline startup."""
        spider.logger.info(
            f"OddsChangeTrackerPipeline initialized with {self.storage_type} storage"
        )
    
    def process_item(self, item, spider):
        """
        Process each scraped item and check for odds changes.
        
        Args:
            item: Scraped game item
            spider: Spider instance
            
        Returns:
            The item (unchanged)
        """
        try:
            # Check for changes and log if detected
            self.detector.check_and_log_changes(item)
        except Exception as e:
            spider.logger.error(f"Error tracking odds change: {e}")
        
        return item
    
    def close_spider(self, spider):
        """Clean up storage resources."""
        try:
            self.storage.close()
            spider.logger.info("OddsChangeTrackerPipeline closed")
        except Exception as e:
            spider.logger.error(f"Error closing odds tracker: {e}")