#!/usr/bin/env python3
"""
Demo script showing how to use the weather analyzer programmatically.

This demonstrates the Billy Walters weather methodology in action.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from walters_analyzer.weather_fetcher import fetch_game_weather
from rich.console import Console
from rich.table import Table


def demo_single_game():
    """Fetch weather for a single game."""
    console = Console()
    console.print("\n[bold cyan]Demo: Single Game Weather Analysis[/bold cyan]\n")
    
    # Example: Lambeau Field (outdoor, cold weather venue)
    weather = fetch_game_weather(
        stadium="Lambeau Field",
        location="Green Bay, WI",
        is_dome=False,
        sport="nfl"
    )
    
    if weather:
        console.print(f"[green]✓[/green] Fetched weather for {weather['stadium']}")
        console.print(f"  Location: {weather['location']}")
        console.print(f"  Temperature: {weather['temperature_f']}°F (Feels like {weather['feels_like_f']}°F)")
        console.print(f"  Wind: {weather['wind_speed_mph']} mph")
        console.print(f"  Precipitation: {weather['precipitation_prob']}% ({weather['precipitation_type']})")
        
        impact = weather['weather_impact_score']
        impact_color = "green" if impact < 20 else "yellow" if impact < 50 else "red"
        console.print(f"  [{impact_color}]Impact Score: {impact}/100[/{impact_color}]")
        console.print(f"  Betting Adjustment: {weather['betting_adjustment']}\n")
    else:
        console.print("[red]Failed to fetch weather data[/red]")


def demo_multiple_games():
    """Fetch weather for multiple games (card simulation)."""
    console = Console()
    console.print("\n[bold cyan]Demo: Multiple Games Weather Analysis[/bold cyan]\n")
    
    games = [
        {"stadium": "Soldier Field", "location": "Chicago, IL", "dome": False},
        {"stadium": "US Bank Stadium", "location": "Minneapolis, MN", "dome": True},
        {"stadium": "Lambeau Field", "location": "Green Bay, WI", "dome": False},
    ]
    
    results = []
    
    for game in games:
        console.print(f"[yellow]→[/yellow] Fetching {game['stadium']}...")
        weather = fetch_game_weather(
            stadium=game['stadium'],
            location=game['location'],
            is_dome=game['dome'],
            sport="nfl"
        )
        if weather:
            results.append(weather)
    
    if results:
        # Display summary table
        table = Table(title="Weather Summary")
        table.add_column("Stadium", style="cyan")
        table.add_column("Temp (°F)", justify="right")
        table.add_column("Wind (mph)", justify="right")
        table.add_column("Precip %", justify="right")
        table.add_column("Impact", justify="right")
        table.add_column("Adjustment", style="yellow")
        
        for weather in results:
            impact = weather['weather_impact_score']
            impact_str = f"{impact}"
            if impact > 50:
                impact_str = f"[red]{impact}[/red]"
            elif impact > 20:
                impact_str = f"[yellow]{impact}[/yellow]"
            else:
                impact_str = f"[green]{impact}[/green]"
            
            table.add_row(
                weather['stadium'],
                f"{weather['temperature_f']:.0f}",
                f"{weather['wind_speed_mph']:.0f}",
                f"{weather['precipitation_prob']}",
                impact_str,
                weather['betting_adjustment'][:30] + "..." if len(weather['betting_adjustment']) > 30 else weather['betting_adjustment']
            )
        
        console.print(table)


def demo_billy_walters_analysis():
    """Demonstrate Billy Walters thresholds."""
    console = Console()
    console.print("\n[bold cyan]Billy Walters Weather Thresholds[/bold cyan]\n")
    
    table = Table(title="Impact Thresholds")
    table.add_column("Factor", style="cyan")
    table.add_column("Threshold", style="white")
    table.add_column("Impact", justify="right")
    table.add_column("Betting Strategy", style="yellow")
    
    table.add_row("Wind", "> 25 mph", "[red]40 pts[/red]", "Heavy Under, fade all passing")
    table.add_row("Wind", "20-25 mph", "[yellow]30 pts[/yellow]", "Favor Under, reduce passing props")
    table.add_row("Wind", "15-20 mph", "[yellow]20 pts[/yellow]", "Monitor totals, reduce FG confidence")
    table.add_row("Snow", "> 50% chance", "[red]35 pts[/red]", "Heavy Under, favor rush teams")
    table.add_row("Rain", "> 50% chance", "[yellow]25 pts[/yellow]", "Favor Under, monitor turnovers")
    table.add_row("Temperature", "< 20°F", "[red]20 pts[/red]", "Ball handling issues, low scoring")
    table.add_row("Temperature", "20-32°F", "[yellow]15 pts[/yellow]", "Monitor fumbles, passing accuracy")
    table.add_row("Dome", "Indoor", "[green]0 pts[/green]", "No adjustment needed")
    
    console.print(table)
    
    console.print("\n[bold]Key Insight:[/bold] Weather >15mph wind is an [red]automatic Under consideration[/red] in Walters' system.")
    console.print("[dim]The public is consistently slow to adjust totals for wind impact.[/dim]\n")


if __name__ == "__main__":
    console = Console()
    
    console.print("[bold green]Weather Analyzer Demo - Billy Walters Methodology[/bold green]")
    console.print("[dim]This demonstrates the weather analysis system for betting decisions[/dim]\n")
    
    try:
        # Run demos
        demo_billy_walters_analysis()
        demo_single_game()
        demo_multiple_games()
        
        console.print("\n[green]✓ Demo complete![/green]")
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("  1. Add ACCUWEATHER_API_KEY to .env")
        console.print("  2. Run: uv run walters-analyzer scrape-weather --card ./cards/wk-card-2025-10-31.json")
        console.print("  3. Review output in data/weather/")
        console.print("  4. Integrate with your betting workflow\n")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Make sure ACCUWEATHER_API_KEY is set in .env[/yellow]")

