# Billy Walters SDK Upgrade Checklist

Quick reference for implementing vNext improvements to your project.

---

## 🎯 Phase 1: Quick Wins (2-3 hours)

### ☐ HTTP Client Implementation (1 hour)
- [ ] Create `walters_analyzer/core/` directory
- [ ] Create `walters_analyzer/core/__init__.py`
- [ ] Copy HTTP client code from vNext
- [ ] Create `walters_analyzer/core/http_client.py`
- [ ] Update `weather_fetcher.py` to use `async_get()`
- [ ] Test weather fetching: `uv run walters-analyzer scrape-weather --stadium "Highmark Stadium" --location "Buffalo, NY"`
- [ ] Verify no errors in logs

**Expected Result:** Weather API calls use connection pooling

---

### ☐ Caching System (1 hour)
- [ ] Create `walters_analyzer/core/cache.py`
- [ ] Add `@cache_weather_data()` decorator to weather functions
- [ ] Test caching performance
  ```bash
  python -c "
  import asyncio
  from walters_analyzer.weather_fetcher import fetch_game_weather
  
  async def test():
      # First call - slow
      import time
      start = time.time()
      w1 = await fetch_game_weather('Stadium', 'Buffalo, NY')
      print(f'First call: {time.time() - start:.2f}s')
      
      # Second call - fast
      start = time.time()
      w2 = await fetch_game_weather('Stadium', 'Buffalo, NY')
      print(f'Second call: {time.time() - start:.2f}s (cached!)')
  
  asyncio.run(test())
  "
  ```
- [ ] Add caching to injury fetchers (optional)
- [ ] Document cache TTL settings

**Expected Result:** Second identical call is 100x faster

---

### ☐ Models Consolidation (30 min)
- [ ] Create `walters_analyzer/core/models.py`
- [ ] Copy all `@dataclass` definitions:
  - [ ] TeamRating (from `power_ratings.py`)
  - [ ] GameResult (from `power_ratings.py`)
  - [ ] GameContext (from `situational_factors.py`)
  - [ ] BetRecommendation (from `bet_sizing.py`)
  - [ ] BetType (from `bet_sizing.py`)
  - [ ] KeyNumberAnalysis (from `key_numbers.py`)
  - [ ] ComprehensiveAnalysis (from `analyzer.py`)
- [ ] Add new InjuryReport model from vNext
- [ ] Test imports work:
  ```python
  from walters_analyzer.core.models import TeamRating, GameContext
  ```
- [ ] Keep old imports working (backward compatibility)

**Expected Result:** All models in one file

---

### ☐ Testing (30 min)
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Test key commands:
  ```bash
  uv run walters-analyzer scrape-weather --card cards/wk-card-2025-10-31.json
  uv run walters-analyzer weekly-nfl-update --week 10
  uv run walters-analyzer scrape-massey --data-type games
  ```
- [ ] Check logs for errors
- [ ] Verify cache stats:
  ```python
  from walters_analyzer.core.cache import get_cache_stats
  print(get_cache_stats())
  ```

**Expected Result:** All tests pass, no regressions

---

## 🔧 Phase 2: Research Enhancement (2-3 hours)

### ☐ Research Module Organization
- [ ] Create `walters_analyzer/research/` directory
- [ ] Create `walters_analyzer/research/__init__.py`
- [ ] Move `weather_fetcher.py` → `research/weather.py`
- [ ] Update imports in dependent files
- [ ] Test weather commands still work

---

### ☐ ProFootballDoc Integration
- [ ] Copy `profootballdoc_fetcher.py` from vNext
- [ ] Create `walters_analyzer/research/profootballdoc.py`
- [ ] Test medical analysis fetching
- [ ] Integrate with injury research workflow
- [ ] Update injury analysis to use multiple sources:
  - [ ] ESPN (existing)
  - [ ] ProFootballDoc (new)
  - [ ] News API (optional)
- [ ] Add confidence scoring
- [ ] Document new features

**Expected Result:** Richer injury analysis with medical insights

---

