"""
Experiment harness for tournament scheduling optimization.

Runs reproducible experiments comparing baseline, hill-climbing, and simulated
annealing optimizers. Outputs JSON per run and CSV summary.
"""

import sys
import os
import json
import csv
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tourney_starter import generate_teams, distance_matrix, round_robin_pairs, evaluate_schedule_travel
from optimizers import hill_climb, simulated_annealing
from validators import validate_schedule, check_max_consecutive_aways, check_repeaters, check_home_away_balance


def run_baseline(teams: List[Dict[str, Any]], D: List[List[float]], schedule: List[List[Tuple[int, int]]]) -> Dict[str, Any]:
    """Run baseline evaluation (no optimization)."""
    start_time = time.time()
    per_team, total = evaluate_schedule_travel(schedule, teams, D)
    runtime = time.time() - start_time
    
    # Validate baseline
    n_teams = len(teams)
    ok1, reasons1 = validate_schedule(schedule, n_teams)
    ok2, reasons2 = check_max_consecutive_aways(schedule, k=3)
    ok3, reasons3 = check_repeaters(schedule)
    ok4, reasons4 = check_home_away_balance(schedule, n_teams)
    
    violations = []
    if not ok1:
        violations.extend(reasons1)
    if not ok2:
        violations.extend(reasons2)
    if not ok3:
        violations.extend(reasons3)
    if not ok4:
        violations.extend(reasons4)
    
    return {
        'optimizer': 'baseline',
        'best_total': total,
        'runtime_s': runtime,
        'improvements': [],
        'violations': violations,
        'valid': len(violations) == 0
    }


def run_optimizer(
    optimizer_name: str,
    schedule: List[List[Tuple[int, int]]],
    teams: List[Dict[str, Any]],
    D: List[List[float]],
    random_seed: int
) -> Dict[str, Any]:
    """Run a single optimizer and return results."""
    start_time = time.time()
    
    if optimizer_name == 'hill_climb':
        best_schedule, best_score, log = hill_climb(
            schedule, teams, D,
            max_iters=1000,
            max_no_improve=100,
            validate=True,
            random_seed=random_seed
        )
    elif optimizer_name == 'simanneal':
        best_schedule, best_score, log = simulated_annealing(
            schedule, teams, D,
            max_iters=5000,
            T0=1.0,
            decay=0.995,
            validate=True,
            random_seed=random_seed
        )
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_name}")
    
    runtime = time.time() - start_time
    
    # Validate result
    n_teams = len(teams)
    ok1, reasons1 = validate_schedule(best_schedule, n_teams)
    ok2, reasons2 = check_max_consecutive_aways(best_schedule, k=3)
    ok3, reasons3 = check_repeaters(best_schedule)
    ok4, reasons4 = check_home_away_balance(best_schedule, n_teams)
    
    violations = []
    if not ok1:
        violations.extend(reasons1)
    if not ok2:
        violations.extend(reasons2)
    if not ok3:
        violations.extend(reasons3)
    if not ok4:
        violations.extend(reasons4)
    
    return {
        'optimizer': optimizer_name,
        'best_total': best_score,
        'runtime_s': runtime,
        'improvements': log.get('improvements', []),
        'violations': violations,
        'valid': len(violations) == 0,
        'iterations': log.get('iter', 0),
        'time_elapsed': log.get('time_elapsed', runtime)
    }


def run_single_experiment(
    N: int,
    seed: int,
    optimizers: List[str] = ['baseline', 'hill_climb', 'simanneal'],
    center: tuple = (37.7749, -122.4194),
    spread_km: float = 20.0
) -> Dict[str, Any]:
    """
    Run a single experiment with given parameters.
    
    Args:
        N: Number of teams
        seed: Random seed for reproducibility
        optimizers: List of optimizers to run
        center: (lat, lon) center for team generation
        spread_km: Spread in km for team generation
        
    Returns:
        Dictionary with experiment results
    """
    # Fix random seed
    random.seed(seed)
    
    # Generate teams and schedule
    teams = generate_teams(N, center=center, spread_km=spread_km)
    D = distance_matrix(teams)
    schedule = round_robin_pairs(teams)
    
    # Evaluate baseline
    baseline_result = run_baseline(teams, D, schedule)
    baseline_total = baseline_result['best_total']
    
    # Run optimizers
    results = []
    for opt_name in optimizers:
        if opt_name == 'baseline':
            results.append(baseline_result)
        else:
            result = run_optimizer(opt_name, schedule, teams, D, seed)
            result['baseline_total'] = baseline_total
            result['improvement_pct'] = ((baseline_total - result['best_total']) / baseline_total * 100) if baseline_total > 0 else 0.0
            results.append(result)
    
    # Create experiment record
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    experiment = {
        'timestamp': timestamp,
        'seed': seed,
        'N': N,
        'baseline_total': baseline_total,
        'center': center,
        'spread_km': spread_km,
        'results': results
    }
    
    return experiment


