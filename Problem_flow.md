# Project: Traveling Tournament Problem (TTP) Solver
**Status:** MVP / Algorithmic Core  
**Domain:** Operations Research, Combinatorial Optimization, Scheduling


## Executive summary
This repository implements an optimized tournament scheduler that minimizes total team travel under realistic scheduling constraints. This document (the "Problem Flow") is a precise implementation plan and development checklist: data contracts, constraints, module APIs, optimization moves, experiment protocol, testing plan, visualization, and a 4‑week milestone schedule with measurable acceptance criteria.

Goals (measurable)
- Produce a validator-safe scheduler that enforces flow constraints and common TTP constraints.
- Implement modular heuristic optimizers (hill-climbing and simulated annealing) and a CP-SAT exact solver for small N (N <= 10).
- Provide reproducible experiments and a minimal visualization to inspect schedules and team tours.
- Deliver unit tests covering core behavior and a small experiment harness that records baseline vs optimized travel.

Success metrics
- Correctness: `validate_schedule(...)` returns OK on produced schedules and flags violations otherwise.
- Quality: For small instances (N=6,8,10) heuristics should reduce baseline travel by at least 10% on average across seeds (target 10–30%).
- Reproducibility: `experiments/run_experiment.py` produces CSV/JSON records with seed, baseline, best, runtime and constraint-violation indicators.


## Data contract (types & shapes)
All modules should assume these canonical shapes.
- Team: dict with {'id': int, 'name': str, 'lat': float, 'lon': float}
- Teams: List[Team]
- Distance matrix `D`: List[List[float]] where `D[i][j]` is km between team i and j (`D[i][i] = 0.0`)
- Match: Tuple[int, int] == (home_team_id, away_team_id)
- Round: List[Match]
- Schedule / Season: List[Round]
- Evaluation outputs: `per_team: List[float]`, `total: float`

Contracts for key functions (informal):
- `generate_teams(n: int, center=(lat,lon), spread_km=20) -> Teams`
- `distance_matrix(teams: Teams) -> D`
- `round_robin_pairs(teams: Teams) -> Schedule`
- `evaluate_schedule_travel(rounds: Schedule, teams: Teams, D: D) -> (per_team, total)`


## Chosen constraints (defaults)
I selected conservative, realistic defaults; they may be adjusted later.
1. Max consecutive away games `k = 3` (no team may be scheduled for more than 3 consecutive away rounds).
2. No immediate repeaters: if A@B occurs in round t then B@A is forbidden in round t+1.
3. Home/away balance for DRR: each team should have home games within ±1 of away games (i.e., perfectly balanced or off by one when odd number of rounds).
4. No team plays >1 match per round; all matches must reference existing team ids.
5. For odd N, byes are allowed (represented by `-1` id) and count as staying at home (no travel).


## Validators (prototypes & behavior)
Create `validators.py`. Each function returns `(ok: bool, reasons: List[str])` where `ok` is True when schedule passes the check.
- `validate_schedule(schedule: Schedule, n_teams: int) -> (bool, List[str])`
  - High-level: ensure each round uses valid team ids, no duplicate appearances in a round, and length is consistent.
- `check_max_consecutive_aways(schedule: Schedule, k: int=3) -> (bool, List[str])`
  - Per-team scan of consecutive away rounds; returns violations listing team id, start round, length.
- `check_repeaters(schedule: Schedule) -> (bool, List[str])`
  - Detects immediate reversals: (A@B in r) followed by (B@A in r+1).
- `check_home_away_balance(schedule: Schedule, n_teams: int) -> (bool, List[str])`
  - For DRR, count home vs away per team and ensure balance ±1.

Validators must NOT mutate schedules. They should be fast (O(R * N)) and include optional `verbose` output mode for debugging.


