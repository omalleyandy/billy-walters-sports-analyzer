"""
Output pipeline for weather data - writes JSONL and Parquet formats.
"""

import orjson
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any


class WeatherDataPipeline:
    """
    Pipeline to write weather data to JSONL and Parquet files.
    Similar to the odds/injury scrapers for consistency.
    """
    
    def __init__(self, output_dir: str = "data/weather"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.buffer: List[Dict[str, Any]] = []
    
    def add_item(self, item: Dict[str, Any]):
        """Add a weather item to the buffer."""
        self.buffer.append(item)
    
    def write_files(self) -> tuple[Path, Path]:
        """
        Write buffered items to JSONL and Parquet files.
        
        Returns:
            Tuple of (jsonl_path, parquet_path)
        """
        if not self.buffer:
            raise ValueError("No weather data to write")
        
        # Generate timestamp for filenames
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        base_name = f"weather-{timestamp}"
        
        jsonl_path = self.output_dir / f"{base_name}.jsonl"
        parquet_path = self.output_dir / f"{base_name}.parquet"
        
        # Write JSONL
        with open(jsonl_path, 'wb') as f:
            for item in self.buffer:
                line = orjson.dumps(item) + b'\n'
                f.write(line)
        
        # Write Parquet
        # Define schema with nullable fields to match Optional types in WeatherReportItem
        schema = pa.schema([
            pa.field('source', pa.string(), nullable=False),
            pa.field('sport', pa.string(), nullable=False),
            pa.field('collected_at', pa.string(), nullable=False),
            pa.field('game_date', pa.string(), nullable=True),
            pa.field('game_time', pa.string(), nullable=True),
            pa.field('stadium', pa.string(), nullable=False),
            pa.field('location', pa.string(), nullable=False),
            pa.field('is_dome', pa.bool_(), nullable=False),
            pa.field('temperature_f', pa.float64(), nullable=True),
            pa.field('feels_like_f', pa.float64(), nullable=True),
            pa.field('wind_speed_mph', pa.float64(), nullable=True),
            pa.field('wind_gust_mph', pa.float64(), nullable=True),
            pa.field('wind_direction', pa.string(), nullable=True),
            pa.field('precipitation_prob', pa.int64(), nullable=True),
            pa.field('precipitation_type', pa.string(), nullable=True),
            pa.field('humidity', pa.int64(), nullable=True),
            pa.field('weather_description', pa.string(), nullable=True),
            pa.field('cloud_cover', pa.int64(), nullable=True),
            pa.field('visibility_miles', pa.float64(), nullable=True),
            pa.field('weather_impact_score', pa.int64(), nullable=True),
            pa.field('betting_adjustment', pa.string(), nullable=True),
            pa.field('location_key', pa.string(), nullable=True),
            pa.field('forecast_url', pa.string(), nullable=True),
        ])
        
        # Convert buffer to PyArrow table
        table = pa.Table.from_pylist(self.buffer, schema=schema)
        
        # Write Parquet file
        pq.write_table(table, parquet_path, compression='snappy')
        
        return jsonl_path, parquet_path
    
    def clear_buffer(self):
        """Clear the buffer after writing."""
        self.buffer.clear()

