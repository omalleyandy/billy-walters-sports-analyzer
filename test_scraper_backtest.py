#!/usr/bin/env python3
"""
Scraper Data Validation and Analysis Script

This script performs comprehensive backtesting and validation of scraper outputs:
- Schema validation
- Data quality metrics
- Market completeness analysis
- Missing/invalid field detection
- Timestamp accuracy checks
- Sample data inspection

Usage:
    uv run python test_scraper_backtest.py [--data-dir ./data/overtime_live]
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

try:
    import pyarrow.parquet as pq
except ImportError:
    pq = None


class ScraperDataAnalyzer:
    """Analyze and validate scraper output data"""

    def __init__(self, data_dir: str = "./data/overtime_live"):
        self.data_dir = Path(data_dir)
        self.results = {
            "files_analyzed": 0,
            "total_records": 0,
            "errors": [],
            "warnings": [],
            "metrics": {},
            "samples": [],
        }

    def analyze_all(self):
        """Run complete analysis on all data files"""
        print("=" * 80)
        print("SCRAPER DATA VALIDATION & BACKTESTING REPORT")
        print("=" * 80)
        print(f"\nData Directory: {self.data_dir}")
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not self.data_dir.exists():
            print(f"❌ ERROR: Data directory not found: {self.data_dir}")
            return

        # Find all JSONL files
        jsonl_files = sorted(self.data_dir.glob("*.jsonl"))
        parquet_files = sorted(self.data_dir.glob("*.parquet"))
        csv_files = sorted(self.data_dir.glob("*.csv"))

        print(f"📊 Files Found:")
        print(f"   - JSONL: {len(jsonl_files)}")
        print(f"   - Parquet: {len(parquet_files)}")
        print(f"   - CSV: {len(csv_files)}")
        print()

        if not jsonl_files:
            print("⚠️  No JSONL files found. Run scrapers first.")
            return

        # Analyze each file
        all_records = []
        for file_path in jsonl_files:
            records = self._analyze_jsonl_file(file_path)
            all_records.extend(records)

        if not all_records:
            print("❌ No records found in data files")
            return

        # Separate injury data from odds data
        injury_records = [r for r in all_records if "player_name" in r or "injury_status" in r]
        odds_records = [r for r in all_records if "game_key" in r and "markets" in r]

        print(f"\n📋 Data Type Distribution:")
        print(f"   • Injury Data: {len(injury_records)} records")
        print(f"   • Odds Data: {len(odds_records)} records")
        print(f"   • Other: {len(all_records) - len(injury_records) - len(odds_records)} records")

        # Filter out invalid odds records (bad team names, no markets)
        valid_odds_records = []
        invalid_odds_records = []
        for r in odds_records:
            teams = r.get("teams", {})
            away = teams.get("away", "")
            home = teams.get("home", "")

            # Validate team names: must be at least 3 chars, no emojis, valid characters only
            import re
            is_valid_away = len(away) >= 3 and re.match(r'^[A-Za-z\s\-\.&\']+$', away)
            is_valid_home = len(home) >= 3 and re.match(r'^[A-Za-z\s\-\.&\']+$', home)

            # Check if at least one market has data
            markets = r.get("markets", {})
            has_any_market = (
                markets.get("spread", {}).get("away") or
                markets.get("spread", {}).get("home") or
                markets.get("total", {}).get("over") or
                markets.get("total", {}).get("under") or
                markets.get("moneyline", {}).get("away") or
                markets.get("moneyline", {}).get("home")
            )

            if is_valid_away and is_valid_home and has_any_market:
                valid_odds_records.append(r)
            else:
                invalid_odds_records.append(r)
                self.results["warnings"].append(
                    f"Filtered invalid odds record: away='{away}', home='{home}', has_markets={has_any_market}"
                )

        print(f"\n🔍 Odds Data Quality:")
        print(f"   • Valid: {len(valid_odds_records)} records")
        print(f"   • Invalid (filtered): {len(invalid_odds_records)} records")

        if not valid_odds_records:
            print("\n⚠️  No valid odds records found. Cannot perform odds analysis.")
            print("   This is normal if you've only run the injury scraper.")
            print("   To generate odds data, run: uv run walters-analyzer scrape-overtime --sport nfl")
            self._print_summary()
            return

        # Aggregate analysis on valid odds data only
        self._analyze_schema(valid_odds_records)
        self._analyze_data_quality(valid_odds_records)
        self._analyze_markets(valid_odds_records)
        self._analyze_timestamps(valid_odds_records)
        self._show_samples(valid_odds_records)

        # Final summary
        self._print_summary()

    def _analyze_jsonl_file(self, file_path: Path) -> List[Dict]:
        """Load and parse a JSONL file"""
        print(f"📄 Analyzing: {file_path.name}")
        records = []

        try:
            with open(file_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        self.results["errors"].append(
                            f"{file_path.name}:{line_num} - JSON parse error: {e}"
                        )

            self.results["files_analyzed"] += 1
            self.results["total_records"] += len(records)
            print(f"   ✓ Loaded {len(records)} records")

        except Exception as e:
            self.results["errors"].append(f"{file_path.name} - Read error: {e}")
            print(f"   ❌ Error reading file: {e}")

        return records

    def _analyze_schema(self, records: List[Dict]):
        """Validate schema and required fields"""
        print("\n" + "=" * 80)
        print("SCHEMA VALIDATION")
        print("=" * 80)

        required_fields = [
            "source",
            "sport",
            "league",
            "collected_at",
            "game_key",
            "teams",
            "markets",
            "is_live",
        ]

        optional_fields = [
            "event_date",
            "event_time",
            "rotation_number",
            "state",
        ]

        # Check field presence
        field_counts = defaultdict(int)
        for record in records:
            for field in record.keys():
                field_counts[field] += 1

        total = len(records)

        print(f"\n📋 Required Fields (out of {total} records):")
        for field in required_fields:
            count = field_counts.get(field, 0)
            percentage = (count / total * 100) if total > 0 else 0
            status = "✓" if count == total else "⚠️"
            print(f"   {status} {field:20s}: {count:6d} ({percentage:5.1f}%)")

            if count < total:
                self.results["warnings"].append(
                    f"Missing '{field}' in {total - count} records"
                )

        print(f"\n📋 Optional Fields:")
        for field in optional_fields:
            count = field_counts.get(field, 0)
            percentage = (count / total * 100) if total > 0 else 0
            print(f"   • {field:20s}: {count:6d} ({percentage:5.1f}%)")

        self.results["metrics"]["field_coverage"] = dict(field_counts)

    def _analyze_data_quality(self, records: List[Dict]):
        """Analyze data quality metrics"""
        print("\n" + "=" * 80)
        print("DATA QUALITY METRICS")
        print("=" * 80)

        # Source distribution
        sources = Counter(r.get("source") for r in records)
        print(f"\n📊 Source Distribution:")
        for source, count in sources.most_common():
            print(f"   • {source}: {count} records")

        # Sport/League distribution
        sports = Counter(r.get("sport") for r in records)
        leagues = Counter(r.get("league") for r in records)

        print(f"\n🏈 Sport Distribution:")
        for sport, count in sports.most_common():
            print(f"   • {sport}: {count} records")

        print(f"\n🏆 League Distribution:")
        for league, count in leagues.most_common():
            print(f"   • {league}: {count} records")

        # Team name quality
        print(f"\n👥 Team Data Quality:")
        teams_with_away = sum(
            1 for r in records if r.get("teams", {}).get("away")
        )
        teams_with_home = sum(
            1 for r in records if r.get("teams", {}).get("home")
        )
        print(f"   • Away team present: {teams_with_away}/{len(records)}")
        print(f"   • Home team present: {teams_with_home}/{len(records)}")

        # Live vs Pre-game
        live_games = sum(1 for r in records if r.get("is_live") is True)
        pregame_games = sum(1 for r in records if r.get("is_live") is False)
        print(f"\n⚡ Game Status:")
        print(f"   • Live games: {live_games}")
        print(f"   • Pre-game: {pregame_games}")

        self.results["metrics"]["sources"] = dict(sources)
        self.results["metrics"]["sports"] = dict(sports)
        self.results["metrics"]["leagues"] = dict(leagues)

    def _analyze_markets(self, records: List[Dict]):
        """Analyze betting market completeness"""
        print("\n" + "=" * 80)
        print("BETTING MARKETS ANALYSIS")
        print("=" * 80)

        total = len(records)

        # Market presence
        has_spread = 0
        has_total = 0
        has_moneyline = 0
        complete_markets = 0

        spread_away_complete = 0
        spread_home_complete = 0
        total_over_complete = 0
        total_under_complete = 0
        ml_away_complete = 0
        ml_home_complete = 0

        for record in records:
            markets = record.get("markets", {})

            # Spread
            spread = markets.get("spread", {})
            if spread and (spread.get("away") or spread.get("home")):
                has_spread += 1
            if self._is_quote_complete(spread.get("away")):
                spread_away_complete += 1
            if self._is_quote_complete(spread.get("home")):
                spread_home_complete += 1

            # Total
            total_market = markets.get("total", {})
            if total_market and (total_market.get("over") or total_market.get("under")):
                has_total += 1
            if self._is_quote_complete(total_market.get("over")):
                total_over_complete += 1
            if self._is_quote_complete(total_market.get("under")):
                total_under_complete += 1

            # Moneyline
            moneyline = markets.get("moneyline", {})
            if moneyline and (moneyline.get("away") or moneyline.get("home")):
                has_moneyline += 1
            if self._is_quote_complete(moneyline.get("away"), require_line=False):
                ml_away_complete += 1
            if self._is_quote_complete(moneyline.get("home"), require_line=False):
                ml_home_complete += 1

            # Complete markets (all three present)
            if has_spread and has_total and has_moneyline:
                complete_markets += 1

        print(f"\n📈 Market Presence (out of {total} records):")
        print(f"   • Spread:    {has_spread:6d} ({has_spread/total*100:5.1f}%)")
        print(f"   • Total:     {has_total:6d} ({has_total/total*100:5.1f}%)")
        print(f"   • Moneyline: {has_moneyline:6d} ({has_moneyline/total*100:5.1f}%)")
        print(f"   • Complete:  {complete_markets:6d} ({complete_markets/total*100:5.1f}%)")

        print(f"\n📊 Quote Completeness (line + price):")
        print(f"   Spread:")
        print(f"      • Away: {spread_away_complete:6d} ({spread_away_complete/total*100:5.1f}%)")
        print(f"      • Home: {spread_home_complete:6d} ({spread_home_complete/total*100:5.1f}%)")
        print(f"   Total:")
        print(f"      • Over:  {total_over_complete:6d} ({total_over_complete/total*100:5.1f}%)")
        print(f"      • Under: {total_under_complete:6d} ({total_under_complete/total*100:5.1f}%)")
        print(f"   Moneyline (price only):")
        print(f"      • Away: {ml_away_complete:6d} ({ml_away_complete/total*100:5.1f}%)")
        print(f"      • Home: {ml_home_complete:6d} ({ml_home_complete/total*100:5.1f}%)")

        # Warnings
        if has_spread < total * 0.9:
            self.results["warnings"].append(
                f"Low spread coverage: {has_spread/total*100:.1f}%"
            )
        if has_total < total * 0.9:
            self.results["warnings"].append(
                f"Low total coverage: {has_total/total*100:.1f}%"
            )

        self.results["metrics"]["markets"] = {
            "spread": has_spread,
            "total": has_total,
            "moneyline": has_moneyline,
            "complete": complete_markets,
        }

    def _is_quote_complete(self, quote: Optional[Dict], require_line: bool = True) -> bool:
        """Check if a quote has required fields"""
        if not quote:
            return False

        has_price = quote.get("price") is not None
        has_line = quote.get("line") is not None

        if require_line:
            return has_price and has_line
        else:
            return has_price

    def _analyze_timestamps(self, records: List[Dict]):
        """Analyze timestamp data"""
        print("\n" + "=" * 80)
        print("TIMESTAMP ANALYSIS")
        print("=" * 80)

        # Parse collected_at timestamps
        timestamps = []
        for record in records:
            ts_str = record.get("collected_at")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    timestamps.append(ts)
                except Exception:
                    pass

        if timestamps:
            earliest = min(timestamps)
            latest = max(timestamps)
            print(f"\n🕐 Collection Timeline:")
            print(f"   • Earliest: {earliest.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   • Latest:   {latest.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   • Span:     {(latest - earliest).total_seconds() / 3600:.1f} hours")

        # Event dates
        event_dates = [r.get("event_date") for r in records if r.get("event_date")]
        if event_dates:
            unique_dates = len(set(event_dates))
            print(f"\n📅 Event Dates:")
            print(f"   • Unique dates: {unique_dates}")
            print(f"   • Date range: {min(event_dates)} to {max(event_dates)}")

    def _show_samples(self, records: List[Dict]):
        """Display sample records"""
        print("\n" + "=" * 80)
        print("SAMPLE RECORDS")
        print("=" * 80)

        # Show 3 diverse samples
        samples = []

        # Get one with complete markets
        for r in records:
            markets = r.get("markets", {})
            if (markets.get("spread", {}).get("away") and
                markets.get("total", {}).get("over") and
                markets.get("moneyline", {}).get("away")):
                samples.append(("Complete Markets", r))
                break

        # Get one live game if available
        for r in records:
            if r.get("is_live"):
                samples.append(("Live Game", r))
                break

        # Get one pre-game
        for r in records:
            if not r.get("is_live"):
                samples.append(("Pre-Game", r))
                break

        for label, sample in samples:
            print(f"\n{'─' * 80}")
            print(f"Sample: {label}")
            print(f"{'─' * 80}")
            print(json.dumps(sample, indent=2, default=str))

    def _print_summary(self):
        """Print final summary"""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        print(f"\n✅ Files Analyzed: {self.results['files_analyzed']}")
        print(f"✅ Total Records: {self.results['total_records']}")

        if self.results["errors"]:
            print(f"\n❌ Errors ({len(self.results['errors'])}):")
            for error in self.results["errors"][:10]:  # Show first 10
                print(f"   • {error}")
            if len(self.results["errors"]) > 10:
                print(f"   ... and {len(self.results['errors']) - 10} more")

        if self.results["warnings"]:
            print(f"\n⚠️  Warnings ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"][:10]:  # Show first 10
                print(f"   • {warning}")
            if len(self.results["warnings"]) > 10:
                print(f"   ... and {len(self.results['warnings']) - 10} more")

        # Overall score
        issues = len(self.results["errors"]) + len(self.results["warnings"])
        if issues == 0:
            print(f"\n🎉 EXCELLENT: No issues detected!")
        elif issues <= 5:
            print(f"\n✅ GOOD: Minor issues detected ({issues} total)")
        elif issues <= 20:
            print(f"\n⚠️  FAIR: Some issues detected ({issues} total)")
        else:
            print(f"\n❌ POOR: Many issues detected ({issues} total)")

        print("\n" + "=" * 80)


def main():
    """Main entry point"""
    data_dir = "./data/overtime_live"

    if len(sys.argv) > 1:
        data_dir = sys.argv[1]

    analyzer = ScraperDataAnalyzer(data_dir)
    analyzer.analyze_all()


if __name__ == "__main__":
    main()
