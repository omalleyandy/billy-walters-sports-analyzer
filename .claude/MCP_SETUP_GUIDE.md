# Billy Walters MCP Server - Setup & Fix Guide

## Issues Fixed in v2.0.1

The original MCP server had several critical issues that prevented it from starting:

1. **Wrong class name**: Used `WaltersSportsAnalyzer` instead of `BillyWaltersAnalyzer`
2. **Missing imports**: Didn't import required classes from `walters_analyzer.core`
3. **Undefined functions**: Called `apply_default_team_ratings()` which doesn't exist
4. **Commented code still used**: `SlashCommandHandler` was commented in imports but used in code
5. **Missing error handling**: No try/catch blocks for initialization failures

## Installation Steps

### 1. Install MCP Dependencies

```bash
# Navigate to project directory
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

# Install MCP dependencies with uv
uv pip install 'walters-analyzer[mcp]'

# Or install manually:
uv pip install fastmcp pydantic aiohttp uvicorn
```

### 2. Verify Installation

Run the diagnostic script:

```bash
uv run python .claude/diagnose_mcp.py
```

This will check:
- Python version (3.10+)
- uv installation
- Project structure
- All required dependencies
- Environment variables
- Server initialization

### 3. Update Claude Desktop Configuration

Your current config (from the screenshot):

```json
{
  "mcpServers": {
    "billy-walters-expert": {
      "command": "uv",
      "args": ["run", "python", ".claude/walters_mcp_server.py"],
      "env": {
        "ACCUWEATHER_API_KEY": "${ACCUWEATHER_API_KEY}",
        "HIGHLIGHTLY_API_KEY": "${HIGHLIGHTLY_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "PROXY_URL": "${PROXY_URL}",
        "PROXY_USER": "${PROXY_USER}",
        "PROXY_PASSWORD": "${PROXY_PASSWORD}",
        "PYTHONPATH": "${PYTHONPATH}:./src"
      }
    }
  }
}
```

**Recommended improvements:**

```json
{
  "mcpServers": {
    "billy-walters-expert": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\omall\\Documents\\python_projects\\billy-walters-sports-analyzer",
        "run",
        "python",
        ".claude/walters_mcp_server.py"
      ],
      "env": {
        "ACCUWEATHER_API_KEY": "${ACCUWEATHER_API_KEY}",
        "HIGHLIGHTLY_API_KEY": "${HIGHLIGHTLY_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "PROXY_URL": "${PROXY_URL}",
        "PROXY_USER": "${PROXY_USER}",
        "PROXY_PASSWORD": "${PROXY_PASSWORD}",
        "PYTHONPATH": "C:\\Users\\omall\\Documents\\python_projects\\billy-walters-sports-analyzer\\src"
      }
    }
  }
}
```

Key changes:
- Added `--directory` flag to set working directory explicitly
- Used absolute path for PYTHONPATH instead of relative

### 4. Test the Server

Option A - Direct test (recommended first):

```bash
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
uv run python .claude/walters_mcp_server.py
```

Expected output:
```
2025-11-17 ... [INFO] MCP Server initialized with unified configuration
2025-11-17 ... [INFO] Initialized analyzer with bankroll: $10000
2025-11-17 ... [INFO] Skills enabled: {'market_analysis': True, ...}
2025-11-17 ... [INFO] Engine initialized successfully
2025-11-17 ... [INFO] Billy Walters MCP Server starting...
2025-11-17 ... [INFO] Billy Walters MCP Server ready!
```

If you see errors, they'll appear in the console for debugging.

Option B - Test with Claude Desktop:

1. Save the updated config to `%APPDATA%\Claude\claude_desktop_config.json`
2. Restart Claude Desktop completely (close from system tray)
3. Open Settings > Developer
4. Check if "billy-walters-expert" shows green status

### 5. Check Logs If Issues Persist

If the server still fails:

1. Click "Open Logs Folder" in Claude Desktop settings
2. Find `mcp-server-billy-walters-expert.log`
3. Look for Python tracebacks and error messages

Common log locations:
- `%APPDATA%\Claude\logs\mcp-server-billy-walters-expert.log`
- `C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\logs\mcp-server.log`

## Available MCP Tools

Once working, you'll have access to these tools in Claude:

### Core Analysis
- `analyze_game()` - Full Billy Walters methodology analysis
- `calculate_kelly_stake()` - Optimal bet sizing with Kelly Criterion
- `get_injury_report()` - Comprehensive injury impact analysis

### Resources
- `betting-history` - Access your bet tracking and performance
- `system-config` - View current configuration and bankroll

## Troubleshooting

### Error: "Module 'walters_analyzer' not found"

```bash
# Install in editable mode
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
uv pip install -e .
```

### Error: "Module 'fastmcp' not found"

```bash
# Install MCP dependencies
uv pip install 'walters-analyzer[mcp]'
```

### Error: "Could not initialize research engine"

This is a WARNING, not an error. The server will work but research features will be limited.

To fix:
1. Check your `.env` file has API keys
2. Ensure environment variables are loaded

### Server shows "disconnected" immediately

1. Run diagnostic script: `uv run python .claude/diagnose_mcp.py`
2. Test server directly: `uv run python .claude/walters_mcp_server.py`
3. Check Python path and working directory in config
4. Verify all dependencies are installed

## What's New in v2.0.1

### Fixes
- ✅ Corrected class names (`BillyWaltersAnalyzer`)
- ✅ Added all required imports
- ✅ Removed undefined function calls
- ✅ Added comprehensive error handling
- ✅ Fixed path resolution for imports

### Improvements
- Better logging throughout
- Graceful degradation when features unavailable
- Clearer error messages
- Safer initialization with try/catch blocks

## Next Steps After Setup

1. Test basic functionality:
   ```
   Ask Claude: "Analyze Chiefs vs Bills with spread -3"
   ```

2. Test research integration:
   ```
   Ask Claude: "Get injury report for Kansas City Chiefs"
   ```

3. Test Kelly sizing:
   ```
   Ask Claude: "Calculate Kelly stake for 2.5% edge at -110 odds with $10k bankroll"
   ```

## Support

If you encounter issues:

1. Run the diagnostic script first
2. Check the server logs
3. Test direct execution before Claude Desktop
4. Verify environment variables are set
5. Ensure uv and dependencies are up to date

The fixed server (v2.0.1) has much better error handling and will provide clear error messages if something goes wrong.
