"""
Optimization algorithms for tournament scheduling.

This module provides:
- Move primitives for schedule modification
- Hill climbing optimizer (greedy local search)
- Simulated annealing optimizer (stochastic local search)

All move primitives return new schedules (deep copies) and do not mutate input.
"""

import copy
import random
import time
from typing import List, Tuple, Dict, Any, Callable, Optional

from .tourney_starter import evaluate_schedule_travel
from .validators import (
    validate_schedule,
    check_max_consecutive_aways,
    check_repeaters,
    check_home_away_balance,
)


def move_swap_rounds(schedule: List[List[Tuple[int, int]]], r1: int, r2: int) -> Tuple[List[List[Tuple[int, int]]], bool]:
    """
    Swap two entire rounds in the schedule.
    
    Args:
        schedule: List of rounds, each round is a list of (home_id, away_id) tuples
        r1: Index of first round to swap
        r2: Index of second round to swap
        
    Returns:
        Tuple of (new_schedule, is_valid):
        - new_schedule: Deep copy of schedule with rounds swapped
        - is_valid: Always True (round swaps don't create per-round conflicts)
        
    Time Complexity: O(R) where R is number of rounds (deep copy)
    """
    if r1 < 0 or r2 < 0 or r1 >= len(schedule) or r2 >= len(schedule):
        return copy.deepcopy(schedule), False
    
    new_schedule = copy.deepcopy(schedule)
    new_schedule[r1], new_schedule[r2] = new_schedule[r2], new_schedule[r1]
    return new_schedule, True


def move_swap_matches(
    schedule: List[List[Tuple[int, int]]], 
    r1: int, i1: int, 
    r2: int, i2: int
) -> Tuple[List[List[Tuple[int, int]]], bool]:
    """
    Swap two matches between different rounds.
    
    Precondition: Teams in swapped matches must not conflict (no team appears
    twice in same round after swap).
    
    Args:
        schedule: List of rounds
        r1: Index of first round
        i1: Index of match in first round
        r2: Index of second round
        i2: Index of match in second round
        
    Returns:
        Tuple of (new_schedule, is_valid):
        - new_schedule: Deep copy with matches swapped
        - is_valid: True if swap doesn't create conflicts, False otherwise
    """
    if (r1 < 0 or r2 < 0 or r1 >= len(schedule) or r2 >= len(schedule) or
        i1 < 0 or i2 < 0 or i1 >= len(schedule[r1]) or i2 >= len(schedule[r2])):
        return copy.deepcopy(schedule), False
    
    # Get teams from both matches
    match1 = schedule[r1][i1]
    match2 = schedule[r2][i2]
    teams1 = {match1[0], match1[1]}
    teams2 = {match2[0], match2[1]}
    
    # Check for conflicts: if any team from match1 appears in round2 (excluding match2)
    # or any team from match2 appears in round1 (excluding match1)
    round1_teams = set()
    for idx, match in enumerate(schedule[r1]):
        if idx != i1:
            round1_teams.add(match[0])
            round1_teams.add(match[1])
    
    round2_teams = set()
    for idx, match in enumerate(schedule[r2]):
        if idx != i2:
            round2_teams.add(match[0])
            round2_teams.add(match[1])
    
    # Check conflicts (excluding -1 for byes)
    teams1_no_bye = {t for t in teams1 if t != -1}
    teams2_no_bye = {t for t in teams2 if t != -1}
    
    if teams1_no_bye & round2_teams or teams2_no_bye & round1_teams:
        return copy.deepcopy(schedule), False
    
    # Perform swap
    new_schedule = copy.deepcopy(schedule)
    new_schedule[r1][i1], new_schedule[r2][i2] = new_schedule[r2][i2], new_schedule[r1][i1]
    return new_schedule, True


