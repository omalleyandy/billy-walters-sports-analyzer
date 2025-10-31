import argparse, json, sys, pathlib
from walters_analyzer.wkcard import load_card, summarize_card, validate_gates

def main():
    parser = argparse.ArgumentParser(prog="walters-analyzer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    wk = sub.add_parser("wk-card", help="Run/preview a wk-card JSON")
    wk.add_argument("--file", required=True, help="Path to wk-card JSON")
    wk.add_argument("--dry-run", action="store_true", help="Preview entries and gating without 'placing'")
    args = parser.parse_args()

    p = pathlib.Path(args.file)
    if not p.exists():
        print(f"ERROR: card not found: {p}", file=sys.stderr)
        sys.exit(2)

    card = load_card(p)
    problems = validate_gates(card)
    if problems:
        print("GATE CHECKS FAILED:")
        for pr in problems:
            print(f" - {pr}")
        sys.exit(1)

    print(summarize_card(card, dry_run=args.dry_run))

if __name__ == "__main__":
    main()
