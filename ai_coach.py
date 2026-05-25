"""
ai_coach.py
================================================================================
Dota 2 Real-Time AI Coach using Valve Game State Integration (GSI).
Analyzes player telemetry (HP, runes, stash, overextension) and alerts via audio & console.
================================================================================
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
import time
import sys

# Force UTF-8 encoding on stdout for Windows terminals to ensure perfect Cyrillic rendering
if sys.platform == "win32" and sys.stdout is not None:
    import io
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Try importing winsound (Windows only), fallback to generic beep on other OS
try:
    import winsound
    def play_sound(freq, duration):
        winsound.Beep(freq, duration)
except ImportError:
    def play_sound(freq, duration):
        sys.stdout.write("\a")
        sys.stdout.flush()

# ANSI Color Codes for premium console aesthetics
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"

# Standard active tower coordinates (Centered map coordinates)
RADIANT_TOWERS = [
    {"name": "Radiant Tier 1 Bottom (Safe)", "x": 4800, "y": -3800},
    {"name": "Radiant Tier 1 Mid", "x": -1600, "y": -1600},
    {"name": "Radiant Tier 1 Top (Off)", "x": -6100, "y": -1500},
    {"name": "Radiant Base / Tier 3", "x": -5500, "y": -5500}
]

DIRE_TOWERS = [
    {"name": "Dire Tier 1 Top (Safe)", "x": -4800, "y": 3800},
    {"name": "Dire Tier 1 Mid", "x": 1600, "y": 1800},
    {"name": "Dire Tier 1 Bottom (Off)", "x": 6200, "y": 1500},
    {"name": "Dire Base / Tier 3", "x": 5500, "y": 5500}
]

# Track rate-limiting states for warnings (timestamp of last warning)
last_warning_time = {
    "hp": 0,
    "stash": 0,
    "overextend": 0,
    "rune_power": 0,
    "rune_bounty": 0,
    "rune_wisdom": 0
}

def log_coach(message, color=COLOR_CYAN):
    """Prints a beautifully formatted AI Coach recommendation."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {color}[AI COACH] {message}{COLOR_RESET}")

def play_alert_pattern(pattern_type):
    """Plays distinct audible winsound beeps for different alert types."""
    try:
        if pattern_type == "hp":
            # 3 urgent high-pitch beeps
            for _ in range(3):
                play_sound(1200, 100)
                time.sleep(0.05)
        elif pattern_type == "rune":
            # 2 pleasant rising medium-pitch beeps
            play_sound(600, 200)
            time.sleep(0.05)
            play_sound(800, 200)
        elif pattern_type == "stash":
            # 2 quick double-beeps
            play_sound(440, 100)
            time.sleep(0.05)
            play_sound(440, 100)
        elif pattern_type == "warning":
            # 1 long low warning beep
            play_sound(350, 400)
    except Exception:
        pass

