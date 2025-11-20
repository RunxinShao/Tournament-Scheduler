"""
Unit tests for core tournament scheduling functionality.

Tests cover:
- round_robin_pairs for even and odd N
- evaluate_schedule_travel correctness
- Validator functions with constructed violations
"""

import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tourney_starter import (
    generate_teams,
    distance_matrix,
    round_robin_pairs,
    evaluate_schedule_travel,
    haversine
)
from core.validators import (
    validate_schedule,
    check_max_consecutive_aways,
    check_repeaters,
    check_home_away_balance,
)


class TestRoundRobinPairs(unittest.TestCase):
    """Test round_robin_pairs function for even and odd numbers of teams."""
    
    def test_even_n_teams(self):
        """Test round-robin with even number of teams (4 teams -> 3 rounds)."""
        teams = [{'id': i, 'name': f'Team{i}'} for i in range(4)]
        schedule = round_robin_pairs(teams)
        
        # 4 teams should produce 3 rounds
        self.assertEqual(len(schedule), 3)
        
        # Each round should have 2 matches (4 teams / 2)
        for round_matches in schedule:
            self.assertEqual(len(round_matches), 2)
        
        # Check each team appears exactly once per round
        for round_matches in schedule:
            teams_in_round = set()
            for home_id, away_id in round_matches:
                self.assertNotEqual(home_id, away_id, "Team cannot play itself")
                teams_in_round.add(home_id)
                teams_in_round.add(away_id)
            self.assertEqual(len(teams_in_round), 4, "All 4 teams must appear in each round")
    
    def test_odd_n_teams(self):
        """Test round-robin with odd number of teams (5 teams -> 5 rounds with byes)."""
        teams = [{'id': i, 'name': f'Team{i}'} for i in range(5)]
        schedule = round_robin_pairs(teams)
        
        # 5 teams should produce 5 rounds
        self.assertEqual(len(schedule), 5)
        
        # Each round should have 2 matches (5 teams + 1 bye = 6, so 3 pairs, but bye is skipped)
        for round_matches in schedule:
            # Should have 2 matches (bye team doesn't play)
            self.assertEqual(len(round_matches), 2)
        
        # Check no team appears twice in a round
        for round_matches in schedule:
            teams_in_round = set()
            for home_id, away_id in round_matches:
                if home_id != -1:
                    self.assertNotIn(home_id, teams_in_round, f"Team {home_id} appears twice")
                    teams_in_round.add(home_id)
                if away_id != -1:
                    self.assertNotIn(away_id, teams_in_round, f"Team {away_id} appears twice")
                    teams_in_round.add(away_id)
    
    def test_small_n(self):
        """Test with minimal teams (2 teams -> 1 round)."""
        teams = [{'id': 0}, {'id': 1}]
        schedule = round_robin_pairs(teams)
        self.assertEqual(len(schedule), 1)
        self.assertEqual(len(schedule[0]), 1)
        self.assertIn((0, 1), schedule[0])


class TestEvaluateScheduleTravel(unittest.TestCase):
    """Test travel evaluation with hand-crafted layouts."""
    
    def test_simple_two_teams(self):
        """Test travel evaluation with 2 teams at known distance."""
        teams = [
            {'id': 0, 'lat': 40.0, 'lon': -74.0},  # New York
            {'id': 1, 'lat': 40.0, 'lon': -74.1}   # Nearby (should be ~8.9 km)
        ]
        D = distance_matrix(teams)
        
        # Schedule: Team 0 plays at home, then Team 1 plays at home
        # Round 1: (0, 1) - Team 1 travels to Team 0's stadium
        # After round 1: Team 1 returns home
        rounds = [[(0, 1)]]
        per_team, total = evaluate_schedule_travel(rounds, teams, D)
        
        # Team 1 travels: home -> Team 0 -> home = 2 * distance
        expected_team1 = D[1][0] + D[0][1]  # away + return
        self.assertAlmostEqual(per_team[1], expected_team1, places=1)
        self.assertAlmostEqual(per_team[0], 0.0, places=1)  # Team 0 stays home
        self.assertAlmostEqual(total, expected_team1, places=1)
    
    def test_four_teams_two_close_pairs(self):
        """Test with 4 teams arranged as two close pairs and two distant."""
        # Two close pairs: (0,1) close, (2,3) close, but pairs far apart
        teams = [
            {'id': 0, 'lat': 40.0, 'lon': -74.0},   # Pair 1
            {'id': 1, 'lat': 40.0, 'lon': -74.1},   # Pair 1 (close to 0)
            {'id': 2, 'lat': 37.7, 'lon': -122.4},  # Pair 2 (far from Pair 1)
            {'id': 3, 'lat': 37.7, 'lon': -122.5},  # Pair 2 (close to 2)
        ]
        D = distance_matrix(teams)
        
        # Create a schedule where teams travel between pairs
        # Round 1: (0, 1) and (2, 3) - local matches
        # Round 2: (0, 2) and (1, 3) - cross-pair matches (long travel)
        rounds = [
            [(0, 1), (2, 3)],  # Local matches
            [(0, 2), (1, 3)],  # Cross-pair matches
        ]
        
        per_team, total = evaluate_schedule_travel(rounds, teams, D)
        
        # Verify total is positive
        self.assertGreater(total, 0.0)
        
        # In round 2, teams 0, 1, 2, 3 all travel long distances
        # All should have significant travel
        for i in range(4):
            self.assertGreaterEqual(per_team[i], 0.0)
    
    def test_bye_handling(self):
        """Test that teams with byes don't travel."""
        teams = [
            {'id': 0, 'lat': 40.0, 'lon': -74.0},
            {'id': 1, 'lat': 40.0, 'lon': -74.1},
            {'id': 2, 'lat': 40.0, 'lon': -74.2},
        ]
        D = distance_matrix(teams)
        
        # Schedule with bye (team 2 has bye in round 1)
        rounds = [[(0, 1)]]  # Only 2 teams play, team 2 has bye
        
        per_team, total = evaluate_schedule_travel(rounds, teams, D)
        
        # Team 2 should have 0 travel (stays home)
        self.assertEqual(per_team[2], 0.0)


