# MCP Server Testing - Complete Guide

## Summary of What We Created

I've created several tools to help you test your Billy Walters MCP Server. Here's what each does and when to use it:

## 📁 Files Created

### **Testing Scripts**

1. **`test_analyzer.bat`** ⭐ **SIMPLEST - START HERE** ⭐
   - **No requirements:** Works with or without Node.js
   - **What it does:** Tests the core analyzer functionality
   - **How to run:** Double-click the file or `.\test_analyzer.bat`
   - **Use when:** You want to verify the analyzer works

2. **`test_analyzer_simple.py`**
   - Python script that tests the analyzer
   - Called by `test_analyzer.bat`
   - Can also run directly: `.\.venv\Scripts\python.exe test_analyzer_simple.py`

3. **`diagnose_mcp.py`**
   - Tests all imports and dependencies
   - **Run:** `.\.venv\Scripts\python.exe diagnose_mcp.py`
   - Shows what's installed and what's missing

4. **`test_mcp_server.ps1`**
   - **Requires:** Node.js installed
   - **What it does:** Launches MCP Inspector for interactive testing
   - **Use when:** You want the full Inspector experience

5. **`setup_mcp.ps1`**
   - Installs all MCP dependencies
   - Run once to set up environment

### **Documentation**

6. **`QUICK_START_MCP.md`**
   - Complete quick start guide
   - Covers all installation scenarios
   - Troubleshooting guide

7. **`MCP_DIAGNOSTIC_GUIDE.md`**
   - In-depth diagnostic procedures
   - Advanced testing strategies
   - Integration with Claude Desktop

## 🚀 Quick Start (Choose Your Path)

### Path A: Test Without Node.js (Fastest)

```cmd
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
test_analyzer.bat
```

**What this does:**
- ✓ Uses your existing .venv
- ✓ Tests core analyzer functionality
- ✓ Shows if everything is working
- ✓ **No Node.js required**

**Expected output:**
```
======================================================================
  Billy Walters Sports Analyzer - Test Suite
======================================================================

[Step 1] Initializing Analyzer...
  Status..................................... ✓ SUCCESS
  Bankroll................................... $10,000
  Max Bet.................................... 3% of bankroll

[Step 2] Creating Test Game...
  Home Team.................................. Kansas City Chiefs
  Away Team.................................. Buffalo Bills
  Spread..................................... Kansas City Chiefs -2.5
  Total...................................... O/U 47.5
  Status..................................... ✓ Game created

[Step 3] Running Billy Walters Analysis...
  Predicted Spread........................... -3.2
  Market Spread.............................. -2.5
  Edge....................................... 0.70 points
  Confidence................................. 65.0%
  Status..................................... ✓ Analysis complete

[Step 4] Generating Betting Recommendation...
  Recommendation............................. ✗ PASS
  Reasoning.................................. Edge too small (0.70 points)
  Minimum Required........................... 1 point edge

======================================================================
  ✓ All Tests Passed!
======================================================================
```

### Path B: Install Node.js Then Use Inspector

1. **Install Node.js:**
   - Go to: https://nodejs.org/
   - Download LTS version
   - Install with defaults
   - Restart PowerShell

2. **Run Inspector:**
   ```powershell
   .\test_mcp_server.ps1
   ```

3. **Test in Browser:**
   - Inspector opens automatically
   - Test tools interactively
   - See real-time results

### Path C: Add to Claude Desktop Directly

Skip testing, go straight to Claude Desktop:

1. **Open config file:**
   - Location: `%APPDATA%\Claude\claude_desktop_config.json`
   - Create if doesn't exist