## Modules & API sketch (files to create/update)
- `tourney_starter.py` — keep as the core utilities (haversine, generate_teams, distance_matrix, round_robin_pairs, evaluate_schedule_travel, example_run). Improve docstrings and add type hints where missing.
- `validators.py` — implement the validator functions above.
- `optimizers.py` — implement move primitives and high-level optimizers (hill-climb, simulated annealing). Export:
  - Move primitives: `move_swap_rounds(schedule, r1, r2)`, `move_swap_matches(schedule, r1, i1, r2, i2)`, `move_flip_venue(schedule, round_idx, match_idx)`, `move_swap_pairings(schedule, r1, r2, pairs_to_swap)`.
  - Heuristics: `hill_climb(schedule, teams, D, moves, max_iters=1000, validate=True) -> (best_schedule, best_score, log)`.
  - `simulated_annealing(schedule, teams, D, moves, T0=1.0, decay=0.995, max_iters=10000, validate=True) -> (best_schedule, best_score, log)`.
  - Logs: a small dict or object with fields {best_score, iter, time_elapsed, improvements: List[(iter, delta)]}
- `exact_solver.py` (optional / requires `ortools`) — for N <= 10 build a CP-SAT model to minimize travel under constraints. Keep core logic behind an optional import guard and descriptive error if `ortools` is unavailable.
- `experiments/run_experiment.py` — small harness to run baseline, heuristics, SA, and exact solver (when available). Save output records to `experiments/results/YYYYMMDD-hhmmss-seed.json` and a CSV summary.
- `visualize.py` (optional) — small helpers to plot schedules and team tours using `folium` (map) and `pandas` (schedule heatmap). Keep optional dependencies.
- `tests/` — unit tests using `unittest` or `pytest` (project uses stdlib only by default; prefer `unittest` to avoid external deps).


## Move primitives (semantics & preconditions)
Each move primitive returns a new schedule (deep copy) and does not modify input schedule in-place.
1. `move_swap_rounds(schedule, r1, r2)`
   - Swaps entire rounds r1 and r2.
   - Precondition: 0 <= r1,r2 < R.
   - Effect: changes temporal order of matches; cheap to evaluate.
2. `move_swap_matches(schedule, r1, i1, r2, i2)`
   - Swap single matches between rounds.
   - Precondition: teams in swapped matches must not conflict (no team appears twice in same round after swap).
3. `move_flip_venue(schedule, round_idx, match_idx)`
   - Swap home/away for a given match.
   - Precondition: flipping should keep home/away balance within allowed limits (if `validate=True` the optimizer will discard illegal flips).
4. `move_swap_pairings(schedule, r1, r2, pairs_to_swap)`
   - More complex: swap subsets of matches between rounds ensuring no conflicts.

Each move should provide a small `valid` boolean indicating whether the move is legal wrt immediate per-round conflicts (e.g., duplicates in the same round). Higher-level validators enforce global constraints.


## Optimization algorithms (details)
Designs are modular so new moves/acceptance policies can be added.

Hill Climbing (greedy)
- Start with base schedule (SRR / DRR).
- Repeatedly sample from the move set (uniform or biased towards promising moves) and apply move if it improves total travel and passes `validate(schedule)` (if enabled).
- Stop after `max_no_improve` iterations or `max_iters`.
- Track best solution and return logs.

Simulated Annealing
- Same move set but accept worse solutions with probability e^{-delta/T}.
- Temperature schedule: T <- T * decay each iteration or every `k` iterations.
- Use randomized neighbor selection; keep record of best found.

Exact solver (CP-SAT)
- For N <= 10 encode schedule as binary/time assignment variables and add constraints (no team plays twice in round, max_consecutive_aways via sequence constraints, no repeaters, home balance), objective is travel distance computed via precomputed D and a linearization/approximation. Document limits: CP-SAT formulation can grow quickly — expect slow solves > 10 teams.


## Experiment protocol (reproducible)
Create `experiments/README.md` describing the procedure.
- Experiment inputs: `N`, `seed`, `num_repeats` (default 5), `optimizers` list (['greedy','simanneal','exact' if available])
- For each repeat: generate teams (seeded), compute D, generate base schedule, validate base schedule and record violations.
- Run each optimizer, time it, record best schedule and score and any constraint violations (if `validate=False` allowed for internal moves, record the final validator result).
- Output JSON summary per-run with keys: {timestamp, seed, N, baseline_total, optimizer, best_total, runtime_s, improvements, violations}
- Produce a CSV summary across repeats for plotting and reporting.