def process_gsi_data(data):
    """Main GSI payload processing and telemetric analysis."""
    now = time.time()
    
    # 1. Verify game state is active
    map_state = data.get("map", {})
    game_state = map_state.get("game_state", "")
    if game_state != "DOTA_GAMESTATE_GAME_IN_PROGRESS":
        return

    # Extract nested tables
    hero = data.get("hero", {})
    player = data.get("player", {})
    items = data.get("items", {})
    clock_time = map_state.get("clock_time", 0)

    # 2. Check if hero is alive
    is_alive = hero.get("alive", False)
    if not is_alive:
        return

    # A. CRITICAL HP ANALYSIS
    max_hp = hero.get("max_health", 0)
    curr_hp = hero.get("health", 0)
    if max_hp > 0:
        hp_pct = curr_hp / max_hp
        if hp_pct < 0.35 and (now - last_warning_time["hp"] > 8.0):
            last_warning_time["hp"] = now
            log_coach(f"ВНИМАНИЕ! Критическое здоровье: {curr_hp}/{max_hp} ({hp_pct*100:.0f}%)! Срочно отступи под вышку!", COLOR_RED)
            play_alert_pattern("hp")

    # B. RUNES TIMING WARNINGS (15 seconds before spawn)
    # Wisdom Runes (spawn every 7 minutes = 420s starting at 7:00)
    if clock_time >= 405 and (clock_time + 15) % 420 == 0:
        if now - last_warning_time["rune_wisdom"] > 30.0:
            last_warning_time["rune_wisdom"] = now
            log_coach("Через 15 секунд появится руна МУДРОСТИ (Wisdom Rune)! Соберитесь на краю карты!", COLOR_BLUE)
            play_alert_pattern("rune")
            
    # Bounty Runes (spawn every 3 minutes = 180s starting at 3:00)
    elif clock_time >= 165 and (clock_time + 15) % 180 == 0:
        if now - last_warning_time["rune_bounty"] > 30.0:
            last_warning_time["rune_bounty"] = now
            log_coach("Через 15 секунд появятся руны БОГАТСТВА (Bounty Runes)! Проверьте споты рун!", COLOR_YELLOW)
            play_alert_pattern("rune")
            
    # Active Power Runes (spawn every 2 minutes = 120s starting at 6:00)
    elif clock_time >= 345 and (clock_time + 15) % 120 == 0:
        if now - last_warning_time["rune_power"] > 30.0:
            last_warning_time["rune_power"] = now
            log_coach("Через 15 секунд на реке появится АКТИВНАЯ РУНА (Power Rune)! Бегите на реку!", COLOR_CYAN)
            play_alert_pattern("rune")

    # C. STASH & COURIER ANALYSIS
    # Look for items in stash slots (stash0 to stash5)
    has_stash_items = False
    for slot_idx in range(6):
        slot_name = f"stash{slot_idx}"
        item_slot = items.get(slot_name)
        if item_slot:
            item_name = item_slot.get("name", "")
            if item_name and item_name != "empty":
                has_stash_items = True
                break
                
    if has_stash_items and (now - last_warning_time["stash"] > 25.0):
        last_warning_time["stash"] = now
        log_coach("В твоем тайнике лежат купленные предметы! Отправь курьера для доставки (клавиша F3)!", COLOR_YELLOW)
        play_alert_pattern("stash")

    # D. OVEREXTENSION & TOWER SAFETY ANALYSIS
    xpos = hero.get("xpos")
    ypos = hero.get("ypos")
    team = player.get("team_name", "").lower()
    
    if xpos is not None and ypos is not None and team in ["radiant", "dire"]:
        # Find distance to nearest allied tower
        allied_towers = RADIANT_TOWERS if team == "radiant" else DIRE_TOWERS
        min_dist = 999999
        nearest_tower_name = ""
        for tower in allied_towers:
            dist = math.sqrt((xpos - tower["x"])**2 + (ypos - tower["y"])**2)
            if dist < min_dist:
                min_dist = dist
                nearest_tower_name = tower["name"]
                
        # If too far from nearest tower, warn about overextension
        if min_dist > 1200 and (now - last_warning_time["overextend"] > 12.0):
            last_warning_time["overextend"] = now
            log_coach(f"ВНИМАНИЕ! Ты далеко от вышки (дистанция до {nearest_tower_name}: {min_dist:.0f}). Будь осторожен, возможен ганк!", COLOR_RED)
            play_alert_pattern("warning")

class GSIServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default HTTP request printing to keep console clean for coach advice
        return

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse GSI JSON packet
            data = json.loads(post_data.decode('utf-8'))
            process_gsi_data(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        except Exception as e:
            # Silence or handle parser errors gracefully
            self.send_response(500)
            self.end_headers()

def run(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, GSIServer)
    
    print("=" * 60)
    print(f"{COLOR_GREEN}=== Dota 2 Real-Time AI Coach Server successfully started! ==={COLOR_RESET}")
    print(f"Listening for Game State Integration (GSI) on {COLOR_CYAN}http://localhost:{port}/{COLOR_RESET}")
    print("AI Coach is active. Simply launch Dota 2 and start a match!")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{COLOR_YELLOW}AI Coach Server stopped.{COLOR_RESET}")

if __name__ == '__main__':
    run()