2. **Add this config:**
   ```json
   {
     "mcpServers": {
       "billy-walters-expert": {
         "command": "C:\\Users\\omall\\Documents\\python_projects\\billy-walters-sports-analyzer\\.venv\\Scripts\\python.exe",
         "args": [
           "C:\\Users\\omall\\Documents\\python_projects\\billy-walters-sports-analyzer\\.claude\\walters_mcp_server.py"
         ]
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Test it:**
   - Look for MCP server indicator
   - Try: "analyze the Chiefs vs Bills game"

## 🔧 Troubleshooting

### Issue: "Cannot find python"

**Solution:**
```powershell
# Use the venv Python directly
.\.venv\Scripts\python.exe test_analyzer_simple.py
```

### Issue: "No module named 'walters_analyzer'"

**Solution:**
```powershell
# Install the package
.\.venv\Scripts\python.exe -m pip install -e .
```

### Issue: "No module named 'fastmcp'"

**Solution:**
```powershell
# Install MCP dependencies
.\.venv\Scripts\python.exe -m pip install fastmcp pydantic aiohttp
```

### Issue: "npx not found"

**Solution:** Install Node.js from https://nodejs.org/ OR use Path A (test without Node.js)

### Issue: Test runs but shows errors

**Check logs:**
```powershell
Get-Content logs\mcp-server.log -Tail 50
```

## 📊 What Each Test Validates

### `test_analyzer.bat` validates:
- ✓ Python environment works
- ✓ Package imports correctly
- ✓ Core analyzer functionality
- ✓ Betting calculations
- ✓ Configuration loading

### `test_mcp_server.ps1` + Inspector validates:
- ✓ MCP protocol working
- ✓ Tool definitions correct
- ✓ Resource endpoints working
- ✓ Error handling
- ✓ Full integration

### Claude Desktop integration validates:
- ✓ Server starts automatically
- ✓ Tools available in Claude
- ✓ Natural language queries work
- ✓ Results formatted correctly

## 🎯 Recommended Workflow

1. **First:** Run `test_analyzer.bat`
   - Verifies core functionality
   - No extra dependencies

2. **Then:** Install Node.js (if you want Inspector)
   - Download from nodejs.org
   - Restart terminal

3. **Next:** Run `.\test_mcp_server.ps1`
   - Opens Inspector
   - Interactive testing

4. **Finally:** Add to Claude Desktop
   - Production use
   - Natural language interface

## 📝 Command Reference

### With Virtual Environment

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Run tests
python test_analyzer_simple.py
python diagnose_mcp.py

# Install dependencies
pip install -e ".[mcp]"

# Deactivate
deactivate
```

### Without Activating Venv

```powershell
# Run with venv Python directly
.\.venv\Scripts\python.exe test_analyzer_simple.py
.\.venv\Scripts\python.exe diagnose_mcp.py

# Install with venv pip
.\.venv\Scripts\python.exe -m pip install -e ".[mcp]"
```

### With MCP Inspector

```powershell
# Run Inspector (needs Node.js)
npx @modelcontextprotocol/inspector python .claude\walters_mcp_server.py

# Or use the helper script
.\test_mcp_server.ps1
```

## 🏆 Success Criteria

Your setup is working if:

- [ ] `test_analyzer.bat` completes without errors
- [ ] Shows "✓ All Tests Passed!"
- [ ] Generates betting recommendation
- [ ] No import errors in output

Optional (with Node.js):
- [ ] Inspector opens in browser
- [ ] Tools tab shows 3 tools
- [ ] Resources tab shows 2 resources
- [ ] Can execute tools successfully

## 📚 Additional Resources

- **Full diagnostic guide:** See `MCP_DIAGNOSTIC_GUIDE.md`
- **Quick start:** See `QUICK_START_MCP.md`
- **Project README:** See `README.md`
- **MCP Docs:** https://modelcontextprotocol.io

## 💡 Tips

1. **Start simple:** Use `test_analyzer.bat` first
2. **Check logs:** Always check `logs\mcp-server.log` if something fails
3. **Use venv:** Your `.venv` is already set up, use it
4. **Node.js optional:** Core testing doesn't need it
5. **Incremental:** Test each component before moving to next

## Need Help?

If you're stuck:
1. Run `test_analyzer.bat` and share the output
2. Check `logs\mcp-server.log` for errors
3. Verify `.env` file exists and has credentials
4. Make sure `.venv` is activated or use full path to Python
