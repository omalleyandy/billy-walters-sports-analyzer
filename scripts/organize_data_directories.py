#!/usr/bin/env python3
"""
Reorganize data directories for better separation:
- Injuries vs Odds
- NFL vs NCAAF

New structure:
data/
  injuries/
    nfl/
      nfl-injuries-YYYYMMDD-HHMMSS.jsonl
      nfl-injuries-YYYYMMDD-HHMMSS.parquet
    ncaaf/
      ncaaf-injuries-YYYYMMDD-HHMMSS.jsonl
      ncaaf-injuries-YYYYMMDD-HHMMSS.parquet
  odds/
    nfl/
      nfl-odds-YYYYMMDD-HHMMSS.jsonl
      nfl-odds-YYYYMMDD-HHMMSS.json
      nfl-odds-YYYYMMDD-HHMMSS.csv
    ncaaf/
      ncaaf-odds-YYYYMMDD-HHMMSS.jsonl
      ncaaf-odds-YYYYMMDD-HHMMSS.json
      ncaaf-odds-YYYYMMDD-HHMMSS.csv
"""

import json
import shutil
from pathlib import Path
from datetime import datetime


def create_directory_structure():
    """Create new organized directory structure"""
    base = Path("data")
    
    # Create directories
    dirs = [
        base / "injuries" / "nfl",
        base / "injuries" / "ncaaf",
        base / "odds" / "nfl",
        base / "odds" / "ncaaf",
        base / "archive" / "old_overtime_live",  # Archive old mixed data
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created: {d}")
    
    return True


def move_existing_files():
    """Move existing files to appropriate directories"""
    base = Path("data")
    
    # Move existing injury files
    overtime_live_dir = base / "overtime_live"
    if overtime_live_dir.exists():
        print(f"\nProcessing files in {overtime_live_dir}...")
        
        for file in overtime_live_dir.glob("*.jsonl"):
            # Read first line to determine type
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    data = json.loads(first_line)
                    
                    # Check if it's injury data
                    if 'player_name' in data or 'injury_status' in data:
                        sport = data.get('sport', 'unknown')
                        league = data.get('league', 'unknown')
                        
                        if league == 'NFL' or sport == 'nfl':
                            dest_dir = base / "injuries" / "nfl"
                        elif league == 'NCAAF' or sport == 'college_football':
                            dest_dir = base / "injuries" / "ncaaf"
                        else:
                            dest_dir = base / "archive" / "old_overtime_live"
                        
                        # Keep original filename or rename
                        dest_file = dest_dir / file.name
                        print(f"  Moving injury file: {file.name} to {dest_dir}/")
                        shutil.copy2(file, dest_file)
                    
                    # Check if it's odds data (has game_key and markets)
                    elif 'game_key' in data and 'markets' in data:
                        sport = data.get('sport', 'unknown')
                        league = data.get('league', 'unknown')
                        
                        if league == 'NFL' or sport == 'nfl':
                            dest_dir = base / "odds" / "nfl"
                        elif league == 'NCAAF' or sport == 'college_football':
                            dest_dir = base / "odds" / "ncaaf"
                        else:
                            dest_dir = base / "archive" / "old_overtime_live"
                        
                        dest_file = dest_dir / file.name
                        print(f"  Moving odds file: {file.name} to {dest_dir}/")
                        shutil.copy2(file, dest_file)
                    
                    else:
                        # Unknown format, archive it
                        dest_dir = base / "archive" / "old_overtime_live"
                        dest_file = dest_dir / file.name
                        print(f"  Archiving unknown: {file.name} to {dest_dir}/")
                        shutil.copy2(file, dest_file)
                        
            except Exception as e:
                print(f"  ERROR processing {file.name}: {e}")
    
    # Move existing odds_chrome files
    odds_chrome_dir = base / "odds_chrome"
    if odds_chrome_dir.exists():
        print(f"\nProcessing files in {odds_chrome_dir}...")
        
        for file in odds_chrome_dir.glob("nfl-odds-*"):
            dest_dir = base / "odds" / "nfl"
            dest_file = dest_dir / file.name
            print(f"  Moving NFL odds: {file.name} to {dest_dir}/")
            shutil.copy2(file, dest_file)
        
        for file in odds_chrome_dir.glob("ncaaf-odds-*"):
            dest_dir = base / "odds" / "ncaaf"
            dest_file = dest_dir / file.name
            print(f"  Moving NCAAF odds: {file.name} to {dest_dir}/")
            shutil.copy2(file, dest_file)


def create_readme_files():
    """Create README files in each directory"""
    base = Path("data")
    
    readmes = {
        base / "injuries" / "nfl" / "README.md": 
"""# NFL Injury Data

Source: ESPN NFL Injury Reports (https://www.espn.com/nfl/injuries)

Files in this directory:
- `nfl-injuries-YYYYMMDD-HHMMSS.jsonl` - Line-delimited JSON
- `nfl-injuries-YYYYMMDD-HHMMSS.parquet` - Columnar format

Scrape command:
```bash
uv run walters-analyzer scrape-injuries --sport nfl
```
""",
        
        base / "injuries" / "ncaaf" / "README.md":
"""# NCAA Football Injury Data

Source: ESPN College Football Injury Reports (https://www.espn.com/college-football/injuries)

Files in this directory:
- `ncaaf-injuries-YYYYMMDD-HHMMSS.jsonl` - Line-delimited JSON
- `ncaaf-injuries-YYYYMMDD-HHMMSS.parquet` - Columnar format

Scrape command:
```bash
uv run walters-analyzer scrape-injuries --sport cfb
```
""",
        
        base / "odds" / "nfl" / "README.md":
"""# NFL Betting Odds Data

Source: overtime.ag (https://overtime.ag/sports/)

Files in this directory:
- `nfl-odds-YYYYMMDD-HHMMSS.jsonl` - Line-delimited JSON (one game per line)
- `nfl-odds-YYYYMMDD-HHMMSS.json` - Pretty-printed JSON
- `nfl-odds-YYYYMMDD-HHMMSS.csv` - Flattened CSV

Scrape command:
```bash
# Using Chrome DevTools MCP (via agent)
# Manual: python scrape_odds_mcp.py <snapshot_file>
```
""",
        
        base / "odds" / "ncaaf" / "README.md":
"""# NCAA Football Betting Odds Data

Source: overtime.ag (https://overtime.ag/sports/)

Files in this directory:
- `ncaaf-odds-YYYYMMDD-HHMMSS.jsonl` - Line-delimited JSON (one game per line)
- `ncaaf-odds-YYYYMMDD-HHMMSS.json` - Pretty-printed JSON
- `ncaaf-odds-YYYYMMDD-HHMMSS.csv` - Flattened CSV

Scrape command:
```bash
# Using Chrome DevTools MCP (via agent)
# Manual: python scrape_odds_mcp.py <snapshot_file>
```
"""
    }
    
    for path, content in readmes.items():
        path.write_text(content, encoding='utf-8')
        print(f"[OK] Created README: {path}")


def main():
    print("=" * 80)
    print("  DATA DIRECTORY REORGANIZATION")
    print("=" * 80)
    print()
    
    print("Step 1: Creating new directory structure...")
    create_directory_structure()
    
    print("\nStep 2: Moving existing files...")
    move_existing_files()
    
    print("\nStep 3: Creating README files...")
    create_readme_files()
    
    print("\n" + "=" * 80)
    print("  REORGANIZATION COMPLETE")
    print("=" * 80)
    print()
    print("New structure:")
    print("  data/")
    print("    injuries/")
    print("      nfl/       <- ESPN NFL injury reports")
    print("      ncaaf/     <- ESPN College Football injury reports")
    print("    odds/")
    print("      nfl/       <- overtime.ag NFL betting odds")
    print("      ncaaf/     <- overtime.ag NCAAF betting odds")
    print("    archive/")
    print("      old_overtime_live/  <- Original mixed files (backup)")
    print()
    print("[OK] Files have been copied (originals preserved)")
    print()


if __name__ == "__main__":
    main()

