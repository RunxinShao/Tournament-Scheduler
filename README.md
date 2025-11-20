# Tournament Scheduler - Traveling Tournament Problem (TTP) Solver

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A complete Python implementation of the **Traveling Tournament Problem (TTP) Solver** that generates and optimizes round-robin tournament schedules to minimize total team travel distance while enforcing realistic scheduling constraints.

## 🎯 Project Overview

This project implements a comprehensive tournament scheduling system that:
- Generates teams with geographic coordinates
- Creates round-robin tournament schedules
- Optimizes schedules to minimize travel distance
- Enforces realistic constraints (max consecutive away games, no immediate repeaters, home/away balance)
- Provides multiple optimization algorithms (greedy, simulated annealing, exact solver)
- Includes interactive visualizations and web application

## ✨ Key Features

### Core Functionality
- **Team Generation**: Create teams with stadium coordinates using geographic distribution
- **Distance Calculation**: Haversine formula for accurate distance computation
- **Schedule Generation**: Round-robin tournament schedules using circle method
- **Travel Evaluation**: Sequential-round model for realistic travel calculation
- **Constraint Validation**: 4 comprehensive validators ensuring schedule feasibility

### Optimization Algorithms
- **Hill Climbing**: Greedy local search optimizer
- **Simulated Annealing**: Stochastic metaheuristic with temperature schedule
- **Exact Solver**: CP-SAT constraint programming (for N ≤ 10 teams)

### Visualization & Interaction
- **Interactive Maps**: Folium-based maps showing team locations and travel routes
- **Schedule Grids**: Visual representation of match assignments
- **Streamlit Web App**: Full-featured interactive web application
- **Export Capabilities**: JSON, HTML, and CSV export options

### Experiment Framework
- **Reproducible Experiments**: Fixed seeds and comprehensive logging
- **Batch Processing**: Run multiple experiments across different parameters
- **Results Analysis**: JSON and CSV output for statistical analysis

## 📊 Visualization Results

### Demo Run (6 teams, seed=42, San Francisco area)

**Baseline Performance:**
- **Total Travel:** 524.43 km
- **Per-team range:** 57.65 - 111.54 km
- **Average per team:** 87.41 km

**Optimization Results:**

| Optimizer | Total Travel | Improvement | Runtime | Iterations |
|-----------|--------------|-------------|---------|------------|
| Baseline | 524.43 km | 0.00% | 0.000s | - |
| Hill Climbing | 439.19 km | **16.25%** | 0.014s | 290 |
| Simulated Annealing | 431.85 km | **17.65%** | 0.095s | 2000 |

**Constraint Validation:**
- ✅ Schedule structure: VALID
- ✅ Max consecutive away games (≤3): VALID
- ✅ No immediate repeaters: VALID
- ✅ Home/away balance: Maintained after optimization

**Visualization Outputs:**
- Interactive map with team locations and travel routes
- Schedule grid showing round-by-round match assignments
- Per-team travel statistics and comparisons

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/RunxinShao/Tournament-Scheduler.git
cd Tournament-Scheduler
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

**Core dependencies:**
- `streamlit>=1.28.0` - Web application
- `folium>=0.14.0` - Map visualization
- `pandas>=2.0.0` - Data manipulation

**Optional:**
- `ortools>=9.8.0` - For exact solver (CP-SAT)

### Basic Usage

**1. Run the complete demo:**
```bash
python demo_visualization.py
```

This demonstrates:
- Team generation
- Schedule creation
- Baseline evaluation
- Optimization with multiple algorithms
- Constraint validation
- Visualization generation

**2. Launch the interactive web application:**
```bash
# Option 1: Use the helper script
./run_streamlit.sh

# Option 2: Run directly
python3 -m streamlit run streamlit_app.py
```

Then open `http://localhost:8501` in your browser.

**3. Run batch experiments:**
```bash
python experiments/run_experiment.py --N 6 8 10 --seeds 42 123 456
```

**4. Run tests:**
```bash
python -m unittest discover tests -v
```

## 📖 Usage Examples

### Basic Tournament Scheduling

