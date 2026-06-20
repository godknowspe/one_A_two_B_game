import unittest
import sys
import os

# Adjust path to import game_logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game_logic

class TestGameLogic(unittest.TestCase):
    
    def test_calculate_ab(self):
        # 4-digit
        self.assertEqual(game_logic.calculate_ab("1234", "1234"), (4, 0))
        self.assertEqual(game_logic.calculate_ab("1234", "4321"), (0, 4))
        # 3-digit
        self.assertEqual(game_logic.calculate_ab("123", "123"), (3, 0))
        self.assertEqual(game_logic.calculate_ab("123", "321"), (1, 2))

    def test_generate_all_candidates(self):
        # 4-digit 0-9
        c4 = game_logic.generate_all_candidates(4, "0123456789")
        self.assertEqual(len(c4), 5040)
        
        # 3-digit 1-9
        c3 = game_logic.generate_all_candidates(3, "123456789")
        self.assertEqual(len(c3), 504) # 9 * 8 * 7 = 504

    def test_get_remaining_candidates(self):
        # 3-digit 1-9
        # Guess 123 -> 0A0B. Candidates left should be 6 * 5 * 4 = 120 (using digits 4,5,6,7,8,9)
        history = [{"guess": "123", "a": 0, "b": 0}]
        candidates = game_logic.get_remaining_candidates(history, digits=3, pool="123456789")
        self.assertEqual(len(candidates), 120)
        for c in candidates:
            self.assertFalse(any(d in c for d in "123"))

    def test_analyze_pending_guess_3_digits(self):
        pool = "123456789"
        history = [
            {"guess": "123", "a": 0, "b": 0}
        ]
        
        # Input has '0' which is not in pool
        res = game_logic.analyze_pending_guess("450", history, digits=3, pool=pool)
        self.assertEqual(res["status"], "error")
        self.assertTrue("不包含數字 '0'" in res["reason"])
        
        # Warning: uses 1, which is eliminated
        res = game_logic.analyze_pending_guess("145", history, digits=3, pool=pool)
        self.assertEqual(res["status"], "warning")
        
        # Exploratory: 456 (not candidate since 123 got 0A0B, wait: 456 has no 1,2,3, so it actually COULD be the candidate! Let's check: 123 vs 456 gives 0A0B. Matches feedback! So 456 is a valid candidate!)
        res = game_logic.analyze_pending_guess("456", history, digits=3, pool=pool)
        self.assertEqual(res["status"], "valid")
        
        # Exploratory: 451 is warned since 1 is eliminated.
        # What about 457 (candidate).
        # Let's add a clue: 457 -> 1A1B.
        history.append({"guess": "457", "a": 1, "b": 1})
        # Now, guess 458: 457 vs 458 is 2A0B (not 1A1B). So 458 is exploratory!
        res = game_logic.analyze_pending_guess("458", history, digits=3, pool=pool)
        self.assertEqual(res["status"], "exploratory")

    def test_deduce_digit_statuses_3_digits(self):
        pool = "123456789"
        history = [
            {"guess": "123", "a": 0, "b": 0}
        ]
        res = game_logic.deduce_digit_statuses(history, digits=3, pool=pool)
        states = res["digit_states"]
        probs = res["digit_probabilities"]
        
        # 1,2,3 must be eliminated
        for d in "123":
            self.assertEqual(states[d], "eliminated")
            self.assertEqual(probs[d], 0)
            
        # 0 must not be in the dictionary!
        self.assertNotIn("0", states)
        self.assertNotIn("0", probs)
        
        # Others must have >0% probability
        for d in "456789":
            self.assertEqual(states[d], "possible")
            self.assertGreater(probs[d], 0)

if __name__ == "__main__":
    unittest.main()
