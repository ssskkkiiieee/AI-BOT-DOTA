import os
import re
import sys
import math
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

# Force UTF-8 encoding on stdout for Windows terminals to ensure perfect Cyrillic rendering
if sys.platform == "win32" and sys.stdout is not None:
    import io
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Try importing winsound (Windows only) for audio alerts
try:
    import winsound
    def play_sound(freq, duration):
        winsound.Beep(freq, duration)
except ImportError:
    def play_sound(freq, duration):
        sys.stdout.write("\a")
        sys.stdout.flush()

# Set up CustomTkinter design parameters
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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

# GSI & Bot Monitoring State
_G_COACH_AUDIO = True
_G_COACH_LAST_WARNINGS = {
    "hp": 0, "stash": 0, "overextend": 0, "rune_power": 0, "rune_bounty": 0, "rune_wisdom": 0
}

# ==================== COURIER & ALERTS HELPER ====================
def play_alert_pattern(pattern_type):
    """Plays distinct audible winsound beeps for different alert types."""
    global _G_COACH_AUDIO
    if not _G_COACH_AUDIO:
        return
    try:
        if pattern_type == "hp":
            for _ in range(3):
                play_sound(1200, 100)
                time.sleep(0.05)
        elif pattern_type == "rune":
            play_sound(600, 200)
            time.sleep(0.05)
            play_sound(800, 200)
        elif pattern_type == "stash":
            play_sound(440, 100)
            time.sleep(0.05)
            play_sound(440, 100)
        elif pattern_type == "warning":
            play_sound(350, 400)
    except Exception:
        pass

# ==================== HTTP STATS SERVER HANDLER ====================
def make_stats_handler(dashboard):
    class StatsHTTPHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
        def do_POST(self):
            if self.path == '/stats':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                try:
                    stats = json.loads(post_data)
                    bot_id = str(stats.get("ID"))
                    if bot_id is not None:
                        dashboard.root.after(0, dashboard.update_bot_ui, bot_id, stats)
                        hero_clean = stats.get("HERO", "").replace("npc_dota_hero_", "").replace("_", " ").title()
                        log_str = f"[LIVE_HTTP] ID:{bot_id} | HERO:{hero_clean} | HP:{float(stats.get('HP', 0))*100:.0f}% | ACTION:{stats.get('ACTION')}"
                        dashboard.root.after(0, dashboard.append_log, log_str)
                except Exception:
                    pass
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            else:
                self.send_response(404)
                self.end_headers()
    return StatsHTTPHandler

