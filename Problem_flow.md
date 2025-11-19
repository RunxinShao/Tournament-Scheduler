# Project: Traveling Tournament Problem (TTP) Solver
**Status:** MVP / Algorithmic Core  
**Domain:** Operations Research, Combinatorial Optimization, Scheduling  

## 1. Project Overview
This system generates and optimizes sports tournament schedules to minimize total team travel distance. It models the **Traveling Tournament Problem (TTP)**, an NP-hard optimization problem that combines:
1.  **Round-Robin Scheduling:** Who plays whom and when.
2.  **Traveling Salesman Problem (TSP):** optimizing the route each team takes through the schedule.

## 2. Core Data Structures
* **Distance Matrix ($D$):** An $N \times N$ matrix where $D_{i,j}$ is the geodetic distance (Haversine) between Team $i$ and Team $j$.
* **Schedule Representation:** A list of Rounds. Each Round is a list of Matches `(home_id, away_id)`.
    * *Constraint:* In every round, every team must play exactly once (assuming even $N$).

## 3. Current Capabilities (MVP)
* **Ingestion:** Synthetic generation of Teams with (Lat, Lon).
* **Base Scheduling:** * **Single Round Robin (SRR):** Uses the Polygon/Circle Method.
    * **Double Round Robin (DRR):** Mirrors the SRR (Home/Away flipped) to ensure perfectly balanced venues.
* **Evaluation:** Sequential travel calculation. Teams start at home, travel to away games, stay for consecutive away games, and return home at season end.
* **Optimization (Hill Climbing):** * **Move A (Swap Rounds):** Swaps time slots of two complete rounds.
    * **Move B (Flip Venue):** Swaps Home/Away designation for a specific match (Note: Currently unconstrained, may affect Home/Away balance).

## 4. Agent Objectives & Roadmap
The goal is to evolve this from a script to a production-grade solver.

### Phase 1: Constraints & Validity (Priority)
* **Flow Constraints:** Ensure teams do not play more than $k$ consecutive away games (usually $k=3$).
* **Repeat Constraints:** In DRR, teams should not play A vs B in Week $t$ and B vs A in Week $t+1$ (No "Repeaters").

### Phase 2: Advanced Optimization
* **Simulated Annealing:** Implement temperature decay to escape local minima.
* **Integer Programming:** Use `OR-Tools` (CP-SAT) to find mathematically optimal schedules for $N < 10$.

### Phase 3: Visualization
* **Map Visualization:** Plot team trajectories using `folium`.
* **Schedule Grid:** Render a Pandas DataFrame heatmap of the season.

## 5. Technical Constraints
* Use **Python 3.10+** (Type hinting required).
* Avoid external dependencies for core logic (Standard Lib only). 
* Use `numpy` only for matrix heavylifting if $N > 100$.