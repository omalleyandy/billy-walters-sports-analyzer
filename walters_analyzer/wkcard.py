import json
import pathlib
from typing import Optional
from walters_analyzer.core import BillyWaltersAnalyzer


def load_card(path: pathlib.Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _gate_bool(game: dict, key: str) -> bool:
    return bool(game.get("entry_gates_checklist", {}).get(key, False))


def validate_gates(card: dict):
    problems = []
    for g in card.get("games", []):
        ident = f"{g.get('matchup', '?')}"
        if not _gate_bool(g, "injuries_confirmed"):
            problems.append(f"{ident}: injuries_confirmed is false")
        if not _gate_bool(g, "weather_confirmed"):
            problems.append(f"{ident}: weather_confirmed is false")
        if not _gate_bool(g, "steam_ok"):
            problems.append(f"{ident}: steam_ok is false")
    return problems


def summarize_card(
    card: dict,
    dry_run: bool = True,
    analyzer: Optional[BillyWaltersAnalyzer] = None,
    show_bankroll: bool = False,
) -> str:
    """
    Summarize card with optional bankroll-aware recommendations.

    Args:
        card: Week card dictionary
        dry_run: Whether this is a dry run
        analyzer: Optional analyzer for bankroll-aware sizing
        show_bankroll: Whether to show bankroll percentages and amounts
    """
    lines = []

    # Header
    header = f"Wk-Card {card.get('date', '?')} | source={card.get('source', '?')} | dry_run={dry_run}"
    if show_bankroll and analyzer:
        current_br = analyzer.bankroll.bankroll
        lines.append(f"{header} | Bankroll=${current_br:,.2f}")
    else:
        lines.append(header)

    # Games
    for g in card.get("games", []):
        lines.append(f"- {g.get('rotation', '?')} {g.get('matchup', '?')}")
        sides = g.get("sides", {})
        se = sides.get("spread_entry", {})
        me = sides.get("moneyline_entry", {})
        te = sides.get("total_entry", {})

        if se.get("pick"):
            line = f"  spread: {se['pick']} (size={se.get('size_units', '?')}u, max_juice={se.get('target_price_max_juice', '?')})"
            if show_bankroll and analyzer:
                # Calculate recommended stake
                stake_pct = se.get("recommended_stake_pct", 0.0)
                stake_amt = analyzer.bankroll.stake_amount(stake_pct)
                line += f" → {stake_pct:.2f}% (${stake_amt:.2f})"
            lines.append(line)

        if me.get("pick"):
            if "target_min_price" in me:
                line = f"  moneyline: {me['pick']} (min_price={me['target_min_price']}, size={me.get('size_units', '?')}u)"
            else:
                line = f"  moneyline: {me['pick']} (max_price={me.get('target_price_max', '?')}, size={me.get('size_units', '?')}u)"
            if show_bankroll and analyzer:
                stake_pct = me.get("recommended_stake_pct", 0.0)
                stake_amt = analyzer.bankroll.stake_amount(stake_pct)
                line += f" → {stake_pct:.2f}% (${stake_amt:.2f})"
            lines.append(line)

        if te.get("pick"):
            line = f"  total: {te['pick']} (max_juice={te.get('target_price_max_juice', '?')}, size={te.get('size_units', '?')}u)"
            if show_bankroll and analyzer:
                stake_pct = te.get("recommended_stake_pct", 0.0)
                stake_amt = analyzer.bankroll.stake_amount(stake_pct)
                line += f" → {stake_pct:.2f}% (${stake_amt:.2f})"
            lines.append(line)

        if g.get("live_triggers"):
            lines.append(f"  live_triggers: {g['live_triggers']}")

    return "\n".join(lines)
