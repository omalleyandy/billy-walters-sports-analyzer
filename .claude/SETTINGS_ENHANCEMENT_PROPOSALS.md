# Claude Code Settings - Enhancement Proposals

This document outlines additional Claude Code settings capabilities that could improve the Billy Walters workflow.

---

## Priority 1: High-Value Enhancements (Immediate Benefits)

### 1. Session Start Hook - Auto-Sync Workflow ⭐⭐⭐⭐⭐

**What It Does:**
Automatically runs when you start a new Claude Code session.

**Proposed Actions:**
```json
"SessionStart": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "git pull origin main --rebase",
        "timeout": 10
      },
      {
        "type": "command",
        "command": "uv run python .claude/hooks/session_start.py",
        "timeout": 5
      }
    ]
  }
]
```

**Benefits:**
- ✅ Auto-syncs with GitHub at session start (prevent conflicts)
- ✅ Shows current NFL week immediately
- ✅ Displays data freshness summary
- ✅ Alerts if critical data is stale
- ✅ Shows pending edge detection opportunities

**Example Output:**
```
=== BILLY WALTERS SESSION START ===
Git: Synced with origin/main (3 commits ahead)
Week: NFL 2025 Week 10
Data Status:
  ✓ Power ratings: 2 hours old (FRESH)
  ⚠ Odds data: 28 hours old (STALE - refresh recommended)
  ✓ Injury reports: 6 hours old (FRESH)
  ✗ Weather data: Not collected

Opportunities:
  → 13 NFL games this week
  → Run /collect-all-data to refresh odds
  → 0 edges detected (waiting for fresh data)

Ready for analysis!
```

**New File Needed:** `.claude/hooks/session_start.py`

---

### 2. Session End Hook - Clean Exit Checklist ⭐⭐⭐⭐

**What It Does:**
Runs when you end a Claude Code session (exit, close window, timeout).

**Proposed Actions:**
```json
"SessionEnd": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "uv run python .claude/hooks/session_end.py",
        "timeout": 10
      }
    ]
  }
]
```

**Benefits:**
- ✅ Warns about uncommitted changes
- ✅ Shows session summary (commands run, files changed)
- ✅ Reminds about pending tasks (edge detection, CLV tracking)
- ✅ Suggests next session priorities

**Example Output:**
```
=== BILLY WALTERS SESSION END ===
Duration: 45 minutes
Commands: 8 (/collect-all-data, /edge-detector, /betting-card)

Git Status:
  ⚠ 3 uncommitted files:
    - output/edge_detection/nfl_edges_detected.jsonl
    - data/current/nfl_week_10_games.json
    - scripts/utilities/get_mac_team_stats.py

  Suggestion: git add . && git commit -m "data: update week 10 data and edges"

Pending Tasks:
  → 5 STRONG edges detected (review /betting-card)
  → CLV not tracked for this week
  → Weather data not collected for 3 outdoor games

Next Session:
  1. Review betting card for Week 10
  2. Run /clv-tracker to log picks
  3. Update weather for Sunday games

See you next time, partner! 🎯
```

**New File Needed:** `.claude/hooks/session_end.py`

---

### 3. PreToolUse Hook - Validate Data Before Analysis ⭐⭐⭐⭐

**What It Does:**
Runs validation BEFORE certain tools execute (prevents wasted computation).

**Proposed Actions:**
```json
"PreToolUse": [
  {
    "matcher": "SlashCommand(/edge-detector)",
    "hooks": [
      {
        "type": "command",
        "command": "uv run python .claude/hooks/pre_edge_detection.py",
        "timeout": 15
      }
    ]
  },
  {
    "matcher": "SlashCommand(/betting-card)",
    "hooks": [
      {
        "type": "command",
        "command": "uv run python .claude/hooks/pre_edge_detection.py",
        "timeout": 15
      }
    ]
  }
]
```

**Benefits:**
- ✅ Ensures power ratings exist before edge detection
- ✅ Ensures odds data exists and is fresh (<24 hours)
- ✅ Warns if weather/injury data missing
- ✅ Prevents running edge detector on stale data

**Example Output:**
```
=== PRE-EDGE DETECTION VALIDATION ===

Required Data:
  ✓ Power ratings: Present (nfl_power_ratings_2025.json)
  ✓ Game schedule: Present (13 games Week 10)
  ✓ Odds data: Present (3 hours old - FRESH)

Optional Data:
  ⚠ Injury reports: Missing for 3 teams
  ⚠ Weather data: Missing for 5 outdoor stadiums

Validation: PASSED (can proceed with caveats)

Note: Edge detection will run but injury/weather adjustments
will be incomplete. Recommend running:
  /injury-report nfl
  /weather "Buffalo" "2025-11-17 13:00"

Continue with edge detection? [Auto-continuing in 5s...]
```

