"""
Tournament Scheduler Core Utilities.

This module provides core functionality for tournament scheduling:
- Team generation with geographic coordinates
- Distance calculations using haversine formula
- Round-robin schedule generation
- Travel distance evaluation
- Basic greedy optimization heuristic

Dependencies: Python stdlib (math, random, typing, copy)
Optional later: pandas, folium, ortools, streamlit
"""

import math
import random
from typing import List, Dict, Tuple, Any

# ----------------------------
# Utilities: haversine distance
# ----------------------------
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using the haversine formula.
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
        
    Returns:
        Distance in kilometers between the two points
        
    Reference:
        https://en.wikipedia.org/wiki/Haversine_formula
    """
    R = 6371.0  # Earth's radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ----------------------------
# Data generator: N teams with stadium coordinates
# ----------------------------
def generate_teams(n: int, center: Tuple[float, float] = (37.7749, -122.4194), spread_km: float = 20.0) -> List[Dict[str, Any]]:
    """
    Generate n teams with stadium coordinates randomly distributed around a center point.
    
    Teams are generated with random offsets within a square region defined by spread_km.
    The default center is San Francisco, CA (37.7749°N, 122.4194°W).
    
    Args:
        n: Number of teams to generate (must be positive)
        center: Tuple of (latitude, longitude) in degrees for the center point
        spread_km: Maximum distance in kilometers from center (teams distributed in ±spread_km square)
        
    Returns:
        List of team dictionaries, each with keys:
        - 'id': int (0 to n-1)
        - 'name': str (e.g., 'Team1', 'Team2')
        - 'lat': float (latitude in degrees)
        - 'lon': float (longitude in degrees)
        
    Raises:
        ValueError: If n <= 0
        
    Example:
        >>> teams = generate_teams(4, center=(40.0, -74.0), spread_km=10.0)
        >>> len(teams)
        4
        >>> teams[0]['id']
        0
    """
    if n <= 0:
        raise ValueError(f"Number of teams must be positive, got {n}")
    center_lat, center_lon = center
    teams = []
    for i in range(n):
        # random offset in degrees approximated by km -> degrees (~111 km per degree lat)
        # rough conversion: 1 deg ~ 111 km; adjust for lon by cos(lat)
        dx_km = random.uniform(-spread_km, spread_km)
        dy_km = random.uniform(-spread_km, spread_km)
        dlat = dy_km / 111.0
        dlon = dx_km / (111.0 * math.cos(math.radians(center_lat)))
        teams.append({'id': i, 'name': f'Team{i+1}', 'lat': center_lat + dlat, 'lon': center_lon + dlon})
    return teams

# ----------------------------
# Distance matrix
# ----------------------------
def distance_matrix(teams: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Compute pairwise distance matrix for all teams using haversine formula.
    
    Args:
        teams: List of team dictionaries, each must have 'lat' and 'lon' keys
        
    Returns:
        Symmetric n×n matrix D where D[i][j] is the distance in kilometers
        between team i and team j. D[i][i] = 0.0 for all i.
        
    Time Complexity: O(n²) where n is the number of teams
        
    Example:
        >>> teams = [{'id': 0, 'lat': 40.0, 'lon': -74.0}, {'id': 1, 'lat': 41.0, 'lon': -75.0}]
        >>> D = distance_matrix(teams)
        >>> len(D)
        2
        >>> D[0][0]
        0.0
    """
    n = len(teams)
    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            D[i][j] = haversine(teams[i]['lat'], teams[i]['lon'], teams[j]['lat'], teams[j]['lon'])
    return D

