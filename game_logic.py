import itertools
import random

def generate_all_candidates():
    """Generate all 5040 possible 4-digit numbers with unique digits."""
    digits = "0123456789"
    return ["".join(p) for p in itertools.permutations(digits, 4)]

def calculate_ab(secret, guess):
    """
    Calculate the A and B score between a secret and a guess.
    A: correct digit in correct position.
    B: correct digit in incorrect position.
    """
    if len(secret) != 4 or len(guess) != 4:
        return 0, 0
    
    # Since digits in both secret and guess are unique, we can use sets
    common_digits = len(set(secret) & set(guess))
    a_count = sum(1 for s, g in zip(secret, guess) if s == g)
    b_count = common_digits - a_count
    return a_count, b_count

def get_remaining_candidates(history, all_candidates=None):
    """
    Filter the candidate space based on the guess history.
    history is a list of dicts: [{"guess": "1234", "a": 0, "b": 1}]
    """
    if all_candidates is None:
        candidates = generate_all_candidates()
    else:
        candidates = list(all_candidates)
        
    for entry in history:
        past_guess = entry["guess"]
        past_a = entry["a"]
        past_b = entry["b"]
        candidates = [
            c for c in candidates 
            if calculate_ab(c, past_guess) == (past_a, past_b)
        ]
    return candidates

def analyze_pending_guess(pending_guess, history):
    """
    Analyze a 4-digit guess before it is submitted.
    Returns a dict with the evaluation results.
    """
    # 1. Basic validation
    if not pending_guess:
        return {"status": "incomplete", "reason": "請輸入 4 個不同的數字開始分析喔！"}
    
    if not pending_guess.isdigit():
        return {"status": "error", "reason": "輸入必須全部是數字喔！"}
        
    if len(pending_guess) != 4:
        return {"status": "incomplete", "reason": f"目前輸入了 {len(pending_guess)} 個數字，還差 {4 - len(pending_guess)} 個！"}
        
    if len(set(pending_guess)) != 4:
        return {"status": "error", "reason": "數字不能重複喔！請檢查看看。"}

    # Generate currently consistent candidates
    all_c = generate_all_candidates()
    current_candidates = get_remaining_candidates(history, all_candidates=all_c)
    remaining_before = len(current_candidates)

    # 2. Check compatibility with history
    contradicting_clue_index = None
    contradiction_detail = None

    for idx, entry in enumerate(history):
        past_guess = entry["guess"]
        past_a = entry["a"]
        past_b = entry["b"]
        
        # Calculate what score this pending guess would give to the past guess
        calc_a, calc_b = calculate_ab(pending_guess, past_guess)
        
        if (calc_a, calc_b) != (past_a, past_b):
            contradicting_clue_index = idx + 1
            contradiction_detail = {
                "past_guess": past_guess,
                "past_a": past_a,
                "past_b": past_b,
                "calc_a": calc_a,
                "calc_b": calc_b
            }
            break

    if contradicting_clue_index is not None:
        detail = contradiction_detail
        reason = (
            f"❌ 發現邏輯矛盾！這不可能是答案喔。\n"
            f"因為在第 {contradicting_clue_index} 次猜測中，你猜了 '{detail['past_guess']}' 得到了 {detail['past_a']}A{detail['past_b']}B。\n"
            f"但如果答案真的是 '{pending_guess}' 的話，對 '{detail['past_guess']}' 進行比對應該要得到 {detail['calc_a']}A{detail['calc_b']}B，這與提示不符合。"
        )
        return {
            "status": "contradictory",
            "reason": reason,
            "clue_index": contradicting_clue_index,
            "detail": detail,
            "remaining_count": remaining_before
        }

    # If it is consistent, check how good it is
    # If the pending guess is in the remaining candidates, it is a valid candidate
    is_valid_candidate = pending_guess in current_candidates
    
    if is_valid_candidate:
        reason = (
            f"🌟 太棒了！這個數字完全符合目前所有的線索！\n"
            f"它有可能就是真正的謎底喔。目前符合所有線索的答案還剩下 {remaining_before} 種組合。"
        )
        return {
            "status": "valid",
            "reason": reason,
            "remaining_count": remaining_before
        }
    else:
        # This branch shouldn't normally be reached if contradiction logic is perfect,
        # but just in case, handle it.
        reason = "⚠️ 這個數字無法與過去的某些線索吻合，請再檢查看看！"
        return {
            "status": "contradictory",
            "reason": reason,
            "remaining_count": remaining_before
        }

def deduce_digit_statuses(history):
    """
    Deduce the logic state of each digit (0-9) and position-specific locks based on history.
    """
    all_c = generate_all_candidates()
    candidates = get_remaining_candidates(history, all_candidates=all_c)
    total = len(candidates)
    
    if total == 0:
        # No candidates left (should only happen if history is self-contradictory)
        return {
            "digit_states": {str(d): "possible" for d in range(10)},
            "position_locks": [None, None, None, None]
        }
        
    # Count occurrences of each digit in remaining candidates
    digit_counts = {str(d): 0 for d in range(10)}
    for c in candidates:
        for digit in c:
            digit_counts[digit] += 1
            
    # Determine state: confirmed, eliminated, possible
    digit_states = {}
    for d_str, count in digit_counts.items():
        if count == 0:
            digit_states[d_str] = "eliminated"  # 🔴
        elif count == total:
            digit_states[d_str] = "confirmed"   # 🟢
        else:
            digit_states[d_str] = "possible"    # ⚪

    # Deduce position locks (if a digit is at the same index for all candidates)
    position_locks = [None, None, None, None]
    for i in range(4):
        digits_at_i = set(c[i] for c in candidates)
        if len(digits_at_i) == 1:
            position_locks[i] = list(digits_at_i)[0]

    return {
        "digit_states": digit_states,
        "position_locks": position_locks,
        "remaining_count": total
    }

def generate_random_secret():
    """Generate a random 4-digit secret code with unique digits."""
    digits = list("0123456789")
    random.shuffle(digits)
    return "".join(digits[:4])
