import json, pathlib

def load_card(path: pathlib.Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _gate_bool(game: dict, key: str) -> bool:
    return bool(game.get("entry_gates_checklist", {}).get(key, False))

def validate_gates(card: dict):
    problems = []
    for g in card.get("games", []):
        ident = f"{g.get('matchup','?')}"
        if not _gate_bool(g, "injuries_confirmed"):
            problems.append(f"{ident}: injuries_confirmed is false")
        if not _gate_bool(g, "weather_confirmed"):
            problems.append(f"{ident}: weather_confirmed is false")
        if not _gate_bool(g, "steam_ok"):
            problems.append(f"{ident}: steam_ok is false")
    return problems

def summarize_card(card: dict, dry_run: bool = True) -> str:
    lines = []
    lines.append(f"Wk-Card {card.get('date','?')} | source={card.get('source','?')} | dry_run={dry_run}")
    for g in card.get("games", []):
        lines.append(f"- {g.get('rotation','?')} {g.get('matchup','?')}")
        sides = g.get("sides", {})
        se = sides.get("spread_entry", {})
        me = sides.get("moneyline_entry", {})
        te = sides.get("total_entry", {})
        if se.get("pick"):
            lines.append(f"  spread: {se['pick']} (size={se.get('size_units','?')}u, max_juice={se.get('target_price_max_juice','?')})")
        if me.get("pick"):
            if "target_min_price" in me:
                lines.append(f"  moneyline: {me['pick']} (min_price={me['target_min_price']}, size={me.get('size_units','?')}u)")
            else:
                lines.append(f"  moneyline: {me['pick']} (max_price={me.get('target_price_max','?')}, size={me.get('size_units','?')}u)")
        if te.get("pick"):
            lines.append(f"  total: {te['pick']} (max_juice={te.get('target_price_max_juice','?')}, size={te.get('size_units','?')}u)")
        if g.get("live_triggers"):
            lines.append(f"  live_triggers: {g['live_triggers']}")
    return "\n".join(lines)