### ☐ Enhanced Research Engine
- [ ] Review vNext `research/engine.py`
- [ ] Add multi-source injury research
- [ ] Add comprehensive analysis aggregation
- [ ] Test with real teams:
  ```python
  from walters_analyzer.research.engine import ResearchEngine
  
  engine = ResearchEngine(enable_web_fetch=True)
  analysis = await engine.comprehensive_injury_research("Kansas City Chiefs")
  print(analysis)
  ```

**Expected Result:** Comprehensive injury reports from multiple sources

---

## 🎨 Phase 3: CLI Modernization (2-3 hours)

### ☐ CLI Module Organization
- [ ] Create `walters_analyzer/cli/` directory
- [ ] Create `walters_analyzer/cli/__init__.py`
- [ ] Move `cli.py` → `cli/commands.py`
- [ ] Update entry point in `pyproject.toml`
- [ ] Test all CLI commands work
- [ ] Update documentation

---

### ☐ Slash Commands (Optional)
- [ ] Copy `slash_commands.py` from vNext
- [ ] Create `walters_analyzer/cli/slash_commands.py`
- [ ] Add command registry
- [ ] Test slash commands:
  ```python
  from walters_analyzer.cli.slash_commands import analyze_game
  
  result = await analyze_game(
      "Kansas City Chiefs", 
      "Buffalo Bills",
      date="2024-12-15"
  )
  print(result)
  ```
- [ ] Document AI integration features

**Expected Result:** Natural language command interface

---

### ☐ Interactive Mode (Optional)
- [ ] Copy `cli_interface.py` from vNext
- [ ] Create `walters_analyzer/cli/interactive.py`
- [ ] Add interactive menu system
- [ ] Test interactive mode:
  ```bash
  uv run walters-analyzer interactive
  ```

**Expected Result:** User-friendly interactive CLI

---

## 🏗️ Phase 4: Core Reorganization (1-2 days)

### ☐ Move Core Files
- [ ] Move `power_ratings.py` → `core/power_ratings.py`
- [ ] Move `bet_sizing.py` → `core/bet_sizing.py`
- [ ] Move `key_numbers.py` → `core/key_numbers.py`
- [ ] Move `situational_factors.py` → `core/swe_factors.py`
- [ ] Move `analyzer.py` → `core/analyzer.py`
- [ ] Update all imports across codebase
- [ ] Test after each move

---

### ☐ Update Import Paths
- [ ] Find all old imports:
  ```bash
  grep -r "from walters_analyzer.power_ratings" .
  ```
- [ ] Replace with new paths:
  ```python
  # Old:
  from walters_analyzer.power_ratings import PowerRatingEngine
  
  # New:
  from walters_analyzer.core.power_ratings import PowerRatingEngine
  ```
- [ ] Use find/replace in IDE
- [ ] Test incrementally

---

### ☐ Add Backward Compatibility
- [ ] Create compatibility shims in old locations:
  ```python
  # walters_analyzer/power_ratings.py (old location)
  from walters_analyzer.core.power_ratings import *  # noqa
  ```
- [ ] Add deprecation warnings (optional)
- [ ] Document migration path

---

### ☐ Default Ratings System
- [ ] Copy `default_ratings.py` from vNext
- [ ] Create `walters_analyzer/core/default_ratings.py`
- [ ] Add NFL team default ratings
- [ ] Add CFB team default ratings (optional)
- [ ] Update analyzer to use defaults
- [ ] Test early-season predictions improve

**Expected Result:** Better Week 1-2 accuracy

---

## 📝 Phase 5: Polish & Documentation (1-2 days)

### ☐ Documentation Updates
- [ ] Update README.md with new structure
- [ ] Update CLAUDE.md with new commands
- [ ] Add architecture diagram
- [ ] Document caching system
- [ ] Document HTTP client usage
- [ ] Add migration guide
- [ ] Update examples
- [ ] Add API documentation

---

### ☐ Testing & Validation
- [ ] Run full test suite
- [ ] Add tests for new features:
  - [ ] HTTP client tests
  - [ ] Caching tests
  - [ ] Model tests
  - [ ] ProFootballDoc tests
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Memory profiling

