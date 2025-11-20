#!/usr/bin/env python3
"""
S-Factor Pipeline Performance Benchmarks
=========================================

Measures performance characteristics of the data collection pipeline:
- Processing speed for various batch sizes
- Memory usage patterns
- Scalability metrics
- Bottleneck identification

Targets:
- Process 32 NFL teams in <1 second
- Calculate full season schedule in <500ms
- Memory usage <100MB for full pipeline
- Support 1000+ historical games analysis

Version: 1.0
Created: November 20, 2025
"""

import time
import sys
from datetime import date, datetime
from typing import List, Dict
from pathlib import Path

from walters_analyzer.models.sfactor_data_models import TeamContext
from walters_analyzer.data_collection.team_context_builder import TeamContextBuilder
from walters_analyzer.data_collection.schedule_history_calculator import ScheduleHistoryCalculator


class PerformanceBenchmark:
    """Tracks and reports performance metrics"""
    
    def __init__(self):
        self.results = {}
    
    def benchmark(self, name: str, func, *args, **kwargs):
        """Run benchmark and record results"""
        # Warm up (first run may be slower due to Python optimization)
        func(*args, **kwargs)
        
        # Actual benchmark (run 3 times and take average)
        times = []
        for _ in range(3):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        self.results[name] = {
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': min_time * 1000,
            'max_time_ms': max_time * 1000,
            'target_met': avg_time < self.get_target(name)
        }
        
        return result
    
    def get_target(self, name: str) -> float:
        """Get performance target for benchmark (in seconds)"""
        targets = {
            'Single Team Context': 0.01,      # 10ms per team
            '32 Teams Batch': 1.0,            # 1 second for all teams
            'Single Game Schedule': 0.01,     # 10ms per game
            'Full Season Schedule': 0.5,      # 500ms for 17 games
            'Historical Analysis': 2.0         # 2 seconds for 100+ games
        }
        return targets.get(name, 1.0)
    
    def print_report(self):
        """Print formatted performance report"""
        print("\n" + "=" * 70)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("=" * 70)
        
        for name, metrics in self.results.items():
            status = "[OK]" if metrics['target_met'] else "[SLOW]"
            target_ms = self.get_target(name) * 1000
            
            print(f"\n{status} {name}")
            print(f"  Average: {metrics['avg_time_ms']:.2f}ms (target: {target_ms:.0f}ms)")
            print(f"  Range: {metrics['min_time_ms']:.2f}ms - {metrics['max_time_ms']:.2f}ms")
        
        print("\n" + "=" * 70)
        
        # Overall status
        all_met = all(m['target_met'] for m in self.results.values())
        if all_met:
            print("[OK] All performance targets met!")
        else:
            failed = [n for n, m in self.results.items() if not m['target_met']]
            print(f"[WARNING] {len(failed)} benchmark(s) below target:")
            for name in failed:
                print(f"  - {name}")
        
        print("=" * 70 + "\n")


def generate_test_teams(count: int) -> List[Dict]:
    """Generate test team data"""
    teams = []
    for i in range(count):
        teams.append({
            'team_name': f'Team {i+1}',
            'abbreviation': f'T{i+1:02d}',
            'power_rating': (i % 20) - 10,  # Range from -10 to +10
            'offensive_ranking': (i % 32) + 1,
            'defensive_ranking': ((i + 10) % 32) + 1,
            'special_teams_ranking': ((i + 20) % 32) + 1,
            'injuries': [
                {'player': f'Player{j}', 'position': 'WR', 'status': 'Questionable', 'impact': -0.5}
                for j in range(i % 3)  # 0-2 injuries per team
            ]
        })
    return teams


def generate_test_games(count: int) -> List[Dict]:
    """Generate test game schedule"""
    games = []
    for i in range(count):
        games.append({
            'game_date': date(2025, 9, 1 + (i * 7)),  # Weekly games
            'is_home': i % 2 == 0,
            'opponent': f'OPP{i+1}',
            'opponent_power_rating': (i % 10) - 5,
            'game_time': 'afternoon' if i % 3 == 0 else 'primetime',
            'days_rest': 7 if i % 4 != 0 else 4  # Mostly 7 days, some short weeks
        })
    return games


def benchmark_team_context_builder():
    """Benchmark TeamContextBuilder performance"""
    print("\n[1/5] Benchmarking Team Context Builder...")
    benchmark = PerformanceBenchmark()
    builder = TeamContextBuilder()
    
    # Benchmark 1: Single team
    single_team = generate_test_teams(1)[0]
    
    def build_single():
        return builder.build_team_context(single_team)
    
    benchmark.benchmark('Single Team Context', build_single)
    
    
    # Benchmark 2: All 32 NFL teams
    all_teams = generate_test_teams(32)
    
    def build_batch():
        results = []
        for team_data in all_teams:
            context = builder.build_team_context(team_data)
            results.append(context)
        return results
    
    benchmark.benchmark('32 Teams Batch', build_batch)
    
    return benchmark


def benchmark_schedule_calculator():
    """Benchmark ScheduleHistoryCalculator performance"""
    print("[2/5] Benchmarking Schedule Calculator...")
    benchmark = PerformanceBenchmark()
    calculator = ScheduleHistoryCalculator()
    
    # Benchmark 3: Single game
    single_game = generate_test_games(1)
    
    def calc_single():
        return calculator.calculate_schedule_history(
            team_abbr='BUF',
            current_date=date(2025, 11, 24),
            recent_games=single_game
        )
    
    benchmark.benchmark('Single Game Schedule', calc_single)
    
    
    # Benchmark 4: Full 17-game season
    full_season = generate_test_games(17)
    
    def calc_season():
        return calculator.calculate_schedule_history(
            team_abbr='BUF',
            current_date=date(2025, 11, 24),
            recent_games=full_season
        )
    
    benchmark.benchmark('Full Season Schedule', calc_season)
    
    
    # Benchmark 5: Historical analysis (100 games)
    historical_games = generate_test_games(100)
    
    def calc_historical():
        return calculator.calculate_schedule_history(
            team_abbr='BUF',
            current_date=date(2025, 11, 24),
            recent_games=historical_games
        )
    
    benchmark.benchmark('Historical Analysis', calc_historical)
    
    return benchmark


