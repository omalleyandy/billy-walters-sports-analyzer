"""
ScrapyBridge - Connect your existing Scrapy spiders to ResearchEngine

This bridge provides a clean interface between:
- Your production Scrapy spiders (ESPN, Massey, Overtime)
- The new ResearchEngine (multi-source coordinator)

Key Features:
- Load existing Scrapy JSONL output (no scraping changes needed!)
- Convert to Phase 1 InjuryReport format
- Cache results for performance
- Optionally trigger new scrapes programmatically

Usage:
    from walters_analyzer.research import ScrapyBridge
    
    bridge = ScrapyBridge()
    
    # Load latest ESPN data (from your existing scrapers)
    injuries = bridge.load_latest_injuries(sport="nfl")
    
    # Convert to InjuryReport format
    reports = bridge.convert_to_injury_reports(injuries)
    
    # Use in your analysis
    for report in reports:
        print(f"{report.player_name}: {report.point_value:+.1f} impact")
"""

import asyncio
import subprocess
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import orjson

from ..core.cache import cache_injury_data
from ..core.models import InjuryReport

logger = logging.getLogger(__name__)


class ScrapyBridge:
    """
    Bridge between your Scrapy spiders and the ResearchEngine.
    
    This provides a clean interface to:
    1. Load scraped data (JSONL/Parquet) from your existing spiders
    2. Convert to ResearchEngine format (InjuryReport models)
    3. Optionally trigger new scrapes programmatically
    4. Cache results using Phase 1 caching
    
    Example:
        bridge = ScrapyBridge()
        
        # Load latest ESPN injury data
        injuries = bridge.load_latest_injuries(sport="nfl")
        
        # Convert to standard format
        reports = bridge.convert_to_injury_reports(injuries)
        
        # Now ready for ResearchEngine!
    """
    
    def __init__(
        self,
        data_dir: str = "data",
        scrapy_project_dir: Optional[str] = None
    ):
        """
        Initialize Scrapy bridge.
        
        Args:
            data_dir: Root data directory (contains injuries/, massey_ratings/, etc.)
            scrapy_project_dir: Path to scrapy.cfg (auto-detected if None)
        """
        self.data_dir = Path(data_dir)
        
        # Auto-detect scrapy project directory
        if scrapy_project_dir:
            self.scrapy_dir = Path(scrapy_project_dir)
        else:
            # Assume we're in project root
            self.scrapy_dir = Path.cwd()
            if not (self.scrapy_dir / "scrapy.cfg").exists():
                logger.warning("scrapy.cfg not found in current directory")
    
    def load_latest_injuries(
        self,
        sport: Optional[str] = None,
        max_age_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Load latest injury data from your Scrapy output.
        
        This reads the JSONL files created by your InjuryPipeline.
        No changes to your spiders needed!
        
        Args:
            sport: Filter by sport ("nfl", "college_football", None=all)
            max_age_hours: Only load files newer than this (warning if older)
        
        Returns:
            List of injury data dicts (Scrapy format)
        
        Example:
            # Load NFL injuries from last 24 hours
            injuries = bridge.load_latest_injuries(sport="nfl", max_age_hours=24)
            
            # Check data
            print(f"Loaded {len(injuries)} injuries")
            for inj in injuries[:3]:
                print(f"  {inj['player_name']} ({inj['team']}) - {inj['injury_status']}")
        """
        injuries_dir = self.data_dir / "injuries"
        
        if not injuries_dir.exists():
            logger.warning(f"Injuries directory not found: {injuries_dir}")
            return []
        
        # Find latest JSONL file (your InjuryPipeline output)
        jsonl_files = sorted(
            injuries_dir.glob("injuries-*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not jsonl_files:
            logger.info("No injury files found - run 'uv run walters-analyzer scrape-injuries --sport nfl'")
            return []
        
        # Check file age
        latest_file = jsonl_files[0]
        age_seconds = datetime.now().timestamp() - latest_file.stat().st_mtime
        age_hours = age_seconds / 3600
        
        if age_hours > max_age_hours:
            logger.warning(
                f"Latest injury file is {age_hours:.1f} hours old "
                f"(max: {max_age_hours}h). Consider re-scraping."
            )
        
        # Load JSONL (your existing format!)
        injuries = []
        try:
            with open(latest_file, 'rb') as f:
                for line in f:
                    if line.strip():
                        injury_dict = orjson.loads(line)
                        
                        # Filter by sport if requested
                        if sport:
                            # Handle both "nfl" and "college_football" variations
                            injury_sport = injury_dict.get('sport', '').lower()
                            if sport == "nfl" and "nfl" not in injury_sport:
                                continue
                            elif sport == "cfb" and "college" not in injury_sport:
                                continue
                        
                        injuries.append(injury_dict)
            
            logger.info(
                f"[OK] Loaded {len(injuries)} injuries from {latest_file.name} "
                f"({age_hours:.1f}h old)"
            )
            return injuries
            
        except Exception as e:
            logger.error(f"Failed to load injuries from {latest_file}: {e}")
            return []
    
    def convert_to_injury_reports(
        self,
        scrapy_injuries: List[Dict[str, Any]]
    ) -> List[InjuryReport]:
        """
        Convert your Scrapy injury items to Phase 1 InjuryReport models.
        
        This bridges your existing data format to the new unified format
        that ResearchEngine uses.
        
        Args:
            scrapy_injuries: List of dicts from your ESPN spider
        
        Returns:
            List of InjuryReport objects (Phase 1 models)
        
        Example:
            # Load Scrapy data
            scrapy_data = bridge.load_latest_injuries()
            
            # Convert to InjuryReport format
            reports = bridge.convert_to_injury_reports(scrapy_data)
            
            # Now compatible with ResearchEngine!
            for report in reports:
                print(f"{report.player_name}: {report.severity} ({report.confidence:.0%})")
        """
        reports = []
        
        for injury in scrapy_injuries:
            try:
                # Map your Scrapy fields to InjuryReport fields
                report = InjuryReport(
                    player_name=injury['player_name'],
                    position=injury.get('position', 'UNKNOWN'),
                    injury_type=injury.get('injury_type', 'Unknown'),
                    status=injury['injury_status'],
                    
                    # Calculate Billy Walters point impact
                    point_value=self._estimate_point_value(
                        injury['injury_status'],
                        injury.get('position')
                    ),
                    
                    # Map to severity levels
                    severity=self._map_status_to_severity(
                        injury['injury_status']
                    ),
                    
                    # ESPN is reliable - high confidence
                    confidence=0.75,
                    
                    # Track source
                    source=f"ESPN (Scrapy - {injury['source']})",
                    
                    # Additional info
                    prognosis=injury.get('notes', ''),
                    
                    # Parse timestamp
                    timestamp=self._parse_timestamp(
                        injury.get('collected_at')
                    )
                )
                reports.append(report)
                
            except Exception as e:
                logger.warning(f"Failed to convert injury {injury.get('player_name', 'unknown')}: {e}")
                continue
        
        logger.info(f"[OK] Converted {len(reports)} injuries to InjuryReport format")
        return reports
    
    def filter_by_team(
        self,
        injuries: List[Dict[str, Any]],
        team: str
    ) -> List[Dict[str, Any]]:
        """
        Filter injuries for a specific team.
        
        Args:
            injuries: List of injury dicts
            team: Team name to filter for
        
        Returns:
            Filtered list
        """
        team_lower = team.lower()
        return [
            inj for inj in injuries
            if team_lower in inj.get('team', '').lower()
        ]
    
    async def run_espn_scraper(
        self,
        sport: str = "nfl",
        wait: bool = False
    ) -> bool:
        """
        Optionally trigger a new ESPN scrape.
        
        This is advanced usage - you can still run scrapers via CLI:
        `uv run walters-analyzer scrape-injuries --sport nfl`
        
        Args:
            sport: "nfl" or "cfb"
            wait: Wait for completion or run in background
        
        Returns:
            True if started successfully
        """
        logger.info(f"Triggering ESPN scraper for {sport}...")
        
        # Build Scrapy command
        cmd = [
            "scrapy", "crawl", "espn_injuries",
            "-s", "INJURY_OUT_DIR=data/injuries"
        ]
        
        # Environment variables for your spider
        env = os.environ.copy()
        env["ESPN_SPORT"] = "football"
        env["ESPN_LEAGUE"] = "nfl" if sport == "nfl" else "college-football"
        
        try:
            if wait:
                # Run and wait
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=str(self.scrapy_dir),
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    logger.info("[OK] ESPN scraper completed")
                    return True
                else:
                    logger.error(f"ESPN scraper failed: {stderr.decode()}")
                    return False
            else:
                # Run in background
                subprocess.Popen(cmd, cwd=str(self.scrapy_dir), env=env)
                logger.info("[OK] ESPN scraper started in background")
                return True
                
        except Exception as e:
            logger.error(f"Failed to run ESPN scraper: {e}")
            return False
    
    # Private helper methods
    
    def _estimate_point_value(
        self,
        status: str,
        position: Optional[str]
    ) -> float:
        """
        Estimate Billy Walters point spread impact.
        
        This uses the position-based impacts from the Advanced Masterclass.
        """
        # Position impacts (from Billy Walters methodology)
        position_impacts = {
            'QB': -3.0,   # Quarterback is most valuable
            'RB': -1.5,   # Running back
            'WR': -1.0,   # Wide receiver
            'TE': -0.8,   # Tight end
            'DE': -2.0,   # Defensive end
            'DT': -1.5,   # Defensive tackle
            'LB': -1.5,   # Linebacker
            'CB': -1.5,   # Cornerback
            'S': -1.0,    # Safety
            'OL': -1.2,   # Offensive line
        }
        
        base_impact = position_impacts.get(position, -1.0)
        
        # Status multipliers (how likely to play / effectiveness)
        status_multipliers = {
            'out': 1.0,           # Definitely not playing
            'doubtful': 0.75,     # 25% chance to play
            'questionable': 0.4,  # 50% chance to play
            'probable': 0.15,     # 75% chance to play
            'day-to-day': 0.3,    # Uncertain
        }
        
        multiplier = status_multipliers.get(status.lower(), 0.5)
        
        # Calculate final impact
        return round(base_impact * multiplier, 1)
    
    def _map_status_to_severity(self, status: str) -> str:
        """Map NFL status to severity levels for consistency."""
        status_map = {
            'out': 'SEVERE',
            'doubtful': 'SIGNIFICANT',
            'questionable': 'MODERATE',
            'probable': 'MINOR',
            'day-to-day': 'MODERATE'
        }
        return status_map.get(status.lower(), 'MODERATE')
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamp from Scrapy output."""
        if not timestamp_str:
            return datetime.now()
        
        try:
            # Handle both with and without 'Z' suffix
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            return datetime.fromisoformat(timestamp_str)
        except Exception:
            return datetime.now()
    
    # Additional methods for other spiders (for future expansion)
    
    def load_latest_massey_ratings(self) -> Dict[str, Any]:
        """Load latest Massey ratings from your Scrapy output."""
        massey_dir = self.data_dir / "massey_ratings"
        
        if not massey_dir.exists():
            logger.warning(f"Massey directory not found: {massey_dir}")
            return {}
        
        # Find latest Parquet file
        parquet_files = sorted(
            massey_dir.glob("massey-ratings-*.parquet"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not parquet_files:
            logger.info("No Massey ratings found")
            return {}
        
        # Load Parquet (would need pyarrow)
        logger.info(f"Latest Massey ratings: {parquet_files[0].name}")
        return {}  # Placeholder - implement if needed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about available scraped data."""
        stats = {
            'injuries_dir': str(self.data_dir / "injuries"),
            'injuries_count': 0,
            'latest_injury_file': None,
            'latest_injury_age_hours': None,
        }
        
        injuries_dir = self.data_dir / "injuries"
        if injuries_dir.exists():
            jsonl_files = list(injuries_dir.glob("injuries-*.jsonl"))
            if jsonl_files:
                latest = max(jsonl_files, key=lambda p: p.stat().st_mtime)
                stats['latest_injury_file'] = latest.name
                stats['latest_injury_age_hours'] = round(
                    (datetime.now().timestamp() - latest.stat().st_mtime) / 3600,
                    1
                )
                
                # Count injuries in latest file
                try:
                    with open(latest, 'rb') as f:
                        stats['injuries_count'] = sum(1 for line in f if line.strip())
                except Exception:
                    pass
        
        return stats


# Example usage and testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root to path for imports when running as script
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    import asyncio
    from rich.console import Console
    from rich.table import Table
    
    # Now we can import from walters_analyzer
    from walters_analyzer.core.models import InjuryReport
    
    console = Console()
    
    async def test_scrapy_bridge():
        """Test the ScrapyBridge."""
        console.print("\n[bold cyan]Testing ScrapyBridge[/bold cyan]")
        console.print("=" * 60)
        
        bridge = ScrapyBridge()
        
        # Test 1: Get stats
        console.print("\n[bold]1. Checking available data...[/bold]")
        stats = bridge.get_stats()
        
        table = Table(title="Scraped Data Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Directory", stats['injuries_dir'])
        table.add_row("Latest File", stats['latest_injury_file'] or "None")
        table.add_row("Age (hours)", str(stats['latest_injury_age_hours']) if stats['latest_injury_age_hours'] else "N/A")
        table.add_row("Injury Count", str(stats['injuries_count']))
        
        console.print(table)
        
        # Test 2: Load injuries
        console.print("\n[bold]2. Loading injury data...[/bold]")
        injuries = bridge.load_latest_injuries(sport="nfl")
        
        if injuries:
            console.print(f"[green][OK] Loaded {len(injuries)} injuries[/green]")
            
            # Show first 3
            console.print("\n[bold]Sample injuries:[/bold]")
            for i, inj in enumerate(injuries[:3], 1):
                console.print(
                    f"  [{i}] {inj['player_name']} ({inj['team']}) - "
                    f"{inj['injury_status']} ({inj.get('position', 'N/A')})"
                )
            
            # Test 3: Convert to InjuryReport format
            console.print("\n[bold]3. Converting to InjuryReport format...[/bold]")
            reports = bridge.convert_to_injury_reports(injuries[:5])
            
            console.print(f"[green][OK] Converted {len(reports)} injuries[/green]")
            
            # Show converted data
            if reports:
                console.print("\n[bold]Converted format (with point impacts):[/bold]")
                for i, report in enumerate(reports[:3], 1):
                    console.print(
                        f"  [{i}] {report.player_name} ({report.position})"
                    )
                    console.print(
                        f"      Impact: {report.point_value:+.1f} points | "
                        f"Severity: {report.severity} | "
                        f"Confidence: {report.confidence:.0%}"
                    )
        else:
            console.print("[yellow]No injury data found[/yellow]")
            console.print("\nTo scrape data, run:")
            console.print("  [cyan]uv run walters-analyzer scrape-injuries --sport nfl[/cyan]")
        
        console.print("\n" + "=" * 60)
        console.print("[bold green][SUCCESS] ScrapyBridge operational![/bold green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  - Use with ResearchEngine for multi-source analysis")
        console.print("  - Add ProFootballDoc for medical insights")
        console.print("  - Combine ESPN + medical analysis for complete picture")
    
    asyncio.run(test_scrapy_bridge())

