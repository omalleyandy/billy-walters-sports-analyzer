# Billy Walters MCP Architecture - Quick Start

**Purpose**: Get started with MCP server architecture in 5 minutes

---

## What is MCP?

**Model Context Protocol (MCP)** is a standard for exposing tools, data, and workflows to AI applications like Claude.

**Think of it as**: APIs for AI

---

## Current State

Your project has:
- ✅ 1 basic MCP server (3 tools, 2 resources, 0 prompts)
- ✅ 27 slash commands (human workflow)
- ❌ Only 15% of capabilities exposed to AI

**Gap**: Your powerful betting analysis system isn't AI-accessible!

---

## Proposed Architecture

### Multi-Server Design

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Host (Claude)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  MCP Client  │  │  MCP Client  │  │  MCP Client  │     │
│  │      1       │  │      2       │  │      3       │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│                  Billy Walters MCP Servers                   │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Sports Data     │  │  Edge Detection  │                │
│  │  Server          │  │  Server          │                │
│  │                  │  │                  │                │
│  │  • Odds          │  │  • Analyze games │                │
│  │  • Schedules     │  │  • Find value    │                │
│  │  • Power ratings │  │  • Key numbers   │                │
│  │  • Team stats    │  │                  │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Weather &       │  │  Performance     │                │
│  │  Research Server │  │  Tracking Server │                │
│  │                  │  │                  │                │
│  │  • Weather       │  │  • CLV tracking  │                │
│  │  • Injuries      │  │  • ROI analysis  │                │
│  │  • Stadium info  │  │  • Bet history   │                │
│  └──────────────────┘  └──────────────────┘                │
└──────────────────────────────────────────────────────────────┘
```

### Server Responsibilities

| Server | What It Does | Example Tools |
|--------|--------------|---------------|
| **Sports Data** | Collects all betting data | `collect_week_data`, `scrape_odds`, `get_schedule` |
| **Edge Detection** | Finds betting value | `detect_edges`, `analyze_matchup`, `compare_lines` |
| **Weather/Research** | Contextual analysis | `check_weather`, `get_injuries`, `stadium_info` |
| **Performance** | Tracks results | `track_clv`, `calculate_roi`, `log_bet` |

---

## MCP Primitives Explained

### 1. Tools (Model-Controlled)
**What**: Functions the AI can call
**Who decides**: The AI model
**Example**: `analyze_game("Bills", "Chiefs", spread=-3.5)`

### 2. Resources (Application-Controlled)
**What**: Data sources the AI can read
**Who decides**: The application (Claude Desktop/Code)
**Example**: `sports://odds/nfl/11` → Returns Week 11 NFL odds

### 3. Prompts (User-Controlled)
**What**: Reusable workflow templates
**Who decides**: The user
**Example**: "Use collect-weekly-data prompt for NFL Week 11"

---

## Real-World Example

**User asks**: "What's the best NFL bet this week?"

### How AI Uses MCP Servers

```
1. LLM discovers tools:
   → Sports Data Server: "I can collect odds"
   → Edge Detection Server: "I can find edges"

2. LLM collects data:
   → collect_week_data(week=11, league="nfl")
   ✅ Collected odds, schedules, power ratings

3. LLM analyzes:
   → detect_spread_edges(week=11, min_edge=1.0)
   ✅ Found 4 games with edges

4. LLM enhances:
   → check_weather("Buffalo", "2025-11-21 20:15")
   ✅ Cold & windy → UNDER factor

5. LLM recommends:
   → "Best bet: Bills +3.5 (1.4 edge, moderate confidence)"
```

**Result**: AI autonomously performed complete Billy Walters workflow!

---

## Phase 1: Quick Win (Start Here)

**Goal**: Enhance existing MCP server with data collection tools

**Time**: 4-6 hours
**Risk**: Low (no breaking changes)
**Impact**: High (expose 50% of workflow to AI)

### What You're Adding

```
Before Phase 1:
  Tools: 3
  Resources: 2
  Prompts: 0

After Phase 1:
  Tools: 10 (+7 new)
  Resources: 7 (+5 new)
  Prompts: 3 (+3 new)
```

### Implementation Steps

1. **Read the implementation guide**: `docs/MCP_PHASE1_IMPLEMENTATION.md`

2. **Add 7 new tools** to `walters_mcp_server.py`:
   - `collect_week_data` (Billy Walters complete workflow)
   - `scrape_massey_ratings` (power ratings)
   - `scrape_overtime_odds` (odds from Overtime.ag)
   - `get_espn_team_stats` (team statistics)
   - `get_espn_schedule` (game schedules)
   - `get_current_nfl_week` (week calculation)
   - `validate_collected_data` (data quality checks)