class TestValidators(unittest.TestCase):
    """Test validator functions with constructed violations."""
    
    def test_validate_schedule_valid(self):
        """Test validate_schedule with a valid schedule."""
        schedule = [
            [(0, 1), (2, 3)],
            [(1, 2), (3, 0)],
        ]
        ok, reasons = validate_schedule(schedule, 4)
        self.assertTrue(ok)
        self.assertEqual(reasons, [])
    
    def test_validate_schedule_invalid_id(self):
        """Test validate_schedule detects invalid team IDs."""
        schedule = [[(0, 5)]]  # Team 5 doesn't exist (only 0-3)
        ok, reasons = validate_schedule(schedule, 4)
        self.assertFalse(ok)
        self.assertTrue(any('invalid team id' in r.lower() for r in reasons))
    
    def test_validate_schedule_duplicate_team(self):
        """Test validate_schedule detects duplicate teams in same round."""
        schedule = [[(0, 1), (0, 2)]]  # Team 0 appears twice
        ok, reasons = validate_schedule(schedule, 4)
        self.assertFalse(ok)
        self.assertTrue(any('appears multiple times' in r for r in reasons))
    
    def test_check_max_consecutive_aways_no_violation(self):
        """Test check_max_consecutive_aways with valid schedule."""
        schedule = [
            [(0, 1), (2, 3)],
            [(1, 0), (3, 2)],
            [(0, 2), (1, 3)],
            [(2, 1), (3, 0)],
        ]
        ok, reasons = check_max_consecutive_aways(schedule, k=3)
        self.assertTrue(ok)
        self.assertEqual(reasons, [])
    
    def test_check_max_consecutive_aways_violation(self):
        """Test check_max_consecutive_aways detects violations."""
        # Team 0 away 4 consecutive times
        schedule = [
            [(1, 0), (2, 3)],
            [(2, 0), (3, 1)],
            [(3, 0), (1, 2)],
            [(1, 0), (2, 3)],
        ]
        ok, reasons = check_max_consecutive_aways(schedule, k=3)
        self.assertFalse(ok)
        self.assertTrue(any('Team 0' in r for r in reasons))
        self.assertTrue(any('consecutive away' in r.lower() for r in reasons))
    
    def test_check_repeaters_no_violation(self):
        """Test check_repeaters with valid schedule (no immediate reversals)."""
        schedule = [
            [(0, 1), (2, 3)],
            [(0, 2), (1, 3)],
            [(1, 0), (3, 2)],
        ]
        ok, reasons = check_repeaters(schedule)
        self.assertTrue(ok)
    
    def test_check_repeaters_violation(self):
        """Test check_repeaters detects immediate reversals."""
        schedule = [
            [(0, 1), (2, 3)],
            [(1, 0), (3, 2)],  # Immediate reversal of (0,1) -> (1,0)
        ]
        ok, reasons = check_repeaters(schedule)
        self.assertFalse(ok)
        self.assertTrue(any('Repeater detected' in r for r in reasons))
    
    def test_check_home_away_balance_valid(self):
        """Test check_home_away_balance with balanced schedule."""
        schedule = [
            [(0, 1), (2, 3)],
            [(1, 0), (3, 2)],
        ]
        ok, reasons = check_home_away_balance(schedule, 4)
        self.assertTrue(ok)
    
    def test_check_home_away_balance_imbalance(self):
        """Test check_home_away_balance detects imbalance."""
        # Team 0 always at home
        schedule = [
            [(0, 1), (2, 3)],
            [(0, 2), (1, 3)],
            [(0, 3), (1, 2)],
        ]
        ok, reasons = check_home_away_balance(schedule, 4)
        self.assertFalse(ok)
        self.assertTrue(any('imbalance' in r.lower() for r in reasons))


if __name__ == '__main__':
    unittest.main()