```python
from tourney_starter import generate_teams, distance_matrix, round_robin_pairs, evaluate_schedule_travel
from optimizers import hill_climb, simulated_annealing
from validators import validate_schedule, check_max_consecutive_aways

# Generate teams
teams = generate_teams(n=6, center=(37.7749, -122.4194), spread_km=20.0)
D = distance_matrix(teams)
schedule = round_robin_pairs(teams)

# Evaluate baseline
per_team, total = evaluate_schedule_travel(schedule, teams, D)
print(f"Baseline travel: {total:.2f} km")

# Optimize with hill climbing
best_schedule, best_score, log = hill_climb(
    schedule, teams, D,
    max_iters=1000,
    validate=True,
    random_seed=42
)
print(f"Optimized travel: {best_score:.2f} km")
print(f"Improvement: {(total - best_score) / total * 100:.2f}%")

# Validate constraints
ok, reasons = validate_schedule(best_schedule, len(teams))
print(f"Schedule valid: {ok}")
```

### Constraint Validation

```python
from validators import (
    validate_schedule,
    check_max_consecutive_aways,
    check_repeaters,
    check_home_away_balance
)

# Validate all constraints
n_teams = len(teams)
ok1, _ = validate_schedule(schedule, n_teams)
ok2, _ = check_max_consecutive_aways(schedule, k=3)
ok3, _ = check_repeaters(schedule)
ok4, _ = check_home_away_balance(schedule, n_teams)

if ok1 and ok2 and ok3 and ok4:
    print("All constraints satisfied!")
```

### Visualization

```python
from visualize import create_team_map, create_schedule_grid, save_map_html

# Create interactive map
map_obj = create_team_map(teams, schedule, D, title="Tournament Schedule")
if map_obj:
    save_map_html(map_obj, "tournament_map.html")

# Create schedule grid
grid_html = create_schedule_grid(schedule, teams)
print(grid_html)
```

## 📁 Project Structure

```
Tournament-Scheduler/
├── Core Modules
│   ├── tourney_starter.py      # Team generation, distances, schedules
│   ├── validators.py            # 4 constraint validators
│   ├── optimizers.py            # Hill-climb & Simulated Annealing
│   └── exact_solver.py          # CP-SAT exact solver (optional)
│
├── Visualization
│   ├── visualize.py             # Maps & grids
│   └── streamlit_app.py         # Interactive web app
│
├── Experiments
│   ├── run_experiment.py        # Batch experiment harness
│   └── README.md                # Experiment protocol
│
├── Tests
│   ├── test_core.py             # 15 core tests
│   └── test_optimizers.py       # 9 optimizer tests
│
├── Documentation
│   ├── PROJECT_LOG.md             # Complete development log
│   ├── PROJECT_SUMMARY.md       # Project overview
│   ├── VISUALIZATION_GUIDE.md   # Visualization instructions
│   └── Problem_flow.md           # Original specification
│
├── Demo & Utilities
│   ├── demo_visualization.py    # Complete demo script
│   └── run_streamlit.sh          # Streamlit launcher
│
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## 🔬 Algorithms & Complexity

### Time Complexity

| Operation | Complexity | Description |
|-----------|------------|-------------|
| Team Generation | O(N) | Generate N teams with coordinates |
| Distance Matrix | O(N²) | Compute all pairwise distances |
| Schedule Generation | O(N²) | Round-robin using circle method |
| Travel Evaluation | O(R × N) | R rounds, N teams |
| Hill Climbing | O(max_iters × R × (M + N)) | M matches per round |
| Simulated Annealing | O(max_iters × R × (M + N)) | Same as hill climbing |

### Space Complexity

- **Distance Matrix:** O(N²)
- **Schedule:** O(R × M) where M = matches per round
- **Optimizers:** O(R × M) for schedule copies

## 🎓 CS 5800 Topics Covered

1. **Greedy Algorithms**: Hill climbing optimizer
2. **Local Search**: Move primitives and neighborhood exploration
3. **Metaheuristics**: Simulated annealing with temperature schedules
4. **Constraint Satisfaction**: 4 validators enforcing tournament rules
5. **Exact Algorithms**: CP-SAT constraint programming
6. **Data Structures**: Lists, dictionaries, sets for schedule representation
7. **Algorithm Analysis**: Time/space complexity documented
8. **Software Engineering**: Modular design, testing, documentation

## 📝 Constraint Specifications

The solver enforces the following constraints:

1. **Max Consecutive Away Games (k=3)**: No team may play more than 3 consecutive away games
2. **No Immediate Repeaters**: If team A plays at team B's stadium in round t, then team B cannot play at team A's stadium in round t+1
3. **Home/Away Balance**: Each team should have home games within ±1 of away games
4. **Schedule Structure**: Each team plays exactly once per round; all team IDs are valid

## 🧪 Testing

Run the complete test suite:

```bash
python -m unittest discover tests -v
```

**Test Coverage:**
- ✅ 15 core functionality tests
- ✅ 9 optimizer smoke tests
- ✅ All tests passing

**Test Files:**
- `tests/test_core.py` - Round-robin, travel evaluation, validators
- `tests/test_optimizers.py` - Move primitives, hill climbing, simulated annealing

## 📊 Experiment Results

### Performance Metrics

Based on experiments with N = [6, 8, 10] teams and 5 random seeds:

- **Average Improvement**: 10-30% travel reduction
- **Constraint Satisfaction**: 100% (all optimized schedules pass validators)
- **Runtime**: < 1 second for N ≤ 10 teams

### Example Experiment Output

```json
{
  "timestamp": "20241219-143022",
  "seed": 42,
  "N": 6,
  "baseline_total": 524.43,
  "results": [
    {
      "optimizer": "hill_climb",
      "best_total": 439.19,
      "improvement_pct": 16.25,
      "runtime_s": 0.014,
      "valid": true
    }
  ]
}
```

## 🛠️ Development

### Running Experiments

```bash
# Default: N=[6,8,10], 5 seeds
python experiments/run_experiment.py

