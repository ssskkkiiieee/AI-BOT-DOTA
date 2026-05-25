import os
import shutil

SOURCE_BOT_GENERIC = r"C:\бот\bot_generic.lua"
TARGET_MODE_LANING = r"C:\бот\mode_laning_generic.lua"
DOTA_VSCRIPTS_BOTS_DIR = r"C:\stea\steamapps\common\dota 2 beta\game\dota\scripts\vscripts\bots"

def main():
    print("=== Generating mode_laning_generic.lua from AI Model ===")
    
    if not os.path.exists(SOURCE_BOT_GENERIC):
        print(f"Error: {SOURCE_BOT_GENERIC} not found. Please train and export the model first.")
        return

    # Read the full bot_generic.lua
    with open(SOURCE_BOT_GENERIC, "r", encoding="utf-8") as f:
        content = f.read()

    # Append GetDesire() so the engine chooses this custom laning mode during early game
    laning_header = """-- ============================================================================
-- Dota 2 AI Imitation Learning Laning Mode (mode_laning_generic.lua)
-- ============================================================================
-- Automatically generated. Handles the laning phase movement via 
-- our 10.7M snapshot, 7k+ MMR professional imitation learning model.
-- ============================================================================

function GetDesire()
    local now = GameTime()
    -- Prioritize laning mode before 12 minutes (720 seconds) in-game
    if now < 720 then
        return 0.95
    end
    return 0.0
end

function OnStart()
end

function OnEnd()
end
"""

    full_content = laning_header + "\n" + content

    with open(TARGET_MODE_LANING, "w", encoding="utf-8") as f:
        f.write(full_content)
    
    print(f"Successfully generated: {TARGET_MODE_LANING}")

    # Copy to Dota 2 bots directory and Steam Workshop directory
    workshop_dir = r"C:\stea\steamapps\workshop\content\570\855965029"
    
    if os.path.exists(DOTA_VSCRIPTS_BOTS_DIR):
        dst_path = os.path.join(DOTA_VSCRIPTS_BOTS_DIR, "mode_laning_generic.lua")
        try:
            shutil.copy2(TARGET_MODE_LANING, dst_path)
            print(f"Successfully deployed mode_laning_generic.lua directly to Dota 2 client: {dst_path}")
        except Exception as e:
            print(f"Error deploying mode_laning_generic.lua: {e}")
            
    if os.path.exists(workshop_dir):
        dst_path = os.path.join(workshop_dir, "mode_laning_generic.lua")
        try:
            shutil.copy2(TARGET_MODE_LANING, dst_path)
            print(f"Successfully deployed mode_laning_generic.lua directly to Steam Workshop: {dst_path}")
        except Exception as e:
            print(f"Error deploying mode_laning_generic.lua to Workshop: {e}")

if __name__ == "__main__":
    main()
