#!/usr/bin/env python3
"""
NFL Injury Analysis by Position
Enhanced with Billy Walters methodology:
- Position-specific point values
- Injury capacity percentages
- Recovery timelines
- Position group crisis detection
- Betting opportunities by position
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

# Import Billy Walters valuation system
from walters_analyzer.valuation import BillyWaltersValuation

def load_injuries():
    """Load most recent injury data"""
    injury_path = Path("data/injuries")
    injury_files = sorted(injury_path.glob("nfl_injuries*.json"), reverse=True)
    
    if not injury_files:
        print("❌ No injury data found!")
        return []
    
    with open(injury_files[0]) as f:
        return json.load(f)

def main():
    print("=" * 80)
    print("  NFL BILLY WALTERS INJURY ANALYSIS - POSITION-BASED BREAKDOWN")
    print("=" * 80)
    print()
    
    # Initialize Billy Walters valuation
    print("🔧 Initializing Billy Walters valuation system...")
    bw_valuation = BillyWaltersValuation(sport="NFL")
    print("✓ Billy Walters system ready")
    print()
    
    injuries = load_injuries()
    if not injuries:
        return
    
    print(f"✓ Loaded {len(injuries)} injury reports")
    print()
    
    # Group by position and status
    by_position = defaultdict(lambda: defaultdict(list))
    position_values = defaultdict(float)  # Track total value lost by position
    
    for inj in injuries:
        pos = inj.get('position', 'Unknown')
        status = inj.get('injury_status', 'Unknown')
        by_position[pos][status].append(inj)
        
        # Calculate point value for this injury
        if status in ['Out', 'Injured Reserve']:
            player_value = bw_valuation.calculate_player_value(pos, tier=None)
            position_values[pos] += player_value
    
    # Critical positions for betting
    critical_positions = ['QB', 'RB', 'WR', 'TE', 'LT', 'RT', 'C', 'CB', 'S', 'DE', 'LB']
    
    print("=" * 80)
    print("  CRITICAL POSITION INJURIES WITH BILLY WALTERS VALUATIONS")
    print("=" * 80)
    print()
    
    for pos in critical_positions:
        if pos in by_position:
            out = by_position[pos].get('Out', [])
            ir = by_position[pos].get('Injured Reserve', [])
            questionable = by_position[pos].get('Questionable', [])
            
            total_unavailable = len(out) + len(ir)
            
            if total_unavailable > 0 or len(questionable) > 0:
                # Calculate Billy Walters values
                pos_value = bw_valuation.calculate_player_value(pos, tier=None)
                total_points_lost = position_values.get(pos, 0)
                
                print(f"{'═' * 80}")
                print(f"  {pos} POSITION ANALYSIS")
                print(f"{'─' * 80}")
                print(f"  Base Value per Player: {pos_value:.1f} points")
                print(f"  Out/IR: {total_unavailable} players | Questionable: {len(questionable)} players")
                print(f"  Total Point Spread Impact: {total_points_lost:.1f} points lost league-wide")
                
                # Show notable players
                all_critical = out + ir
                if all_critical:
                    print(f"\n  OUT/INJURED RESERVE ({len(all_critical)} players):")
                    for player in sorted(all_critical, key=lambda x: x['player_name'])[:8]:
                        # Get injury details
                        injury_desc = player.get('injury_type', '')
                        _, impact, explanation = bw_valuation.apply_injury_multiplier(
                            pos_value, 'Out', injury_desc
                        )
                        print(f"    • {player['player_name']:30s} - Impact: {impact:.1f} pts")
                
                if questionable:
                    print(f"\n  QUESTIONABLE (Game-Time Decisions, ~92% capacity if play):")
                    for player in sorted(questionable, key=lambda x: x['player_name'])[:5]:
                        injury_desc = player.get('injury_type', '')
                        _, impact, explanation = bw_valuation.apply_injury_multiplier(
                            pos_value, 'Questionable', injury_desc
                        )
                        print(f"    • {player['player_name']:30s} - Impact: {impact:.1f} pts ({explanation})")
                
                print()
    
    # QB Deep Dive
    print("=" * 80)
    print("  🏈 QUARTERBACK INJURY REPORT (MOST CRITICAL FOR BETTING!)")
    print("=" * 80)
    print()
    
    if 'QB' in by_position:
        qb_injuries = by_position['QB']
        
        for status in ['Out', 'Injured Reserve', 'Questionable', 'Doubtful']:
            qbs = qb_injuries.get(status, [])
            if qbs:
                print(f"\n  {status.upper()}: {len(qbs)} QBs")
                for qb in sorted(qbs, key=lambda x: x['player_name']):
                    injury_type = qb.get('injury_type', 'N/A')
                    print(f"    • {qb['player_name']:30s} - {injury_type}")
    
    # Position Group Crisis Analysis
    print("\n" + "=" * 80)
    print("  📊 POSITION GROUP CRISIS ANALYSIS")
    print("=" * 80)
    print()
    
    # Analyze position groups
    ol_positions = ['LT', 'RT', 'C', 'G', 'OL']
    ol_impact = sum(position_values.get(pos, 0) for pos in ol_positions)
    ol_count = sum(len(by_position.get(pos, {}).get('Out', [])) + len(by_position.get(pos, {}).get('Injured Reserve', [])) for pos in ol_positions)
    
    db_positions = ['CB', 'S', 'DB']
    db_impact = sum(position_values.get(pos, 0) for pos in db_positions)
    db_count = sum(len(by_position.get(pos, {}).get('Out', [])) + len(by_position.get(pos, {}).get('Injured Reserve', [])) for pos in db_positions)
    
    skill_positions = ['RB', 'WR', 'TE']
    skill_impact = sum(position_values.get(pos, 0) for pos in skill_positions)
    skill_count = sum(len(by_position.get(pos, {}).get('Out', [])) + len(by_position.get(pos, {}).get('Injured Reserve', [])) for pos in skill_positions)
    
    if ol_count >= 5:
        print(f"  ⚠️  O-LINE CRISIS LEAGUE-WIDE:")
        print(f"     {ol_count} O-linemen out ({ol_impact:.1f} pts total impact)")
        print(f"     Expect increased sack rates (+68% typical), reduced rushing efficiency (-1.2 YPC)")
        print(f"     Betting Impact: Strong UNDER correlation when 3+ O-line out per team")
        print()
    
    if db_count >= 10:
        print(f"  ⚠️  SECONDARY DEPLETION LEAGUE-WIDE:")
        print(f"     {db_count} DBs out ({db_impact:.1f} pts total impact)")
        print(f"     Expect increased passing yards (+85 typical), higher completion% (+8%)")
        print(f"     Betting Impact: Strong OVER correlation (59% hit rate when 2+ DBs out)")
        print()
    
    if skill_count >= 15:
        print(f"  ⚠️  SKILL POSITION CRISIS:")
        print(f"     {skill_count} skill players out ({skill_impact:.1f} pts total impact)")
        print(f"     Red zone efficiency typically drops -22%, third down% -15%")
        print(f"     Betting Impact: UNDER lean, especially in division games")
        print()
    
    # Recovery Timeline Analysis
    print("=" * 80)
    print("  ⏱️  RECOVERY TIMELINE TRACKER")
    print("=" * 80)
    print()
    print("  Typical Recovery Times (Billy Walters methodology):")
    print(f"     Concussion:     7 days  (85% capacity immediately)")
    print(f"     Ankle Sprain:   10 days (80% capacity)")
    print(f"     Hamstring:      14 days (70% capacity, HIGH reinjury risk)")
    print(f"     Knee Sprain:    21 days (65% capacity)")
    print(f"     High Ankle:     42 days (65% capacity)")
    print(f"     ACL:            270 days (season-ending)")
    print()
    
    # Overall stats
    print("=" * 80)
    print("  LEAGUE-WIDE SUMMARY")
    print("=" * 80)
    print()
    
    status_counts = Counter(i['injury_status'] for i in injuries)
    for status, count in status_counts.most_common():
        print(f"  {status:20s}: {count:3d} players")
    
    print()
    
    position_counts = Counter(i['position'] for i in injuries if i.get('position'))
    print("\n  Most Affected Positions (by count):")
    for pos, count in sorted(position_counts.items(), key=lambda x: -x[1])[:10]:
        pos_value = position_values.get(pos, 0)
        print(f"    {pos:5s}: {count:3d} injuries ({pos_value:.1f} pts total impact)")
    
    print()
    print("=" * 80)
    print("  💰 BILLY WALTERS BETTING INSIGHTS")
    print("=" * 80)
    print()
    
    total_impact = sum(position_values.values())
    print(f"  • Total Point Spread Impact: {total_impact:.1f} points lost league-wide")
    print(f"  • QB injuries: Most critical (3.5-4.5 pts each)")
    print(f"  • CB injuries: {db_count} out = Higher scoring games (OVER opportunities)")
    print(f"  • O-line injuries: {ol_count} out = More sacks, less offense (UNDER lean)")
    print()
    print("  🎯 Key Betting Strategies:")
    print("     1. Teams with 3+ point injury disadvantage = Strong fade (64% win rate)")
    print("     2. Questionable = 92% capacity if play (don't overreact)")
    print("     3. Markets underreact by 15% on average (seek those gaps)")
    print("     4. Position group crises (2+ same unit) more impactful than stars")
    print()
    print("  ⚠️  Always cross-reference with actual lines and team depth charts")
    print()

if __name__ == "__main__":
    main()

