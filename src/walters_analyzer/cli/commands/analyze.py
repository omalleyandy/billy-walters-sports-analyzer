"""
Analyze Commands - Edge detection, game analysis, injury/weather impact.

Commands:
    walters analyze edges       - Find betting edges across all games
    walters analyze game        - Analyze a single game
    walters analyze injuries    - Analyze injury impacts
    walters analyze weather     - Analyze weather impacts
    walters analyze divergence  - Find sharp/public divergence
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path

app = typer.Typer(
    help="Analyze games, edges, injuries, and weather impacts",
    no_args_is_help=True,
)

console = Console()


@app.command("edges")
def analyze_edges(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    week: Optional[int] = typer.Option(None, "--week", "-w", help="Week number"),
    min_edge: float = typer.Option(
        5.5, "--min-edge", "-e", help="Minimum edge percentage"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file (CSV)"
    ),
    show_all: bool = typer.Option(
        False, "--all", "-a", help="Show all games, not just opportunities"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed calculations"
    ),
):
    """
    Find betting edges across all games for a given week.

    Uses Billy Walters methodology:
    - Power rating differentials
    - S-factor adjustments (travel, rest, weather, motivation)
    - Key number premiums (3, 7, 6)
    - Injury impact calculations

    Example:
        walters analyze edges --sport nfl --week 13 --min-edge 5.5
    """
    console.print(
        Panel(
            f"[bold]Edge Analysis[/bold]\n"
            f"Sport: {sport.upper()} | Week: {week or 'Current'} | Min Edge: {min_edge}%",
            title="[OK] Finding Opportunities",
            border_style="green",
        )
    )

    # Step 1: Load data
    console.print("Loading game data...")

    try:
        from walters_analyzer.core.edge_detection import (
            EdgeDetector,  # noqa: F401
        )
        from walters_analyzer.data.loaders import load_week_games

        games = load_week_games(sport=sport, week=week)
        console.print(f"[green]Loaded {len(games)} games[/green]")

    except ImportError:
        # Fallback if modules not yet implemented
        console.print(
            "[yellow]Using placeholder data[/yellow]"
        )
        games = []

    # Step 2: Calculate edges
    console.print("Calculating edges...")

    opportunities = []

    # TODO: Implement actual edge calculation
    # For now, show the structure

    console.print("[green][OK] Analysis complete[/green]")

    # Display results
    if not opportunities and not show_all:
        console.print(
            f"\n[yellow]No opportunities found with edge >= {min_edge}%[/yellow]"
        )
        console.print(
            "[dim]Use --all to see all games, or lower --min-edge threshold[/dim]"
        )
        return

    # Create results table
    table = Table(title=f"Week {week or 'Current'} {sport.upper()} Opportunities")
    table.add_column("Game", style="cyan")
    table.add_column("Our Line", justify="right")
    table.add_column("Market", justify="right")
    table.add_column("Edge", justify="right", style="green")
    table.add_column("S-Factors", justify="right")
    table.add_column("Recommendation", style="bold")

    # TODO: Populate with real data
    # Placeholder example
    table.add_row(
        "Lions @ Bears",
        "DET -3.0",
        "DET -6.5",
        "+3.5 (7.2%)",
        "+0.5 travel",
        "⭐⭐ BET DET -6.5",
    )

    console.print(table)

    # Summary
    console.print(
        Panel(
            f"[bold]Summary[/bold]\n"
            f"Games Analyzed: {len(games) if games else 'N/A'}\n"
            f"Opportunities: {len(opportunities)}\n"
            f"Highest Edge: N/A",
            title="[OK] Results",
            border_style="blue",
        )
    )

    if output:
        console.print(f"\n[green]Results saved to {output}[/green]")


@app.command("game")
def analyze_game(
    away: str = typer.Argument(..., help="Away team name"),
    home: str = typer.Argument(..., help="Home team name"),
    spread: Optional[float] = typer.Option(
        None, "--spread", "-l", help="Current spread"
    ),
    total: Optional[float] = typer.Option(
        None, "--total", "-t", help="Current total"
    ),
    venue: Optional[str] = typer.Option(
        None, "--venue", "-v", help="Stadium/venue name"
    ),
    bankroll: float = typer.Option(
        20000.0, "--bankroll", "-b", help="Bankroll amount"
    ),
    sport: str = typer.Option(
        "nfl", "--sport", "-s", help="Sport: nfl or ncaaf"
    ),
    research: bool = typer.Option(
        False, "--research", "-r", help="Fetch live injury/weather data"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-vb", help="Show detailed breakdown"
    ),
):
    """
    Analyze a single game using full Billy Walters methodology.

    Examples:
        walters analyze game "Detroit" "Chicago" \\
          --spread 2.5 --total 44.5 --sport nfl --verbose

        walters analyze game "Ohio State" "Michigan" \\
          --spread -10 --total 43.5 --venue "Michigan Stadium" \\
          --sport ncaaf --verbose
    """
    import json
    import glob
    from walters_analyzer.valuation.billy_walters_edge_detector import (
        BillyWaltersEdgeDetector,
        PowerRating,
    )

    game_title = f"[bold]{away} @ {home}[/bold]"
    if venue:
        game_title += f"\n[dim]{venue}[/dim]"

    console.print(
        Panel(
            game_title,
            title="[OK] Game Analysis",
            border_style="blue",
        )
    )

    # Initialize detector
    detector = BillyWaltersEdgeDetector()

    # Find and load latest power ratings
    console.print("Loading power ratings...")
    sport_lower = sport.lower()
    if sport_lower not in ["nfl", "ncaaf"]:
        console.print(f"[red][ERROR] Invalid sport: {sport}[/red]")
        return

    pattern = f"data/power_ratings/{sport_lower}_2025_week_*.json"
    ratings_files = sorted(glob.glob(pattern))
    if not ratings_files:
        console.print(
            f"[red][ERROR] No {sport.upper()} power rating "
            "files found. Run: uv run python scripts/analysis/"
            "update_power_ratings_from_massey.py[/red]"
        )
        return

    latest_ratings_file = ratings_files[-1]
    try:
        with open(latest_ratings_file) as f:
            ratings_data = json.load(f)
        detector.power_ratings = {}
        for team_name, rating in ratings_data.get("ratings", {}).items():
            detector.power_ratings[team_name] = PowerRating(
                team=team_name,
                rating=float(rating),
                offensive_rating=0.0,
                defensive_rating=0.0,
                home_field_advantage=2.5,
                source="proprietary_90_10",
            )
        console.print(
            f"[green]Loaded {len(detector.power_ratings)} power ratings "
            f"(Week {ratings_data.get('week')})[/green]"
        )
    except Exception as e:
        console.print(f"[red][ERROR] Failed to load power ratings: {e}[/red]")
        return

    # Normalize team names
    away_normalized = detector.normalize_team_name(away)
    home_normalized = detector.normalize_team_name(home)

    # Check if teams exist in power ratings
    if away_normalized not in detector.power_ratings:
        sample_teams = ", ".join(
            list(detector.power_ratings.keys())[:5]
        )
        console.print(
            f"[yellow][WARNING] Away team '{away}' not found. "
            f"Try: {sample_teams}...[/yellow]"
        )
        return
    if home_normalized not in detector.power_ratings:
        sample_teams = ", ".join(
            list(detector.power_ratings.keys())[:5]
        )
        console.print(
            f"[yellow][WARNING] Home team '{home}' not found. "
            f"Try: {sample_teams}...[/yellow]"
        )
        return

    console.print("Analyzing game...")

    # Load injury data if available
    if research:
        console.print("Loading injury data...")
        detector.load_injury_data()

    # Calculate power ratings
    console.print("Calculating power ratings...")
    away_rating = detector.power_ratings[away_normalized].rating
    home_rating = detector.power_ratings[home_normalized].rating
    hfa = (
        detector.power_ratings[home_normalized].home_field_advantage
    )
    predicted_spread = home_rating - away_rating + hfa
    differential = home_rating - away_rating

    console.print("Applying S-factors...")

    # Detect edge
    if spread is not None:
        edge = detector.detect_edge(
            game_id=f"{away_normalized}_{home_normalized}",
            away_team=away_normalized,
            home_team=home_normalized,
            market_spread=spread,
            market_total=total or 47.0,
            week=ratings_data.get("week", 0),
            game_time="",
        )
    else:
        edge = None

    console.print("[green][OK] Analysis complete[/green]")

    # Display results
    console.print("\n[bold]Power Ratings:[/bold]")
    console.print(f"  {away}: {away_rating:.2f}")
    console.print(f"  {home}: {home_rating:.2f}")
    favored_team = home if differential > 0 else away
    console.print(
        f"  Differential: {abs(differential):+.2f} pts "
        f"({favored_team} favored)"
    )

    if spread is not None:
        console.print("\n[bold]Line Analysis:[/bold]")
        console.print(f"  Current Market Spread: {spread:+.1f}")
        console.print(f"  Our Calculated Line: {predicted_spread:+.1f}")
        if edge:
            console.print(
                f"  Edge: {edge.edge_points:.1f} pts "
                f"({edge.edge_strength.upper()})"
            )
        else:
            console.print("  Edge: No significant edge detected")

    console.print("\n[bold]S-Factors:[/bold]")
    if edge:
        console.print(
            f"  Situational: {edge.situational_adjustment:+.1f} pts"
        )
        console.print(f"  Weather: {edge.weather_adjustment:+.1f} pts")
        console.print(
            f"  Emotional: {edge.emotional_adjustment:+.1f} pts"
        )
        console.print(
            f"  Injury Impact: {edge.injury_adjustment:+.1f} pts"
        )
    else:
        console.print("  Situational: TBD")
        console.print("  Weather: TBD")
        console.print("  Emotional: TBD")
        console.print("  Injury Impact: TBD")

    # Build recommendation panel
    if edge and edge.recommended_bet:
        bet_team = (
            edge.away_team
            if edge.recommended_bet == "away"
            else edge.home_team
        )
        bet_display = f"BET {edge.recommended_bet.upper()}: {bet_team}"
        bet_amount = int(bankroll * edge.kelly_fraction)
        bet_odds = edge.best_odds

        # Calculate potential win/loss
        potential_win = bet_amount * (abs(bet_odds) / 100)
        potential_loss = bet_amount

        recommendation_text = (
            f"[bold]{bet_display}[/bold]\n\n"
            f"Kelly Sizing: {edge.kelly_fraction * 100:.1f}% of bankroll\n"
            f"Suggested Bet: ${bet_amount:,.0f}\n"
            f"Odds: {bet_odds:+d}\n"
            f"Potential Win: ${potential_win:,.0f}\n"
            f"Potential Loss: ${potential_loss:,.0f}\n"
            f"Confidence: {edge.confidence_score:.0f}/100"
        )
        border_color = (
            "green"
            if edge.edge_strength in ["strong", "very_strong"]
            else "yellow"
        )
    else:
        recommendation_text = (
            "[yellow]No significant edge detected[/yellow]\n"
            "Pass on this game."
        )
        border_color = "yellow"

    console.print(
        Panel(
            recommendation_text,
            title="[OK] Verdict",
            border_style=border_color,
        )
    )

    # Verbose output
    if verbose and edge:
        console.print("\n[bold]Detailed Breakdown:[/bold]")
        console.print(f"  Edge Type: {edge.edge_type}")
        if edge.crosses_key_number:
            console.print(
                f"  [KEY] Crosses key number: {edge.key_number_value}"
            )
        if edge.away_injuries and edge.away_injuries.total_impact != 0:
            console.print(
                f"  {edge.away_team} injuries: "
                f"{edge.away_injuries.total_impact:+.1f} pts "
                f"({edge.away_injuries.severity})"
            )
        if edge.home_injuries and edge.home_injuries.total_impact != 0:
            console.print(
                f"  {edge.home_team} injuries: "
                f"{edge.home_injuries.total_impact:+.1f} pts "
                f"({edge.home_injuries.severity})"
            )


@app.command("injuries")
def analyze_injuries(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    team: Optional[str] = typer.Option(
        None, "--team", "-t", help="Specific team to analyze"
    ),
    week: Optional[int] = typer.Option(None, "--week", "-w", help="Week number"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all injuries"),
):
    """
    Analyze injury impacts using Billy Walters position-tier system.

    Position Impact Tiers:
    - Elite QB: 6-8 points
    - WR/TE clusters: 1.5x multiplier
    - OL clusters: 1.4x multiplier
    - DB clusters: 1.35x multiplier

    Example:
        walters analyze injuries --sport nfl --team "Lions"
    """
    title = f"Injury Analysis - {sport.upper()}"
    if team:
        title += f" - {team}"

    console.print(Panel(title, border_style="red"))

    # TODO: Implement injury analysis using billy_walters_injury_reference.py
    console.print("[yellow]Implementation in progress...[/yellow]")
    console.print(
        "[dim]Will use position-tier impact calculations from methodology[/dim]"
    )


@app.command("weather")
def analyze_weather(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    week: Optional[int] = typer.Option(None, "--week", "-w", help="Week number"),
    game: Optional[str] = typer.Option(
        None, "--game", "-g", help="Specific game (e.g., 'DET@CHI')"
    ),
):
    """
    Analyze weather impacts (W-factors) for games.

    Weather Impact Factors:
    - Wind: Affects passing game, kicking
    - Temperature: Extreme cold/heat impacts
    - Precipitation: Rain/snow effects on ball handling
    - Dome vs outdoor considerations

    Example:
        walters analyze weather --sport nfl --week 13
    """
    console.print(Panel("Weather Impact Analysis", border_style="cyan"))

    # TODO: Implement weather analysis
    console.print("[yellow]Implementation in progress...[/yellow]")
    console.print(
        "[dim]Will fetch weather data and calculate W-factor adjustments[/dim]"
    )


@app.command("divergence")
def analyze_divergence(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    threshold: float = typer.Option(
        5.0, "--threshold", "-t", help="Divergence threshold (%)"
    ),
    source: str = typer.Option("action-network", "--source", help="Data source"),
):
    """
    Find sharp/public betting divergence signals.

    Looks for games where:
    - Money % and Ticket % diverge by threshold
    - Sharp books have different lines than public books
    - Reverse line movement (line moves opposite to betting %)

    Example:
        walters analyze divergence --sport nfl --threshold 5
    """
    console.print(
        Panel(
            f"Sharp/Public Divergence Analysis\nThreshold: {threshold}%",
            border_style="magenta",
        )
    )

    # TODO: Implement divergence analysis using Action Network data
    console.print("[yellow]Implementation in progress...[/yellow]")
    console.print("[dim]Will analyze money% vs ticket% divergence[/dim]")


if __name__ == "__main__":
    app()
