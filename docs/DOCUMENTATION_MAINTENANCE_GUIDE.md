# Documentation Maintenance Guide

**Purpose**: Keep CLAUDE.md and _INDEX.md current and accurate without duplication or outdated information.

**Last Updated**: 2025-11-24

---

## Core Principle: Single Source of Truth

- **CLAUDE.md** = Current session status + Recent Updates section
- **_INDEX.md** = Complete navigation index + Feature summaries
- **Feature Guides** = Detailed documentation (doesn't get duplicated in main files)

**Never duplicate information between CLAUDE.md and _INDEX.md**

---

## End-of-Session Checklist

After completing a development session, run this checklist **before committing**:

### 1. Update CLAUDE.md (5 minutes)

```markdown
## Project Status
- Update "Last Session" line with:
  - Date (YYYY-MM-DD)
  - Brief one-line summary (what was accomplished)
  - Example: "2025-11-24 - NFL scoreboard client, results validator"

## Recent Updates Section
1. Update timestamp: "**Latest Session (2025-MM-DD)**"
2. Remove old session info (anything older than current session)
3. Add new section with:
   - What was built (modules, features)
   - Key metrics or results (if applicable)
   - Files created/modified
   - Key improvements (bullet points)
   - Next steps (for following session)
4. Keep it to current session only (move old stuff to archive)
```

**Example Block**:
```markdown
**Latest Session (2025-11-24)**:

#### New: NFL Scoreboard Client & Results Validator ✨
- **NFL Scoreboard Client** (`src/data/espn_nfl_scoreboard_client.py`)
  - Fetches scores from ESPN API for any week
  - Auto-detects current week

- **Results Validator** (`src/walters_analyzer/results/results_validator.py`)
  - Compares predictions vs actual results
  - Calculates ATS and ROI metrics

**Week 12 Results**: 4-3 ATS, +13% ROI

**Key Files Added**:
- `src/data/espn_nfl_scoreboard_client.py`
- `src/walters_analyzer/results/results_validator.py`
- `docs/guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md`

**Next Steps**: Run `/collect-all-data` on Tuesday for Week 13 prep
```

### 2. Update _INDEX.md (5 minutes)

```markdown
## Top of File
- Update "**Last Update**" timestamp
- Example: "2025-11-24 - Added NFL Scoreboard Client & Results Validator"

## Relevant Sections
1. Find the section where feature belongs (e.g., "Performance & Results Checking")
2. Add new subsection with:
   - Feature name + date + "✨ NEW" (if brand new)
   - Brief description (1-2 sentences)
   - Key components (bullet list)
   - Key metrics/results (if applicable)
   - Usage example (code block)
   - Cross-reference to detailed guide
   - Key features checklist
3. Update existing related sections to avoid duplication

## Important: DON'T Duplicate
- Don't repeat content from CLAUDE.md Recent Updates
- _INDEX.md should guide navigation, not replicate content
- Link to detailed guides, don't expand them here
```

**Example Addition**:
```markdown
### NFL Scoreboard Client & Results Validator ✨ NEW (2025-11-24)
Complete automated system for fetching NFL game scores and validating predictions.

**Components:**
- NFL Scoreboard Client - Fetches scores from ESPN API
- Results Validator - Compares predictions vs actual results

**Week 12 Results**: 4-3 ATS, +13% ROI

**Documentation**: [Detailed Guide](guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md)

**Key Features:**
- ✅ Automatic week detection
- ✅ ESPN API integration
```

### 3. Commit

```bash
git add CLAUDE.md docs/_INDEX.md
git commit -m "docs: update CLAUDE.md and _INDEX.md with session info

## CLAUDE.md
- Updated Last Session: 2025-11-24
- Added Recent Updates section
- Removed outdated content

## _INDEX.md
- Updated Last Update timestamp
- Added new features section
- Fixed links if needed

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## File-Specific Guidelines

### CLAUDE.md

**What Goes Here:**
- Project status summary
- Current week/session information
- Recent changes (last 1-2 sessions max)
- Next immediate steps
- End-of-session checklist reminder

**What Does NOT Go Here:**
- Detailed feature documentation (→ feature guide)
- Historical information (→ archive)
- Duplicate navigation (→ _INDEX.md)
- Implementation details (→ code comments)

**Format Rules:**
- "Recent Updates" section: Current session ONLY
- One session per update cycle
- Remove old sessions when adding new ones
- Keep headings consistent

### _INDEX.md

**What Goes Here:**
- Navigation structure for entire codebase
- Feature summaries (with links to details)
- Quick start guides
- Command reference
- Most common questions
- Current features with status badges

**What Does NOT Go Here:**
- Implementation details (→ code comments)
- Session history (→ CLAUDE.md)
- Duplicate content from feature guides (→ link instead)
- Outdated information (→ archive)

**Format Rules:**
- Use section hierarchy (##, ###, ####)
- One feature per subsection
- Always link to detailed docs
- Use status badges: ✨ NEW, ✅, 🔄, ❌
- Keep examples short and practical

---

## Avoiding Outdated Information

### When to Delete
- Session notes older than 1-2 weeks
- Features that have been superseded
- Broken links (fix or remove)
- Duplicate information

### When to Archive
- Significant session summaries (old but historically valuable)
- Features that are no longer active
- Detailed workflow descriptions (move to guides/)

**Archive Location**: `docs/reports/archive/sessions/`

### Quick Cleanup Checklist
- [ ] Remove session notes older than 2 weeks from CLAUDE.md
- [ ] Check all links in _INDEX.md (no 404s)
- [ ] Remove duplicate info between files
- [ ] Verify dates are current
- [ ] Check for "TODO" or "XXX" comments that should be resolved
- [ ] Confirm "Next Steps" still apply

---

## Information Architecture

```
CLAUDE.md (Project Status)
├─ Last Session (current date + summary)
├─ Recent Updates (this session only)
└─ Session Maintenance (reminders)

_INDEX.md (Navigation)
├─ Quick Start
├─ Command Reference
├─ Features (with links)
│  ├─ NFL Scoreboard Client → guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md
│  ├─ Edge Detector → guides/EDGE_DETECTOR_WORKFLOW.md
│  └─ Results Validator → guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md
└─ Data Sources
   ├─ ESPN API → api/espn/
   └─ Overtime.ag → data_sources/overtime/

Feature Guides (src/ and docs/guides/)
├─ src/data/espn_nfl_scoreboard_client.py (implementation)
├─ src/walters_analyzer/results/results_validator.py (implementation)
└─ docs/guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md (user guide)
```

---

## Common Mistakes to Avoid

❌ **Don't:**
- Leave multiple sessions in CLAUDE.md Recent Updates
- Duplicate feature summaries in both CLAUDE.md and _INDEX.md
- Include implementation details in navigation files
- Forget to update timestamps
- Leave broken links in _INDEX.md
- Put outdated information in Recent Updates

✅ **Do:**
- Update files at end of session
- Remove old session notes when adding new ones
- Link to detailed guides instead of duplicating
- Keep timestamps current
- Test links before committing
- Only include current/future information

---

## Tools & Shortcuts

### Quick Session Update Template

```markdown
**Latest Session (YYYY-MM-DD)**:

#### New: [Feature Name] ✨
- Brief description (1-2 sentences)

**Key Results**:
- Metric 1: Value
- Metric 2: Value

**Files Added**:
- File 1
- File 2

**Next Steps**:
- Action 1
- Action 2
```

### Link Format for _INDEX.md

```markdown
- [Feature Name](path/to/guide.md) - Brief description
  - Key feature 1
  - Key feature 2
```

### Status Badges

- ✨ NEW - Recently added
- ✅ Ready - Production ready
- 🔄 In Progress - Being worked on
- ⚠️ Needs Review - Requires attention
- ❌ Deprecated - No longer in use

---

## Schedule

**When to Update**:
- **End of each development session** (before committing)
- **Weekly review** (Monday morning - check for stale info)
- **Monthly archive** (move old session notes to archive/)

**Estimated Time**:
- Session update: 10 minutes
- Weekly review: 5 minutes
- Monthly archive: 15 minutes

---

## Examples

### Good CLAUDE.md Recent Updates

```markdown
**Latest Session (2025-11-24)**:

#### New: NFL Scoreboard Client & Results Validator ✨
- **NFL Scoreboard Client** fetches actual game scores from ESPN API
- **Results Validator** compares predictions vs actual results
- Successfully validated Week 12: 4-3 ATS, +13% ROI

**Files Added**:
- src/data/espn_nfl_scoreboard_client.py
- src/walters_analyzer/results/results_validator.py
- docs/guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md

**Next**: Run `/collect-all-data` Tuesday for Week 13 prep
```

### Good _INDEX.md Feature Section

```markdown
### NFL Scoreboard Client & Results Validator ✨ NEW (2025-11-24)

Automated system for fetching NFL game scores and validating predictions.

**Components**:
- ESPN API integration for score retrieval
- Results validator for prediction comparison
- ATS and ROI calculation

**Week 12 Results**: 4-3 ATS, +13% ROI

**Documentation**: [Week 12 Closeout Guide](guides/WEEK_12_CLOSEOUT_AND_WEEK_13_SETUP.md)

**Key Features**:
- ✅ Automatic week detection
- ✅ Team name/abbreviation mapping
- ✅ Ready for full season tracking
```

---

## Questions?

**Q: How much detail should CLAUDE.md have?**
A: Enough to understand what was done (2-3 paragraphs max). Details go in feature guides.

**Q: Should I update _INDEX.md every session?**
A: Only if you added new features. Update the "Last Update" date and add new sections.

**Q: What do I do with old session notes?**
A: Delete them from Recent Updates in CLAUDE.md. If historically important, archive to `docs/reports/archive/sessions/`.

**Q: How do I avoid duplication?**
A: Ask: "Is this in CLAUDE.md Recent Updates?" If yes, then _INDEX.md just links to it. If not, link to detailed guide instead.

---

**Remember**: Your future self will thank you for clear, current documentation. Keep it simple, keep it current.
