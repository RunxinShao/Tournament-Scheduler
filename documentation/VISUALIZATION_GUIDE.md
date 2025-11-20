# Tournament Scheduler - Visualization Guide

This guide demonstrates how to visualize and interact with the Tournament Scheduler project.

## Quick Start

### 1. Run the Complete Demo
```bash
python demo_visualization.py
```

This demonstrates:
- Project structure
- Team generation
- Distance calculations
- Schedule generation
- Baseline evaluation
- Constraint validation
- Optimization (Hill Climbing & Simulated Annealing)
- Visualization (maps and grids)

### 2. Interactive Web Application (Streamlit)
```bash
# Option 1: Use the helper script
./run_streamlit.sh

# Option 2: Run directly with Python module
python3 -m streamlit run streamlit_app.py

# Option 3: If streamlit is in your PATH
streamlit run streamlit_app.py
```

Features:
- **Sidebar Controls:**
  - Number of teams (4-20)
  - Random seed
  - Center location (latitude/longitude)
  - Spread in kilometers
  - Constraint parameters
  - Optimizer selection
  - Optimizer parameters

- **Main Dashboard:**
  - Optimization comparison table
  - Interactive map visualization
  - Travel statistics
  - Per-team travel breakdown
  - Schedule grid
  - Export options (JSON, HTML, CSV)

### 3. Run Experiments
```bash
python experiments/run_experiment.py --N 6 8 10 --seeds 42 123 456
```

Outputs:
- JSON files per experiment: `experiments/results/{optimizer}/{N}-{seed}-{timestamp}.json`
- CSV summary: `experiments/results/summary-{timestamp}.csv`

## Generated Visualizations

### 1. Interactive Map (`demo_map.html`)
- **Location:** Root directory
- **Contents:**
  - Team stadium locations (blue markers)
  - Travel routes for representative team (red/green polylines)
  - Interactive popups with team information
  - Total travel distance per team

**To view:** Open `demo_map.html` in a web browser

### 2. Schedule Grid (`demo_schedule_grid.html`)
- **Location:** Root directory
- **Contents:**
  - Round-by-round match assignments
  - Home/away indicators
  - Team names and matchups

**To view:** Open `demo_schedule_grid.html` in a web browser

## Project Architecture Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    Tournament Scheduler                      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌───────▼────────┐
│  Data Layer    │  │  Validation      │  │  Optimization   │
│                │  │                  │  │                 │
│ • Teams        │  │ • Schedule       │  │ • Hill Climb    │
│ • Distances    │  │ • Constraints    │  │ • Sim Annealing │
│ • Schedules    │  │ • Violations    │  │ • Exact (CP-SAT)│
└───────┬────────┘  └────────┬────────┘  └───────┬────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Visualization  │
                    │                  │
                    │ • Maps (Folium)  │
                    │ • Grids (Pandas) │
                    │ • Streamlit App  │
                    └──────────────────┘
```

## Data Flow

1. **Input:** Number of teams, location, seed
2. **Generation:** Teams → Distance Matrix → Schedule
3. **Evaluation:** Baseline travel calculation
4. **Validation:** Check constraints (4 validators)
5. **Optimization:** Apply algorithms (greedy, SA, exact)
6. **Output:** Optimized schedule, statistics, visualizations

## Key Metrics Visualized

### Travel Distance
- **Per-team:** Individual team travel in kilometers
- **Total:** Sum of all team travel
- **Improvement:** Percentage reduction from baseline

### Optimization Performance
- **Iterations:** Number of optimization steps
- **Runtime:** Execution time in seconds
- **Improvement %:** Travel reduction achieved

### Constraint Satisfaction
- ✓ Schedule structure valid
- ✓ Max consecutive away games ≤ k
- ✓ No immediate repeaters
- ✓ Home/away balance ±1

## Example Output

From the demo run:
```
Baseline Total Travel:     524.43 km
Hill Climbing:             439.19 km (16.25% improvement)
Simulated Annealing:       431.85 km (17.65% improvement)
```

## Visualization Files Generated

After running `demo_visualization.py`:
- `demo_map.html` - Interactive Folium map
- `demo_schedule_grid.html` - Schedule grid table

After running Streamlit app:
- User can download:
  - Schedule JSON files
  - Map HTML files
  - Comparison CSV files

## Next Steps

1. **Explore the Streamlit App:**
   - Adjust parameters in sidebar
   - Compare different optimizers
   - Export results

2. **Run Batch Experiments:**
   - Test multiple team counts
   - Compare across seeds
   - Analyze CSV summaries

3. **Customize Visualizations:**
   - Modify `visualize.py` for custom maps
   - Add new visualization types
   - Integrate with other tools

## Troubleshooting

### Map not displaying?
- Install folium: `pip install folium`
- Check browser compatibility
- Verify HTML file was created

### Streamlit app not starting?
- Install streamlit: `pip install streamlit`
- Check port availability (default: 8501)
- Review error messages in terminal

### Experiments not running?
- Check file permissions
- Verify `experiments/results/` directory exists
- Review JSON/CSV output format

## References

- **Project Log:** `PROJECT_LOG.md` - Complete development history
- **Experiment Protocol:** `experiments/README.md` - Experiment documentation
- **Problem Flow:** `Problem_flow.md` - Original project specification

