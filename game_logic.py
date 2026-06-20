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

def deduce_digit_statuses(history):
    """
    Deduce the logic state of each digit (0-9) and position-specific locks based on history.
    Also calculates the percentage probability of each digit being in the secret code.
    """
    all_c = generate_all_candidates()
    candidates = get_remaining_candidates(history, all_candidates=all_c)
    total = len(candidates)
    
    if total == 0:
        # No candidates left (should only happen if history is self-contradictory)
        return {
            "digit_states": {str(d): "possible" for d in range(10)},
            "digit_probabilities": {str(d): 0 for d in range(10)},
            "position_locks": [None, None, None, None],
            "remaining_count": 0
        }
        
    # Count occurrences of each digit in remaining candidates
    digit_counts = {str(d): 0 for d in range(10)}
    for c in candidates:
        for digit in c:
            digit_counts[digit] += 1
            
    # Determine state: confirmed, eliminated, possible and their probabilities
    digit_states = {}
    digit_probabilities = {}
    for d_str, count in digit_counts.items():
        prob = round((count / total) * 100)
        digit_probabilities[d_str] = prob
        
        if prob == 0:
            digit_states[d_str] = "eliminated"  # 🔴
        elif prob == 100:
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
        "digit_probabilities": digit_probabilities,
        "position_locks": position_locks,
        "remaining_count": total
    }

def analyze_pending_guess(pending_guess, history):
    """
    Analyze a 4-digit guess before it is submitted.
    Returns a dict with the evaluation results.
    Allows exploratory guesses (not candidates but logically sound) and warns on logical contradictions.
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

    # Generate current deduction state
    deduction = deduce_digit_statuses(history)
    digit_states = deduction["digit_states"]
    position_locks = deduction["position_locks"]
    remaining_count = deduction["remaining_count"]

    # 2. Check for logical warnings
    warnings = []
    
    # Warning A: Re-using eliminated digits (prob = 0%)
    eliminated_used = [d for d in pending_guess if digit_states.get(d) == "eliminated"]
    if eliminated_used:
        warnings.append(f"數字 '{', '.join(eliminated_used)}' 已經確定不在密碼中囉！")
        
    # Warning B: Violating position locks
    for i, lock_digit in enumerate(position_locks):
        if lock_digit is not None and pending_guess[i] != lock_digit:
            warnings.append(f"第 {i+1} 位已經確定是 '{lock_digit}'，但你填了 '{pending_guess[i]}'。")
            
    # Warning C: Repeated guess
    is_repeated = any(entry["guess"] == pending_guess for entry in history)
    if is_repeated:
        # Find when it was guessed
        past_idx = next(idx + 1 for idx, entry in enumerate(history) if entry["guess"] == pending_guess)
        warnings.append(f"你已經在第 {past_idx} 次猜測過 '{pending_guess}' 囉！")

    # 3. Categorize Guess Status
    if warnings:
        reason = "⚠️ 注意邏輯漏洞喔：\n" + "\n".join(f"• {w}" for w in warnings)
        return {
            "status": "warning",
            "reason": reason,
            "warnings": warnings,
            "remaining_count": remaining_count
        }

    # If no warnings, check if it's a direct candidate or an exploratory guess
    all_c = generate_all_candidates()
    current_candidates = get_remaining_candidates(history, all_candidates=all_c)
    
    is_candidate = pending_guess in current_candidates
    if is_candidate:
        reason = (
            f"🌟 完美的候選者！這個數字完全符合目前所有的線索！\n"
            f"它有可能就是真正的密碼喔。目前符合所有線索的答案還剩下 {remaining_count} 種組合。"
        )
        return {
            "status": "valid",
            "reason": reason,
            "remaining_count": remaining_count
        }
    else:
        reason = (
            f"💡 聰明的探索！雖然這個數字本身不可能是答案，但它沒有使用已被排除的數字，"
            f"非常適合用來探測和排除其他數字的分布喔！目前符合所有線索的答案剩餘 {remaining_count} 種組合。"
        )
        return {
            "status": "exploratory",
            "reason": reason,
            "remaining_count": remaining_count
        }

def generate_random_secret():
    """Generate a random 4-digit secret code with unique digits."""
    digits = list("0123456789")
    random.shuffle(digits)
    return "".join(digits[:4])
