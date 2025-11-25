# Documentation Audit & Migration Plan

**Date**: 2025-11-24
**Status**: Analysis Complete - Ready for Implementation
**Total Files Analyzed**: 60 markdown files across root, `.github/`, and `.claude/`

---

## Executive Summary

Your documentation is fragmented across multiple locations with significant redundancy and outdated session summaries. This audit categorizes all 60 files and provides a migration strategy.

**Key Findings**:
- **58 files** need organization (96% of total)
- **35+ session summaries** that should be archived
- **4 "START_HERE"** variants creating confusion
- **6 "QUICK_START"** variants with overlapping content
- **14 strategic files** that belong in `docs/`
- **4 `.github/` guides** that are well-placed
- **`.claude/` files** are well-organized

---

## File Categorization

### CATEGORY A: CORE STRATEGIC FILES (Keep in Root, Update for _INDEX.md)

These define the project and should stay at root level but be referenced in `_INDEX.md`:

| File | Purpose | Status | Action |
|------|---------|--------|--------|
| `CLAUDE.md` | Project development guidelines | ✅ Current | Reference in _INDEX.md "Getting Started" |
| `README.md` | Project overview | ✅ Current | Ensure links to _INDEX.md |
| `LESSONS_LEARNED.md` | Historical issues & solutions | ✅ Current | Reference in _INDEX.md troubleshooting |

**Action**: These 3 files stay at root. Add a "See Also" section in _INDEX.md linking to them.

---

### CATEGORY B: QUICK START FILES (Consolidate into 1, Archive Others)

**Problem**: 4 "START_HERE" files + 6 "QUICK_START" variants = 10 entry points

| File | Content | Status | Action |
|------|---------|--------|--------|
| `START_HERE.md` | ❓ | Analyze | Check which is most current |
| `START_HERE_NOW.md` | ❓ | Analyze | Check which is most current |
| `START_HERE_NEXT_SESSION.md` | ❓ | Analyze | Check which is most current |
| `QUICK_START.md` | ❓ | Analyze | Check which is most current |
| `QUICK_START_MCP.md` | ❓ | Analyze | Check which is most current |
| `QUICK_START_WEEK12.md` | ❓ | Analyze | Check which is most current |
| `WEDNESDAY_QUICK_START.md` | ❓ | Analyze | Check which is most current |
| `WINDOWS_QUICK_START_TASK_2_2.md` | ❓ | Analyze | Check which is most current |

**Recommendation**:
- Keep: ONE "START_HERE.md" (consolidate best content)
- Move to `docs/guides/`: `QUICK_START_MCP.md`, `WINDOWS_QUICK_START_TASK_2_2.md`
- Archive: All others to `docs/archive/old_quickstart_variants/`

---

### CATEGORY C: SESSION SUMMARIES & MEMORY FILES (Archive)

**Problem**: 15+ session summary files cluttering root

| Files | Type | Action |
|-------|------|--------|
| `SESSION_*.md` (6 files) | Session notes | Archive to `docs/archive/sessions/` |
| `SESSION_MEMORY_2025_11_24.md` | Latest memory | Move to `docs/reports/current_session.md` or archive |
| `PROJECT_MEMORY.md` | Project memory | Consider moving to `.claude/memory/` |
| `PROJECT_CONTINUITY_WEEK12.md` | Week-specific memory | Archive |

**Recommendation**: Create `docs/archive/sessions/` and move all dated session files there.

---

### CATEGORY D: PHASE/IMPLEMENTATION SUMMARIES (Archive or Integrate)

**Problem**: 8 files documenting completed phases

| File | Phase | Status | Action |
|------|-------|--------|--------|
| `PHASE4_COMPLETE_SUMMARY.md` | Phase 4 completion | Completed | Archive to `docs/archive/phases/` |
| `PHASE4_VISUAL_REFERENCE.md` | Phase 4 visual ref | Completed | Archive to `docs/archive/phases/` |
| `CLV_PHASE3_COMPLETION.md` | CLV Phase 3 | Completed | Archive to `docs/archive/phases/` |
| `SESSION_SFACTOR_IMPLEMENTATION_COMPLETE.md` | SFACTOR impl | Completed | Archive to `docs/archive/phases/` |
| `ESPN_PHASE1_EXECUTION_SUMMARY.md` | ESPN Phase 1 | Completed | Archive to `docs/archive/phases/` |
| `EMOJI_FIX_SUMMARY.md` | Bug fix | Completed | Archive to `docs/archive/fixes/` |
| `CODE_REVIEW_SUMMARY.md` | Review doc | Old | Archive to `docs/archive/reviews/` |
| `COMPLETE_SYSTEM_READY.md` | System status | Old | Archive to `docs/archive/status/` |

