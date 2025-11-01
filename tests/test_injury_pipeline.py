"""Test the InjuryPipeline to ensure it properly writes JSONL and Parquet files."""
import os
import tempfile
import json
from scrapers.overtime_live.pipelines import InjuryPipeline
from scrapers.overtime_live.items import InjuryReportItem, iso_now


class MockSpider:
    """Mock spider for testing."""
    def __init__(self):
        self.logger = self
    
    def info(self, msg):
        print(f"INFO: {msg}")
    
    def warning(self, msg):
        print(f"WARNING: {msg}")


def test_injury_pipeline_writes_files():
    """Test that InjuryPipeline creates both JSONL and Parquet files."""
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create pipeline with temp directory
        pipeline = InjuryPipeline(out_dir=tmpdir)
        spider = MockSpider()
        
        # Create sample injury items
        items = [
            InjuryReportItem(
                source="espn",
                sport="college_football",
                league="NCAAF",
                collected_at=iso_now(),
                team="Alabama Crimson Tide",
                team_abbr="ALA",
                player_name="Jalen Milroe",
                position="QB",
                injury_status="Questionable",
                injury_type="Ankle",
                date_reported="2025-10-30",
                game_date="2025-11-02",
                opponent="LSU Tigers",
                notes="Limited in practice",
            ).to_dict(),
            InjuryReportItem(
                source="espn",
                sport="college_football",
                league="NCAAF",
                collected_at=iso_now(),
                team="Ohio State Buckeyes",
                team_abbr="OSU",
                player_name="Will Howard",
                position="QB",
                injury_status="Out",
                injury_type="Shoulder",
                date_reported="2025-10-29",
                game_date="2025-11-02",
                opponent="Penn State",
                notes=None,
            ).to_dict(),
        ]
        
        # Process items
        for item in items:
            pipeline.process_item(item, spider)
        
        # Close spider (triggers file writes)
        pipeline.close_spider(spider)
        
        # Verify files were created
        files = os.listdir(tmpdir)
        jsonl_files = [f for f in files if f.endswith('.jsonl')]
        parquet_files = [f for f in files if f.endswith('.parquet')]
        
        assert len(jsonl_files) == 1, f"Expected 1 JSONL file, found {len(jsonl_files)}"
        assert len(parquet_files) == 1, f"Expected 1 Parquet file, found {len(parquet_files)}"
        
        # Verify JSONL content
        jsonl_path = os.path.join(tmpdir, jsonl_files[0])
        with open(jsonl_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2, f"Expected 2 lines in JSONL, found {len(lines)}"
            
            # Parse first line
            first_injury = json.loads(lines[0])
            assert first_injury["player_name"] == "Jalen Milroe"
            assert first_injury["injury_status"] == "Questionable"
            assert first_injury["position"] == "QB"
            
            # Parse second line
            second_injury = json.loads(lines[1])
            assert second_injury["player_name"] == "Will Howard"
            assert second_injury["injury_status"] == "Out"
        
        print(f"[PASS] Pipeline created files: {files}")
        print(f"[PASS] JSONL file contains {len(lines)} injury records")
        
        # Verify Parquet file exists and has correct structure
        try:
            import pyarrow.parquet as pq
            parquet_path = os.path.join(tmpdir, parquet_files[0])
            table = pq.read_table(parquet_path)
            
            assert table.num_rows == 2, f"Expected 2 rows in Parquet, found {table.num_rows}"
            
            # Check that expected columns exist
            expected_columns = [
                "source", "sport", "league", "collected_at", "team", "team_abbr",
                "player_name", "position", "injury_status", "injury_type",
                "date_reported", "game_date", "opponent", "notes"
            ]
            
            for col in expected_columns:
                assert col in table.column_names, f"Expected column '{col}' not found in Parquet"
            
            print(f"[PASS] Parquet file has {table.num_rows} rows and {len(table.column_names)} columns")
            
        except ImportError:
            print("[SKIP] PyArrow not available for Parquet validation")


def test_injury_pipeline_empty_buffer():
    """Test that pipeline handles empty buffer gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = InjuryPipeline(out_dir=tmpdir)
        spider = MockSpider()
        
        # Close spider without processing any items
        pipeline.close_spider(spider)
        
        # Verify no files were created
        files = os.listdir(tmpdir)
        assert len(files) == 0, f"Expected no files for empty buffer, found {files}"
        
        print("[PASS] Pipeline correctly handles empty buffer")


if __name__ == "__main__":
    print("Running InjuryPipeline tests...\n")
    
    test_injury_pipeline_writes_files()
    print()
    
    test_injury_pipeline_empty_buffer()
    print()
    
    print("[SUCCESS] All InjuryPipeline tests passed!")

