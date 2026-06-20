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

    def test_generate_all_candidates(self):
        candidates = game_logic.generate_all_candidates()
        self.assertEqual(len(candidates), 5040)

    def test_get_remaining_candidates(self):
        all_c = game_logic.generate_all_candidates()
        candidates = game_logic.get_remaining_candidates([], all_c)
        self.assertEqual(len(candidates), 5040)
        
        # Guessed 5678 -> 0A0B. Remaining candidates should be 360
        history1 = [{"guess": "5678", "a": 0, "b": 0}]
        candidates = game_logic.get_remaining_candidates(history1, all_c)
        self.assertEqual(len(candidates), 360)

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

        # Warnings: contains 5, which is 0% probability (eliminated)
        res = game_logic.analyze_pending_guess("5123", history)
        self.assertEqual(res["status"], "warning")
        self.assertTrue(any("數字 '5'" in w for w in res["warnings"]))
        
        # Exploratory: 9012. 
        # All digits 9, 0, 1, 2 have prob > 0% (none are eliminated).
        # But is 9012 a candidate? Let's check: 
        # For 9012, 1234 vs 9012 gives: 1 is in 9012 (wrong pos), 2 is in 9012 (wrong pos). So 0A2B.
        # But the feedback for 1234 was 1A1B. So 9012 cannot be the secret.
        # However, it contains no eliminated digits or lock violations, so it is an exploratory guess!
        res = game_logic.analyze_pending_guess("9012", history)
        self.assertEqual(res["status"], "exploratory")
        
        # Valid candidate: 1902
        # Check: 5678 vs 1902 -> 0A0B.
        # Check: 1234 vs 1902 -> 1 is at pos 0 (1A), 2 is at pos 3 (1B). Total 1A1B.
        # 1902 is a candidate secret.
        res = game_logic.analyze_pending_guess("1902", history)
        self.assertEqual(res["status"], "valid")

    def test_deduce_digit_statuses(self):
        history = [
            {"guess": "5678", "a": 0, "b": 0}
        ]
        res = game_logic.deduce_digit_statuses(history)
        states = res["digit_states"]
        probs = res["digit_probabilities"]
        
        # 5,6,7,8 must have 0% probability
        for d in "5678":
            self.assertEqual(states[d], "eliminated")
            self.assertEqual(probs[d], 0)
            
        # Others must have >0% probability
        for d in "012349":
            self.assertEqual(states[d], "possible")
            self.assertGreater(probs[d], 0)

if __name__ == "__main__":
    unittest.main()
