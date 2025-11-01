from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime
import os, orjson, pyarrow as pa, pyarrow.parquet as pq

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
            "teams_json":   [orjson.dumps(r.get("teams")).decode() for r in self._buffer],
            "state_json":   [orjson.dumps(r.get("state")).decode() for r in self._buffer],
            "markets_json": [orjson.dumps(r.get("markets")).decode() for r in self._buffer],
        })
        pq_path = os.path.join(self.out_dir, f"overtime-live-{ts}.parquet")
        pq.write_table(table, pq_path)