def save_experiment_json(experiment: Dict[str, Any], output_dir: str = 'experiments/results'):
    """Save experiment results as JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = experiment['timestamp']
    seed = experiment['seed']
    N = experiment['N']
    optimizer = experiment['results'][0]['optimizer'] if experiment['results'] else 'unknown'
    
    filename = f"{output_dir}/{optimizer}/{N}-{seed}-{timestamp}.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(experiment, f, indent=2)
    
    return filename


def run_experiment_batch(
    N_values: List[int] = [6, 8, 10],
    seeds: List[int] = [42, 123, 456, 789, 999],
    optimizers: List[str] = ['baseline', 'hill_climb', 'simanneal'],
    output_dir: str = 'experiments/results'
) -> List[Dict[str, Any]]:
    """
    Run a batch of experiments.
    
    Args:
        N_values: List of team counts to test
        seeds: List of random seeds
        optimizers: List of optimizers to run
        output_dir: Directory to save results
        
    Returns:
        List of experiment dictionaries
    """
    all_experiments = []
    
    for N in N_values:
        for seed in seeds:
            print(f"Running experiment: N={N}, seed={seed}")
            experiment = run_single_experiment(N, seed, optimizers)
            save_experiment_json(experiment, output_dir)
            all_experiments.append(experiment)
    
    # Generate CSV summary
    generate_csv_summary(all_experiments, output_dir)
    
    return all_experiments


def generate_csv_summary(experiments: List[Dict[str, Any]], output_dir: str = 'experiments/results'):
    """Generate CSV summary of all experiments."""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    csv_filename = f"{output_dir}/summary-{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'seed', 'N', 'optimizer', 'baseline_total',
            'best_total', 'improvement_pct', 'runtime_s', 'iterations',
            'valid', 'num_violations'
        ])
        
        for exp in experiments:
            for result in exp['results']:
                writer.writerow([
                    exp['timestamp'],
                    exp['seed'],
                    exp['N'],
                    result['optimizer'],
                    exp['baseline_total'],
                    result['best_total'],
                    result.get('improvement_pct', 0.0),
                    result['runtime_s'],
                    result.get('iterations', 0),
                    result['valid'],
                    len(result.get('violations', []))
                ])
    
    print(f"CSV summary saved to {csv_filename}")
    return csv_filename


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tournament scheduling experiments')
    parser.add_argument('--N', type=int, nargs='+', default=[6, 8, 10],
                        help='Number of teams (default: 6 8 10)')
    parser.add_argument('--seeds', type=int, nargs='+', default=[42, 123, 456, 789, 999],
                        help='Random seeds (default: 42 123 456 789 999)')
    parser.add_argument('--optimizers', type=str, nargs='+',
                        default=['baseline', 'hill_climb', 'simanneal'],
                        help='Optimizers to run (default: baseline hill_climb simanneal)')
    parser.add_argument('--output-dir', type=str, default='experiments/results',
                        help='Output directory (default: experiments/results)')
    
    args = parser.parse_args()
    
    print("Starting experiment batch...")
    print(f"N values: {args.N}")
    print(f"Seeds: {args.seeds}")
    print(f"Optimizers: {args.optimizers}")
    
    experiments = run_experiment_batch(
        N_values=args.N,
        seeds=args.seeds,
        optimizers=args.optimizers,
        output_dir=args.output_dir
    )
    
    print(f"\nCompleted {len(experiments)} experiments")

