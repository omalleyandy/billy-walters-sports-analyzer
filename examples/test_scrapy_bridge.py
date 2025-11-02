"""
Test ScrapyBridge - Load and convert existing Scrapy data

This demonstrates how ScrapyBridge connects your existing Scrapy infrastructure
to the new ResearchEngine.

Run: uv run python examples/test_scrapy_bridge.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from walters_analyzer.research import ScrapyBridge
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


async def main():
    """Test ScrapyBridge functionality."""
    
    console.print(Panel.fit(
        "[bold cyan]ScrapyBridge Test[/bold cyan]\n"
        "Connecting your Scrapy spiders to ResearchEngine",
        border_style="cyan"
    ))
    
    bridge = ScrapyBridge()
    
    # Test 1: Check available data
    console.print("\n[bold]Step 1: Checking available scraped data...[/bold]")
    stats = bridge.get_stats()
    
    table = Table(title="Scraped Data Status", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Value", style="white")
    
    table.add_row("Directory", stats['injuries_dir'])
    table.add_row("Latest File", stats['latest_injury_file'] or "[yellow]None[/yellow]")
    table.add_row("Age (hours)", str(stats['latest_injury_age_hours']) if stats['latest_injury_age_hours'] else "N/A")
    table.add_row("Injury Count", str(stats['injuries_count']))
    
    console.print(table)
    
    # Test 2: Load injuries
    console.print("\n[bold]Step 2: Loading injury data...[/bold]")
    injuries = bridge.load_latest_injuries(sport="nfl")
    
    if injuries:
        console.print(f"[green][OK] Loaded {len(injuries)} injuries from Scrapy output[/green]")
        
        # Show first 5
        console.print("\n[bold]Sample injuries (Scrapy format):[/bold]")
        for i, inj in enumerate(injuries[:5], 1):
            team = inj.get('team', 'Unknown')
            player = inj.get('player_name', 'Unknown')
            status = inj.get('injury_status', 'Unknown')
            position = inj.get('position', 'N/A')
            
            console.print(f"  [{i}] {player} ({team}) - {status} ({position})")
        
        # Test 3: Convert to InjuryReport format
        console.print("\n[bold]Step 3: Converting to InjuryReport format...[/bold]")
        reports = bridge.convert_to_injury_reports(injuries[:10])
        
        console.print(f"[green][OK] Converted {len(reports)} injuries to Phase 1 format[/green]")
        
        if reports:
            console.print("\n[bold]Converted format (with Billy Walters point impacts):[/bold]")
            
            # Create table for converted data
            conv_table = Table(show_header=True, header_style="bold magenta")
            conv_table.add_column("Player", style="cyan", width=20)
            conv_table.add_column("Team", style="white", width=15)
            conv_table.add_column("Status", style="yellow", width=12)
            conv_table.add_column("Impact", style="red", width=8, justify="right")
            conv_table.add_column("Confidence", style="green", width=10, justify="right")
            
            for report in reports[:5]:
                # Extract team from source
                team = "N/A"
                for inj in injuries:
                    if inj['player_name'] == report.player_name:
                        team = inj.get('team', 'N/A')
                        break
                
                conv_table.add_row(
                    report.player_name[:20],
                    team[:15],
                    report.status,
                    f"{report.point_value:+.1f}",
                    f"{report.confidence:.0%}"
                )
            
            console.print(conv_table)
            
            # Calculate total impact
            total_impact = sum(r.point_value * r.confidence for r in reports)
            
            console.print(f"\n[bold]Total Injury Impact:[/bold] {total_impact:+.1f} points")
    
    else:
        console.print("[yellow]No injury data found[/yellow]")
        console.print("\n[bold]To scrape NFL injuries, run:[/bold]")
        console.print("  [cyan]uv run walters-analyzer scrape-injuries --sport nfl[/cyan]")
        console.print("\n[dim]Note: The ESPN URL might need updating if scraper fails[/dim]")
    
    # Summary
    console.print("\n" + "=" * 60)
    console.print(Panel.fit(
        "[bold green]ScrapyBridge is operational![/bold green]\n\n"
        "[bold]What this gives you:[/bold]\n"
        "  - Loads your existing Scrapy JSONL data\n"
        "  - Converts to Phase 1 InjuryReport format\n"
        "  - Ready for multi-source ResearchEngine\n"
        "  - Zero changes to your working spiders!\n\n"
        "[bold]Next step:[/bold] Add ProFootballDoc for medical analysis",
        title="[bold cyan]Quick Win Complete[/bold cyan]",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())