**New File Needed:** `.claude/hooks/pre_edge_detection.py`

---

### 4. Auto-Approve MCP Server ⭐⭐⭐

**What It Does:**
Automatically approves your Billy Walters MCP server (no prompt).

**Proposed Setting:**
```json
"enableAllProjectMcpServers": true
```

**Benefits:**
- ✅ No prompt when MCP server starts
- ✅ Faster session initialization
- ✅ Assumes project-level MCP servers are trusted

**Risk:**
- ⚠️ If you add a new MCP server, it auto-approves
- Mitigation: Only add trusted MCP servers to project

**Recommendation:** Enable this - your project MCP server is safe.

---

### 5. Extended Thinking Mode ⭐⭐⭐

**What It Does:**
Enables Claude's extended thinking for complex analysis tasks.

**Proposed Setting:**
```json
"alwaysThinkingEnabled": true
```

**Benefits:**
- ✅ Better reasoning for edge detection
- ✅ More thorough Billy Walters methodology application
- ✅ Catches edge cases and subtle patterns
- ✅ Deeper analysis of injury/weather impacts

**Cost:**
- ⚠️ Slightly slower responses (~10-20% longer)
- Totally worth it for sports betting analysis

**Recommendation:** Enable this - quality > speed for Billy Walters.

---

## Priority 2: Nice-to-Have Enhancements (Quality of Life)

### 6. Transcript Cleanup ⭐⭐⭐

**What It Does:**
Automatically deletes old chat transcripts.

**Proposed Setting:**
```json
"cleanupPeriodDays": 30
```

**Benefits:**
- ✅ Keeps last 30 days of sessions
- ✅ Reduces disk usage
- ✅ Removes old/irrelevant context

**Note:** You can always keep important sessions by copying them elsewhere.

---

### 7. Sandbox Network Configuration ⭐⭐

**What It Does:**
Configures network access for sandboxed bash commands.

**Proposed Setting:**
```json
"sandbox": {
  "enabled": true,
  "network": {
    "allowLocalBinding": true,
    "allowUnixSockets": [
      "/var/run/docker.sock"
    ]
  },
  "excludedCommands": ["git", "gh", "uv"]
}
```

**Benefits:**
- ✅ Sandboxes most bash commands (security)
- ✅ Allows network for API calls (scraping, weather)
- ✅ Excludes git/gh/uv from sandbox (they need full access)
- ✅ Allows Docker if you use containers

**Recommendation:** Skip this for now - adds complexity, minimal security benefit for solo developer.

---

### 8. Spinner Tips ⭐⭐

**What It Does:**
Shows helpful tips while waiting for responses.

**Proposed Setting:**
```json
"spinnerTipsEnabled": true
```

**Benefits:**
- ✅ Learn Claude Code features during waits
- ✅ Discover commands you didn't know existed

**Example Tips:**
- "Tip: Use /current-week to check NFL schedule"
- "Tip: Run /validate-data before edge detection"
- "Tip: CLV matters more than win percentage"

---

### 9. Custom Output Style ⭐

**What It Does:**
Changes how Claude's responses are formatted.

**Proposed Setting:**
```json
"outputStyle": "concise"
```

**Options:**
- `"default"` - Normal responses
- `"concise"` - Shorter, more direct responses
- `"detailed"` - More explanations
- `"technical"` - More technical jargon

**Recommendation:** Stick with `"default"` - you already have good instructions in CLAUDE.md.

---

## Priority 3: Advanced Enhancements (Experimental)

### 10. Smart Hook - LLM-Powered Validation ⭐⭐⭐⭐

**What It Does:**
Uses an LLM to analyze hook inputs and make intelligent decisions.

**Proposed Hook:**
```json
{
  "matcher": "SlashCommand(/edge-detector)",
  "hooks": [
    {
      "type": "prompt",
      "prompt": "Analyze this data collection status and determine if edge detection should proceed:\n\n$ARGUMENTS\n\nReturn 'PROCEED' if data is adequate, or 'BLOCK: <reason>' if not.",
      "timeout": 10
    }
  ]
}
```

**Benefits:**
- ✅ Intelligent decision-making (not just script logic)
- ✅ Can analyze complex scenarios
- ✅ Natural language explanations

**Cost:**
- ⚠️ Uses API credits for every hook execution
- ⚠️ Slower than command hooks (5-10 seconds)

