"""
CLV (Closing Line Value) Commands - Track and analyze bet performance.

Commands:
    walters clv record   - Record a new bet with opening line
    walters clv update   - Update closing lines for pending bets
    walters clv report   - Generate CLV performance report
    walters clv list     - List all tracked bets
    walters clv analyze  - Analyze CLV trends
"""

import typer
from typing import Optional
from datetime import datetime, date
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from enum import Enum

app = typer.Typer(
    help="Closing Line Value tracking and analysis",
    no_args_is_help=True,
)

console = Console()


class BetType(str, Enum):
    SPREAD = "spread"
    TOTAL = "total"
    MONEYLINE = "moneyline"


class BetResult(str, Enum):
    PENDING = "pending"
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"


@app.command("record")
def clv_record(
    game: str = typer.Argument(..., help="Game description (e.g., 'DET @ CHI')"),
    pick: str = typer.Argument(..., help="Your pick (e.g., 'DET -3.5' or 'OVER 45.5')"),
    opening_line: float = typer.Option(..., "--line", "-l", help="Opening line when bet was placed"),
    stake: float = typer.Option(100.0, "--stake", "-s", help="Stake amount"),
    odds: int = typer.Option(-110, "--odds", "-o", help="Odds (American format)"),
    edge: Optional[float] = typer.Option(None, "--edge", "-e", help="Calculated edge %"),
    bet_type: BetType = typer.Option(BetType.SPREAD, "--type", "-t", help="Bet type"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Additional notes"),
    sport: str = typer.Option("nfl", "--sport", help="Sport: nfl or ncaaf"),
    week: Optional[int] = typer.Option(None, "--week", "-w", help="Week number"),
):
    """
    Record a new bet with opening line for CLV tracking.
    
    The opening line is critical for CLV calculation - it should be
    the line at the time you placed the bet.
    
    Example:
        walters clv record "DET @ CHI" "DET -3.5" -3.5 --stake 200 --edge 6.5
        walters clv record "KC @ LV" "OVER 47.5" 47.5 --type total --stake 150
    """
    timestamp = datetime.now()
    
    console.print(Panel(
        f"[bold]Recording New Bet[/bold]\n\n"
        f"Game: {game}\n"
        f"Pick: {pick}\n"
        f"Opening Line: {opening_line}\n"
        f"Stake: ${stake:.2f}\n"
        f"Odds: {odds:+d}\n"
        f"Edge: {edge:.1f}%" if edge else "Edge: Not specified",
        title="📝 CLV Tracker",
        border_style="green",
    ))
    
    # Build bet record
    bet_record = {
        "id": timestamp.strftime("%Y%m%d%H%M%S"),
        "timestamp": timestamp.isoformat(),
        "sport": sport,
        "week": week,
        "game": game,
        "pick": pick,
        "bet_type": bet_type.value,
        "opening_line": opening_line,
        "closing_line": None,  # To be updated later
        "stake": stake,
        "odds": odds,
        "edge": edge,
        "result": BetResult.PENDING.value,
        "clv": None,  # Calculated when closing line is recorded
        "notes": notes,
    }
    
    # Save to storage - use simple JSON for CLI compatibility
    import json
    storage_path = Path("data/clv/bets.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing bets
    bets = []
    if storage_path.exists():
        with open(storage_path) as f:
            data = json.load(f)
            # Handle both formats
            if isinstance(data, dict):
                bets = list(data.values())
            else:
                bets = data
    
    bets.append(bet_record)
    
    with open(storage_path, 'w') as f:
        json.dump(bets, f, indent=2, default=str)
    
    console.print(f"\n[green]✓ Bet saved to {storage_path}[/green]")
    console.print(f"[dim]ID: {bet_record['id']}[/dim]")
    
    # Remind about closing line update
    console.print("\n[yellow]Remember to update the closing line before kickoff![/yellow]")
    console.print(f"[dim]walters clv update {bet_record['id']} --closing-line <LINE>[/dim]")


@app.command("update")
def clv_update(
    bet_id: Optional[str] = typer.Argument(None, help="Bet ID to update (or 'all' for batch)"),
    closing_line: Optional[float] = typer.Option(None, "--closing-line", "-c", help="Closing line"),
    result: Optional[BetResult] = typer.Option(None, "--result", "-r", help="Bet result"),
    auto_fetch: bool = typer.Option(False, "--auto", "-a", help="Auto-fetch closing lines from Overtime"),
):
    """
    Update closing lines and results for tracked bets.
    
    CLV = Opening Line - Closing Line (for spread bets)
    Positive CLV means you got a better number than the market.
    
    Example:
        walters clv update 20241127143022 --closing-line -6.5 --result win
        walters clv update all --auto  # Auto-fetch all closing lines
    """
    if auto_fetch:
        console.print(Panel(
            "[bold]Auto-Fetching Closing Lines[/bold]\n\n"
            "Will fetch closing lines from Overtime.ag for all pending bets.",
            title="🔄 CLV Update",
            border_style="blue",
        ))
        # TODO: Implement auto-fetch
        console.print("[yellow]Auto-fetch implementation in progress...[/yellow]")
        return
    
    if not bet_id:
        console.print("[red]Error: Please provide a bet ID or use --auto[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"[bold]Updating Bet[/bold]\n\n"
        f"ID: {bet_id}\n"
        f"Closing Line: {closing_line}\n"
        f"Result: {result.value if result else 'Not specified'}",
        title="🔄 CLV Update",
        border_style="blue",
    ))
    
    # Load and update bet
    import json
    storage_path = Path("data/clv/bets.json")
    
    if not storage_path.exists():
        console.print("[red]No bets found. Record a bet first with 'walters clv record'[/red]")
        raise typer.Exit(1)
    
    with open(storage_path) as f:
        data = json.load(f)
    
    # Handle both formats: list or dict with IDs as keys
    if isinstance(data, dict):
        bets = list(data.values())
        is_dict_format = True
    else:
        bets = data
        is_dict_format = False
    
    # Find and update bet
    found = False
    for bet in bets:
        bet_id_value = bet.get("id") or bet.get("recommendation_id", "")
        if bet_id_value == bet_id:
            found = True
            
            if closing_line is not None:
                bet["closing_line"] = closing_line
                # Calculate CLV
                opening = bet["opening_line"]
                if bet["bet_type"] == "spread":
                    # For spread bets: CLV = difference in your favor
                    # If you bet favorite -3.5 and it closed at -6.5, CLV = +3.0
                    bet["clv"] = closing_line - opening
                elif bet["bet_type"] == "total":
                    # For totals: depends on over/under
                    if "over" in bet["pick"].lower():
                        bet["clv"] = closing_line - opening  # Higher close = better for over
                    else:
                        bet["clv"] = opening - closing_line  # Lower close = better for under
            
            if result:
                bet["result"] = result.value
            
            break
    
    if not found:
        console.print(f"[red]Bet ID {bet_id} not found[/red]")
        raise typer.Exit(1)
    
    # Save updated bets (preserve original format)
    with open(storage_path, 'w') as f:
        if is_dict_format:
            # Convert back to dict format
            data_to_save = {b.get('id', b.get('recommendation_id', '')): b for b in bets}
        else:
            data_to_save = bets
        json.dump(data_to_save, f, indent=2, default=str)
    
    # Show updated bet
    for bet in bets:
        bet_id_value = bet.get("id") or bet.get("recommendation_id", "")
        if bet_id_value == bet_id:
            clv_display = f"{bet['clv']:+.1f}" if bet['clv'] is not None else "N/A"
            clv_color = "green" if bet.get('clv', 0) and bet['clv'] > 0 else "red" if bet.get('clv', 0) and bet['clv'] < 0 else "white"
            
            console.print(f"\n[green]✓ Bet updated[/green]")
            console.print(f"Opening: {bet['opening_line']}")
            console.print(f"Closing: {bet['closing_line']}")
            console.print(f"CLV: [{clv_color}]{clv_display}[/{clv_color}]")
            if bet['result'] != 'pending':
                result_color = "green" if bet['result'] == 'win' else "red" if bet['result'] == 'loss' else "yellow"
                console.print(f"Result: [{result_color}]{bet['result'].upper()}[/{result_color}]")


@app.command("report")
def clv_report(
    sport: Optional[str] = typer.Option(None, "--sport", "-s", help="Filter by sport"),
    week: Optional[int] = typer.Option(None, "--week", "-w", help="Filter by week"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed breakdown"),
):
    """
    Generate CLV performance report.
    
    Key metrics:
    - CLV Win Rate: % of bets that beat closing line
    - Average CLV: Mean CLV across all bets
    - CLV by bet type: Breakdown for spreads/totals/ML
    
    Target: >55% CLV win rate, +0.3 average CLV
    
    Example:
        walters clv report --sport nfl --detailed
    """
    console.print(Panel(
        "[bold]CLV Performance Report[/bold]",
        title="📊 Closing Line Value Analysis",
        border_style="green",
    ))
    
    # Load bets
    import json
    storage_path = Path("data/clv/bets.json")
    
    if not storage_path.exists():
        console.print("[yellow]No bets found. Record some bets first![/yellow]")
        return
    
    with open(storage_path) as f:
        data = json.load(f)
    
    # Handle both formats: list or dict with IDs as keys
    if isinstance(data, dict):
        bets = list(data.values())
    else:
        bets = data
    
    # Filter if specified
    if sport:
        bets = [b for b in bets if b.get("sport") == sport]
    if week:
        bets = [b for b in bets if b.get("week") == week]
    
    if not bets:
        console.print("[yellow]No bets match the filter criteria[/yellow]")
        return
    
    # Calculate metrics
    bets_with_clv = [b for b in bets if b.get("clv") is not None]
    
    if not bets_with_clv:
        console.print("[yellow]No bets have closing line data yet[/yellow]")
        console.print("[dim]Update closing lines with: walters clv update <ID> --closing-line <LINE>[/dim]")
        return
    
    total_bets = len(bets)
    clv_recorded = len(bets_with_clv)
    positive_clv = sum(1 for b in bets_with_clv if b["clv"] > 0)
    clv_win_rate = (positive_clv / clv_recorded * 100) if clv_recorded > 0 else 0
    avg_clv = sum(b["clv"] for b in bets_with_clv) / clv_recorded if clv_recorded > 0 else 0
    
    # Results
    completed = [b for b in bets if b.get("result") in ["win", "loss", "push"]]
    wins = sum(1 for b in completed if b["result"] == "win")
    losses = sum(1 for b in completed if b["result"] == "loss")
    pushes = sum(1 for b in completed if b["result"] == "push")
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    # Summary panel
    clv_color = "green" if clv_win_rate >= 55 else "yellow" if clv_win_rate >= 50 else "red"
    avg_clv_color = "green" if avg_clv >= 0.3 else "yellow" if avg_clv >= 0 else "red"
    
    console.print(f"\n[bold]Sample Size:[/bold] {total_bets} total bets")
    if total_bets < 50:
        console.print(f"[yellow]⚠️ Building phase - need {50 - total_bets} more for validation[/yellow]")
    elif total_bets < 100:
        console.print(f"[yellow]⚠️ Validation phase - need {100 - total_bets} more for statistical proof[/yellow]")
    else:
        console.print(f"[green]✓ Statistical proof threshold reached![/green]")
    
    console.print(f"\n[bold]CLV Metrics:[/bold]")
    console.print(f"  CLV Recorded: {clv_recorded}/{total_bets}")
    console.print(f"  CLV Win Rate: [{clv_color}]{clv_win_rate:.1f}%[/{clv_color}] (target: >55%)")
    console.print(f"  Average CLV: [{avg_clv_color}]{avg_clv:+.2f}[/{avg_clv_color}] (target: >+0.3)")
    
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Record: {wins}-{losses}-{pushes}")
    console.print(f"  Win Rate: {win_rate:.1f}%")
    
    # Detailed breakdown
    if detailed:
        console.print("\n")
        table = Table(title="Bet Details")
        table.add_column("ID", style="dim")
        table.add_column("Game")
        table.add_column("Pick")
        table.add_column("Open", justify="right")
        table.add_column("Close", justify="right")
        table.add_column("CLV", justify="right")
        table.add_column("Result", justify="center")
        
        for bet in sorted(bets, key=lambda x: x.get("timestamp", ""), reverse=True):
            clv_val = bet.get("clv")
            clv_str = f"{clv_val:+.1f}" if clv_val is not None else "-"
            clv_style = "green" if clv_val and clv_val > 0 else "red" if clv_val and clv_val < 0 else ""
            
            result = bet.get("result", "pending")
            result_style = "green" if result == "win" else "red" if result == "loss" else "yellow"
            
            table.add_row(
                bet.get("id", "")[:12],
                bet.get("game", ""),
                bet.get("pick", ""),
                str(bet.get("opening_line", "")),
                str(bet.get("closing_line", "-")),
                f"[{clv_style}]{clv_str}[/{clv_style}]" if clv_style else clv_str,
                f"[{result_style}]{result.upper()}[/{result_style}]",
            )
        
        console.print(table)


@app.command("list")
def clv_list(
    status: Optional[BetResult] = typer.Option(None, "--status", "-s", help="Filter by status"),
    sport: Optional[str] = typer.Option(None, "--sport", help="Filter by sport"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max bets to show"),
):
    """
    List all tracked bets.
    
    Example:
        walters clv list --status pending
        walters clv list --sport nfl --limit 10
    """
    import json
    storage_path = Path("data/clv/bets.json")
    
    if not storage_path.exists():
        console.print("[yellow]No bets found. Record some bets first![/yellow]")
        console.print("[dim]walters clv record \"DET @ CHI\" \"DET -3.5\" -3.5 --stake 200[/dim]")
        return
    
    with open(storage_path) as f:
        data = json.load(f)
    
    # Handle both formats: list or dict with IDs as keys
    if isinstance(data, dict):
        bets = list(data.values())
    else:
        bets = data
    
    # Apply filters
    if status:
        bets = [b for b in bets if b.get("result") == status.value]
    if sport:
        bets = [b for b in bets if b.get("sport") == sport]
    
    # Sort by timestamp descending (handle both field names)
    bets = sorted(bets, key=lambda x: x.get("timestamp", x.get("opening_date", "")), reverse=True)[:limit]
    
    if not bets:
        console.print("[yellow]No bets match the filter criteria[/yellow]")
        return
    
    table = Table(title=f"Tracked Bets ({len(bets)} shown)")
    table.add_column("ID", style="dim")
    table.add_column("Date")
    table.add_column("Game", style="cyan")
    table.add_column("Pick")
    table.add_column("Stake", justify="right")
    table.add_column("Status", justify="center")
    
    for bet in bets:
        bet_id_display = bet.get("id", bet.get("recommendation_id", ""))[:12]
        timestamp = bet.get("timestamp", bet.get("opening_date", ""))[:10]
        result = bet.get("result", "pending")
        result_style = "green" if result == "win" else "red" if result == "loss" else "yellow"
        
        table.add_row(
            bet_id_display,
            timestamp,
            bet.get("game", bet.get("game_id", "")),
            bet.get("pick", bet.get("bet_side", "")),
            f"${bet.get('stake', bet.get('bankroll', 0) * bet.get('stake_fraction', 0)):.0f}",
            f"[{result_style}]{result.upper()}[/{result_style}]",
        )
    
    console.print(table)


@app.command("analyze")
def clv_analyze(
    by: str = typer.Option("week", "--by", "-b", help="Group by: week, sport, bet_type, edge"),
):
    """
    Analyze CLV trends and patterns.
    
    Helps identify:
    - Which weeks have best CLV performance
    - Which bet types generate most CLV
    - Whether edge predictions correlate with CLV
    
    Example:
        walters clv analyze --by week
        walters clv analyze --by edge
    """
    console.print(Panel(
        f"[bold]CLV Trend Analysis[/bold]\n"
        f"Grouping by: {by}",
        title="📈 CLV Analysis",
        border_style="blue",
    ))
    
    # TODO: Implement detailed analysis
    console.print("[yellow]Implementation in progress...[/yellow]")
    console.print("[dim]Will show CLV breakdown by the specified grouping[/dim]")


if __name__ == "__main__":
    app()