**Recommendation**: Archive all phase summaries to preserve history but clean root directory.

---

### CATEGORY E: TECHNICAL GUIDES (Integrate into docs/guides/)

**Problem**: 7 technical guides at root that should be in organized location

| File | Topic | Current | Action |
|------|-------|---------|--------|
| `TESTING_GUIDE.md` | Testing framework | ✅ | Move to `docs/guides/TESTING_GUIDE.md` |
| `WEB_FETCH_CLIENT_README.md` | Web client docs | ✅ | Move to `docs/api/web_fetch_client.md` |
| `MCP_DIAGNOSTIC_GUIDE.md` | MCP troubleshooting | ✅ | Move to `docs/guides/mcp_diagnostic_guide.md` |
| `LIVE_ODDS_SCRAPER_GUIDE.md` | Scraper guide | ✅ | Move to `docs/guides/LIVE_ODDS_SCRAPER_GUIDE.md` |
| `CHECK_OVERTIME_EDGES_GUIDE.md` | Overtime guide | ✅ | Move to `docs/guides/CHECK_OVERTIME_EDGES_GUIDE.md` |
| `MONITOR_SETUP_GUIDE.md` | Monitoring | ✅ | Move to `docs/guides/MONITOR_SETUP_GUIDE.md` |
| `MONITORING_REFERENCE.md` | Monitoring ref | ✅ | Move to `docs/guides/monitoring_reference.md` |

**Recommendation**: Move all 7 to appropriate `docs/guides/` subdirectories and update cross-references.

---

### CATEGORY F: WORKFLOW & SCHEDULING GUIDES (Integrate into docs/)

**Problem**: 5 workflow files scattered

| File | Purpose | Action |
|------|---------|--------|
| `WEEK12_DATA_COLLECTION_GUIDE.md` | Week-specific workflow | Archive to `docs/archive/week_specific/` |
| `WEEK12_QUICK_COMMANDS.md` | Week-specific commands | Archive to `docs/archive/week_specific/` |
| `WEEK12_BETTING_CARD.md` | Week-specific results | Archive to `docs/archive/week_specific/` |
| `WEEK13_NCAAF_DATA_UPDATE.md` | Week-specific update | Archive to `docs/archive/week_specific/` |
| `WEEK12_NFL_DATA_UPDATE.md` | Week-specific update | Archive to `docs/archive/week_specific/` |
| `WEEKLY_TRACKING_IMPLEMENTATION.md` | Weekly workflow impl | Consolidate into `docs/guides/weekly_workflow.md` |
| `WEEK12_CLV_MONITOR_GUIDE.md` | CLV monitoring guide | Move to `docs/guides/clv_monitoring_guide.md` |
| `PROJECT_INSTRUCTIONS_*.md` (3 versions) | Project instructions | Archive or consolidate with CLAUDE.md |

---

### CATEGORY G: ANALYSIS & REFERENCE DOCUMENTS (Integrate or Archive)

**Problem**: 6 reference/analysis files with unclear ownership

| File | Topic | Status | Action |
|------|-------|--------|--------|
| `HTML_STRUCTURE_ANALYSIS.md` | HTML parsing reference | Technical ref | Move to `docs/technical/html_structure_analysis.md` |
| `DYNAMIC_WEEK_TRACKING_SUMMARY.md` | Week tracking design | Design doc | Move to `docs/architecture/dynamic_week_tracking.md` |
| `FIX_SUMMARY_AND_FILES.md` | Bug fix summary | Old | Archive to `docs/archive/fixes/` |
| `CRITICAL_QUESTIONS.md` | Q&A document | Context | Archive to `docs/archive/q_and_a/` |
| `CHANGES_LOG.md` | Change log | Log file | Archive to `docs/archive/` and use git log instead |
| `maction_predictions_summary.md` | Predictions summary | Unknown | Archive to `docs/archive/` |

---

### CATEGORY H: CONFIGURATION & SETUP (Integrate or Archive)