# ----------------------------
# Round-robin (circle method) schedule
# ----------------------------
def round_robin_pairs(teams: List[Dict[str, Any]]) -> List[List[Tuple[int, int]]]:
    """
    Generate a single round-robin tournament schedule using the circle method.
    
    Each team plays every other team exactly once. For even numbers of teams,
    uses the standard circle method. For odd numbers, adds a bye (represented
    by team id -1) which is skipped in match generation.
    
    Args:
        teams: List of team dictionaries, each must have 'id' key
        
    Returns:
        List of rounds, where each round is a list of (home_id, away_id) tuples.
        For n teams:
        - If n is even: returns n-1 rounds
        - If n is odd: returns n rounds (with byes)
        
    Time Complexity: O(n²) where n is the number of teams
        
    Algorithm: Circle method (Berger tables)
    - Fix one team and rotate others
    - Alternate home/away assignment by round parity
        
    Example:
        >>> teams = [{'id': 0}, {'id': 1}, {'id': 2}, {'id': 3}]
        >>> schedule = round_robin_pairs(teams)
        >>> len(schedule)  # 4 teams -> 3 rounds
        3
    """
    n = len(teams)
    ids = list(range(n))
    bye = None
    if n % 2 == 1:
        ids.append(-1)
        bye = -1
    m = len(ids)
    rounds = []
    for r in range(m-1):
        pairs = []
        for i in range(m//2):
            a = ids[i]
            b = ids[m-1-i]
            if a == -1 or b == -1:
                # bye - skip
                continue
            # assign home/away deterministically: alternate by round parity
            if r % 2 == 0:
                pairs.append((a, b))
            else:
                pairs.append((b, a))
        # rotate (keep first fixed)
        ids = [ids[0]] + [ids[-1]] + ids[1:-1]
        rounds.append(pairs)
    return rounds

# ----------------------------
# Travel evaluation
# ----------------------------
def evaluate_schedule_travel(
    rounds: List[List[Tuple[int, int]]], 
    teams: List[Dict[str, Any]], 
    D: List[List[float]]
) -> Tuple[List[float], float]:
    """
    Evaluate total travel distance for all teams under the sequential-round model.
    
    Travel model:
    - Each team starts at their home stadium
    - For each round: if team plays at home, they stay; if away, they travel to opponent's stadium
    - After the last round, each team returns home (if not already there)
    - Teams with byes stay at their current location
    
    Args:
        rounds: List of rounds, each round is a list of (home_id, away_id) tuples
        teams: List of team dictionaries (used to determine number of teams)
        D: Distance matrix where D[i][j] is distance from team i to team j in km
        
    Returns:
        Tuple of (per_team_distances, total_distance):
        - per_team_distances: List[float] of travel distance for each team in km
        - total_distance: float sum of all team travel distances in km
        
    Time Complexity: O(R * N) where R is number of rounds and N is number of teams
        
    Example:
        >>> teams = [{'id': 0}, {'id': 1}]
        >>> rounds = [[(0, 1)]]
        >>> D = [[0.0, 100.0], [100.0, 0.0]]
        >>> per_team, total = evaluate_schedule_travel(rounds, teams, D)
        >>> total  # Team 1 travels 100km away, then 100km back = 200km
        200.0
    """
    n = len(teams)
    # location pointer: current location id for each team (start at home)
    loc = list(range(n))
    tot_team = [0.0]*n
    for rnd in rounds:
        # create a mapping: for each team, where they play this round (home team stays at own stadium, away plays at home team's stadium)
        round_loc = [None]*n
        for (home, away) in rnd:
            round_loc[home] = home
            round_loc[away] = home  # away plays at home team's stadium
        # for teams that might have byes -> round_loc remains None -> stays at home
        for t in range(n):
            if round_loc[t] is None:
                # bye or no game: stay put
                round_loc[t] = loc[t]
        # compute movement
        for t in range(n):
            if loc[t] != round_loc[t]:
                dist = D[loc[t]][round_loc[t]]
                tot_team[t] += dist
                loc[t] = round_loc[t]
        # end of round
    # return home if not at home
    for t in range(n):
        if loc[t] != t:
            tot_team[t] += D[loc[t]][t]
            loc[t] = t
    total = sum(tot_team)
    return tot_team, total

# ----------------------------
# Greedy tour optimizer (heuristic)
# ----------------------------
def greedy_optimize_tours(
    rounds: List[List[Tuple[int, int]]], 
    D: List[List[float]], 
    max_tour_len: int = 3
) -> Tuple[List[List[Tuple[int, int]]], bool]:
    """
    Greedy heuristic to reduce travel by swapping matches between rounds.
    
    This is a lightweight heuristic that attempts to improve travel by:
    - Swapping matches between rounds when teams don't conflict
    - Accepting swaps that reduce total travel distance
    - Restarting search after each improvement (greedy approach)
    
    Note: This is not guaranteed to find optimal solutions. More sophisticated
    optimizers (hill-climbing, simulated annealing) are provided in optimizers.py.
    
    Args:
        rounds: List of rounds, each round is a list of (home_id, away_id) tuples
        D: Distance matrix where D[i][j] is distance from team i to team j in km
        max_tour_len: Unused parameter (kept for compatibility)
        
    Returns:
        Tuple of (new_rounds, improved):
        - new_rounds: Deep copy of rounds (potentially modified)
        - improved: Boolean indicating if any improvement was found
        
    Time Complexity: O(R² * M² * N) where R is rounds, M is matches per round, N is teams
        (worst case, but typically exits early on first improvement)
        
    Example:
        >>> rounds = [[(0, 1), (2, 3)], [(1, 0), (3, 2)]]
        >>> D = [[0, 10, 20, 30], [10, 0, 15, 25], [20, 15, 0, 5], [30, 25, 5, 0]]
        >>> new_rounds, improved = greedy_optimize_tours(rounds, D)
        >>> isinstance(improved, bool)
        True
    """
    import copy
    rounds_new = copy.deepcopy(rounds)
    n_rounds = len(rounds_new)
    n_teams = len(D)
    improved_any = False

    # Build index: for quick lookup which pair in which round involves given team
    def find_match(round_idx, team):
        for i,(h,a) in enumerate(rounds_new[round_idx]):
            if h==team or a==team:
                return i, (h,a)
        return None, None

    # compute team travel under current schedule
    before_team, before_total = evaluate_schedule_travel(rounds_new, [{'id':i} for i in range(n_teams)], D)

    # Try simple swaps: for each pair of rounds r1<r2, swap entire match assignments between the two rounds for matches that are disjoint teams
    for r1 in range(n_rounds):
        for r2 in range(r1+1, n_rounds):
            # try swapping a single match from r1 with a single match from r2 where teams don't conflict (no team appears twice in same round)
            for i1,(h1,a1) in enumerate(rounds_new[r1]):
                for i2,(h2,a2) in enumerate(rounds_new[r2]):
                    teams1 = {h1,a1}; teams2 = {h2,a2}
                    if teams1 & teams2:
                        continue
                    # perform swap
                    rounds_candidate = copy.deepcopy(rounds_new)
                    rounds_candidate[r1][i1] = (h2,a2)
                    rounds_candidate[r2][i2] = (h1,a1)
                    _, cand_total = evaluate_schedule_travel(rounds_candidate, [{'id':i} for i in range(n_teams)], D)
                    if cand_total + 1e-6 < before_total: # improved
                        rounds_new = rounds_candidate
                        before_total = cand_total
                        improved_any = True
                        # restart search (greedy)
                        break
                if improved_any:
                    break
            if improved_any:
                break
        if improved_any:
            break

    return rounds_new, improved_any

# ----------------------------
# Example: run on 6 teams
# ----------------------------
def example_run(n: int = 6, seed: int = 42) -> None:
    """
    Example function demonstrating tournament scheduling workflow.
    
    Generates teams, creates schedule, evaluates travel, and attempts optimization.
    
    Args:
        n: Number of teams to generate
        seed: Random seed for reproducible team generation
        
    Returns:
        None (prints results to stdout)
    """
    random.seed(seed)
    teams = generate_teams(n)
    D = distance_matrix(teams)
    rounds = round_robin_pairs(teams)
    print(f"Generated {n} teams; schedule rounds: {len(rounds)}")
    for r_idx, rnd in enumerate(rounds):
        print(f"Round {r_idx+1}: " + ", ".join([f"{teams[h]['name']} vs {teams[a]['name']}" for h,a in rnd]))
    per_team, total = evaluate_schedule_travel(rounds, teams, D)
    print("\nBaseline travel per team (km):")
    for t,km in enumerate(per_team):
        print(f"  {teams[t]['name']}: {km:.1f} km")
    print(f"Total baseline travel: {total:.1f} km")

    # Try greedy optimize
    rounds2, improved = greedy_optimize_tours(rounds, D)
    per2, total2 = evaluate_schedule_travel(rounds2, teams, D)
    if improved:
        print("\nFound improvement via naive swap heuristic:")
        for t,km in enumerate(per2):
            print(f"  {teams[t]['name']}: {km:.1f} km")
        print(f"Total improved travel: {total2:.1f} km (delta: {total2-total:.1f})")
    else:
        print("\nGreedy swap heuristic found no improvement.")

if __name__ == "__main__":
    example_run()
