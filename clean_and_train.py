import os
import pandas as pd

DATA_DIR = r"C:\бот\data"
TRAINER_SCRIPT = r"C:\бот\trainer.py"
EXPORT_SCRIPT = r"C:\бот\export_model_to_lua.py"
DOTA_VSCRIPTS_BOTS_DIR = r"C:\stea\steamapps\common\dota 2 beta\game\dota\scripts\vscripts\bots"

def main():
    print("=== Cleaning Up Data Directory ===")
    
    # Remove corrupt/empty CSV files
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    removed_csv = 0
    valid_csv = 0
    
    for csv_file in csv_files:
        filepath = os.path.join(DATA_DIR, csv_file)
        
        # Check file size first
        if os.path.getsize(filepath) < 100:  # less than 100 bytes is definitely corrupt/empty
            print(f"Removing empty CSV: {csv_file}")
            os.remove(filepath)
            removed_csv += 1
            continue
            
        try:
            # Try reading just the first 5 rows to verify it's a valid CSV
            df = pd.read_csv(filepath, nrows=5)
            if df.empty or len(df.columns) < 2:
                print(f"Removing empty/invalid CSV structure: {csv_file}")
                os.remove(filepath)
                removed_csv += 1
            else:
                valid_csv += 1
        except Exception as e:
            print(f"Removing corrupted CSV ({e}): {csv_file}")
            try:
                os.remove(filepath)
            except Exception:
                pass
            removed_csv += 1

    print(f"Data cleanup complete. Removed {removed_csv} invalid CSV files. {valid_csv} valid CSV files remain.")

    # Remove incomplete .dem and .dem.bz2 files to clean up disk space
    other_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.dem') or f.endswith('.bz2')]
    for other_file in other_files:
        filepath = os.path.join(DATA_DIR, other_file)
        try:
            os.remove(filepath)
            print(f"Removed temporary/corrupt file: {other_file}")
        except Exception:
            pass

    if valid_csv == 0:
        print("Error: No valid CSV datasets found. Cannot train model.")
        return

    # Trigger ML model training
    print("\n=== Running AI Model Re-Training on Cleaned Datasets ===")
    import subprocess
    try:
        subprocess.run(["python", "-u", TRAINER_SCRIPT], check=True)
        print("Training successfully finished.")
    except Exception as e:
        print(f"Training failed: {e}")
        return

    # Re-export models to Lua
    print("\n=== Exporting New Model to Pure Lua ===")
    try:
        subprocess.run(["python", EXPORT_SCRIPT], check=True)
        print("Export to Lua complete.")
    except Exception as e:
        print(f"Export failed: {e}")
        return

    # Copy new bot_generic.lua to Dota 2 folder
    bot_generic_src = r"C:\бот\bot_generic.lua"
    bot_generic_dst = os.path.join(DOTA_VSCRIPTS_BOTS_DIR, "bot_generic.lua")
    if os.path.exists(bot_generic_src) and os.path.exists(DOTA_VSCRIPTS_BOTS_DIR):
        print("\n=== Deploying New AI Bot to Dota 2 Client ===")
        import shutil
        try:
            shutil.copy2(bot_generic_src, bot_generic_dst)
            print(f"Successfully copied bot_generic.lua ({os.path.getsize(bot_generic_dst)/1024:.1f} KB) to Dota 2!")
        except Exception as e:
            print(f"Error copying bot_generic.lua: {e}")

if __name__ == "__main__":
    main()
