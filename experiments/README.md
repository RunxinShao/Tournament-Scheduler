# Experiment Protocol

This directory contains the experiment harness for evaluating tournament scheduling optimizers.

## Overview

The experiment framework runs reproducible experiments comparing:
- **Baseline**: Unoptimized round-robin schedule
- **Hill Climbing**: Greedy local search optimizer
- **Simulated Annealing**: Stochastic local search optimizer

## Usage

### Basic Usage

Run experiments with default parameters (N=[6,8,10], 5 seeds each):

```bash
python experiments/run_experiment.py
```

### Custom Parameters

```bash
python experiments/run_experiment.py --N 6 8 10 12 --seeds 42 123 456 --optimizers baseline hill_climb simanneal
```

### Parameters

- `--N`: Number of teams (default: 6 8 10)
- `--seeds`: Random seeds for reproducibility (default: 42 123 456 789 999)
- `--optimizers`: Optimizers to run (default: baseline hill_climb simanneal)
- `--output-dir`: Output directory (default: experiments/results)

## Output Format

### JSON Files

Each experiment run produces a JSON file:
```
experiments/results/{optimizer}/{N}-{seed}-{timestamp}.json
```

JSON structure:
```json
{
  "timestamp": "20241219-143022",
  "seed": 42,
  "N": 6,
  "baseline_total": 1234.56,
  "center": [37.7749, -122.4194],
  "spread_km": 20.0,
  "results": [
    {
      "optimizer": "baseline",
      "best_total": 1234.56,
      "runtime_s": 0.001,
      "improvements": [],
      "violations": [],
      "valid": true
    },
    {
      "optimizer": "hill_climb",
      "best_total": 1100.00,
      "runtime_s": 0.5,
      "improvement_pct": 10.9,
      "improvements": [[10, -50.0], [25, -84.56]],
      "violations": [],
      "valid": true,
      "iterations": 100
    }
  ]
}
```

### CSV Summary

A CSV summary is generated with all experiments:
```
experiments/results/summary-{timestamp}.csv
```

Columns:
- `timestamp`: Experiment timestamp
- `seed`: Random seed
- `N`: Number of teams
- `optimizer`: Optimizer name
- `baseline_total`: Baseline travel distance (km)
- `best_total`: Optimized travel distance (km)
- `improvement_pct`: Percentage improvement
- `runtime_s`: Runtime in seconds
- `iterations`: Number of iterations (for optimizers)
- `valid`: Whether schedule passes all validators
- `num_violations`: Number of constraint violations

## Reproducibility

Experiments are fully reproducible:
- Random seeds are fixed and recorded in JSON
- All parameters (N, center, spread_km) are recorded
- Timestamps ensure unique file names

## Experiment Protocol

1. **Team Generation**: Generate N teams with fixed seed around center point
2. **Baseline**: Evaluate unoptimized round-robin schedule
3. **Optimization**: Run each optimizer with same seed
4. **Validation**: Check all constraints (max consecutive aways, repeaters, balance)
5. **Recording**: Save results to JSON and update CSV summary

## Success Metrics

- **Correctness**: All schedules pass validators (`valid: true`)
- **Quality**: Optimizers reduce travel by 10-30% on average
- **Reproducibility**: Same seed produces same results

## Analysis

Use the CSV summary for analysis:
- Compare optimizers across different N values
- Analyze improvement percentages
- Check runtime vs. quality trade-offs
- Identify constraint violations

Example analysis:
```python
import pandas as pd
df = pd.read_csv('experiments/results/summary-20241219-143022.csv')
print(df.groupby(['N', 'optimizer'])['improvement_pct'].mean())
```