| File | Topic | Status | Action |
|------|-------|--------|--------|
| `CLAUDE_CONFIG.md` | Claude configuration | Old | Archive - superseded by CLAUDE.md |
| `POWERSHELL_COMMANDS.md` | PowerShell ref | Utility | Move to `docs/utilities/powershell_reference.md` |
| `TASK_2_2_WINDOWS_READY.md` | Windows setup task | Old | Archive to `docs/archive/setup/` |
| `PROJECT_INSTRUCTIONS_V2.md` | Old instructions | Superseded | Archive to `docs/archive/versions/` |
| `PROJECT_INSTRUCTIONS_V3.md` | Old instructions | Superseded | Archive to `docs/archive/versions/` |

---

### CATEGORY I: WELL-ORGANIZED LOCATIONS (No Changes Needed)

These are already in proper locations:

#### `.github/` Directory (4 files - ✅ Well-placed)
- `CI_CD.md` - CI/CD technical details
- `BRANCH_PROTECTION_SETUP.md` - Branch protection guide
- `GIT_WORKFLOW_GUIDE.md` - Git workflow
- `PR_WORKFLOW.md` - PR workflow

**Action**: No changes. Reference these in `docs/_INDEX.md` under "Development" section.

#### `.claude/` Directory (35+ files - ✅ Well-organized)
- `commands/` - Slash commands documentation (18 files)
- `hooks/` - Automation hooks documentation (README + hooks)
- `memory/` - Session memory files
- `AGENT_WORKFLOWS.md` - Agent automation guide
- `MCP_SETUP_GUIDE.md` - MCP configuration
- `SETTINGS_GUIDE.md` - Settings documentation

**Action**: No changes. Already well-organized. Add summary in `docs/_INDEX.md`.

---

## Migration Plan

### Phase 1: Create Archive Structure (5 min)

```bash
# Create archive subdirectories
mkdir -p docs/archive/{sessions,phases,fixes,reviews,status,week_specific,setup,versions,q_and_a}
mkdir -p docs/utilities
mkdir -p docs/technical
mkdir -p docs/architecture
```

### Phase 2: Move Technical Guides (10 min)

**Move these files to `docs/guides/`**:
```bash
# From root to docs/guides/
move TESTING_GUIDE.md → docs/guides/
move MCP_DIAGNOSTIC_GUIDE.md → docs/guides/
move LIVE_ODDS_SCRAPER_GUIDE.md → docs/guides/
move CHECK_OVERTIME_EDGES_GUIDE.md → docs/guides/
move MONITOR_SETUP_GUIDE.md → docs/guides/
move MONITORING_REFERENCE.md → docs/guides/
move WEEK12_CLV_MONITOR_GUIDE.md → docs/guides/clv_monitoring_guide.md
move WEEKLY_TRACKING_IMPLEMENTATION.md → docs/guides/weekly_workflow.md
```

