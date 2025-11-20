"""
Demo script to visualize the entire Tournament Scheduler project.

This script demonstrates:
1. Project structure overview
2. Team generation and schedule creation
3. Baseline evaluation
4. Optimization with different algorithms
5. Visualization of results
6. Constraint validation
"""

import sys
import os
import random
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tourney_starter import generate_teams, distance_matrix, round_robin_pairs, evaluate_schedule_travel
from optimizers import hill_climb, simulated_annealing
from validators import validate_schedule, check_max_consecutive_aways, check_repeaters, check_home_away_balance
from visualize import create_team_map, create_schedule_grid, save_map_html


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_project_structure():
    """Display the project structure."""
    print_section("PROJECT STRUCTURE")
    
    structure = """
Tournament-Scheduler/
├── tourney_starter.py      # Core utilities (team generation, distances, schedules)
├── validators.py            # Constraint validators (4 validation functions)
├── optimizers.py            # Optimization algorithms (hill-climb, simulated annealing)
├── exact_solver.py          # Exact CP-SAT solver (optional, for N <= 10)
├── visualize.py             # Visualization utilities (maps, grids)
├── streamlit_app.py         # Interactive web application
├── experiments/
│   ├── run_experiment.py    # Experiment harness (JSON/CSV output)
│   └── README.md            # Experiment protocol documentation
├── tests/
│   ├── test_core.py         # Core functionality tests (15 tests)
│   └── test_optimizers.py   # Optimizer smoke tests (9 tests)
├── PROJECT_LOG.md           # Development log with all changes
├── requirements.txt         # Dependencies
└── README.md                # Project documentation
"""
    print(structure)


def demo_team_generation():
    """Demonstrate team generation."""
    print_section("STEP 1: TEAM GENERATION")
    
    random.seed(42)
    n_teams = 6
    teams = generate_teams(n_teams, center=(37.7749, -122.4194), spread_km=20.0)
    
    print(f"Generated {n_teams} teams around San Francisco (37.77°N, 122.42°W):")
    print(f"{'Team ID':<10} {'Name':<15} {'Latitude':<12} {'Longitude':<12}")
    print("-" * 50)
    for team in teams:
        print(f"{team['id']:<10} {team['name']:<15} {team['lat']:<12.4f} {team['lon']:<12.4f}")
    
    return teams


def demo_distance_matrix(teams: List[Dict[str, Any]]):
    """Demonstrate distance matrix calculation."""
    print_section("STEP 2: DISTANCE MATRIX")
    
    D = distance_matrix(teams)
    
    print("Distance matrix (kilometers):")
    print(f"{'From/To':<10}", end="")
    for i in range(len(teams)):
        print(f"Team{i+1:<6}", end="")
    print()
    
    for i in range(len(teams)):
        print(f"Team{i+1:<6}", end="")
        for j in range(len(teams)):
            print(f"{D[i][j]:>8.2f}", end="")
        print()
    
    return D


def demo_schedule_generation(teams: List[Dict[str, Any]]):
    """Demonstrate schedule generation."""
    print_section("STEP 3: SCHEDULE GENERATION (Round-Robin)")
    
    schedule = round_robin_pairs(teams)
    
    print(f"Generated {len(schedule)} rounds for {len(teams)} teams:")
    print()
    for r, round_matches in enumerate(schedule):
        print(f"Round {r+1}:")
        for home, away in round_matches:
            print(f"  {teams[home]['name']} vs {teams[away]['name']} (at {teams[home]['name']})")
        print()
    
    return schedule


def demo_baseline_evaluation(teams: List[Dict[str, Any]], schedule: List, D: List[List[float]]):
    """Demonstrate baseline travel evaluation."""
    print_section("STEP 4: BASELINE TRAVEL EVALUATION")
    
    per_team, total = evaluate_schedule_travel(schedule, teams, D)
    
    print("Travel distance per team (kilometers):")
    print(f"{'Team':<15} {'Travel (km)':<15}")
    print("-" * 30)
    for i, team in enumerate(teams):
        print(f"{team['name']:<15} {per_team[i]:>14.2f}")
    print("-" * 30)
    print(f"{'TOTAL':<15} {total:>14.2f}")
    
    return total


