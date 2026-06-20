import os
import sys
import threading
import time
import webbrowser

# Auto-install Flask if not present
try:
    from flask import Flask, jsonify, request, session, render_template
except ImportError:
    print("偵測到尚未安裝 Flask，正在自動安裝中...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        from flask import Flask, jsonify, request, session, render_template
        print("Flask 安裝成功！")
    except Exception as e:
        print(f"自動安裝 Flask 失敗，請手動執行: pip install flask (錯誤訊息: {e})")
        sys.exit(1)

import game_logic

app = Flask(__name__)
# A simple secret key for session encryption
app.secret_key = "1a2b_secret_key_for_kids_logic_training_and_fun_learning"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/start", methods=["POST"])
def start_game():
    secret = game_logic.generate_random_secret()
    session["secret"] = secret
    session["history"] = []
    
    # Get initial deduction state (all digits possible, count = 5040)
    deduction = game_logic.deduce_digit_statuses([])
    
    return jsonify({
        "status": "started",
        "message": "新遊戲開始囉！神秘的 4 位數已經產生了，快來猜猜看吧！",
        "remaining_count": deduction["remaining_count"],
        "deduction": deduction
    })

@app.route("/api/analyze", methods=["POST"])
def analyze_guess():
    data = request.get_json() or {}
    guess = data.get("guess", "").strip()
    history = session.get("history", [])
    
    analysis = game_logic.analyze_pending_guess(guess, history)
    deduction = game_logic.deduce_digit_statuses(history)
    
    return jsonify({
        "analysis": analysis,
        "deduction": deduction
    })

@app.route("/api/submit", methods=["POST"])
def submit_guess():
    data = request.get_json() or {}
    guess = data.get("guess", "").strip()
    
    secret = session.get("secret")
    if not secret:
        return jsonify({"status": "error", "reason": "遊戲尚未開始，請點擊「新遊戲」！"}), 400
        
    history = session.get("history", [])
    
    # 1. Validate guess again
    validation = game_logic.analyze_pending_guess(guess, history)
    if validation["status"] in ["error", "incomplete"]:
        return jsonify({"status": "error", "reason": validation["reason"]}), 400
        
    # 2. Calculate score
    a, b = game_logic.calculate_ab(secret, guess)
    
    # 3. Add to history
    new_clue = {"guess": guess, "a": a, "b": b}
    history.append(new_clue)
    session["history"] = history
    
    # 4. Get new deduction state after submitting
    deduction = game_logic.deduce_digit_statuses(history)
    
    won = (a == 4)
    response_data = {
        "status": "submitted",
        "guess": guess,
        "a": a,
        "b": b,
        "won": won,
        "history": history,
        "deduction": deduction
    }
    
    if won:
        response_data["secret"] = secret
        
    return jsonify(response_data)

def open_browser():
    # Wait a moment for Flask server to spin up
    time.sleep(1.5)
    url = "http://127.0.0.1:5000"
    print(f"正在自動為您開啟瀏覽器：{url}")
    webbrowser.open(url)

if __name__ == "__main__":
    # Prevent browser from opening twice when Flask reloader runs
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Thread(target=open_browser, daemon=True).start()
        
    # Run the server locally on port 5000
    app.run(host="127.0.0.1", port=5000, debug=True)