---

### ☐ Cleanup
- [ ] Remove old backup files
- [ ] Clean up logs
- [ ] Update .gitignore
- [ ] Remove unused imports
- [ ] Format code: `black walters_analyzer/`
- [ ] Lint code: `ruff check walters_analyzer/`
- [ ] Type check: `mypy walters_analyzer/`

---

## ✅ Final Verification

### ☐ Functionality Check
- [ ] All CLI commands work
- [ ] Weather fetching works
- [ ] Injury scraping works
- [ ] Power ratings update works
- [ ] Weekly workflow works
- [ ] Backtesting works
- [ ] CLV tracking works

### ☐ Performance Check
- [ ] Cache hit rate > 80%
- [ ] Weather API calls reduced 90%+
- [ ] Memory usage stable
- [ ] No connection leaks
- [ ] Response times improved

### ☐ Code Quality Check
- [ ] All tests pass
- [ ] No linter errors
- [ ] Type hints complete
- [ ] Documentation complete
- [ ] Examples work
- [ ] Backward compatible

---

## 🎯 Success Criteria

### Phase 1 Complete When:
✅ HTTP client works  
✅ Caching saves 80%+ API calls  
✅ Models centralized  
✅ All tests pass  

### Phase 2 Complete When:
✅ ProFootballDoc integrated  
✅ Multi-source injury research works  
✅ Research module organized  

### Phase 3 Complete When:
✅ CLI module reorganized  
✅ Slash commands work (if added)  
✅ Interactive mode works (if added)  

### Phase 4 Complete When:
✅ All core files in core/  
✅ All imports updated  
✅ Default ratings work  
✅ No regressions  

### Phase 5 Complete When:
✅ Documentation complete  
✅ All tests pass  
✅ Performance improved  
✅ v2.0 ready for release  

---

## 📊 Progress Tracking

Copy this to track your progress:

```
## Progress: ___ / 5 Phases Complete

Phase 1: Quick Wins [____] 0/4 tasks
- [ ] HTTP Client
- [ ] Caching
- [ ] Models
- [ ] Testing

Phase 2: Research [____] 0/3 tasks
- [ ] Module organization
- [ ] ProFootballDoc
- [ ] Research engine

Phase 3: CLI [____] 0/3 tasks
- [ ] Module organization
- [ ] Slash commands
- [ ] Interactive mode

Phase 4: Core [____] 0/4 tasks
- [ ] Move files
- [ ] Update imports
- [ ] Backward compat
- [ ] Default ratings

Phase 5: Polish [____] 0/3 tasks
- [ ] Documentation
- [ ] Testing
- [ ] Cleanup

Total: ___ / 17 tasks complete
Estimated time remaining: ___ hours
```

---

## 🚨 Rollback Plan

If something goes wrong:

1. **Git Reset**
   ```bash
   git status
   git diff
   git checkout -- <file>  # Undo specific file
   git reset --hard HEAD    # Undo everything
   ```

2. **Restore Backup**
   ```bash
   cp backup/walters_analyzer/ walters_analyzer/
   ```

3. **Remove New Files**
   ```bash
   rm walters_analyzer/core/http_client.py
   rm walters_analyzer/core/cache.py
   ```

4. **Revert Imports**
   ```bash
   git checkout -- walters_analyzer/*.py
   ```

---

## 📞 Get Help

Stuck? Reference these docs:

- **Quick start:** `docs/QUICK_UPGRADE_GUIDE.md`
- **Detailed comparison:** `docs/SDK_COMPARISON_AND_UPGRADES.md`
- **Code patterns:** `docs/CODE_PATTERNS_COMPARISON.md`
- **Summary:** `docs/INSPECTION_SUMMARY.md`

Or ask me directly! I can help with:
- Debugging errors
- Writing migration scripts
- Updating tests
- Performance optimization
- Architecture decisions

---

**Let's build the best Billy Walters analyzer together!** 🚀

