"""
Complete status check for Billy Walters MCP Server
Writes detailed results to status_report.txt
"""

import sys
from pathlib import Path
from datetime import datetime

# Setup output file
output_file = Path(__file__).parent / "status_report.txt"

def write_and_print(msg):
    """Write to both console and file"""
    print(msg)
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear previous report
output_file.write_text("", encoding="utf-8")

write_and_print("=" * 70)
write_and_print("  Billy Walters MCP Server - Complete Status Check")
write_and_print("=" * 70)
write_and_print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
write_and_print(f"Python: {sys.version}")
write_and_print(f"Executable: {sys.executable}")

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
write_and_print(f"Project root: {project_root}")

# Test 1: Core Python modules
write_and_print("\n" + "=" * 70)
write_and_print("TEST 1: Core Python Modules")
write_and_print("=" * 70)

try:
    import asyncio
    import json
    import logging
    write_and_print("[OK] All core modules imported successfully")
except ImportError as e:
    write_and_print(f"[X] Core module import failed: {e}")
    sys.exit(1)

# Test 2: Third-party dependencies
write_and_print("\n" + "=" * 70)
write_and_print("TEST 2: Third-Party Dependencies")
write_and_print("=" * 70)

deps_ok = True

try:
    import pydantic
    write_and_print(f"[OK] pydantic {pydantic.VERSION}")
except ImportError as e:
    write_and_print(f"[X] pydantic: {e}")
    deps_ok = False

try:
    import fastmcp
    write_and_print(f"[OK] fastmcp {fastmcp.__version__}")
except ImportError as e:
    write_and_print(f"[X] fastmcp: {e}")
    write_and_print("  Install with: uv pip install fastmcp")
    deps_ok = False

try:
    import aiohttp
    write_and_print(f"[OK] aiohttp {aiohttp.__version__}")
except ImportError as e:
    write_and_print(f"[X] aiohttp: {e}")
    deps_ok = False

# Test 3: Walters Analyzer package
write_and_print("\n" + "=" * 70)
write_and_print("TEST 3: Walters Analyzer Package")
write_and_print("=" * 70)

package_ok = True

try:
    from walters_analyzer.config import get_settings
    write_and_print("[OK] config module imported")
    
    settings = get_settings()
    write_and_print("[OK] Settings loaded successfully")
    write_and_print(f"  - Bankroll: ${settings.autonomous_agent.initial_bankroll:,}")
    write_and_print(f"  - Max Bet: {settings.autonomous_agent.max_bet_percentage}%")
    write_and_print(f"  - Log Level: {settings.global_config.log_level}")
    
except ImportError as e:
    write_and_print(f"[X] Config import failed: {e}")
    package_ok = False
except Exception as e:
    write_and_print(f"[X] Settings load error: {e}")
    package_ok = False

try:
    from walters_analyzer.core.analyzer import BillyWaltersAnalyzer
    write_and_print("[OK] BillyWaltersAnalyzer imported")
except ImportError as e:
    write_and_print(f"[X] BillyWaltersAnalyzer: {e}")
    package_ok = False

try:
    from walters_analyzer.core.config import AnalyzerConfig
    write_and_print("[OK] AnalyzerConfig imported")
    
    config = AnalyzerConfig.from_settings()
    write_and_print(f"  - Bankroll: ${config.bankroll:,}")
    write_and_print(f"  - Max Bet %: {config.max_bet_pct}%")
    write_and_print(f"  - Fractional Kelly: {config.fractional_kelly}")
    
except ImportError as e:
    write_and_print(f"[X] AnalyzerConfig: {e}")
    package_ok = False
except Exception as e:
    write_and_print(f"[X] AnalyzerConfig error: {e}")
    package_ok = False

try:
    from walters_analyzer.core.models import GameInput, TeamSnapshot, GameOdds
    write_and_print("[OK] Core models imported")
except ImportError as e:
    write_and_print(f"[X] Core models: {e}")
    package_ok = False

# Test 4: Research engine (optional)
write_and_print("\n" + "=" * 70)
write_and_print("TEST 4: Research Engine (Optional)")
write_and_print("=" * 70)

try:
    from walters_analyzer.research.engine import ResearchEngine
    write_and_print("[OK] ResearchEngine available")
except ImportError as e:
    write_and_print(f"[WARNING] ResearchEngine not available: {e}")
    write_and_print("  Note: This is optional, core functionality will still work")

# Test 5: MCP Server file
write_and_print("\n" + "=" * 70)
write_and_print("TEST 5: MCP Server File")
write_and_print("=" * 70)

server_path = project_root / ".claude" / "walters_mcp_server.py"
if server_path.exists():
    write_and_print(f"[OK] MCP server file exists")
    write_and_print(f"  Location: {server_path}")
    write_and_print(f"  Size: {server_path.stat().st_size:,} bytes")
else:
    write_and_print(f"[X] MCP server file not found at {server_path}")

# Final summary
write_and_print("\n" + "=" * 70)
write_and_print("SUMMARY")
write_and_print("=" * 70)

all_ok = deps_ok and package_ok

if all_ok:
    write_and_print("\n[OK] ALL TESTS PASSED!")
    write_and_print("\nYour MCP server is ready to use.")
    write_and_print("\nNext steps:")
    write_and_print(r"  1. Test analyzer: .\.venv\Scripts\python.exe test_analyzer_simple.py")
    write_and_print("  2. Install Node.js from https://nodejs.org/")
    write_and_print(r"  3. Run Inspector: npx @modelcontextprotocol/inspector python .claude\walters_mcp_server.py")
    write_and_print("  4. Or add to Claude Desktop (see QUICK_START_MCP.md)")
else:
    write_and_print("\n[X] SOME TESTS FAILED")
    write_and_print("\nIssues found:")
    if not deps_ok:
        write_and_print("  - Missing dependencies. Install with: uv pip install -e .[mcp]")
    if not package_ok:
        write_and_print("  - Package import errors. Install with: uv pip install -e .")
    write_and_print("\nAfter fixing, run this script again.")

write_and_print("\n" + "=" * 70)
write_and_print(f"Report saved to: {output_file}")
write_and_print("=" * 70)

print(f"\n\nFull report saved to: {output_file}")
print("Open this file to see complete results.")
