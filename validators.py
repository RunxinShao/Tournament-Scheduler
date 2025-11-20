"""
Validators for tournament schedules.

This module provides constraint checking functions for tournament schedules.
All validators return (ok: bool, reasons: List[str]) tuples where ok is True
when the schedule passes the check, and reasons contains violation descriptions.
"""

from typing import List, Tuple


def validate_schedule(schedule: List[List[Tuple[int, int]]], n_teams: int) -> Tuple[bool, List[str]]:
    """
    High-level schedule validation.
    
    Checks:
    - Each round uses valid team ids (0 to n_teams-1, or -1 for bye)
    - No team appears twice in the same round
    - Schedule length is consistent
    
    Args:
        schedule: List of rounds, each round is a list of (home_id, away_id) tuples
        n_teams: Number of teams in the tournament
        
    Returns:
        Tuple of (is_valid, list_of_violation_reasons)
    """
    reasons = []
    
    if not schedule:
        reasons.append("Schedule is empty")
        return False, reasons
    
    # Check each round
    for round_idx, round_matches in enumerate(schedule):
        if not isinstance(round_matches, list):
            reasons.append(f"Round {round_idx} is not a list")
            continue
            
        teams_in_round = set()
        
        for match_idx, match in enumerate(round_matches):
            if not isinstance(match, tuple) or len(match) != 2:
                reasons.append(f"Round {round_idx}, match {match_idx}: invalid format (expected tuple of 2)")
                continue
                
            home_id, away_id = match
            
            # Check team IDs are valid
            if home_id != -1 and (home_id < 0 or home_id >= n_teams):
                reasons.append(f"Round {round_idx}, match {match_idx}: invalid team id {home_id} (expected 0-{n_teams-1} or -1)")
            if away_id != -1 and (away_id < 0 or away_id >= n_teams):
                reasons.append(f"Round {round_idx}, match {match_idx}: invalid team id {away_id} (expected 0-{n_teams-1} or -1)")
            
            # Check no team appears twice in same round
            if home_id != -1:
                if home_id in teams_in_round:
                    reasons.append(f"Round {round_idx}: team {home_id} appears multiple times")
                teams_in_round.add(home_id)
            
            if away_id != -1:
                if away_id in teams_in_round:
                    reasons.append(f"Round {round_idx}: team {away_id} appears multiple times")
                teams_in_round.add(away_id)
            
            # Check home != away (unless bye)
            if home_id == away_id and home_id != -1:
                reasons.append(f"Round {round_idx}, match {match_idx}: team {home_id} cannot play itself")
    
    return len(reasons) == 0, reasons


def check_max_consecutive_aways(schedule: List[List[Tuple[int, int]]], k: int = 3) -> Tuple[bool, List[str]]:
    """
    Check that no team has more than k consecutive away games.
    
    Args:
        schedule: List of rounds, each round is a list of (home_id, away_id) tuples
        k: Maximum allowed consecutive away games (default 3)
        
    Returns:
        Tuple of (is_valid, list_of_violation_reasons)
    """
    reasons = []
    
    if not schedule:
        return True, reasons
    
    # Find max team ID to determine number of teams
    max_team_id = -1
    for round_matches in schedule:
        for home_id, away_id in round_matches:
            if home_id != -1:
                max_team_id = max(max_team_id, home_id)
            if away_id != -1:
                max_team_id = max(max_team_id, away_id)
    
    n_teams = max_team_id + 1 if max_team_id >= 0 else 0
    
    if n_teams == 0:
        return True, reasons
    
    # For each team, track consecutive away games
    for team_id in range(n_teams):
        consecutive_aways = 0
        max_consecutive = 0
        violation_start_round = None
        
        for round_idx, round_matches in enumerate(schedule):
            is_away = False
            
            # Check if team plays away this round
            for home_id, away_id in round_matches:
                if away_id == team_id:
                    is_away = True
                    break
                elif home_id == team_id:
                    is_away = False
                    break
            
            if is_away:
                consecutive_aways += 1
                if consecutive_aways == 1:
                    violation_start_round = round_idx
                if consecutive_aways > max_consecutive:
                    max_consecutive = consecutive_aways
            else:
                consecutive_aways = 0
                violation_start_round = None
            
            # Check violation
            if consecutive_aways > k:
                reasons.append(
                    f"Team {team_id}: {consecutive_aways} consecutive away games starting at round {violation_start_round} "
                    f"(max allowed: {k})"
                )
                # Reset to avoid duplicate messages
                consecutive_aways = 0
    
    return len(reasons) == 0, reasons


def check_repeaters(schedule: List[List[Tuple[int, int]]]) -> Tuple[bool, List[str]]:
    """
    Check for immediate reversals: if A@B occurs in round t, then B@A is forbidden in round t+1.
    
    Args:
        schedule: List of rounds, each round is a list of (home_id, away_id) tuples
        
    Returns:
        Tuple of (is_valid, list_of_violation_reasons)
    """
    reasons = []
    
    if len(schedule) < 2:
        return True, reasons
    
    for round_idx in range(len(schedule) - 1):
        current_round = schedule[round_idx]
        next_round = schedule[round_idx + 1]
        
        # Build set of (home, away) pairs in current round
        current_pairs = set()
        for home_id, away_id in current_round:
            if home_id != -1 and away_id != -1:
                current_pairs.add((home_id, away_id))
        
        # Check if next round has reversed pairs
        for home_id, away_id in next_round:
            if home_id != -1 and away_id != -1:
                reversed_pair = (away_id, home_id)
                if reversed_pair in current_pairs:
                    reasons.append(
                        f"Repeater detected: Round {round_idx} has ({reversed_pair[0]}, {reversed_pair[1]}) "
                        f"and Round {round_idx + 1} has ({home_id}, {away_id})"
                    )
    
    return len(reasons) == 0, reasons


def check_home_away_balance(schedule: List[List[Tuple[int, int]]], n_teams: int) -> Tuple[bool, List[str]]:
    """
    Check home/away balance for double round-robin.
    
    Each team should have home games within ±1 of away games (perfectly balanced
    or off by one when odd number of rounds).
    
    Args:
        schedule: List of rounds, each round is a list of (home_id, away_id) tuples
        n_teams: Number of teams in the tournament
        
    Returns:
        Tuple of (is_valid, list_of_violation_reasons)
    """
    reasons = []
    
    if not schedule:
        return True, reasons
    
    # Count home and away games for each team
    home_count = [0] * n_teams
    away_count = [0] * n_teams
    
    for round_matches in schedule:
        for home_id, away_id in round_matches:
            if home_id != -1 and home_id < n_teams:
                home_count[home_id] += 1
            if away_id != -1 and away_id < n_teams:
                away_count[away_id] += 1
    
    # Check balance for each team
    for team_id in range(n_teams):
        diff = abs(home_count[team_id] - away_count[team_id])
        if diff > 1:
            reasons.append(
                f"Team {team_id}: home/away imbalance (home: {home_count[team_id]}, "
                f"away: {away_count[team_id]}, difference: {diff})"
            )
    
    return len(reasons) == 0, reasons