Naming & reproducibility
- File names: `results/{optimizer}/{N}-{seed}-{timestamp}.json`
- Fix random seeds in `random` and `numpy` (if used) and record them in JSON.


## Tests & validation plan
Add `tests/test_core.py` covering:
- `round_robin_pairs` for even and odd N (validate each team plays exactly once per round, bye handled correctly).
- `evaluate_schedule_travel` correctness on small hand-crafted layout (4 teams arranged as two close pairs and two distant — check travel sums).
- Validators: `check_max_consecutive_aways`, `check_repeaters`, `check_home_away_balance` behavior on constructed violations.
- Optimizer smoke tests: run `hill_climb` / `simulated_annealing` for a small N (6) and confirm it returns a valid schedule and does not increase travel by > 100x (sanity).

CI suggestion (optional): add a GitHub Action that runs the tests and a single experiment on push to main.


## Visualization & reporting
Minimal deliverable: a single HTML map (folium) showing team stadiums and the route taken by a representative team under the schedule. Also a schedule grid (CSV or simple heatmap image) for quick inspection.


## Milestones (4-week realistic plan)
Assuming part-time student pace, this is a conservative 4-week schedule. Adjust if you want to accelerate.

Week 1 — Core & Validators (acceptance: unit tests for basic functions pass)
- Tasks:
  - Clean up `tourney_starter.py` docstrings and type hints.
  - Implement `validators.py` and unit tests for validators.
  - Add `tests/test_core.py` for `round_robin_pairs` and `evaluate_schedule_travel`.
- Acceptance criteria: all tests in `tests/test_core.py` pass locally.

Week 2 — Move primitives & greedy optimizer (acceptance: heuristics reduce baseline on some seeds)
- Tasks:
  - Implement move primitives in `optimizers.py`.
  - Implement `hill_climb` and the greedy swap heuristic improved to be configurable.
  - Add smoke tests for optimizer.
- Acceptance criteria: hill-climb reduces total travel on at least 1/3 of seeds for N in [6,8,10].

Week 3 — Simulated Annealing & experiment harness (acceptance: reproducible experiments saved)
- Tasks:
  - Implement `simulated_annealing` in `optimizers.py`.
  - Add `experiments/run_experiment.py` and JSON/CSV output.
  - Run and save baseline experiments for N = [6,8,10] with 5 seeds each.
- Acceptance criteria: experiments generate JSON outputs and a CSV summary; SA sometimes outperforms greedy.

Week 4 — Exact solver (optional) + visualization + final report
- Tasks:
  - Add `exact_solver.py` using CP-SAT (optional dependency). Wrap imports and provide helpful message if not installed.
  - Add `visualize.py` to render a schedule map and schedule grid.
  - Prepare short final report describing algorithms tried, parameter choices, and a results table.
- Acceptance criteria: exact solver runs for N<=8 within reasonable time (minutes) and visuals produced for a sample schedule.


## Development checklist (ready-to-implement)
- [ ] Update `tourney_starter.py` with annotations and small refactors.
- [ ] Create `validators.py` and tests.
- [ ] Create `optimizers.py` with move primitives and hill-climb.
- [ ] Create `experiments/run_experiment.py` and `experiments/README.md`.
- [ ] Add `tests/` and CI (optional GitHub Actions workflow).
- [ ] (Optional) Add `exact_solver.py` and `visualize.py`.


## Next immediate actions (what I will implement first)
1. Add `validators.py` with the functions described and unit tests for them. This unlocks safe optimizer iterations.
2. Improve `tourney_starter.py` typing and small correctness fixes if any.
3. Implement `optimizers.py` (move primitives + hill-climb).

If you'd like, I can now implement the first action (`validators.py` + tests) and run the tests locally; say "yes, implement validators" and I will proceed and report back with the code changes and test results.
