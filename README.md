# Tournament Scheduler

A Python solver for the **Traveling Tournament Problem (TTP)** that generates and optimizes round-robin tournament schedules to minimize total team travel distance.

## Features

- Generate teams with stadium coordinates
- Compute distance matrix using Haversine formula
- Generate round-robin schedules using circle method
- Evaluate and optimize travel distance

## Installation

### 1. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

### Command Line
```bash
python tounrney_starter.py
```

### Web Interface
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

## Usage

```python
from tounrney_starter import *

# Generate teams and schedule
teams = generate_teams(n=6, center=(37.7749, -122.4194), spread_km=20)
D = distance_matrix(teams)
rounds = round_robin_pairs(teams)

# Evaluate travel
per_team, total = evaluate_schedule_travel(rounds, teams, D)

# Optimize
rounds_optimized, improved = greedy_optimize_tours(rounds, D)
```

## Requirements

- Python 3.10+
- Core algorithm (`tounrney_starter.py`): Standard library only (no external dependencies)
- Web interface (`app.py`): See `requirements.txt` for dependencies