def demo_constraint_validation(teams: List[Dict[str, Any]], schedule: List):
    """Demonstrate constraint validation."""
    print_section("STEP 5: CONSTRAINT VALIDATION")
    
    n_teams = len(teams)
    
    # Validate schedule
    ok1, reasons1 = validate_schedule(schedule, n_teams)
    print(f"✓ Schedule structure: {'VALID' if ok1 else 'INVALID'}")
    if reasons1:
        for reason in reasons1:
            print(f"  - {reason}")
    
    # Check consecutive aways
    ok2, reasons2 = check_max_consecutive_aways(schedule, k=3)
    print(f"✓ Max consecutive away games (≤3): {'VALID' if ok2 else 'INVALID'}")
    if reasons2:
        for reason in reasons2:
            print(f"  - {reason}")
    
    # Check repeaters
    ok3, reasons3 = check_repeaters(schedule)
    print(f"✓ No immediate repeaters: {'VALID' if ok3 else 'INVALID'}")
    if reasons3:
        for reason in reasons3:
            print(f"  - {reason}")
    
    # Check home/away balance
    ok4, reasons4 = check_home_away_balance(schedule, n_teams)
    print(f"✓ Home/away balance: {'VALID' if ok4 else 'INVALID'}")
    if reasons4:
        for reason in reasons4:
            print(f"  - {reason}")
    
    all_valid = ok1 and ok2 and ok3 and ok4
    print(f"\n{'='*50}")
    print(f"Overall: {'✓ ALL CONSTRAINTS SATISFIED' if all_valid else '✗ CONSTRAINTS VIOLATED'}")
    print(f"{'='*50}")


def demo_optimization(teams: List[Dict[str, Any]], schedule: List, D: List[List[float]], baseline_total: float):
    """Demonstrate optimization."""
    print_section("STEP 6: OPTIMIZATION")
    
    results = {}
    
    # Hill Climbing
    print("Running Hill Climbing optimizer...")
    best_schedule_hc, best_score_hc, log_hc = hill_climb(
        schedule, teams, D,
        max_iters=500,
        max_no_improve=50,
        validate=True,
        random_seed=42
    )
    improvement_hc = ((baseline_total - best_score_hc) / baseline_total * 100) if baseline_total > 0 else 0.0
    results['hill_climb'] = {
        'score': best_score_hc,
        'improvement': improvement_hc,
        'iterations': log_hc['iter'],
        'runtime': log_hc['time_elapsed']
    }
    print(f"  ✓ Completed in {log_hc['iter']} iterations ({log_hc['time_elapsed']:.3f}s)")
    print(f"  ✓ Best score: {best_score_hc:.2f} km")
    print(f"  ✓ Improvement: {improvement_hc:.2f}%")
    
    # Simulated Annealing
    print("\nRunning Simulated Annealing optimizer...")
    best_schedule_sa, best_score_sa, log_sa = simulated_annealing(
        schedule, teams, D,
        max_iters=2000,
        T0=1.0,
        decay=0.995,
        validate=True,
        random_seed=42
    )
    improvement_sa = ((baseline_total - best_score_sa) / baseline_total * 100) if baseline_total > 0 else 0.0
    results['simanneal'] = {
        'score': best_score_sa,
        'improvement': improvement_sa,
        'iterations': log_sa['iter'],
        'runtime': log_sa['time_elapsed']
    }
    print(f"  ✓ Completed in {log_sa['iter']} iterations ({log_sa['time_elapsed']:.3f}s)")
    print(f"  ✓ Best score: {best_score_sa:.2f} km")
    print(f"  ✓ Improvement: {improvement_sa:.2f}%")
    
    # Comparison
    print("\n" + "="*60)
    print("OPTIMIZATION COMPARISON")
    print("="*60)
    print(f"{'Optimizer':<20} {'Score (km)':<15} {'Improvement':<15} {'Runtime (s)':<15}")
    print("-"*60)
    print(f"{'Baseline':<20} {baseline_total:<15.2f} {'0.00%':<15} {'0.000':<15}")
    print(f"{'Hill Climbing':<20} {best_score_hc:<15.2f} {improvement_hc:<15.2f}% {results['hill_climb']['runtime']:<15.3f}")
    print(f"{'Simulated Annealing':<20} {best_score_sa:<15.2f} {improvement_sa:<15.2f}% {results['simanneal']['runtime']:<15.3f}")
    print("="*60)
    
    return results