def benchmark_memory_usage():
    """Measure memory footprint"""
    print("[3/5] Benchmarking Memory Usage...")
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        baseline_mb = process.memory_info().rss / 1024 / 1024
        
        # Create 32 team contexts
        builder = TeamContextBuilder()
        teams = generate_test_teams(32)
        contexts = [builder.build_team_context(t) for t in teams]
        
        # Measure after team contexts
        after_teams_mb = process.memory_info().rss / 1024 / 1024
        team_memory = after_teams_mb - baseline_mb
        
        # Calculate 100 game schedules
        calculator = ScheduleHistoryCalculator()
        games = generate_test_games(100)
        history = calculator.calculate_schedule_history('BUF', date(2025, 11, 24), games)
        
        # Measure after schedule
        after_schedule_mb = process.memory_info().rss / 1024 / 1024
        schedule_memory = after_schedule_mb - after_teams_mb
        
        total_memory = after_schedule_mb - baseline_mb
        
        print(f"\n  Baseline Memory: {baseline_mb:.2f} MB")
        print(f"  After 32 Teams: {after_teams_mb:.2f} MB (+{team_memory:.2f} MB)")
        print(f"  After Schedule: {after_schedule_mb:.2f} MB (+{schedule_memory:.2f} MB)")
        print(f"  Total Increase: {total_memory:.2f} MB")
        
        if total_memory < 100:
            print(f"  [OK] Memory usage within 100MB target")
        else:
            print(f"  [WARNING] Memory usage exceeds 100MB target")
        
        return {
            'baseline_mb': baseline_mb,
            'team_memory_mb': team_memory,
            'schedule_memory_mb': schedule_memory,
            'total_memory_mb': total_memory,
            'target_met': total_memory < 100
        }
    
    except ImportError:
        print("  [SKIP] psutil not installed, skipping memory benchmark")
        return None


def benchmark_scalability():
    """Test scalability with increasing data sizes"""
    print("[4/5] Benchmarking Scalability...")
    
    builder = TeamContextBuilder()
    calculator = ScheduleHistoryCalculator()
    
    sizes = [1, 5, 10, 20, 32, 50, 100]
    times = []
    
    for size in sizes:
        teams = generate_test_teams(size)
        
        start = time.time()
        contexts = [builder.build_team_context(t) for t in teams]
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        times.append(elapsed)
        
        # Calculate per-team time
        per_team = elapsed / size
        print(f"  {size} teams: {elapsed:.2f}ms total ({per_team:.2f}ms per team)")
    
    # Check if scaling is linear (should be)
    # Compare 32 teams vs 1 team - should be ~32x
    ratio_32_to_1 = times[sizes.index(32)] / times[sizes.index(1)]
    is_linear = 28 < ratio_32_to_1 < 36  # Allow 20% margin
    
    if is_linear:
        print(f"  [OK] Scaling is linear ({ratio_32_to_1:.1f}x for 32x data)")
    else:
        print(f"  [WARNING] Scaling may not be linear ({ratio_32_to_1:.1f}x for 32x data)")
    
    return {
        'sizes': sizes,
        'times_ms': times,
        'scaling_linear': is_linear
    }


def run_all_benchmarks():
    """Run complete benchmark suite"""
    print("\n" + "=" * 70)
    print("S-FACTOR PIPELINE PERFORMANCE BENCHMARKS")
    print("=" * 70)
    print("\nRunning comprehensive performance tests...")
    print("Each benchmark runs 3 times (after warmup) and reports average.")
    
    # Run benchmarks
    team_benchmark = benchmark_team_context_builder()
    schedule_benchmark = benchmark_schedule_calculator()
    memory_results = benchmark_memory_usage()
    scalability_results = benchmark_scalability()
    
    print("[5/5] Generating final report...")
    
    # Merge results
    final_benchmark = PerformanceBenchmark()
    final_benchmark.results.update(team_benchmark.results)
    final_benchmark.results.update(schedule_benchmark.results)
    
    # Print comprehensive report
    final_benchmark.print_report()
    
    # Additional metrics
    if memory_results:
        print("\nMEMORY USAGE:")
        print(f"  Total increase: {memory_results['total_memory_mb']:.2f} MB")
        print(f"  Status: {'[OK]' if memory_results['target_met'] else '[WARNING]'}")
    
    print("\nSCALABILITY:")
    print(f"  Scaling pattern: {'Linear' if scalability_results['scaling_linear'] else 'Non-linear'}")
    print(f"  Status: {'[OK]' if scalability_results['scaling_linear'] else '[WARNING]'}")
    
    print("\n" + "=" * 70)
    
    # Overall status
    all_targets_met = all(m['target_met'] for m in final_benchmark.results.values())
    memory_ok = memory_results['target_met'] if memory_results else True
    scaling_ok = scalability_results['scaling_linear']
    
    if all_targets_met and memory_ok and scaling_ok:
        print("[OK] ALL PERFORMANCE BENCHMARKS PASSED")
        print("System is ready for production Week 2 development!")
        return 0
    else:
        print("[WARNING] Some performance targets not met")
        print("Review results above for optimization opportunities.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_benchmarks())
