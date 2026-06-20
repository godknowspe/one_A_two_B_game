import unittest
import sys
import os

# Adjust path to import game_logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game_logic

class TestGameLogic(unittest.TestCase):
    
    def test_calculate_ab(self):
        # 4A0B
        self.assertEqual(game_logic.calculate_ab("1234", "1234"), (4, 0))
        # 0A4B
        self.assertEqual(game_logic.calculate_ab("1234", "4321"), (0, 4))
        # Mixed
        self.assertEqual(game_logic.calculate_ab("1234", "1356"), (1, 1))
        # None
        self.assertEqual(game_logic.calculate_ab("1234", "5678"), (0, 0))
        # Leading zero
        self.assertEqual(game_logic.calculate_ab("0123", "3210"), (0, 4))
        self.assertEqual(game_logic.calculate_ab("0123", "0156"), (2, 0))

    def test_generate_all_candidates(self):
        candidates = game_logic.generate_all_candidates()
        self.assertEqual(len(candidates), 5040)
        # Check all unique
        for c in candidates:
            self.assertEqual(len(c), 4)
            self.assertEqual(len(set(c)), 4)

    def test_get_remaining_candidates(self):
        all_c = game_logic.generate_all_candidates()
        
        # Test 1: Empty history
        candidates = game_logic.get_remaining_candidates([], all_c)
        self.assertEqual(len(candidates), 5040)
        
        # Test 2: Single guess with 0A0B (eliminates 4 digits)
        # Guessed 5678 -> 0A0B. Remaining candidates should not contain 5, 6, 7, 8.
        # Remaining count should be 6 * 5 * 4 * 3 = 360
        history1 = [{"guess": "5678", "a": 0, "b": 0}]
        candidates = game_logic.get_remaining_candidates(history1, all_c)
        self.assertEqual(len(candidates), 360)
        for c in candidates:
            self.assertFalse(any(d in c for d in "5678"))

        # Test 3: Multiple clues
        history2 = [
            {"guess": "5678", "a": 0, "b": 0},
            {"guess": "1234", "a": 4, "b": 0}
        ]
        candidates = game_logic.get_remaining_candidates(history2, all_c)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0], "1234")

    def test_analyze_pending_guess(self):
        history = [
            {"guess": "5678", "a": 0, "b": 0},
            {"guess": "1234", "a": 1, "b": 1}
        ]
        
        # Incomplete guess
        res = game_logic.analyze_pending_guess("12", history)
        self.assertEqual(res["status"], "incomplete")
        
        # Duplicate digits
        res = game_logic.analyze_pending_guess("1123", history)
        self.assertEqual(res["status"], "error")
        
        # Non-digits
        res = game_logic.analyze_pending_guess("12a4", history)
        self.assertEqual(res["status"], "error")

        # Contradicts clue 1: contains 5, which was 0A0B
        # Guess: 5123
        res = game_logic.analyze_pending_guess("5123", history)
        self.assertEqual(res["status"], "contradictory")
        self.assertEqual(res["clue_index"], 1) # Violates first clue
        
        # Contradicts clue 2: 1234 was 1A1B.
        # If secret is 4321, 1234 score against 4321 is 0A4B. But it was 1A1B.
        res = game_logic.analyze_pending_guess("4321", history)
        self.assertEqual(res["status"], "contradictory")
        self.assertEqual(res["clue_index"], 2) # Violates second clue
        
        # Consistent guess: e.g. 1902.
        # Check if 1234 vs 1902 yields 1A1B.
        # 1 is at pos 0 (1A). 2 is in 1902 at wrong pos (1B). 3,4 not in 1902. Total 1A1B.
        # Check if 5678 vs 1902 yields 0A0B. Yes.
        res = game_logic.analyze_pending_guess("1902", history)
        self.assertEqual(res["status"], "valid")

    def test_deduce_digit_statuses(self):
        history = [
            {"guess": "5678", "a": 0, "b": 0}
        ]
        res = game_logic.deduce_digit_statuses(history)
        states = res["digit_states"]
        locks = res["position_locks"]
        
        # 5,6,7,8 must be eliminated
        for d in "5678":
            self.assertEqual(states[d], "eliminated")
            
        # Others must be possible
        for d in "012349":
            self.assertEqual(states[d], "possible")
            
        # No position locks yet
        self.assertEqual(locks, [None, None, None, None])
        
        # Add another clue that narrows everything to one candidate
        history.append({"guess": "1234", "a": 4, "b": 0})
        res2 = game_logic.deduce_digit_statuses(history)
        states2 = res2["digit_states"]
        locks2 = res2["position_locks"]
        
        # 1,2,3,4 must be confirmed
        for d in "1234":
            self.assertEqual(states2[d], "confirmed")
        # 0,9 must now be eliminated since 1234 is the only answer
        self.assertEqual(states2["0"], "eliminated")
        self.assertEqual(states2["9"], "eliminated")
        
        # All positions locked
        self.assertEqual(locks2, ["1", "2", "3", "4"])

if __name__ == "__main__":
    unittest.main()
