import os
import datetime

LOG_FILE = r"C:\бот\monitor.log"
OUTPUT_REPORT = r"C:\бот\pro_performance_report.txt"

def analyze_logs():
    print("=== Analyzing Bot Performance from Logs ===")
    if not os.path.exists(LOG_FILE):
        print("No log file found yet.")
        return
        
    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        logs = f.readlines()
        
    treads_switches = 0
    armlet_toggles = 0
    manta_dodges = 0
    eul_dodges = 0
    blink_dodges = 0
    lotus_saves = 0
    denies_count = 0
    harass_casts = 0
    rune_snatches = 0
    buybacks = 0
    tp_defenses = 0
    ganks = 0
    rosh_kills = 0
    emergency_buys = 0
    tome_buys = 0
    smoke_buys = 0
    
    # Advanced features
    jungle_paths = 0
    combos = 0
    blink_inits = 0
    aegis_protects = 0
    cd_tracks = 0
    jukes = 0
    hg_defenses = 0
    
    # Ultimate features
    tp_escapes = 0
    ward_deblocks = 0
    purges = 0
    aegis_saves = 0
    baits = 0
    lotus_baits = 0
    
    # Real-Time RL Self-Tuning
    self_tunes = 0
    
    for line in logs:
        if "[TREADS]" in line:
            treads_switches += 1
        elif "[ARMLET]" in line:
            armlet_toggles += 1
        elif "[DODGER]" in line:
            if "Manta" in line: manta_dodges += 1
            elif "Eul" in line: eul_dodges += 1
            elif "Blink" in line: blink_dodges += 1
        elif "[LINKER]" in line:
            lotus_saves += 1
        elif "[MID_DOMINANCE]" in line:
            if "DENYING" in line: denies_count += 1
            elif "snatched" in line: rune_snatches += 1
            elif "AUTO-HARASS" in line: harass_casts += 1
        elif "[BUYBACK]" in line:
            buybacks += 1
        elif "[TP_DEFENSE]" in line:
            tp_defenses += 1
        elif "[GANK]" in line:
            ganks += 1
        elif "[ROSHAN]" in line and "KILLED" in line:
            rosh_kills += 1
        elif "[EMERGENCY_BUY]" in line:
            emergency_buys += 1
        elif "[TOME]" in line:
            tome_buys += 1
        elif "[SMOKE]" in line:
            smoke_buys += 1
        elif "[JUNGLE_PATH]" in line:
            jungle_paths += 1
        elif "[COMBO]" in line:
            combos += 1
        elif "[BLINK_INIT]" in line:
            blink_inits += 1
        elif "[AEGIS_PROTECT]" in line:
            aegis_protects += 1
        elif "[COOLDOWN_TRACK]" in line:
            cd_tracks += 1
        elif "[JUKE]" in line:
            jukes += 1
        elif "[HG_DEFENSE]" in line:
            hg_defenses += 1
        elif "[TP_ESCAPE]" in line:
            tp_escapes += 1
        elif "[WARD_DEBLOCK]" in line:
            ward_deblocks += 1
        elif "[PURGE]" in line:
            purges += 1
        elif "[AEGIS_SAVE]" in line:
            aegis_saves += 1
        elif "[BAITING]" in line:
            baits += 1
        elif "[LOTUS_BAIT]" in line:
            lotus_baits += 1
        elif "[SELF_TUNING]" in line:
            self_tunes += 1
            
    report = []
    report.append("=========================================================================")
    report.append("     DOTA 2 AI 'PRO-ATHLETE' BOT PERFORMANCE OVERNIGHT ANALYTICS REPORT  ")
    report.append(f"     Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=========================================================================")
    report.append("")
    report.append(" [1] MICRO-MECHANICAL EXCELLENCE:")
    report.append(f"   - Power Treads Switches:       {treads_switches:<5} (Tread Switching Micro)")
    report.append(f"   - Perfect Armlet Toggles:      {armlet_toggles:<5} (Unholy Strength Abuse)")
    report.append(f"   - Manta Style Spell Dodges:    {manta_dodges:<5} (0.05s Evasion)")
    report.append(f"   - Eul's Self Cyclone Dodges:   {eul_dodges:<5}")
    report.append(f"   - Blink Spell Dodges:          {blink_dodges:<5}")
    report.append(f"   - Lotus Orb Savior Links:      {lotus_saves:<5} (Ally Refraction Linker)")
    report.append(f"   - Advanced Juke Escapes:       {jukes:<5} (Tree Cutting Pathfinder)")
    report.append(f"   - Smart Teleport Escapes:      {tp_escapes:<5} (Emergency Fountain TP)")
    report.append(f"   - Manta Silence/Track Purges:  {purges:<5} (Perfect Manta Purge)")
    report.append(f"   - Enemy Spell Baiting Moves:   {baits:<5} (Mana Baiting stop-cast)")
    report.append(f"   - Lotus Orb Reflect Baits:     {lotus_baits:<5} (Lotus Reflect Bait)")
    report.append(f"   - Adaptive Parameter Tunings:  {self_tunes:<5} (Real-Time RL Self-Tuning)")
    report.append("")
    report.append(" [2] MID LANE EXTREME DOMINANCE:")
    report.append(f"   - Allied Creep Denies:         {denies_count:<5} (XP Denial)")
    report.append(f"   - Auto-Harass Spell Casts:     {harass_casts:<5} (Reaction Attack)")
    report.append(f"   - River Power Rune Snatches:   {rune_snatches:<5} (2:00/4:00/6:00 Control)")
    report.append(f"   - Zero-frame Combo Casts:      {combos:<5} (Zero-frame Combo Trap)")
    report.append("")
    report.append(" [3] PRO ECONOMY & EMERGENCY TRIGGERS:")
    report.append(f"   - Emergency Purchases on Death: {emergency_buys:<5} (Dynamic Component Buyer)")
    report.append(f"   - Tome of Knowledge Purchases: {tome_buys:<5}")
    report.append(f"   - Smoke of Deceit Purchases:   {smoke_buys:<5}")
    report.append(f"   - Strategic Buybacks:          {buybacks:<5} (T3/Ancient Defense)")
    report.append("")
    report.append(" [4] TEAMPLAY & MACRO COORDINATION:")
    report.append(f"   - Tower TP Defense Responses:  {tp_defenses:<5} (TP Reaction)")
    report.append(f"   - Active Gank Squad Rotations: {ganks:<5} (Pos2 + Pos4 coordination)")
    report.append(f"   - Roshan Pit Slayings:         {rosh_kills:<5} (Roshan Contest)")
    report.append(f"   - Dynamic Jungling Farm Paths: {jungle_paths:<5} (GPM Maximizer)")
    report.append(f"   - Perfect Blink Initiations:   {blink_inits:<5} (3+ Enemies Blink-In)")
    report.append(f"   - Aegis Reincarnate Guards:    {aegis_protects:<5} (Aegis Reincarnation Guard)")
    report.append(f"   - Enemy Ult Cooldown Tracks:   {cd_tracks:<5} (Smart Cooldown Tracker)")
    report.append(f"   - High Ground Defensive Hugs:  {hg_defenses:<5} (HG Defense Director)")
    report.append(f"   - Camp Spawn Deblocks:         {ward_deblocks:<5} (Dynamic Ward Deblock)")
    report.append(f"   - Aegis Reincarnate Saves:     {aegis_saves:<5} (Force Staff Reincarnate Save)")
    report.append("")
    report.append("=========================================================================")
    
    full_report = "\n".join(report)
    print(full_report)
    
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(full_report)
        
    print(f"\nReport written to: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_logs()