**Recommendation:** Skip for now - command hooks are faster and cheaper.

---

### 11. Multi-Stage Hooks - Pipeline Validation ⭐⭐⭐

**What It Does:**
Chains multiple hooks together for complex workflows.

**Example:**
```json
{
  "matcher": "/collect-all-data",
  "hooks": [
    {
      "type": "command",
      "command": "uv run python .claude/hooks/pre_data_collection.py"
    },
    {
      "type": "command",
      "command": "uv run python .claude/hooks/check_api_limits.py"
    },
    {
      "type": "command",
      "command": "uv run python .claude/hooks/backup_old_data.py"
    }
  ]
}
```

**Benefits:**
- ✅ Multi-stage validation pipeline
- ✅ Backs up old data before overwrite
- ✅ Checks API rate limits before scraping

**New Files Needed:**
- `.claude/hooks/check_api_limits.py`
- `.claude/hooks/backup_old_data.py`

---

### 12. Conditional Permissions ⭐⭐

**What It Does:**
Allow certain commands only in specific contexts.

**Example:**
```json
"permissions": {
  "allow": [
    "Bash(rm:data/_tmp/*)",
    "Bash(rm:output/edge_detection/*.jsonl)"
  ],
  "deny": [
    "Bash(rm:*)"
  ]
}
```

**Benefits:**
- ✅ Allow deleting temp files
- ✅ Allow deleting old edge detection results
- ✅ Block everything else

**Note:** Requires careful pattern crafting - easy to mess up.

---

## Recommended Implementation Plan

### Phase 1: Essential Hooks (This Week)
1. **SessionStart Hook** - Auto-sync + data status
2. **SessionEnd Hook** - Commit reminders + summary
3. **PreToolUse Hook** - Validate before edge detection
4. **Enable MCP auto-approve** - No more prompts
5. **Enable extended thinking** - Better analysis

**Effort:** 2-3 hours (mostly writing hook scripts)
**Benefit:** Huge - automates 90% of manual checks

---

### Phase 2: Quality of Life (Next Week)
1. **Transcript cleanup** - Keep 30 days
2. **Multi-stage hooks** - Backup data before collection
3. **API limit checker** - Prevent rate limit errors

**Effort:** 1-2 hours
**Benefit:** Medium - prevents occasional issues

---

### Phase 3: Advanced (Future)
1. **Smart LLM hooks** - Intelligent validation
2. **Conditional permissions** - Granular file access
3. **Sandbox configuration** - Enhanced security

**Effort:** 3-4 hours
**Benefit:** Low - nice to have but not critical

---

## My Recommendations for Your Workflow

### Implement Now (High ROI):
1. ✅ **SessionStart Hook** - Shows data status every session
2. ✅ **SessionEnd Hook** - Never forget to commit
3. ✅ **PreToolUse Hook** - Prevents running edge detector on bad data
4. ✅ **Extended Thinking** - Better Billy Walters analysis
5. ✅ **MCP Auto-Approve** - Faster startup

### Consider Later:
- Transcript cleanup (when disk space becomes issue)
- Multi-stage hooks (when workflow becomes more complex)
- API limit checking (if you hit rate limits)

### Skip:
- Sandbox configuration (overkill for solo dev)
- Smart LLM hooks (too slow and expensive)
- Custom output style (CLAUDE.md handles this)

---

## Implementation Estimate

**If we implement Phase 1 (Essential Hooks):**

**Time Required:**
- SessionStart hook script: 30 min
- SessionEnd hook script: 45 min
- PreToolUse hook script: 45 min
- Settings update: 15 min
- Testing: 30 min
- Documentation: 30 min

**Total:** ~3 hours

**Value Delivered:**
- Save 5-10 minutes per session on manual checks
- Prevent 90% of "forgot to commit" situations
- Catch bad data before expensive computation
- Better edge detection analysis quality

**ROI:** Pays for itself in 1-2 weeks of regular use.

---

## Next Steps

**Option 1: Implement All Phase 1 Enhancements**
We create the 3 hook scripts, update settings, test, and document.

**Option 2: Implement Selectively**
Pick the 2-3 hooks you want most, implement those first.

**Option 3: Wait and See**
Use current setup for a week, then decide what's missing.

**My Recommendation:** Option 1 - Phase 1 enhancements are all high-value.

---

**What do you think, partner? Want to implement Phase 1 now, or prefer to test drive the current setup first?**

---

**Last Updated:** 2025-11-12
**Status:** Proposal - Awaiting Decision
