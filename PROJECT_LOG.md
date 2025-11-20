# Project Development Log

This document tracks all changes, implementations, and design decisions made during the development of the Traveling Tournament Problem (TTP) Solver. Each entry includes methodology, rationale, complexity analysis, and references to CS 5800 course topics.

---

## Entry 1: Project Log Initialization
**Timestamp:** 2024-12-19  
**File:** PROJECT_LOG.md  
**Change:** Created project log to track all development activities

**Rationale:** Following documentation-first approach for academic reporting. This log will capture:
- Algorithm design decisions
- Time complexity analyses
- Library usage and references
- Testing methodology
- Iteration improvements

**CS 5800 Topics:** Software engineering practices, documentation standards

---

## Entry 2: Validators Implementation
**Timestamp:** 2024-12-19  
**File:** validators.py  
**Change:** Implemented all four validator functions

**Functions Implemented:**
1. `validate_schedule()` - High-level validation (team IDs, duplicates, structure)
2. `check_max_consecutive_aways()` - Enforces k=3 consecutive away limit
3. `check_repeaters()` - Detects immediate reversals (A@B then B@A)
4. `check_home_away_balance()` - Ensures ±1 home/away balance

**Rationale:** Validators are critical for constraint satisfaction. All functions return `(bool, List[str])` tuples for detailed violation reporting, enabling debugging and optimizer integration.

**Algorithm/Pseudocode:**
```
validate_schedule(schedule, n_teams):
  for each round:
    for each match:
      validate team IDs are in [0, n_teams-1] or -1
      check no team appears twice in same round
  return (all_valid, violation_list)

check_max_consecutive_aways(schedule, k):
  for each team:
    consecutive_aways = 0
    for each round:
      if team plays away:
        consecutive_aways++
        if consecutive_aways > k: record violation
      else:
        consecutive_aways = 0
  return (no_violations, violation_list)
```

**Time Complexity:**
- `validate_schedule`: O(R * M) where R=rounds, M=matches per round
- `check_max_consecutive_aways`: O(R * N) where N=teams
- `check_repeaters`: O(R * M)
- `check_home_away_balance`: O(R * M)

**Library Functions Used:**
- `typing.List`, `typing.Tuple` - Type hints (Python stdlib)

**CS 5800 Topics:** Constraint satisfaction, validation algorithms, data structure traversal

---

## Entry 3: Enhanced tourney_starter.py
**Timestamp:** 2024-12-19  
**File:** tourney_starter.py  
**Change:** Added comprehensive type hints and improved docstrings

**Improvements:**
- Added type hints to all functions using `typing` module
- Enhanced docstrings with Args, Returns, Examples, Time Complexity
- Added input validation (e.g., n > 0 check in generate_teams)
- Improved code documentation for maintainability

**Rationale:** Type hints improve IDE support, catch errors early, and serve as documentation. Enhanced docstrings follow Python docstring conventions for better API documentation.

**Library Functions Used:**
- `typing.List`, `typing.Dict`, `typing.Tuple`, `typing.Any` - Type annotations (Python stdlib)
- `math.radians`, `math.sin`, `math.cos`, `math.atan2`, `math.sqrt` - Haversine calculation (Python stdlib)

**CS 5800 Topics:** Software engineering best practices, API design, documentation

---

## Entry 4: Core Tests Implementation
**Timestamp:** 2024-12-19  
**File:** tests/test_core.py  
**Change:** Created comprehensive unit tests for core functionality

**Test Coverage:**
1. `TestRoundRobinPairs` - Even/odd N, small N cases
2. `TestEvaluateScheduleTravel` - Two teams, four teams with close pairs, bye handling
3. `TestValidators` - All validator functions with valid and invalid inputs

**Rationale:** Unit tests ensure correctness and prevent regressions. Tests use hand-crafted examples to verify expected behavior, especially for travel evaluation with known distances.

**Test Results:** All 15 tests pass successfully.

**CS 5800 Topics:** Software testing, test-driven development, unit testing

---

## Entry 5: Move Primitives Implementation
**Timestamp:** 2024-12-19  
**File:** optimizers.py  
**Change:** Implemented move primitives for schedule modification

**Functions Implemented:**
1. `move_swap_rounds()` - Swap entire rounds
2. `move_swap_matches()` - Swap matches between rounds with conflict checking
3. `move_flip_venue()` - Swap home/away for a match
4. `move_swap_pairings()` - Complex multi-match swaps

