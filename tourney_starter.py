# tourney_starter.py
# Minimal starter for Tournament Scheduler: data, distances, RR schedule, travel eval, greedy tour heuristic.
# Dependencies: only Python stdlib + math. Optional later: pandas, folium, ortools, streamlit.

import math
import random
from typing import List, Dict, Tuple

# ----------------------------
# Utilities: haversine distance
# ----------------------------
def haversine(lat1, lon1, lat2, lon2):
    # returns kilometers
    R = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ----------------------------
# Data generator: N teams with stadium coordinates
# ----------------------------
def generate_teams(n: int, center: Tuple[float,float]=(37.7749, -122.4194), spread_km=20):
    """
    Generate n teams with stadium coordinates around a center (lat,lon).
    spread_km controls dispersion.
    Returns list of dicts: [{'id':0,'name':'Team0','lat':..., 'lon':...}, ...]
    """
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
def distance_matrix(teams: List[Dict]) -> List[List[float]]:
    n = len(teams)
    D = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i==j: continue
            D[i][j] = haversine(teams[i]['lat'], teams[i]['lon'], teams[j]['lat'], teams[j]['lon'])
    return D

# ----------------------------
# Round-robin (circle method) schedule
# ----------------------------
def round_robin_pairs(teams: List[Dict]) -> List[List[Tuple[int,int]]]:
    """
    Returns rounds: list of rounds; each round is list of (home_id, away_id).
    For even n uses standard circle method. For odd n adds a bye (team id = -1).
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
def evaluate_schedule_travel(rounds: List[List[Tuple[int,int]]], teams: List[Dict], D: List[List[float]]):
    """
    Evaluate total travel under the sequential-round model:
    Each team starts at home. For each round, if team plays at home -> stays; if away -> travels from last location to venue.
    After last round, each team returns home (if not already).
    Returns per-team km and total km.
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
def greedy_optimize_tours(rounds: List[List[Tuple[int,int]]], D: List[List[float]], max_tour_len=3):
    """
    Heuristic: try to reduce travel by reordering rounds' assignments where possible to cluster a team's away matches into contiguous rounds.
    *This is a light heuristic only to illustrate improvement; not guaranteed optimal.*
    Approach:
      - For each team, list away rounds indices.
      - Try to swap matches between rounds if it reduces team's tour travel and doesn't break pairing (we ensure swap is symmetric).
    Returns new rounds (deep-copied) and boolean whether improved.
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
def example_run(n=6, seed=42):
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
