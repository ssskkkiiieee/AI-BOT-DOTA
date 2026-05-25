import os
import time
import sys
import datetime
import subprocess

DOTA_BOTS_DIR = r"C:\stea\steamapps\common\dota 2 beta\game\dota\scripts\vscripts\bots"
LOG_FILE = r"C:\бот\monitor.log"
MODEL_DIR = r"C:\бот\model"
EXPORT_SCRIPT = r"C:\бот\export_model_to_lua.py"

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def check_file_status(filepath):
    if not os.path.exists(filepath):
        return "MISSING", 0
    size = os.path.getsize(filepath) / 1024
    mtime = os.path.getmtime(filepath)
    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%H:%M:%S")
    return f"OK ({size:.1f} KB, Updated at {mtime_str})", mtime

def main():
    log_message("=== STARTING DOTA 2 AI CONTINUOUS MONITOR & AUTOREGEN ===")
    log_message("Monitoring active directories for ML models, positioning overlays, and pipeline...")
    
    # Store initial model timestamps to detect updates
    last_model_timestamps = {}
    for pos in range(1, 6):
        model_file = os.path.join(MODEL_DIR, f"dota_ai_model_x_pos{pos}.joblib")
        if os.path.exists(model_file):
            last_model_timestamps[pos] = os.path.getmtime(model_file)
        else:
            last_model_timestamps[pos] = 0
            
    iteration = 0
    max_iterations = 1000
    
    while iteration < max_iterations:
        iteration += 1
        log_message(f"--- Monitoring Loop Iteration #{iteration} ---")
        
        # 1. Check file integrity
        generic_status, _ = check_file_status(os.path.join(DOTA_BOTS_DIR, "bot_generic.lua"))
        purchase_status, _ = check_file_status(os.path.join(DOTA_BOTS_DIR, "item_purchase_generic.lua"))
        abilities_status, _ = check_file_status(os.path.join(DOTA_BOTS_DIR, "ability_item_usage_generic.lua"))
        hero_sel_status, _ = check_file_status(os.path.join(DOTA_BOTS_DIR, "hero_selection.lua"))
        
        log_message(f"[INTEGRITY] bot_generic.lua: {generic_status}")
        log_message(f"[INTEGRITY] item_purchase_generic.lua: {purchase_status}")
        log_message(f"[INTEGRITY] ability_item_usage_generic.lua: {abilities_status}")
        log_message(f"[INTEGRITY] hero_selection.lua: {hero_sel_status}")
        
        # 2. Check for model updates (Self-Learning trigger)
        model_updated = False
        for pos in range(1, 6):
            model_file = os.path.join(MODEL_DIR, f"dota_ai_model_x_pos{pos}.joblib")
            if os.path.exists(model_file):
                current_mtime = os.path.getmtime(model_file)
                if current_mtime > last_model_timestamps.get(pos, 0):
                    log_message(f"[ALERT] New ML Model for Position {pos} detected!")
                    last_model_timestamps[pos] = current_mtime
                    model_updated = True
                    
        if model_updated:
            log_message("[AUTOREGEN] Launching export_model_to_lua.py to rebuild bot_generic.lua with pro models...")
            try:
                subprocess.run(["python", EXPORT_SCRIPT], check=True)
                log_message("[AUTOREGEN] Rebuild successful! New pro model trees compiled into Lua.")
            except Exception as e:
                log_message(f"[ERROR] Rebuild failed: {e}")
                
        # 3. Check game console logs
        dota_log_path = r"C:\stea\steamapps\common\dota 2 beta\game\dota\console.log"
        if os.path.exists(dota_log_path):
            log_message("[LOGS] Scanning console.log for errors...")
            errors_found = 0
            with open(dota_log_path, "r", errors="ignore") as f:
                lines = f.readlines()[-100:]
                for line in lines:
                    if "script error" in line.lower() or "lua error" in line.lower():
                        log_message(f"[ALERT] Lua Error: {line.strip()}")
                        errors_found += 1
            if errors_found == 0:
                log_message("[LOGS] System stable. No crashes detected.")
        else:
            log_message("[LOGS] Game logging offline.")
            
        time.sleep(30)

if __name__ == "__main__":
    main()
