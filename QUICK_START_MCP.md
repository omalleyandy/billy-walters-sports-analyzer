# Quick Start Guide - Billy Walters MCP Server

## Current Status: Node.js Required

The MCP Inspector requires Node.js to run. Here's how to get started:

## Option 1: Install Node.js (Recommended for Inspector)

### Download and Install:
1. Go to: https://nodejs.org/
2. Download the **LTS version** (Long Term Support)
3. Run the installer
4. Accept all defaults
5. Restart PowerShell

### After Installation:
```powershell
# Verify installation
node --version
npm --version
npx --version

# Then run the test
.\test_mcp_server.ps1
```

## Option 2: Test Server Directly (Without Inspector)

You can test the server without the Inspector using Python:

### A. Quick Import Test
```powershell
python diagnose_mcp.py
```

### B. Direct Server Test
```powershell
# This will start the server and show if it loads without errors
python .claude\walters_mcp_server.py
```

Press `Ctrl+C` to stop the server.

### C. Test with a Simple Client
Create a test script:

```python
# test_mcp_client.py
import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from walters_analyzer.core.analyzer import BillyWaltersAnalyzer
from walters_analyzer.core.config import AnalyzerConfig
from walters_analyzer.core.models import GameInput, TeamSnapshot, GameOdds

async def test_analyzer():
    print("=" * 60)
    print("Testing Billy Walters Analyzer")
    print("=" * 60)
    
    # Initialize
    config = AnalyzerConfig.from_settings()
    analyzer = BillyWaltersAnalyzer(config=config)
    print(f"✓ Analyzer initialized with bankroll: ${config.bankroll}")
    
    # Create test game
    home_team = TeamSnapshot(name="Kansas City Chiefs", injuries=[])
    away_team = TeamSnapshot(name="Buffalo Bills", injuries=[])
    
    odds = GameOdds(
        spread=type('Spread', (), {
            'home_spread': -2.5,
            'home_price': -110,
            'away_price': -110
        })(),
        total=type('Total', (), {
            'over': 47.5,
            'over_price': -110,
            'under_price': -110
        })()
    )
    
    game = GameInput(
        home_team=home_team,
        away_team=away_team,
        odds=odds,
        game_date="2024-11-19"
    )
    
    print("\nAnalyzing: Buffalo Bills @ Kansas City Chiefs (-2.5)")
    
    # Analyze
    result = analyzer.analyze(game)
    
    print(f"\nResults:")
    print(f"  Predicted Spread: {result.predicted_spread}")
    print(f"  Market Spread: {result.market_spread}")
    print(f"  Edge: {result.edge}")
    print(f"  Confidence: {result.confidence}%")
    
    if abs(result.edge) >= 1.0:
        recommendation = "PLAY" if result.edge > 0 else "PLAY"
        side = "Away" if result.edge > 0 else "Home"
        print(f"\n✓ {recommendation} - Take {side} ({abs(result.edge):.1f} point edge)")
    else:
        print(f"\n✗ PASS - Edge too small ({abs(result.edge):.1f} points)")
    
    print("=" * 60)
    print("✓ Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_analyzer())
```

Run it:
```powershell
python test_mcp_client.py
```

## Option 3: Add to Claude Desktop (Skip Inspector)

If you want to use the MCP server directly with Claude Desktop without testing in the Inspector first:

### Edit Claude Desktop Config:

**File Location:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "billy-walters-expert": {
      "command": "python",
      "args": [
        "C:\\Users\\omall\\Documents\\python_projects\\billy-walters-sports-analyzer\\.claude\\walters_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\Users\\omall\\Documents\\python_projects\\billy-walters-sports-analyzer\\src"
      }
    }
  }
}
```

**Then:**
1. Restart Claude Desktop
2. Look for the MCP server icon in Claude
3. Try a command like: "analyze the Chiefs vs Bills game with spread -2.5"

## Troubleshooting

### If you get import errors:
```powershell
# Install the package
uv pip install -e ".[mcp]"

# Or manually install dependencies
uv pip install fastmcp pydantic aiohttp
```

### If server won't start:
1. Check logs: `Get-Content logs\mcp-server.log -Tail 50`
2. Verify .env file exists
3. Test imports: `python diagnose_mcp.py`

### Common Issues:

| Issue | Solution |
|-------|----------|
| "No module named 'fastmcp'" | `uv pip install fastmcp` |
| "No module named 'walters_analyzer'" | `uv pip install -e .` |
| "Research engine error" | Non-critical, server still works |
| Python not found | Verify Python 3.10+ installed |

## What Each File Does

- **test_mcp_server.ps1** - Checks environment and launches Inspector (needs Node.js)
- **setup_mcp.ps1** - Installs all dependencies
- **diagnose_mcp.py** - Tests Python imports without Node.js
- **test_mcp.bat** - Simple batch file launcher
- **.claude/walters_mcp_server.py** - The actual MCP server

## Next Steps

1. **If you want the Inspector:** Install Node.js then run `.\test_mcp_server.ps1`
2. **If you want quick testing:** Run `python diagnose_mcp.py`
3. **If you want to use it now:** Add to Claude Desktop config directly

## Reference

- **MCP Documentation:** https://modelcontextprotocol.io
- **Node.js Download:** https://nodejs.org/
- **Project README:** See `README.md` for full documentation
