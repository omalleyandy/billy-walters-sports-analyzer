---
description: Comprehensive odds analysis for current NFL and NCAAF weeks
---

Analyze betting odds and edges across all current week games for both NFL and NCAAF.

This command automatically detects the current week and provides:

```bash
cd scripts && uv run python analysis/comprehensive_odds_analysis.py
```

Analysis includes:
1. **Edge Detection** - Identifies betting edges by strength tier (MAX BET, STRONG, MODERATE, LEAN)
2. **Market Efficiency** - Assesses how efficiently the market is pricing games
3. **Top Opportunities** - Ranks best bets by edge size and confidence
4. **Week Adaptation** - Automatically detects current NFL Week and NCAAF Week from system date
5. **Data Quality** - Shows which data sources are current and which need refresh

Output includes:
- Total games analyzed and teams matched
- Edge strength distribution (count and average edge)
- Top 5 highest-confidence plays with power ratings and odds
- Data freshness assessment
- Recommendations for next steps

Key Principle: **Follow the money, not the tickets!** (Billy Walters)