# ==================== GSI COACH SERVER HANDLER ====================
def make_gsi_handler(dashboard):
    class GSIHTTPHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
        def do_POST(self):
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Dynamic visual feedback for connection
                if not getattr(dashboard, "gsi_connected", False):
                    dashboard.gsi_connected = True
                    dashboard.root.after(0, dashboard.append_log, "[GSI] Успешное подключение к Dota 2! Данные телеметрии поступают.")
                
                # Analyze GSI data
                dashboard.process_gsi_payload(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
            except Exception:
                self.send_response(500)
                self.end_headers()
    return GSIHTTPHandler

# ==================== MAIN GORILLA GLASS DASHBOARD ====================
class DotaCompanionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.root = self
        
        # Windows sizing and naming
        self.title("DOTA 2 AI COMPANION — BOT MONITOR & COACH")
        self.geometry("1150x785")
        self.configure(fg_color="#0b0a0f") # Deep custom space backdrop
        
        # Bot & GSI states
        self.running = False
        self.http_stats_server = None
        self.http_gsi_server = None
        self.console_log_path = ""
        self.bot_cards = {}
        
        # Auto-detect default console.log
        self.find_default_log_path()
        
        # Create user interface
        self.build_ui()
        self.append_log("[Система] Дашборд и ИИ-Тренер готовы к работе. Нажмите кнопку 'Запустить сервер' для старта.")

    def find_default_log_path(self):
        possible_dirs = [
            r"C:\stea\steamapps\common\dota 2 beta\game\dota",
            r"C:\Steam\steamapps\common\dota 2 beta\game\dota",
            r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota",
            r"C:\Program Files\Steam\steamapps\common\dota 2 beta\game\dota",
        ]
        
        best_path = None
        best_mtime = 0
        
        for d in possible_dirs:
            if os.path.exists(d):
                try:
                    for f in os.listdir(d):
                        if f == "console.log" or (f.startswith("console.") and f.endswith(".log")):
                            full_path = os.path.join(d, f)
                            mtime = os.path.getmtime(full_path)
                            if mtime > best_mtime:
                                best_mtime = mtime
                                best_path = full_path
                except Exception:
                    pass
        
        if best_path:
            self.console_log_path = best_path
        else:
            self.console_log_path = "Выберите файл console.log в папке game\\dota\\"

    def build_ui(self):
        # 1. Title / Header Frame (Sleek Glassmorphic top bar)
        self.header_frame = ctk.CTkFrame(self, fg_color="#13121c", border_color="#2b2740", border_width=1, corner_radius=12)
        self.header_frame.pack(fill="x", padx=15, pady=12)
        
        title_lbl = ctk.CTkLabel(self.header_frame, text="DOTA 2 AI COMPANION", font=("Consolas", 22, "bold"), text_color="#00F5D4")
        title_lbl.pack(side="left", padx=20, pady=10)
        
        subtitle_lbl = ctk.CTkLabel(self.header_frame, text="AI COACH & REAL-TIME BOT MONITOR", font=("Consolas", 10), text_color="#7b6fa6")
        subtitle_lbl.pack(side="left", padx=10, pady=15)
        
        # 2. Control Panel Frame
        self.control_frame = ctk.CTkFrame(self, fg_color="#13121c", border_color="#2b2740", border_width=1, corner_radius=12)
        self.control_frame.pack(fill="x", padx=15, pady=5)
        
        self.start_btn = ctk.CTkButton(self.control_frame, text="Запустить сервер", font=("Consolas", 12, "bold"), 
                                        fg_color="#7B2CBF", hover_color="#9D4EDD", text_color="white", corner_radius=8,
                                        command=self.toggle_servers)
        self.start_btn.pack(side="left", padx=15, pady=10)
        
        self.status_lbl = ctk.CTkLabel(self.control_frame, text="СТАТУС: ОТКЛЮЧЕН", font=("Consolas", 12, "bold"), text_color="#ff5555")
        self.status_lbl.pack(side="left", padx=15)
        
        # console.log selection right-aligned
        path_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        path_frame.pack(side="right", padx=15, pady=10)
        
        display_path = self.console_log_path
        if len(display_path) > 45:
            display_path = display_path[:12] + "..." + display_path[-30:]
        self.path_lbl = ctk.CTkLabel(path_frame, text=f"console.log: {display_path}", font=("Consolas", 10), text_color="#8d84af")
        self.path_lbl.pack(side="left", padx=10)
        
        browse_btn = ctk.CTkButton(path_frame, text="Обзор", font=("Consolas", 10), width=65, height=26,
                                    fg_color="#3e3857", hover_color="#514a6e", corner_radius=6,
                                    command=self.browse_log_file)
        browse_btn.pack(side="right")
        
        # 3. Main Glassmorphic Tab Container
        self.tab_view = ctk.CTkTabview(self, fg_color="#100f17", segmented_button_selected_color="#7B2CBF",
                                         segmented_button_unselected_color="#1a1924",
                                         segmented_button_selected_hover_color="#9D4EDD",
                                         text_color="white", corner_radius=14)
        self.tab_view.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.tab_monitor = self.tab_view.add("МОНИТОР ИИ-БОТОВ")
        self.tab_coach = self.tab_view.add("ЦЕНТР ИИ-ТРЕНЕРА (GSI)")
        
        # ==================== TAB 1: BOT MONITOR ====================
        # Radiant vs Dire Split View
        self.grid_split = ctk.CTkFrame(self.tab_monitor, fg_color="transparent")
        self.grid_split.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.radiant_glass = ctk.CTkScrollableFrame(self.grid_split, label_text="СИЛЫ СВЕТА (RADIANT AI)", 
                                                    label_font=("Consolas", 12, "bold"), label_text_color="#00F5D4",
                                                    fg_color="#13121c", border_color="#2b2740", border_width=1, corner_radius=12)
        self.radiant_glass.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.dire_glass = ctk.CTkScrollableFrame(self.grid_split, label_text="СИЛЫ ТЬМЫ (DIRE AI)", 
                                                 label_font=("Consolas", 12, "bold"), label_text_color="#ff5555",
                                                 fg_color="#13121c", border_color="#2b2740", border_width=1, corner_radius=12)
        self.dire_glass.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # монохромный Live логгер внизу
        self.log_container = ctk.CTkFrame(self.tab_monitor, fg_color="#0a0a0f", border_color="#201f2e", border_width=1, corner_radius=12)
        self.log_container.pack(fill="x", side="bottom", padx=5, pady=5)
        
        self.log_header = ctk.CTkLabel(self.log_container, text="ЖУРНАЛ ДЕЙСТВИЙ (LIVE CONSOLE LOGS)", font=("Consolas", 10, "bold"), text_color="#514a6e")
        self.log_header.pack(anchor="w", padx=12, pady=4)
        
        self.log_text = tk.Text(self.log_container, height=6, bg="#08070d", fg="#00ff88", insertbackground="white", 
                                font=("Consolas", 10), borderwidth=0, highlightthickness=0)
        self.log_text.pack(fill="both", expand=True, padx=8, pady=4)
        
        # ==================== TAB 2: AI COACH ====================
        # Left side control, Right side recommendations list
        self.coach_split = ctk.CTkFrame(self.tab_coach, fg_color="transparent")
        self.coach_split.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.coach_left = ctk.CTkFrame(self.coach_split, width=320, fg_color="#13121c", border_color="#2b2740", border_width=1, corner_radius=12)
        self.coach_left.pack_propagate(False)
        self.coach_left.pack(side="left", fill="both", expand=False, padx=5, pady=5)
        
        # Left Panel Items
        ctk.CTkLabel(self.coach_left, text="TELEMETRY AI COACH", font=("Consolas", 14, "bold"), text_color="#00F5D4").pack(padx=20, pady=15)
        
        self.gsi_status = ctk.CTkLabel(self.coach_left, text="GSI СЕРВЕР: ВЫКЛЮЧЕН", font=("Consolas", 11, "bold"), text_color="#ff5555")
        self.gsi_status.pack(pady=10)
        
        # Audio Alerts Switch
        self.audio_switch = ctk.CTkSwitch(self.coach_left, text="Звуковые оповещения", font=("Consolas", 11),
                                           progress_color="#7B2CBF", fg_color="#3e3857", command=self.toggle_audio_alerts)
        self.audio_switch.select()
        self.audio_switch.pack(pady=20, padx=20)
        
        # Instructions for the user
        inst_box = ctk.CTkFrame(self.coach_left, fg_color="#1c1a27", corner_radius=8)
        inst_box.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(inst_box, text="ИНСТРУКЦИЯ GSI:", font=("Consolas", 11, "bold"), text_color="#7b6fa6").pack(anchor="w", padx=10, pady=8)
        
        instructions = (
            "1. Запустите Дашборд.\n"
            "2. GSI-сервер начнет\n"
            "   слушать порт 5000.\n"
            "3. Запустите Dota 2.\n"
            "4. Игра сама будет слать\n"
            "   пакеты с телеметрией.\n"
            "5. Тренер анализирует HP,\n"
            "   выдвижение от вышек,\n"
            "   предметы в тайнике,\n"
            "   тайминги рун.\n"
            "6. Вы получаете звуковые\n"
            "   предупреждения!"
        )
        ctk.CTkLabel(inst_box, text=instructions, font=("Consolas", 10), justify="left", text_color="#a8a3c2").pack(anchor="w", padx=10, pady=2)
        
        # Right Side - Scrolling Glass Panel for alerts
        self.coach_right = ctk.CTkScrollableFrame(self.coach_split, label_text="СОВЕТЫ И ОПОВЕЩЕНИЯ ИИ-ТРЕНЕРА (LIVE)",
                                                  label_font=("Consolas", 12, "bold"), label_text_color="#00F5D4",
                                                  fg_color="#13121c", border_color="#2b2740", border_width=1, corner_radius=12)
        self.coach_right.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self.coach_right_placeholder = ctk.CTkLabel(self.coach_right, text="Ожидание старта игры в Dota 2...\n(События появятся здесь в реальном времени)", 
                                                     font=("Consolas", 11), text_color="#514a6e")
        self.coach_right_placeholder.pack(pady=100)

    def toggle_audio_alerts(self):
        global _G_COACH_AUDIO
        _G_COACH_AUDIO = self.audio_switch.get() == 1
        state = "ВКЛЮЧЕНЫ" if _G_COACH_AUDIO else "ВЫКЛЮЧЕНЫ"
        self.append_log(f"[Система] Звуковые оповещения тренера: {state}")

    def browse_log_file(self):
        filename = filedialog.askopenfilename(title="Выберите Dota 2 console.log", filetypes=[("Log files", "*.log")])
        if filename:
            self.console_log_path = filename
            display_path = self.console_log_path
            if len(display_path) > 45:
                display_path = display_path[:12] + "..." + display_path[-30:]
            self.path_lbl.configure(text=f"console.log: {display_path}")
            self.append_log(f"[Система] Выбран новый файл логов: {self.console_log_path}")

    def toggle_servers(self):
        if self.running:
            self.running = False
            self.start_btn.configure(text="Запустить сервер", fg_color="#7B2CBF", hover_color="#9D4EDD")
            self.status_lbl.configure(text="СТАТУС: ОТКЛЮЧЕН", text_color="#ff5555")
            self.gsi_status.configure(text="GSI СЕРВЕР: ВЫКЛЮЧЕН", text_color="#ff5555")
            self.stop_http_servers()
        else:
            self.running = True
            self.start_btn.configure(text="Остановить сервер", fg_color="#ff5555", hover_color="#ff3333")
            self.status_lbl.configure(text="СТАТУС: ЗАПУЩЕН", text_color="#00F5D4")
            self.gsi_status.configure(text="GSI СЕРВЕР: СЛУШАЕТ (5000)", text_color="#00F5D4")
            
            # Start HTTP Servers
            self.start_http_servers()
            
            # Start console.log monitor
            if os.path.exists(self.console_log_path):
                self.append_log(f"[Система] Запущен сбор данных через: {self.console_log_path}")
                threading.Thread(target=self.monitor_log_file, daemon=True).start()
            else:
                self.append_log("[Внимание] Файл console.log не найден! Проверьте путь или выберите файл вручную.")
                self.append_log("[Инструкция] Убедитесь, что в параметрах запуска Dota 2 прописаны: -novid -condebug")

    def update_bot_ui(self, bot_id, stats):
        is_radiant = (int(bot_id) <= 6 and int(bot_id) != 5)
        if int(bot_id) >= 7:
            is_radiant = False
            
        parent_frame = self.radiant_glass if is_radiant else self.dire_glass

        if bot_id not in self.bot_cards:
            # Create a premium Glassmorphism Card container
            card = ctk.CTkFrame(parent_frame, fg_color="#181622", border_color="#2b2740", border_width=1, corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)
            
            hero_name = stats.get("HERO", "Unknown").replace("npc_dota_hero_", "").replace("_", " ").title()
            
            hero_lbl = ctk.CTkLabel(card, text=f"[{bot_id}] {hero_name}", font=("Consolas", 12, "bold"), text_color="#00F5D4")
            hero_lbl.pack(anchor="w", padx=12, pady=5)

            pb_frame = ctk.CTkFrame(card, fg_color="transparent")
            pb_frame.pack(fill="x", padx=12, pady=2)
            
            hp_lbl = ctk.CTkLabel(pb_frame, text="HP: 100%", font=("Consolas", 9), text_color="#00ff88", width=55)
            hp_lbl.pack(side="left")
            
            hp_bar = ctk.CTkProgressBar(pb_frame, progress_color="#00ff88", fg_color="#201f2d", height=8, corner_radius=4)
            hp_bar.set(1.0)
            hp_bar.pack(side="left", fill="x", expand=True, padx=5)

            pb_frame2 = ctk.CTkFrame(card, fg_color="transparent")
            pb_frame2.pack(fill="x", padx=12, pady=2)
            
            mp_lbl = ctk.CTkLabel(pb_frame2, text="MP: 100%", font=("Consolas", 9), text_color="#00D2FF", width=55)
            mp_lbl.pack(side="left")
            
            mp_bar = ctk.CTkProgressBar(pb_frame2, progress_color="#00D2FF", fg_color="#201f2d", height=8, corner_radius=4)
            mp_bar.set(1.0)
            mp_bar.pack(side="left", fill="x", expand=True, padx=5)

            action_lbl = ctk.CTkLabel(card, text="ДЕЙСТВИЕ: IDLE", font=("Consolas", 10), text_color="#a8a3c2")
            action_lbl.pack(anchor="w", padx=12, pady=2)

            coords_lbl = ctk.CTkLabel(card, text="КООРДИНАТЫ: 0, 0 | ЛИНИЯ: 0", font=("Consolas", 9), text_color="#514a6e")
            coords_lbl.pack(anchor="w", padx=12, pady=4)

            self.bot_cards[bot_id] = {
                "card": card,
                "hero_lbl": hero_lbl,
                "hp_lbl": hp_lbl,
                "hp_bar": hp_bar,
                "mp_lbl": mp_lbl,
                "mp_bar": mp_bar,
                "action_lbl": action_lbl,
                "coords_lbl": coords_lbl
            }

        card_widgets = self.bot_cards[bot_id]
        
        hero_clean = stats.get("HERO", "").replace("npc_dota_hero_", "").replace("_", " ").title()
        card_widgets["hero_lbl"].configure(text=f"[{bot_id}] {hero_clean}")
        
        hp_val = float(stats.get("HP", 1.0))
        mp_val = float(stats.get("MP", 1.0))
        
        card_widgets["hp_lbl"].configure(text=f"HP: {hp_val*100:.0f}%", text_color="#00ff88" if hp_val > 0.3 else "#ff5555")
        card_widgets["hp_bar"].set(hp_val)
        card_widgets["hp_bar"].configure(progress_color="#00ff88" if hp_val > 0.3 else "#ff5555")
        
        card_widgets["mp_lbl"].configure(text=f"MP: {mp_val*100:.0f}%")
        card_widgets["mp_bar"].set(mp_val)
        
        action = stats.get("ACTION", "UNKNOWN")
        creeps = stats.get("TARGET_CREEPS", "0")
        
        # Color coding actions dynamically
        act_color = "#00ff88" if "ML_MOVE" in action else "#ffb86c"
        if "RETREAT" in action or "HEAL" in action:
            act_color = "#ff5555"
        elif "JUNGLE" in action:
            act_color = "#bd93f9"
            
        card_widgets["action_lbl"].configure(text=f"ДЕЙСТВИЕ: {action} ({creeps} крипов)", text_color=act_color)
        
        coords = stats.get("LOC", "0,0")
        lane = stats.get("LANE", "0")
        card_widgets["coords_lbl"].configure(text=f"КООРДИНАТЫ: {coords} | ЛИНИЯ: {lane}")

    def monitor_log_file(self):
        self.append_log(f"[Система] Начато чтение лога: {self.console_log_path}")
        current_file_path = self.console_log_path
        last_check_time = time.time()
        
        try:
            f = open(current_file_path, "r", encoding="utf-8", errors="ignore")
            f.seek(0, 2)
            
            while self.running:
                # Every 4 seconds, check if Dota 2 generated a newer console.*.log
                now_t = time.time()
                if now_t - last_check_time > 4.0:
                    last_check_time = now_t
                    self.find_default_log_path()
                    if self.console_log_path != current_file_path and os.path.exists(self.console_log_path):
                        self.append_log(f"[Система] Обнаружен новый лог игры! Переключаюсь на: {self.console_log_path}")
                        f.close()
                        current_file_path = self.console_log_path
                        f = open(current_file_path, "r", encoding="utf-8", errors="ignore")
                        f.seek(0, 2)
                
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                if "[BOT_STAT]" in line:
                    self.parse_stat_line(line)
                
                if "[BOT_STAT]" in line or "bot_generic" in line or "Error" in line:
                    self.root.after(0, self.append_log, line.strip())
                    
            f.close()
        except Exception as e:
            self.root.after(0, self.append_log, f"[Ошибка логов] Ошибка чтения логов: {e}")

    def parse_stat_line(self, line):
        try:
            stat_part = line.split("[BOT_STAT] ")[1].strip()
            pairs = stat_part.split("|")
            stats = {}
            for pair in pairs:
                k, v = pair.split(":")
                stats[k] = v
            
            bot_id = stats.get("ID")
            if bot_id:
                self.root.after(0, self.update_bot_ui, bot_id, stats)
        except Exception:
            pass

    def append_log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def process_gsi_payload(self, data):
        """Telemetric analyzer for real-time GSI player data."""
        now = time.time()
        map_state = data.get("map", {})
        game_state = map_state.get("game_state", "")
        
        # Hide GSI placeholder immediately when any GSI data is received to show connectivity
        if self.coach_right_placeholder.winfo_exists():
            self.coach_right_placeholder.destroy()
            self.add_coach_alert("ИИ-Тренер успешно подключен! Синхронизация с Dota 2 выполнена.", "rune")
            
        if game_state != "DOTA_GAMESTATE_GAME_IN_PROGRESS" and game_state != "DOTA_GAMESTATE_PRE_GAME" and game_state != "DOTA_GAMESTATE_PRE_GAME":
            return

        hero = data.get("hero", {})
        player = data.get("player", {})
        items = data.get("items", {})
        clock_time = map_state.get("clock_time", 0)

        is_alive = hero.get("alive", False)
        if not is_alive:
            return

        # A. Critical HP
        max_hp = hero.get("max_health", 0)
        curr_hp = hero.get("health", 0)
        if max_hp > 0:
            hp_pct = curr_hp / max_hp
            if hp_pct < 0.35 and (now - _G_COACH_LAST_WARNINGS["hp"] > 8.0):
                _G_COACH_LAST_WARNINGS["hp"] = now
                self.add_coach_alert(f"Критическое здоровье: {curr_hp}/{max_hp} ({hp_pct*100:.0f}%)! Срочно отступи под вышку!", "hp")

        # B. Runes Timing (15s before spawn)
        # Wisdom (every 7 minutes)
        if clock_time >= 405 and (clock_time + 15) % 420 == 0:
            if now - _G_COACH_LAST_WARNINGS["rune_wisdom"] > 30.0:
                _G_COACH_LAST_WARNINGS["rune_wisdom"] = now
                self.add_coach_alert(f"Через 15 секунд появится руна МУДРОСТИ (Wisdom Rune)! Соберитесь на краю карты!", "rune")
                
        # Bounty (every 3 minutes)
        elif clock_time >= 165 and (clock_time + 15) % 180 == 0:
            if now - _G_COACH_LAST_WARNINGS["rune_bounty"] > 30.0:
                _G_COACH_LAST_WARNINGS["rune_bounty"] = now
                self.add_coach_alert("Через 15 секунд появятся руны БОГАТСТВА (Bounty Runes)! Проверьте рун-споты!", "rune")
                
        # Power (every 2 minutes from 6:00)
        elif clock_time >= 345 and (clock_time + 15) % 120 == 0:
            if now - _G_COACH_LAST_WARNINGS["rune_power"] > 30.0:
                _G_COACH_LAST_WARNINGS["rune_power"] = now
                self.add_coach_alert("Через 15 секунд появится АКТИВНАЯ РУНА (Power Rune) на реке!", "rune")

        # C. Stash items
        has_stash = False
        for slot_idx in range(6):
            slot_name = f"stash{slot_idx}"
            item_slot = items.get(slot_name)
            if item_slot:
                item_name = item_slot.get("name", "")
                if item_name and item_name != "empty":
                    has_stash = True
                    break
        if has_stash and (now - _G_COACH_LAST_WARNINGS["stash"] > 25.0):
            _G_COACH_LAST_WARNINGS["stash"] = now
            self.add_coach_alert("В твоем тайнике лежат купленные вещи! Отправь курьера для доставки (клавиша F3)!", "stash")

        # D. Overextension
        xpos = hero.get("xpos")
        ypos = hero.get("ypos")
        team = player.get("team_name", "").lower()
        if xpos is not None and ypos is not None and team in ["radiant", "dire"]:
            allied_towers = RADIANT_TOWERS if team == "radiant" else DIRE_TOWERS
            min_dist = 999999
            nearest_tower_name = ""
            for tower in allied_towers:
                dist = math.sqrt((xpos - tower["x"])**2 + (ypos - tower["y"])**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest_tower_name = tower["name"]
            if min_dist > 1200 and (now - _G_COACH_LAST_WARNINGS["overextend"] > 12.0):
                _G_COACH_LAST_WARNINGS["overextend"] = now
                self.add_coach_alert(f"Ты опасно выдвинулся на линии (дистанция до {nearest_tower_name}: {min_dist:.0f}). Возможен ганк!", "overextend")

    def add_coach_alert(self, text, alert_type):
        """Creates a beautiful glowing card for the coach alert in the scrolling frame."""
        # Define color based on alert type
        border_col = "#7B2CBF" # default violet
        title_text = "СОВЕТ ТРЕНЕРА"
        text_col = "#e1e1e6"
        
        if alert_type == "hp":
            border_col = "#ff5555" # glowing red
            title_text = "ОПАСНОСТЬ (ЗДОРОВЬЕ)"
            text_col = "#ff8888"
        elif alert_type == "overextend":
            border_col = "#ff5555" # glowing red
            title_text = "ОПАСНОСТЬ (ПОЗИЦИЯ)"
            text_col = "#ffaa88"
        elif alert_type == "stash":
            border_col = "#ffb86c" # glowing orange
            title_text = "КУРЬЕР & ТАЙНИК"
            text_col = "#ffe3c2"
        elif alert_type == "rune":
            border_col = "#00D2FF" # glowing cyber blue
            title_text = "ТАЙМИНГ РУНЫ"
            text_col = "#b3f0ff"

        # Create glassmorphic card for recommendation
        self.root.after(0, self._render_coach_card, title_text, text, border_col, text_col, alert_type)

    def _render_coach_card(self, title, text, border_color, text_color, alert_type):
        card = ctk.CTkFrame(self.coach_right, fg_color="#181622", border_color=border_color, border_width=1, corner_radius=10)
        card.pack(fill="x", pady=6, padx=5, side="top") # Pack at top to show newest first!
        
        timestamp = time.strftime("%H:%M:%S")
        title_lbl = ctk.CTkLabel(card, text=f"[{timestamp}] — {title}", font=("Consolas", 11, "bold"), text_color=border_color)
        title_lbl.pack(anchor="w", padx=15, pady=4)
        
        msg_lbl = ctk.CTkLabel(card, text=text, font=("Consolas", 12), text_color=text_color, justify="left", wraplength=520)
        msg_lbl.pack(anchor="w", padx=15, pady=4)
        
        # Play acoustic winsound beep
        play_alert_pattern(alert_type if alert_type in ["hp", "rune", "stash"] else "warning")

    def start_http_servers(self):
        # 1. Start Bot stats collector on 8090
        def run_stats_server():
            handler_class = make_stats_handler(self)
            try:
                self.http_stats_server = HTTPServer(('0.0.0.0', 8090), handler_class)
                self.root.after(0, self.append_log, "[Сервер статистики] Успешно запущен на http://127.0.0.1:8090/")
                self.http_stats_server.serve_forever()
            except Exception as e:
                self.root.after(0, self.append_log, f"[Сервер статистики Error] Ошибка запуска: {e}")
                self.root.after(0, self.reset_ui_stopped)
                
        threading.Thread(target=run_stats_server, daemon=True).start()

        # 2. Start GSI Coach server on 5000
        def run_gsi_server():
            handler_class = make_gsi_handler(self)
            try:
                self.http_gsi_server = HTTPServer(('0.0.0.0', 5000), handler_class)
                self.root.after(0, self.append_log, "[GSI Сервер тренера] Успешно запущен на http://127.0.0.1:5000/")
                self.http_gsi_server.serve_forever()
            except Exception as e:
                self.root.after(0, self.append_log, f"[GSI Сервер Error] Ошибка запуска: {e}")
                self.root.after(0, self.reset_ui_stopped)
                
        threading.Thread(target=run_gsi_server, daemon=True).start()

    def stop_http_servers(self):
        if self.http_stats_server:
            try:
                self.http_stats_server.shutdown()
                self.http_stats_server.server_close()
                self.http_stats_server = None
                self.append_log("[Сервер статистики] Остановлен.")
            except Exception:
                pass
                
        if self.http_gsi_server:
            try:
                self.http_gsi_server.shutdown()
                self.http_gsi_server.server_close()
                self.http_gsi_server = None
                self.append_log("[GSI Сервер тренера] Остановлен.")
            except Exception:
                pass

    def reset_ui_stopped(self):
        self.running = False
        self.start_btn.configure(text="Запустить сервер", fg_color="#7B2CBF", hover_color="#9D4EDD")
        self.status_lbl.configure(text="СТАТУС: ОТКЛЮЧЕН", text_color="#ff5555")
        self.gsi_status.configure(text="GSI СЕРВЕР: ВЫКЛЮЧЕН", text_color="#ff5555")

if __name__ == "__main__":
    app = DotaCompanionApp()
    app.mainloop()