def move_flip_venue(schedule: List[List[Tuple[int, int]]], round_idx: int, match_idx: int) -> Tuple[List[List[Tuple[int, int]]], bool]:
    """
    Flip home/away for a given match (swap the tuple order).
    
    Precondition: Flipping should keep home/away balance within allowed limits.
    This function performs the flip; validators check balance constraints.
    
    Args:
        schedule: List of rounds
        round_idx: Index of round containing the match
        match_idx: Index of match within the round
        
    Returns:
        Tuple of (new_schedule, is_valid):
        - new_schedule: Deep copy with venue flipped
        - is_valid: Always True (flip doesn't create per-round conflicts)
    """
    if (round_idx < 0 or round_idx >= len(schedule) or
        match_idx < 0 or match_idx >= len(schedule[round_idx])):
        return copy.deepcopy(schedule), False
    
    new_schedule = copy.deepcopy(schedule)
    home_id, away_id = new_schedule[round_idx][match_idx]
    new_schedule[round_idx][match_idx] = (away_id, home_id)
    return new_schedule, True


def move_swap_pairings(
    schedule: List[List[Tuple[int, int]]], 
    r1: int, r2: int, 
    pairs_to_swap: List[Tuple[int, int]]
) -> Tuple[List[List[Tuple[int, int]]], bool]:
    """
    Swap subsets of matches between rounds ensuring no conflicts.
    
    This is a more complex move that swaps multiple matches at once.
    
    Args:
        schedule: List of rounds
        r1: Index of first round
        r2: Index of second round
        pairs_to_swap: List of (match_idx_in_r1, match_idx_in_r2) tuples
        
    Returns:
        Tuple of (new_schedule, is_valid):
        - new_schedule: Deep copy with matches swapped
        - is_valid: True if swap doesn't create conflicts
    """
    if r1 < 0 or r2 < 0 or r1 >= len(schedule) or r2 >= len(schedule):
        return copy.deepcopy(schedule), False
    
    # Collect all teams from matches to be swapped
    r1_teams_to_swap = set()
    r2_teams_to_swap = set()
    
    for idx1, idx2 in pairs_to_swap:
        if idx1 >= len(schedule[r1]) or idx2 >= len(schedule[r2]):
            return copy.deepcopy(schedule), False
        match1 = schedule[r1][idx1]
        match2 = schedule[r2][idx2]
        r1_teams_to_swap.add(match1[0])
        r1_teams_to_swap.add(match1[1])
        r2_teams_to_swap.add(match2[0])
        r2_teams_to_swap.add(match2[1])
    
    # Check conflicts with matches not being swapped
    r1_other_teams = set()
    r1_swap_indices = {idx1 for idx1, _ in pairs_to_swap}
    for idx, match in enumerate(schedule[r1]):
        if idx not in r1_swap_indices:
            r1_other_teams.add(match[0])
            r1_other_teams.add(match[1])
    
    r2_other_teams = set()
    r2_swap_indices = {idx2 for _, idx2 in pairs_to_swap}
    for idx, match in enumerate(schedule[r2]):
        if idx not in r2_swap_indices:
            r2_other_teams.add(match[0])
            r2_other_teams.add(match[1])
    
    # Remove -1 (bye) from consideration
    r1_teams_to_swap = {t for t in r1_teams_to_swap if t != -1}
    r2_teams_to_swap = {t for t in r2_teams_to_swap if t != -1}
    r1_other_teams = {t for t in r1_other_teams if t != -1}
    r2_other_teams = {t for t in r2_other_teams if t != -1}
    
    # Check for conflicts
    if r1_teams_to_swap & r2_other_teams or r2_teams_to_swap & r1_other_teams:
        return copy.deepcopy(schedule), False
    
    # Perform swap
    new_schedule = copy.deepcopy(schedule)
    for idx1, idx2 in pairs_to_swap:
        new_schedule[r1][idx1], new_schedule[r2][idx2] = new_schedule[r2][idx2], new_schedule[r1][idx1]
    
    return new_schedule, True


def _validate_schedule_constraints(schedule: List[List[Tuple[int, int]]], n_teams: int) -> Tuple[bool, List[str]]:
    """
    Internal helper to validate all constraints.
    
    Returns True if schedule passes all validators.
    """
    ok1, reasons1 = validate_schedule(schedule, n_teams)
    if not ok1:
        return False, reasons1
    
    ok2, reasons2 = check_max_consecutive_aways(schedule, k=3)
    if not ok2:
        return False, reasons2
    
    ok3, reasons3 = check_repeaters(schedule)
    if not ok3:
        return False, reasons3
    
    ok4, reasons4 = check_home_away_balance(schedule, n_teams)
    if not ok4:
        return False, reasons4
    
    return True, []


