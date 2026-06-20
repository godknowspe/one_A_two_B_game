import itertools
import random

def generate_all_candidates(digits=4, pool="0123456789"):
    """Generate all permutations of specified length from the digit pool."""
    return ["".join(p) for p in itertools.permutations(pool, digits)]

def calculate_ab(secret, guess):
    """
    Calculate the A and B score between a secret and a guess.
    A: correct digit in correct position.
    B: correct digit in incorrect position.
    """
    if len(secret) != len(guess):
        return 0, 0
    
    # Since digits in both secret and guess are unique, we can use sets
    common_digits = len(set(secret) & set(guess))
    a_count = sum(1 for s, g in zip(secret, guess) if s == g)
    b_count = common_digits - a_count
    return a_count, b_count

def get_remaining_candidates(history, digits=4, pool="0123456789", all_candidates=None):
    """
    Filter the candidate space based on the guess history.
    history is a list of dicts: [{"guess": "123", "a": 0, "b": 1}]
    """
    if all_candidates is None:
        candidates = generate_all_candidates(digits, pool)
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

def deduce_digit_statuses(history, digits=4, pool="0123456789"):
    """
    Deduce the logic state of each digit and position-specific locks based on history.
    Also calculates the percentage probability of each digit being in the secret code.
    """
    all_c = generate_all_candidates(digits, pool)
    candidates = get_remaining_candidates(history, digits, pool, all_candidates=all_c)
    total = len(candidates)
    
    # Pool mapping
    pool_list = list(pool)
    
    if total == 0:
        return {
            "digit_states": {str(d): "possible" for d in pool_list},
            "digit_probabilities": {str(d): 0 for d in pool_list},
            "position_locks": [None] * digits,
            "remaining_count": 0
        }
        
    # Count occurrences of each digit in remaining candidates
    digit_counts = {str(d): 0 for d in pool_list}
    for c in candidates:
        for digit in c:
            if digit in digit_counts:
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

    # Deduce position locks
    position_locks = [None] * digits
    for i in range(digits):
        digits_at_i = set(c[i] for c in candidates)
        if len(digits_at_i) == 1:
            position_locks[i] = list(digits_at_i)[0]

    return {
        "digit_states": digit_states,
        "digit_probabilities": digit_probabilities,
        "position_locks": position_locks,
        "remaining_count": total
    }

def analyze_pending_guess(pending_guess, history, digits=4, pool="0123456789"):
    """
    Analyze a guess before it is submitted.
    Supports generic digits and pools.
    """
    # 1. Basic validation
    if not pending_guess:
        return {"status": "incomplete", "reason": f"請輸入 {digits} 個不同的數字開始分析喔！"}
    
    if not pending_guess.isdigit():
        return {"status": "error", "reason": "輸入必須全部是數字喔！"}
        
    if len(pending_guess) != digits:
        return {"status": "incomplete", "reason": f"目前輸入了 {len(pending_guess)} 個數字，還差 {digits - len(pending_guess)} 個！"}
        
    if len(set(pending_guess)) != digits:
        return {"status": "error", "reason": "數字不能重複喔！請檢查看看。"}
        
    # Check if any digit is not in the allowed pool
    invalid_digits = [d for d in pending_guess if d not in pool]
    if invalid_digits:
        if "0" in invalid_digits and "0" not in pool:
            return {"status": "error", "reason": "⚠️ 注意：這個版本不包含數字 '0' 喔！請輸入 1-9 的數字。"}
        return {"status": "error", "reason": f"⚠️ 輸入包含無效數字：{', '.join(invalid_digits)}"}

    # Generate current deduction state
    deduction = deduce_digit_statuses(history, digits, pool)
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
    all_c = generate_all_candidates(digits, pool)
    current_candidates = get_remaining_candidates(history, digits, pool, all_candidates=all_c)
    
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
        # Find the first clue in history that this combination contradicts
        contradicting_clue_index = None
        contradiction_detail = None
        for idx, entry in enumerate(history):
            past_guess = entry["guess"]
            past_a = entry["a"]
            past_b = entry["b"]
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
                
        reason = (
            f"💡 聰明的探索！雖然選取的數字機率都不為 0，但 '{pending_guess}' 這個特定排列組合不可能是答案喔。\n"
        )
        if contradicting_clue_index is not None:
            detail = contradiction_detail
            reason += (
                f"**原因**：因為第 {contradicting_clue_index} 次猜測的 '{detail['past_guess']}' 提示為 {detail['past_a']}A{detail['past_b']}B。\n"
                f"但若答案為 '{pending_guess}'，則 '{detail['past_guess']}' 應該會是 {detail['calc_a']}A{detail['calc_b']}B，這與線索衝突。\n"
            )
        reason += f"不過這依然是一個非常好的探索性猜測，可以用來探測數字的分佈喔！目前符合所有線索的答案剩餘 {remaining_count} 種組合。"
        
        return {
            "status": "exploratory",
            "reason": reason,
            "remaining_count": remaining_count
        }

def generate_random_secret(digits=4, pool="0123456789"):
    """Generate a random secret code with unique digits of specified length."""
    digits_list = list(pool)
    random.shuffle(digits_list)
    return "".join(digits_list[:digits])