# Custom parameters
python experiments/run_experiment.py --N 6 8 10 12 --seeds 42 123 456
```

### Adding New Optimizers

1. Implement move primitives in `optimizers.py`
2. Create optimizer function following the pattern:
```python
def my_optimizer(schedule, teams, D, **kwargs):
    # Implementation
    return best_schedule, best_score, log_dict
```
3. Add to experiment harness in `experiments/run_experiment.py`
4. Add tests in `tests/test_optimizers.py`

## 📚 Documentation

- **PROJECT_LOG.md**: Complete development log with 12 detailed entries covering all implementations, algorithms, complexity analysis, and CS 5800 topics
- **PROJECT_SUMMARY.md**: Comprehensive project overview and statistics
- **VISUALIZATION_GUIDE.md**: Step-by-step visualization instructions
- **experiments/README.md**: Experiment protocol and output format
- **Code**: Comprehensive docstrings and type hints throughout

## 🤝 Contributing

This is a CS 5800 Algorithms course project. For contributions:

1. Follow the existing code style
2. Add comprehensive tests for new features
3. Update documentation (PROJECT_LOG.md)
4. Ensure all tests pass

## 📄 License

This project is part of a CS 5800 Algorithms course assignment.

## 🙏 Acknowledgments

- **Problem Specification**: Based on the Traveling Tournament Problem (TTP)
- **Algorithms**: Hill climbing, simulated annealing, constraint programming
- **Libraries**: Streamlit, Folium, Pandas, OR-Tools

## 🔗 Links

- **Repository**: `https://github.com/RunxinShao/Tournament-Scheduler/tree/OTS_YD`
- **Branch**: `OTS_YD`
- **Interactive App**: Run `streamlit run streamlit_app.py` and visit `http://localhost:8501`

## 📈 Project Status

✅ **COMPLETE** - All planned features implemented:
- [x] Core utilities (team generation, distances, schedules)
- [x] Constraint validators (4 validators)
- [x] Optimization algorithms (Hill Climb, Simulated Annealing)
- [x] Exact solver (CP-SAT, optional)
- [x] Experiment framework (reproducible, JSON/CSV output)
- [x] Visualization (maps, grids, interactive app)
- [x] Comprehensive tests (24 tests, all passing)
- [x] Complete documentation (PROJECT_LOG.md with 12 entries)

---

**Last Updated**: December 2024  
**Python Version**: 3.11+  
**Test Coverage**: 24 tests, 100% passing  
**Documentation**: Complete with PROJECT_LOG.md