3. **Add 5 new resources**:
   - `sports://odds/{league}/{week}`
   - `sports://schedule/{league}/{week}`
   - `sports://teams/{league}/stats`
   - `sports://power-ratings/{league}`
   - `sports://data-status/{week}`

4. **Add 3 prompts**:
   - `collect-weekly-data` (complete collection workflow)
   - `refresh-odds` (quick odds update)
   - `prepare-analysis` (prep for edge detection)

5. **Test with MCP Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector uv run python .claude/walters_mcp_server.py
   ```

6. **Test with Claude Desktop**:
   - Update `~/.claude/claude_desktop_config.json`
   - Restart Claude Desktop
   - Try: "Collect NFL Week 11 data"

---

## Key Benefits

### For You (Developer)
- ✅ **Maintain existing workflow**: All slash commands still work
- ✅ **Progressive enhancement**: Add MCP without disruption
- ✅ **Better debugging**: MCP Inspector shows exactly what's happening
- ✅ **Standardized**: Use industry-standard protocol

### For AI (Claude)
- ✅ **Autonomous execution**: AI can run complete workflows
- ✅ **Context awareness**: Direct access to data (power ratings, odds)
- ✅ **Tool composition**: Combine multiple servers seamlessly
- ✅ **Real-time data**: Always fresh information

### For Workflow
- ✅ **Faster analysis**: AI does data collection automatically
- ✅ **Better decisions**: AI considers more factors (weather, injuries, trends)
- ✅ **Reduced errors**: Standardized tool interfaces
- ✅ **Scalable**: Easy to add new capabilities

---

## Migration Path

### Phase 1 (Week 1): Foundation ← START HERE
- Enhance existing server
- Add data collection tools
- **Result**: 50% of workflow AI-accessible

### Phase 2 (Week 2): Modularization
- Split into specialized servers
- **Result**: Clean separation of concerns

### Phase 3 (Week 3): Contextual Intelligence
- Add weather & research server
- **Result**: Complete Billy Walters methodology

### Phase 4 (Week 4): Production Ready
- Optimization & monitoring
- **Result**: Production deployment

---

## Success Metrics

After Phase 1, you should be able to:

1. ✅ Ask Claude: "Collect NFL Week 11 data"
   → AI automatically runs complete collection workflow

2. ✅ Ask Claude: "What's the current power rating for Buffalo?"
   → AI reads `sports://power-ratings/nfl` resource

3. ✅ Ask Claude: "Use the collect-weekly-data prompt"
   → AI executes structured workflow with validation

4. ✅ Ask Claude: "Show me all available betting tools"
   → AI lists all 10 tools with descriptions

5. ✅ Ask Claude: "What data do we have for Week 11?"
   → AI reads `sports://data-status/11` and reports quality

---

## Next Steps

1. **Review architecture**: Read `docs/MCP_ARCHITECTURE.md`
2. **Start Phase 1**: Follow `docs/MCP_PHASE1_IMPLEMENTATION.md`
3. **Test incrementally**: Use MCP Inspector after each tool
4. **Document issues**: Use `/document-lesson` for problems
5. **Iterate**: Gather feedback and improve

---

## Questions?

### "Why multiple servers?"
**Answer**: Separation of concerns. Each server focuses on one domain (data, analysis, weather, tracking). Easier to develop, test, and maintain independently.

### "Can I keep using slash commands?"
**Answer**: Yes! MCP is additive. All existing slash commands continue working. MCP just makes them AI-accessible too.

### "What if a tool fails?"
**Answer**: Each tool returns `{"error": "..."}` on failure. AI can retry, use fallback data, or ask user for help.

### "How do resources differ from tools?"
**Answer**:
- **Tools**: AI calls when it needs to DO something (collect data, analyze game)
- **Resources**: AI reads when it needs to KNOW something (power ratings, odds)

### "Is this compatible with Claude Code?"
**Answer**: Yes! MCP works with both Claude Desktop and Claude Code. Same server, different hosts.

---

## Resources

- **Full Architecture**: `docs/MCP_ARCHITECTURE.md`
- **Phase 1 Guide**: `docs/MCP_PHASE1_IMPLEMENTATION.md`
- **MCP Spec**: https://modelcontextprotocol.io/specification
- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector
- **FastMCP Docs**: https://github.com/jlowin/fastmcp

---

**Ready to start?** → Open `docs/MCP_PHASE1_IMPLEMENTATION.md`

**Questions?** → Ask in conversation or check `/lessons`

**Status**: Architecture approved, ready for Phase 1 implementation