def hill_climb(
    schedule: List[List[Tuple[int, int]]],
    teams: List[Dict[str, Any]],
    D: List[List[float]],
    moves: Optional[List[Callable]] = None,
    max_iters: int = 1000,
    max_no_improve: int = 100,
    validate: bool = True,
    random_seed: Optional[int] = None
) -> Tuple[List[List[Tuple[int, int]]], float, Dict[str, Any]]:
    """
    Hill climbing optimizer using greedy local search.
    
    Repeatedly samples from move set and applies move if it improves total travel
    and passes validation (if enabled). Stops after max_no_improve iterations
    without improvement or max_iters total iterations.
    
    Args:
        schedule: Initial schedule (list of rounds)
        teams: List of team dictionaries
        D: Distance matrix
        moves: List of move functions (default: [swap_rounds, swap_matches, flip_venue])
        max_iters: Maximum total iterations
        max_no_improve: Maximum iterations without improvement before stopping
        validate: If True, only accept moves that pass all validators
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (best_schedule, best_score, log_dict):
        - best_schedule: Best schedule found
        - best_score: Total travel distance of best schedule
        - log_dict: Dictionary with 'best_score', 'iter', 'time_elapsed', 'improvements'
        
    Time Complexity: O(max_iters * (move_cost + eval_cost + validation_cost))
        Typically O(max_iters * (R*M + R*N + R*M)) = O(max_iters * R * (M + N))
        
    CS 5800 Topics: Greedy algorithms, local search, hill climbing
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    if moves is None:
        moves = [move_swap_rounds, move_swap_matches, move_flip_venue]
    
    n_teams = len(teams)
    current_schedule = copy.deepcopy(schedule)
    _, current_score = evaluate_schedule_travel(current_schedule, teams, D)
    
    best_schedule = copy.deepcopy(current_schedule)
    best_score = current_score
    
    improvements = []
    start_time = time.time()
    no_improve_count = 0
    
    for iteration in range(max_iters):
        if no_improve_count >= max_no_improve:
            break
        
        # Select random move
        move_func = random.choice(moves)
        
        # Generate move parameters based on move type
        if move_func == move_swap_rounds:
            if len(current_schedule) < 2:
                continue
            r1, r2 = random.sample(range(len(current_schedule)), 2)
            new_schedule, is_valid = move_func(current_schedule, r1, r2)
            
        elif move_func == move_swap_matches:
            if len(current_schedule) < 2:
                continue
            r1, r2 = random.sample(range(len(current_schedule)), 2)
            if len(current_schedule[r1]) == 0 or len(current_schedule[r2]) == 0:
                continue
            i1 = random.randint(0, len(current_schedule[r1]) - 1)
            i2 = random.randint(0, len(current_schedule[r2]) - 1)
            new_schedule, is_valid = move_func(current_schedule, r1, i1, r2, i2)
            
        elif move_func == move_flip_venue:
            r = random.randint(0, len(current_schedule) - 1)
            if len(current_schedule[r]) == 0:
                continue
            i = random.randint(0, len(current_schedule[r]) - 1)
            new_schedule, is_valid = move_func(current_schedule, r, i)
            
        else:
            continue
        
        if not is_valid:
            continue
        
        # Validate constraints if enabled
        if validate:
            ok, _ = _validate_schedule_constraints(new_schedule, n_teams)
            if not ok:
                continue
        
        # Evaluate new schedule
        _, new_score = evaluate_schedule_travel(new_schedule, teams, D)
        
        # Accept if better
        if new_score < current_score - 1e-6:  # Small epsilon for floating point
            current_schedule = new_schedule
            current_score = new_score
            no_improve_count = 0
            
            if new_score < best_score - 1e-6:
                best_schedule = copy.deepcopy(new_schedule)
                best_score = new_score
                improvements.append((iteration, best_score - current_score))
        else:
            no_improve_count += 1
    
    elapsed_time = time.time() - start_time
    
    log = {
        'best_score': best_score,
        'iter': iteration + 1,
        'time_elapsed': elapsed_time,
        'improvements': improvements
    }
    
    return best_schedule, best_score, log


def simulated_annealing(
    schedule: List[List[Tuple[int, int]]],
    teams: List[Dict[str, Any]],
    D: List[List[float]],
    moves: Optional[List[Callable]] = None,
    T0: float = 1.0,
    decay: float = 0.995,
    max_iters: int = 10000,
    validate: bool = True,
    random_seed: Optional[int] = None
) -> Tuple[List[List[Tuple[int, int]]], float, Dict[str, Any]]:
    """
    Simulated annealing optimizer using stochastic local search.
    
    Accepts worse solutions with probability e^(-delta/T) to escape local optima.
    Temperature decreases each iteration: T <- T * decay.
    
    Args:
        schedule: Initial schedule
        teams: List of team dictionaries
        D: Distance matrix
        moves: List of move functions (default: [swap_rounds, swap_matches, flip_venue])
        T0: Initial temperature
        decay: Temperature decay rate per iteration
        max_iters: Maximum iterations
        validate: If True, only accept moves that pass all validators
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (best_schedule, best_score, log_dict):
        - best_schedule: Best schedule found (tracked separately from current)
        - best_score: Total travel distance of best schedule
        - log_dict: Dictionary with 'best_score', 'iter', 'time_elapsed', 'improvements', 'temperature'
        
    Time Complexity: O(max_iters * (move_cost + eval_cost + validation_cost))
        Same as hill_climb but with acceptance probability calculation
        
    CS 5800 Topics: Simulated annealing, stochastic optimization, metaheuristics
    """
    import math
    
    if random_seed is not None:
        random.seed(random_seed)
    
    if moves is None:
        moves = [move_swap_rounds, move_swap_matches, move_flip_venue]
    
    n_teams = len(teams)
    current_schedule = copy.deepcopy(schedule)
    _, current_score = evaluate_schedule_travel(current_schedule, teams, D)
    
    best_schedule = copy.deepcopy(current_schedule)
    best_score = current_score
    
    improvements = []
    start_time = time.time()
    T = T0
    
    for iteration in range(max_iters):
        # Select random move
        move_func = random.choice(moves)
        
        # Generate move parameters
        if move_func == move_swap_rounds:
            if len(current_schedule) < 2:
                T *= decay
                continue
            r1, r2 = random.sample(range(len(current_schedule)), 2)
            new_schedule, is_valid = move_func(current_schedule, r1, r2)
            
        elif move_func == move_swap_matches:
            if len(current_schedule) < 2:
                T *= decay
                continue
            r1, r2 = random.sample(range(len(current_schedule)), 2)
            if len(current_schedule[r1]) == 0 or len(current_schedule[r2]) == 0:
                T *= decay
                continue
            i1 = random.randint(0, len(current_schedule[r1]) - 1)
            i2 = random.randint(0, len(current_schedule[r2]) - 1)
            new_schedule, is_valid = move_func(current_schedule, r1, i1, r2, i2)
            
        elif move_func == move_flip_venue:
            r = random.randint(0, len(current_schedule) - 1)
            if len(current_schedule[r]) == 0:
                T *= decay
                continue
            i = random.randint(0, len(current_schedule[r]) - 1)
            new_schedule, is_valid = move_func(current_schedule, r, i)
            
        else:
            T *= decay
            continue
        
        if not is_valid:
            T *= decay
            continue
        
        # Validate constraints if enabled
        if validate:
            ok, _ = _validate_schedule_constraints(new_schedule, n_teams)
            if not ok:
                T *= decay
                continue
        
        # Evaluate new schedule
        _, new_score = evaluate_schedule_travel(new_schedule, teams, D)
        
        # Calculate delta (positive means worse)
        delta = new_score - current_score
        
        # Accept if better or with probability e^(-delta/T)
        if delta < 0 or (T > 0 and random.random() < math.exp(-delta / T)):
            current_schedule = new_schedule
            current_score = new_score
            
            if new_score < best_score - 1e-6:
                best_schedule = copy.deepcopy(new_schedule)
                best_score = new_score
                improvements.append((iteration, best_score - current_score))
        
        # Update temperature
        T *= decay
    
    elapsed_time = time.time() - start_time
    
    log = {
        'best_score': best_score,
        'iter': iteration + 1,
        'time_elapsed': elapsed_time,
        'improvements': improvements,
        'final_temperature': T
    }
    
    return best_schedule, best_score, log