**Rationale:** Move primitives are the building blocks for local search algorithms. All functions return new schedules (deep copies) to maintain immutability, enabling safe exploration of solution space.

**Algorithm/Pseudocode:**
```
move_swap_rounds(schedule, r1, r2):
  new_schedule = deep_copy(schedule)
  swap new_schedule[r1] and new_schedule[r2]
  return (new_schedule, True)

move_swap_matches(schedule, r1, i1, r2, i2):
  teams1 = teams from match at (r1, i1)
  teams2 = teams from match at (r2, i2)
  if teams1 overlaps with round2_other_teams: return invalid
  if teams2 overlaps with round1_other_teams: return invalid
  perform swap
  return (new_schedule, True)
```

**Time Complexity:**
- `move_swap_rounds`: O(R) - deep copy of rounds
- `move_swap_matches`: O(M) - check conflicts, deep copy
- `move_flip_venue`: O(1) - single tuple swap
- `move_swap_pairings`: O(P*M) where P is pairs to swap

**Library Functions Used:**
- `copy.deepcopy` - Deep copying (Python stdlib)
- `typing` - Type hints (Python stdlib)

**CS 5800 Topics:** Local search, neighborhood operators, constraint satisfaction

---

## Entry 6: Hill Climbing Optimizer
**Timestamp:** 2024-12-19  
**File:** optimizers.py  
**Change:** Implemented greedy hill climbing optimizer

**Function:** `hill_climb()`

**Rationale:** Hill climbing is a fundamental greedy local search algorithm. It repeatedly applies moves that improve the objective (reduce travel) until no improvement is found. This provides a baseline for comparison with more sophisticated methods.

**Algorithm/Pseudocode:**
```
hill_climb(schedule, teams, D, max_iters, max_no_improve):
  current = schedule
  current_score = evaluate(current)
  best = current
  best_score = current_score
  no_improve = 0
  
  for iteration in range(max_iters):
    if no_improve >= max_no_improve: break
    
    move = random_choice(move_set)
    new_schedule = apply_move(current, move)
    
    if validate(new_schedule):
      new_score = evaluate(new_schedule)
      if new_score < current_score:
        current = new_schedule
        current_score = new_score
        no_improve = 0
        if new_score < best_score:
          best = new_schedule
          best_score = new_score
      else:
        no_improve++
  
  return (best, best_score, log)
```

**Time Complexity:** O(max_iters * (move_cost + eval_cost + validation_cost))
- Typically O(max_iters * R * (M + N)) where R=rounds, M=matches, N=teams

**Library Functions Used:**
- `random.choice`, `random.randint`, `random.sample` - Random selection (Python stdlib)
- `time.time` - Timing (Python stdlib)

**CS 5800 Topics:** Greedy algorithms, local search, hill climbing

---

## Entry 7: Simulated Annealing Optimizer
**Timestamp:** 2024-12-19  
**File:** optimizers.py  
**Change:** Implemented simulated annealing optimizer

**Function:** `simulated_annealing()`

**Rationale:** Simulated annealing escapes local optima by accepting worse solutions with probability e^(-delta/T). Temperature decreases over time, allowing exploration early and exploitation later. This is a metaheuristic that often outperforms hill climbing.

**Algorithm/Pseudocode:**
```
simulated_annealing(schedule, teams, D, T0, decay, max_iters):
  current = schedule
  current_score = evaluate(current)
  best = current
  best_score = current_score
  T = T0
  
  for iteration in range(max_iters):
    move = random_choice(move_set)
    new_schedule = apply_move(current, move)
    
    if validate(new_schedule):
      new_score = evaluate(new_schedule)
      delta = new_score - current_score
      
      if delta < 0 or random() < exp(-delta / T):
        current = new_schedule
        current_score = new_score
        if new_score < best_score:
          best = new_schedule
          best_score = new_score
      
      T = T * decay
  
  return (best, best_score, log)
```

**Time Complexity:** Same as hill_climb, with additional acceptance probability calculation O(1)

**Library Functions Used:**
- `math.exp` - Exponential for acceptance probability (Python stdlib)
- `random.random` - Random number generation (Python stdlib)

**CS 5800 Topics:** Simulated annealing, stochastic optimization, metaheuristics, temperature schedules

---

## Entry 8: Experiment Harness
**Timestamp:** 2024-12-19  
**File:** experiments/run_experiment.py  
**Change:** Created reproducible experiment framework