**Move to specialized docs/**:
```bash
move WEB_FETCH_CLIENT_README.md → docs/api/web_fetch_client.md
move HTML_STRUCTURE_ANALYSIS.md → docs/technical/
move DYNAMIC_WEEK_TRACKING_SUMMARY.md → docs/architecture/
move POWERSHELL_COMMANDS.md → docs/utilities/
```

### Phase 3: Archive Completed Work (10 min)

**Archive session files**:
```bash
# All SESSION_*.md files
move SESSION_*.md → docs/archive/sessions/
move PROJECT_CONTINUITY_WEEK12.md → docs/archive/sessions/
```

**Archive phase completions**:
```bash
move PHASE*.md → docs/archive/phases/
move *_PHASE*.md → docs/archive/phases/
move *COMPLETION*.md → docs/archive/phases/
move EMOJI_FIX_SUMMARY.md → docs/archive/fixes/
move CODE_REVIEW_SUMMARY.md → docs/archive/reviews/
move COMPLETE_SYSTEM_READY.md → docs/archive/status/
move SYSTEM_STATUS_*.md → docs/archive/status/
```

**Archive week-specific guides**:
```bash
move WEEK*.md → docs/archive/week_specific/
```

**Archive old versions**:
```bash
move PROJECT_INSTRUCTIONS_V*.md → docs/archive/versions/
move CLAUDE_CONFIG.md → docs/archive/versions/
move TASK_2_2_WINDOWS_READY.md → docs/archive/setup/
```

**Archive miscellaneous**:
```bash
move FIX_SUMMARY_AND_FILES.md → docs/archive/fixes/
move CRITICAL_QUESTIONS.md → docs/archive/q_and_a/
move CHANGES_LOG.md → docs/archive/
move maction_predictions_summary.md → docs/archive/
move PROJECT_MEMORY.md → .claude/memory/
move SESSION_MEMORY_2025_11_24.md → .claude/memory/ or docs/archive/
```

### Phase 4: Consolidate Quick Start (5 min)

**Option A - Keep latest START_HERE.md, archive others:**
```bash
# Archive old variants
move START_HERE_NOW.md → docs/archive/old_quickstart_variants/
move START_HERE_NEXT_SESSION.md → docs/archive/old_quickstart_variants/
move QUICK_START.md → docs/archive/old_quickstart_variants/
move QUICK_START_MCP.md → docs/guides/ (rename to mcp_quickstart.md)
move QUICK_START_WEEK12.md → docs/archive/week_specific/
move WEDNESDAY_QUICK_START.md → docs/guides/
move WINDOWS_QUICK_START_TASK_2_2.md → docs/guides/windows_setup.md
```

### Phase 5: Update _INDEX.md (15 min)

Add new sections:
- Link to `.github/` guides
- Link to `.claude/` documentation
- Link to `docs/guides/` (all categories)
- Link to CLAUDE.md, README.md, LESSONS_LEARNED.md
- Remove/consolidate duplicate "Quick Start" entries

---

## Final Root Directory Structure

**After Migration** (only essential files at root):

```
billy-walters-sports-analyzer/
├── README.md                    ← Project overview
├── CLAUDE.md                    ← Development guidelines
├── LESSONS_LEARNED.md           ← Troubleshooting guide
├── START_HERE.md                ← Single entry point (updated)
├── .env.example
├── pyproject.toml
├── src/
├── scripts/
├── tests/
├── docs/                        ← All organized documentation
│   ├── _INDEX.md                ← Master index
│   ├── guides/                  ← How-to guides (15+ files)
│   ├── api/                     ← API documentation
│   ├── architecture/            ← System design docs
│   ├── technical/               ← Technical references
│   ├── utilities/               ← Utility references
│   ├── reports/                 ← Analysis reports
│   ├── data_sources/            ← Data schema docs
│   └── archive/                 ← Historical documentation
│       ├── sessions/            ← Session summaries
│       ├── phases/              ← Completed phases
│       ├── week_specific/       ← Week-specific guides
│       ├── versions/            ← Old versions
│       ├── fixes/               ← Bug fix summaries
│       ├── reviews/             ← Code reviews
│       ├── status/              ← System status files
│       ├── q_and_a/             ← Q&A documents
│       └── old_quickstart_variants/  ← Old start guides
├── .github/                     ← CI/CD & workflow docs
└── .claude/                     ← Agent configuration
```

---

## _INDEX.md Updates

### Add This Section to _INDEX.md:

```markdown
## Operational Guides (Detailed Documentation)

### Getting Started & Setup
- [Windows Setup Guide](guides/windows_setup.md)
- [Quick Start - MCP](guides/mcp_quickstart.md)
- [Database Setup](DATABASE_SETUP_GUIDE.md)

### Development
- [Git Workflow Guide](.github/GIT_WORKFLOW_GUIDE.md)
- [PR Workflow](.github/PR_WORKFLOW_GUIDE.md)
- [CI/CD Details](.github/CI_CD.md)
- [Testing Guide](guides/TESTING_GUIDE.md)

### Data Collection & Analysis
- [Live Odds Scraper](guides/LIVE_ODDS_SCRAPER_GUIDE.md)
- [Overtime Edge Detection](guides/CHECK_OVERTIME_EDGES_GUIDE.md)
- [Weekly Workflow](guides/weekly_workflow.md)
- [CLV Monitoring](guides/clv_monitoring_guide.md)

### Troubleshooting & Utilities
- [MCP Diagnostic Guide](guides/mcp_diagnostic_guide.md)
- [Monitoring Setup](guides/MONITOR_SETUP_GUIDE.md)
- [PowerShell Reference](utilities/powershell_reference.md)
- [Common Issues](../LESSONS_LEARNED.md)

### Agent & Automation
- [Agent Workflows](.claude/AGENT_WORKFLOWS.md)
- [Automation Hooks](.claude/hooks/)
- [Slash Commands](.claude/commands/)

### Historical Documentation
- [Session Summaries](archive/sessions/)
- [Completed Phases](archive/phases/)
- [Old Versions](archive/versions/)
```

---

## Recommended Actions (Priority Order)

### HIGH PRIORITY - Do This Today (30 min)
1. **Identify** which START_HERE file is most current (check git history)
2. **Create** archive directory structure
3. **Move** all session files to `docs/archive/sessions/`
4. **Move** all week-specific files to `docs/archive/week_specific/`
5. **Move** all phase completion files to `docs/archive/phases/`

### MEDIUM PRIORITY - Do This Week (30 min)
6. **Move** technical guides to `docs/guides/`
7. **Move** specialized docs to `docs/technical/`, `docs/architecture/`, `docs/utilities/`
8. **Consolidate** START_HERE variants into single file
9. **Update** all cross-references in remaining files
10. **Update** `_INDEX.md` with new structure

### LOW PRIORITY - Polish (15 min)
11. **Archive** old version files (PROJECT_INSTRUCTIONS_V*.md)
12. **Review** `.claude/memory/` files for cleanup
13. **Delete** any truly obsolete files
14. **Add** README files to archive subdirectories explaining what they contain

---

## Quick Decision Tree

**For each markdown file at root, ask:**

1. **Is it CLAUDE.md, README.md, or LESSONS_LEARNED.md?**
   - YES → Keep at root, reference in _INDEX.md
   - NO → Continue to #2

2. **Is it a START_HERE or QUICK_START variant?**
   - YES → Consolidate into one file, archive others
   - NO → Continue to #3

3. **Is it a completed session summary or phase documentation?**
   - YES → Archive to `docs/archive/{sessions|phases}/`
   - NO → Continue to #4

4. **Is it a technical guide (TESTING, LIVE_ODDS, CHECK_OVERTIME, etc.)?**
   - YES → Move to `docs/guides/`
   - NO → Continue to #5

5. **Is it week-specific (WEEK12, WEEK13)?**
   - YES → Archive to `docs/archive/week_specific/`
   - NO → Continue to #6

6. **Is it an old version or configuration file?**
   - YES → Archive to `docs/archive/versions/` or `docs/archive/`
   - NO → Continue to #7

7. **Is it something unique that adds current value?**
   - YES → Move to `docs/technical/` or `docs/architecture/` as appropriate
   - NO → Archive to `docs/archive/`

---

## Implementation Checklist

- [ ] Review and decide on START_HERE consolidation
- [ ] Create archive directory structure
- [ ] Move session files to archive
- [ ] Move week-specific files to archive
- [ ] Move phase completion files to archive
- [ ] Move technical guides to docs/guides/
- [ ] Move specialized docs to docs/technical/, docs/architecture/, docs/utilities/
- [ ] Update all cross-references in markdown files
- [ ] Update _INDEX.md with new structure and links
- [ ] Create README files in archive subdirectories
- [ ] Verify all links work: `uv run python scripts/dev/validate_doc_links.py`
- [ ] Commit: `git commit -m "docs: reorganize documentation structure"`

---

## Expected Benefits

✅ **Clarity**: Single START_HERE entry point instead of 4 variants
✅ **Organization**: All docs organized by purpose in `docs/` directory
✅ **Findability**: Consistent structure makes documentation easier to locate
✅ **Maintenance**: Session history preserved but archived
✅ **Performance**: Faster navigation with clear directory structure
✅ **Professional**: Clean root directory with only essential files
✅ **Scalability**: Archive system can grow without cluttering root

---

## Questions to Clarify

1. **Which START_HERE file is authoritative?** (Check git history to see which was edited most recently)
2. **Should PROJECT_MEMORY.md stay or move to `.claude/memory/`?**
3. **Are any WEEK12/WEEK13 files still needed, or all archive?**
4. **Should old SESSION_MEMORY files be deleted or kept in `.claude/memory/`?**
5. **Are PROJECT_INSTRUCTIONS_V2 and V3 completely superseded by CLAUDE.md?**

---

**Next Steps**: Review this analysis, answer the clarifying questions, then execute the migration plan.
