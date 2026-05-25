import os
import bz2
import subprocess
import time

DATA_DIR = r"C:\бот\data"
PARSER_EXE = r"C:\бот\parser\parser.exe"
TRAINER_SCRIPT = r"C:\бот\trainer.py"
EXPORT_SCRIPT = r"C:\бот\export_model_to_lua.py"
DOTA_VSCRIPTS_BOTS_DIR = r"C:\stea\steamapps\common\dota 2 beta\game\dota\scripts\vscripts\bots"

def decompress_bz2(source_path, dest_path):
    print(f"Decompressing {os.path.basename(source_path)}...")
    try:
        with bz2.BZ2File(source_path, 'rb') as source, open(dest_path, 'wb') as dest:
            buffer_size = 1024 * 1024
            while True:
                chunk = source.read(buffer_size)
                if not chunk:
                    break
                dest.write(chunk)
        return True
    except Exception as e:
        print(f"Error during decompression: {e}")
        return False

def parse_dem(dem_path):
    print(f"Parsing {os.path.basename(dem_path)} using Go parser...")
    try:
        subprocess.run([PARSER_EXE, "-file", dem_path], capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Parsing failed: {e.stderr}")
        return False

def main():
    print("=== Processing Existing Replays in C:\\бот\\data ===")
    
    # 1. Find all bz2 files and decompress them
    bz2_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.dem.bz2')]
    for bz2_file in bz2_files:
        match_id = bz2_file.split('.')[0]
        dem_name = f"{match_id}.dem"
        bz2_path = os.path.join(DATA_DIR, bz2_file)
        dem_path = os.path.join(DATA_DIR, dem_name)
        
        # Decompress if we don't already have dem or csv
        csv_path = os.path.join(DATA_DIR, f"{match_id}.csv")
        if os.path.exists(csv_path):
            print(f"CSV for match {match_id} already exists. Skipping decompression of bz2.")
            try:
                os.remove(bz2_path)
            except Exception:
                pass
            continue
            
        if not os.path.exists(dem_path):
            if decompress_bz2(bz2_path, dem_path):
                # Remove bz2 to save space
                try:
                    os.remove(bz2_path)
                except Exception:
                    pass
            else:
                continue

    # 2. Parse all dem files
    dem_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.dem')]
    print(f"Found {len(dem_files)} .dem files to parse.")
    
    for dem_file in dem_files:
        match_id = dem_file.split('.')[0]
        dem_path = os.path.join(DATA_DIR, dem_file)
        csv_path = os.path.join(DATA_DIR, f"{match_id}.csv")
        
        if os.path.exists(csv_path):
            print(f"CSV for match {match_id} already exists. Deleting dem file.")
            try:
                os.remove(dem_path)
            except Exception:
                pass
            continue
            
        if parse_dem(dem_path):
            # IMMEDIATELY delete the dem file to save space
            try:
                os.remove(dem_path)
                print(f"Deleted parsed .dem file: {dem_file}")
            except Exception as e:
                print(f"Error deleting dem: {e}")
        else:
            print(f"Failed to parse {dem_file}, keeping it for inspection.")

    # 3. Re-train models
    print("\n=== Running AI Model Re-Training ===")
    try:
        subprocess.run(["python", "-u", TRAINER_SCRIPT], check=True)
        print("Training successfully finished.")
    except Exception as e:
        print(f"Training failed: {e}")
        return

    # 4. Re-export models to Lua
    print("\n=== Exporting New Model to Pure Lua ===")
    try:
        subprocess.run(["python", EXPORT_SCRIPT], check=True)
        print("Export to Lua complete.")
    except Exception as e:
        print(f"Export failed: {e}")
        return

    # 5. Copy new bot_generic.lua to Dota 2 folder
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
