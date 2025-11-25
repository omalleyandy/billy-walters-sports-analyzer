# MCP Server Diagnostic & Testing Guide

## Overview

This guide helps you diagnose and test your Billy Walters MCP Server using the MCP Inspector.

## Your MCP Server

**Location:** `.claude\walters_mcp_server.py`  
**Type:** FastMCP server  
**Purpose:** Sports betting analysis using Billy Walters methodology

### Server Features

**Tools:**
- `analyze_game` - Comprehensive game analysis with betting signals
- `calculate_kelly_stake` - Optimal bet sizing using Kelly Criterion
- `get_injury_report` - Detailed injury analysis with point impacts

**Resources:**
- `walters://betting-history` - Complete betting history and performance
- `walters://system-config` - Current system configuration

## Step-by-Step Diagnostic Process

### 1. **Install Dependencies**

Run the setup script:

```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
.\setup_mcp.ps1
```

Or manually:

```powershell
uv pip install -e ".[mcp]"
```

This installs:
- `fastmcp>=0.2.0` - MCP server framework
- `pydantic>=2.0` - Data validation
- `aiohttp>=3.9` - Async HTTP client
- Your `walters-analyzer` package in editable mode

### 2. **Quick Diagnostic Test**

Run the diagnostic script:

```powershell
python diagnose_mcp.py
```

This will verify:
- ✓ Core Python dependencies
- ✓ FastMCP installation
- ✓ walters_analyzer package imports
- ✓ All required modules

### 3. **Launch MCP Inspector**

#### Option A: Use the test script (recommended)

```powershell
.\test_mcp_server.ps1
```

#### Option B: Manual launch

```powershell
npx @modelcontextprotocol/inspector python .claude\walters_mcp_server.py
```

The Inspector will:
1. Start your MCP server
2. Open in your default browser
3. Show an interactive interface

### 4. **Test Server Features**

Once the Inspector opens, test these features:

#### **Tools Tab**

1. **analyze_game**
   ```json
   {
     "home_team": "Kansas City Chiefs",
     "away_team": "Buffalo Bills",
     "spread": -2.5,
     "total": 47.5,
     "include_research": true
   }
   ```
   
   Expected: Detailed analysis with betting signal

2. **calculate_kelly_stake**
   ```json
   {
     "edge_percentage": 2.5,
     "odds": -110,
     "bankroll": 10000,
     "kelly_fraction": 0.25
   }
   ```
   
   Expected: Optimal stake calculations

3. **get_injury_report**
   ```json
   {
     "team": "Kansas City Chiefs"
   }
   ```
   
   Expected: Injury analysis with point impacts

#### **Resources Tab**

1. Click `walters://betting-history` → Should show bet history
2. Click `walters://system-config` → Should show current config

#### **Notifications Pane**

- Check for error messages
- Verify logs are being recorded
- Look for connection issues

## Common Issues & Solutions

### Issue 1: "FastMCP not found"

**Solution:**
```powershell
uv pip install fastmcp
```

### Issue 2: "Cannot import walters_analyzer"

**Solution:**
```powershell
uv pip install -e .
```

### Issue 3: "ResearchEngine initialization failed"

**Cause:** Research engine may require additional configuration  
**Impact:** Limited - core analysis still works  
**Check:** Server logs in `logs/mcp-server.log`

### Issue 4: "npx not found"

**Solution:** Install Node.js from https://nodejs.org/

### Issue 5: Server crashes on startup

**Check:**
1. Review `logs/mcp-server.log`
2. Verify `.env` file exists with required settings
3. Check if all dependencies are installed: `python diagnose_mcp.py`

## Server Configuration

Your server uses unified configuration from:
- **Environment variables** (`.env` file)
- **Settings module** (`walters_analyzer.config.settings`)

Key settings:
- `BANKROLL` - Initial bankroll amount
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `MONITORING.PERFORMANCE_TRACKING` - Enable/disable performance tracking
- `SKILLS.*` - Enable/disable specific analysis features

## Logs

Server logs are written to:
- **File:** `logs/mcp-server.log`
- **Console:** stderr only (stdout reserved for JSON-RPC)

To view logs in real-time:
```powershell
Get-Content logs\mcp-server.log -Wait -Tail 50
```

## Testing Workflow

1. **Initial Setup** (one-time)
   ```powershell
   .\setup_mcp.ps1
   ```

2. **Before Each Test**
   ```powershell
   python diagnose_mcp.py
   ```

3. **Run Inspector**
   ```powershell
   .\test_mcp_server.ps1
   ```

4. **Make Changes** to server
   - Edit `.claude\walters_mcp_server.py`
   - Save changes

5. **Reconnect Inspector**
   - Stop Inspector (Ctrl+C)
   - Run `.\test_mcp_server.ps1` again
   - Test affected features

## Advanced Testing

### Test Edge Cases

1. **Invalid Inputs**
   - Negative spreads
   - Missing required fields
   - Invalid team names

2. **Error Handling**
   - Network timeouts
   - Missing research data
   - Concurrent requests

3. **Performance**
   - Large data requests
   - Multiple simultaneous tool calls
   - Resource-intensive operations

### Monitor Performance

Check these metrics:
- Tool execution time
- Memory usage
- Error rates
- API call success rates

## Integration with Claude Desktop

Once tested, add to Claude Desktop config:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

## Troubleshooting Checklist

- [ ] Node.js installed (for npx)
- [ ] Python 3.10+ available
- [ ] uv package manager working
- [ ] Package installed: `uv pip list | Select-String walters`
- [ ] FastMCP installed: `python -c "import fastmcp"`
- [ ] Server file exists: `.claude\walters_mcp_server.py`
- [ ] Logs directory exists: `logs/`
- [ ] .env file configured
- [ ] No Python syntax errors in server file

## Support Resources

- **MCP Documentation:** https://docs.modelcontextprotocol.com
- **FastMCP GitHub:** https://github.com/jlowin/fastmcp
- **Inspector Repository:** https://github.com/modelcontextprotocol/inspector

## Next Steps

After successful testing:

1. ✓ Server working in Inspector
2. → Add to Claude Desktop config
3. → Test in Claude Desktop
4. → Build production workflows
5. → Add monitoring and alerts
6. → Expand tool capabilities

## Notes

- Server logs to stderr and file (NOT stdout - breaks JSON-RPC)
- Research engine is optional - core analysis works without it
- Skills can be enabled/disabled via configuration
- CLV tracking requires bet history data
