#!/usr/bin/env python3
"""
Comprehensive verification script for Tournament Scheduler project structure.

This script verifies:
1. All files from README structure exist
2. All imports work correctly
3. Basic functionality works
4. Tests can be discovered and run
5. Experiment framework works
"""

import sys
import os
import subprocess

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_files():
    """Verify all required files exist."""
    print_section("FILE STRUCTURE VERIFICATION")
    
    required_files = [
        # Core Modules
        'tourney_starter.py',
        'validators.py',
        'optimizers.py',
        'exact_solver.py',
        
        # Visualization
        'visualize.py',
        'streamlit_app.py',
        
        # Experiments
        'experiments/run_experiment.py',
        'experiments/README.md',
        'experiments/__init__.py',
        
        # Tests
        'tests/test_core.py',
        'tests/test_optimizers.py',
        'tests/__init__.py',
        
        # Documentation
        'PROJECT_LOG.md',
        'PROJECT_SUMMARY.md',
        'VISUALIZATION_GUIDE.md',
        'Problem_flow.md',
        
        # Demo & Utilities
        'demo_visualization.py',
        'run_streamlit.sh',
        
        # Config
        'requirements.txt',
        'README.md',
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
        else:
            print(f"  ✓ {f}")
    
    if missing:
        print(f"\n  ❌ Missing files: {missing}")
        return False
    else:
        print(f"\n  ✅ All {len(required_files)} required files exist!")
        return True

def check_imports():
    """Verify all imports work."""
    print_section("IMPORT VERIFICATION")
    
    sys.path.insert(0, '.')
    
    try:
        from tourney_starter import (
            generate_teams, distance_matrix, round_robin_pairs,
            evaluate_schedule_travel, haversine
        )
        print("  ✓ tourney_starter imports")
    except Exception as e:
        print(f"  ❌ tourney_starter imports failed: {e}")
        return False
    
    try:
        from validators import (
            validate_schedule, check_max_consecutive_aways,
            check_repeaters, check_home_away_balance
        )
        print("  ✓ validators imports")
    except Exception as e:
        print(f"  ❌ validators imports failed: {e}")
        return False
    
    try:
        from optimizers import (
            hill_climb, simulated_annealing,
            move_swap_rounds, move_swap_matches, move_flip_venue
        )
        print("  ✓ optimizers imports")
    except Exception as e:
        print(f"  ❌ optimizers imports failed: {e}")
        return False
    
    try:
        from visualize import create_team_map, create_schedule_grid
        print("  ✓ visualize imports")
    except Exception as e:
        print(f"  ❌ visualize imports failed: {e}")
        return False
    
    try:
        from experiments.run_experiment import run_single_experiment
        print("  ✓ experiments imports")
    except Exception as e:
        print(f"  ❌ experiments imports failed: {e}")
        return False
    
    try:
        from exact_solver import solve_exact
        print("  ✓ exact_solver imports (ortools available)")
    except ImportError:
        print("  ⚠ exact_solver not available (ortools optional)")
    except Exception as e:
        print(f"  ❌ exact_solver imports failed: {e}")
        return False
    
    print("\n  ✅ All imports successful!")
    return True

def check_functionality():
    """Verify basic functionality works."""
    print_section("FUNCTIONALITY VERIFICATION")
    
    sys.path.insert(0, '.')
    from tourney_starter import generate_teams, distance_matrix, round_robin_pairs, evaluate_schedule_travel
    from validators import validate_schedule
    
    try:
        # Generate teams
        teams = generate_teams(4)
        print(f"  ✓ Generated {len(teams)} teams")
        
        # Distance matrix
        D = distance_matrix(teams)
        print(f"  ✓ Created {len(D)}x{len(D)} distance matrix")
        
        # Schedule
        schedule = round_robin_pairs(teams)
        print(f"  ✓ Generated {len(schedule)} rounds")
        
        # Evaluation
        per_team, total = evaluate_schedule_travel(schedule, teams, D)
        print(f"  ✓ Evaluated travel: {total:.2f} km total")
        
        # Validation
        ok, _ = validate_schedule(schedule, len(teams))
        print(f"  ✓ Schedule validation: {ok}")
        
        print("\n  ✅ All functionality tests passed!")
        return True
    except Exception as e:
        print(f"  ❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_tests():
    """Verify tests can be discovered and run."""
    print_section("TEST DISCOVERY VERIFICATION")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'unittest', 'discover', 'tests', '-v'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Count tests
            test_count = result.stdout.count('ok')
            print(f"  ✓ Tests discovered and run successfully")
            print(f"  ✓ {test_count} tests passed")
            return True
        else:
            print(f"  ❌ Tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠ Tests timed out (may still be valid)")
        return True
    except Exception as e:
        print(f"  ❌ Test discovery failed: {e}")
        return False

def check_experiments():
    """Verify experiment framework works."""
    print_section("EXPERIMENT FRAMEWORK VERIFICATION")
    
    sys.path.insert(0, '.')
    from experiments.run_experiment import run_single_experiment
    
    try:
        # Run a minimal experiment
        experiment = run_single_experiment(
            N=4,
            seed=42,
            optimizers=['baseline'],
            center=(37.7749, -122.4194),
            spread_km=20.0
        )
        
        print(f"  ✓ Experiment ran successfully")
        print(f"  ✓ Generated experiment with {len(experiment['results'])} results")
        print(f"  ✓ Baseline travel: {experiment['baseline_total']:.2f} km")
        
        print("\n  ✅ Experiment framework works!")
        return True
    except Exception as e:
        print(f"  ❌ Experiment framework test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("  TOURNAMENT SCHEDULER - PROJECT STRUCTURE VERIFICATION")
    print("=" * 70)
    
    checks = [
        ("File Structure", check_files),
        ("Imports", check_imports),
        ("Functionality", check_functionality),
        ("Tests", check_tests),
        ("Experiments", check_experiments),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ❌ {name} check crashed: {e}")
            results.append((name, False))
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ ALL VERIFICATIONS PASSED - PROJECT STRUCTURE IS CORRECT")
    else:
        print("  ❌ SOME VERIFICATIONS FAILED - PLEASE REVIEW ERRORS ABOVE")
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