def demo_visualization(teams: List[Dict[str, Any]], schedule: List, D: List[List[float]]):
    """Demonstrate visualization."""
    print_section("STEP 7: VISUALIZATION")
    
    # Create map
    print("Creating interactive map...")
    map_obj = create_team_map(teams, schedule, D, title="Tournament Schedule - Baseline")
    
    if map_obj:
        map_filename = "demo_map.html"
        save_map_html(map_obj, map_filename)
        if os.path.exists(map_filename):
            print(f"  ✓ Map saved to: {map_filename}")
            print(f"  ✓ Open in browser to view interactive map")
        else:
            print("  ⚠ Map creation failed")
    else:
        print("  ⚠ Folium not installed. Install with: pip install folium")
    
    # Create schedule grid
    print("\nCreating schedule grid...")
    try:
        grid_html = create_schedule_grid(schedule, teams)
        if grid_html:
            grid_filename = "demo_schedule_grid.html"
            with open(grid_filename, 'w') as f:
                f.write(f"<html><head><title>Schedule Grid</title>")
                f.write("<style>table {{ border-collapse: collapse; width: 100%; }}")
                f.write("th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}")
                f.write("th {{ background-color: #4CAF50; color: white; }}</style></head>")
                f.write(f"<body><h2>Tournament Schedule Grid</h2>{grid_html}</body></html>")
            print(f"  ✓ Schedule grid saved to: {grid_filename}")
        else:
            print("  ⚠ Schedule grid creation failed")
    except Exception as e:
        print(f"  ⚠ Schedule grid creation failed: {e}")
    
    # Text schedule
    print("\nText schedule representation:")
    from visualize import create_schedule_text
    print(create_schedule_text(schedule, teams))


def main():
    """Run the complete demo."""
    print("\n" + "="*80)
    print("  TOURNAMENT SCHEDULER - COMPLETE PROJECT VISUALIZATION DEMO")
    print("="*80)
    
    # Show project structure
    print_project_structure()
    
    # Step 1: Generate teams
    teams = demo_team_generation()
    
    # Step 2: Calculate distances
    D = demo_distance_matrix(teams)
    
    # Step 3: Generate schedule
    schedule = demo_schedule_generation(teams)
    
    # Step 4: Evaluate baseline
    baseline_total = demo_baseline_evaluation(teams, schedule, D)
    
    # Step 5: Validate constraints
    demo_constraint_validation(teams, schedule)
    
    # Step 6: Optimize
    results = demo_optimization(teams, schedule, D, baseline_total)
    
    # Step 7: Visualize
    demo_visualization(teams, schedule, D)
    
    # Summary
    print_section("SUMMARY")
    print("Project components demonstrated:")
    print("  ✓ Team generation with geographic coordinates")
    print("  ✓ Distance matrix calculation (Haversine formula)")
    print("  ✓ Round-robin schedule generation")
    print("  ✓ Travel distance evaluation")
    print("  ✓ Constraint validation (4 validators)")
    print("  ✓ Optimization (Hill Climbing, Simulated Annealing)")
    print("  ✓ Visualization (maps, schedule grids)")
    print("\nNext steps:")
    print("  1. Run experiments: python experiments/run_experiment.py")
    print("  2. Launch Streamlit app: streamlit run streamlit_app.py")
    print("  3. Run tests: python -m unittest discover tests -v")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

