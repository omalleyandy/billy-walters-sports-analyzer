#!/usr/bin/env python
"""Test script to verify CLI imports work correctly."""

import sys


def test_imports():
    """Test all CLI module imports."""
    errors = []

    # Test main CLI
    try:
        from walters_analyzer.cli.main import app, cli

        print("✓ Main CLI imports OK")
    except ImportError as e:
        errors.append(f"Main CLI: {e}")
        print(f"✗ Main CLI: {e}")

    # Test command modules
    modules = [
        ("analyze", "walters_analyzer.cli.commands.analyze"),
        ("scrape", "walters_analyzer.cli.commands.scrape"),
        ("clv", "walters_analyzer.cli.commands.clv"),
        ("status", "walters_analyzer.cli.commands.status"),
        ("power_ratings", "walters_analyzer.cli.commands.power_ratings"),
        ("db", "walters_analyzer.cli.commands.db"),
        ("monitor", "walters_analyzer.cli.commands.monitor"),
        ("quickstart", "walters_analyzer.cli.commands.quickstart"),
    ]

    for name, module_path in modules:
        try:
            __import__(module_path)
            print(f"✓ {name} imports OK")
        except ImportError as e:
            errors.append(f"{name}: {e}")
            print(f"✗ {name}: {e}")

    if errors:
        print(f"\n{len(errors)} import errors found!")
        return 1
    else:
        print("\n✓ All imports successful!")
        return 0


if __name__ == "__main__":
    sys.exit(test_imports())
