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