**Features:**
- Batch experiments across multiple N values and seeds
- JSON output per run with full metadata
- CSV summary for analysis
- Reproducible with fixed seeds

**Rationale:** Reproducibility is critical for scientific evaluation. The framework ensures all parameters are recorded and experiments can be recreated. JSON provides detailed logs while CSV enables easy analysis.

**Time Complexity:** O(num_experiments * (generation + optimization_time))
- Generation: O(N²) for distance matrix
- Optimization: Varies by optimizer and iterations

**Library Functions Used:**
- `json.dump` - JSON serialization (Python stdlib)
- `csv.writer` - CSV writing (Python stdlib)
- `datetime.datetime` - Timestamps (Python stdlib)

**CS 5800 Topics:** Experimental methodology, reproducibility, data collection

---

## Entry 9: Exact Solver (CP-SAT)
**Timestamp:** 2024-12-19  
**File:** exact_solver.py  
**Change:** Implemented exact solver using constraint programming

**Function:** `solve_exact()`

**Rationale:** Exact solvers provide optimal solutions for small instances, serving as a benchmark for heuristic methods. CP-SAT uses constraint propagation and search to find optimal solutions. Limited to N <= 10 due to exponential complexity.

**Algorithm/Pseudocode:**
```
solve_exact(teams, D):
  Create CP-SAT model
  
  Variables: match_vars[(round, home, away)] = BoolVar
  
  Constraints:
    - Each team plays once per round
    - Each pair plays once in tournament
    - Max consecutive away games
    - No immediate repeaters
    - Home/away balance
  
  Objective: minimize sum of travel distances
  
  Solve with CP-SAT solver
  Extract solution
  return (schedule, score, log)
```

**Time Complexity:** Exponential in worst case, but CP-SAT uses efficient constraint propagation. Practical for N <= 10.

**Library Functions Used:**
- `ortools.sat.python.cp_model` - CP-SAT solver (ortools library, optional)

**CS 5800 Topics:** Constraint programming, integer programming, exact algorithms, optimization

---

## Entry 10: Visualization Module
**Timestamp:** 2024-12-19  
**File:** visualize.py  
**Change:** Created visualization utilities

**Functions:**
- `create_team_map()` - Interactive Folium map with team locations and routes
- `create_schedule_grid()` - Schedule grid/heatmap visualization
- `save_map_html()` - Export map to HTML

**Rationale:** Visualization is essential for understanding schedules and travel patterns. Interactive maps allow users to see geographic relationships and team routes. Schedule grids provide quick inspection of match assignments.

**Library Functions Used:**
- `folium.Map`, `folium.Marker`, `folium.PolyLine` - Interactive maps (folium library, optional)
- `pandas.DataFrame` - Data manipulation for grids (pandas library, optional)

**CS 5800 Topics:** Data visualization, user interfaces

---

## Entry 11: Streamlit Interactive Application
**Timestamp:** 2024-12-19  
**File:** streamlit_app.py  
**Change:** Created comprehensive web application

**Features:**
- Interactive team generation with configurable parameters
- Optimizer selection and parameter tuning
- Real-time visualization (maps, schedule grids, statistics)
- Side-by-side comparison of optimizers
- Export functionality (JSON, HTML, CSV)

**Rationale:** Interactive applications make the system accessible to users without programming knowledge. Streamlit provides rapid development of data apps with minimal code. The app demonstrates all functionality in one place.

**User Interface Components:**
- Sidebar: Input controls (N, seed, location, constraints, optimizer params)
- Main area: Results table, map visualization, schedule grid, export options
- Comparison mode: Side-by-side optimizer comparison

**Library Functions Used:**
- `streamlit` - Web application framework (streamlit library)
- `pandas.DataFrame` - Data tables (pandas library)
- `streamlit.components.v1.html` - HTML embedding (streamlit library)

**CS 5800 Topics:** User interfaces, interactive applications, data visualization

---

## Entry 12: Requirements and Dependencies
**Timestamp:** 2024-12-19  
**File:** requirements.txt  
**Change:** Created dependency management file

**Dependencies:**
- `streamlit>=1.28.0` - Web application
- `folium>=0.14.0` - Map visualization
- `pandas>=2.0.0` - Data manipulation
- `ortools>=9.8.0` - Optional, for exact solver

**Rationale:** Dependency management ensures reproducible environments. Separating core and optional dependencies allows users to install only what they need.

**CS 5800 Topics:** Software engineering, dependency management

---

