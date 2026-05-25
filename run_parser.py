import os
import subprocess
import time

DATA_DIR = "C:\\бот\\data"
PARSER_EXE = "C:\\бот\\parser\\parser.exe"

def main():
    print("=== Dota 2 Replay Bulk Parser ===")
    
    if not os.path.exists(PARSER_EXE):
        print(f"Error: Parser executable not found at {PARSER_EXE}")
        print("Please build the parser first using 'go build parser.go'")
        return

    # Get list of all .dem files
    dem_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.dem')]
    if not dem_files:
        print("No .dem replay files found in data directory.")
        return
        
    print(f"Found {len(dem_files)} replay file(s) in data directory.")
    
    parsed_count = 0
    start_time = time.time()
    
    for f in dem_files:
        match_id = f.replace('.dem', '')
        csv_filename = f"{match_id}.csv"
        csv_path = os.path.join(DATA_DIR, csv_filename)
        
        # Skip if already parsed
        if os.path.exists(csv_path):
            print(f"Match {match_id} already has a parsed CSV dataset. Skipping.")
            continue
            
        dem_path = os.path.join(DATA_DIR, f)
        print(f"\n[{parsed_count + 1}] Parsing replay: {f}...")
        
        parse_start = time.time()
        try:
            # Run the compiled parser
            result = subprocess.run([PARSER_EXE, "-file", dem_path], capture_output=True, text=True, check=True)
            duration = time.time() - parse_start
            print(f"Successfully parsed Match {match_id} in {duration:.1f} seconds.")
            parsed_count += 1
        except subprocess.CalledProcessError as e:
            print(f"Error parsing Match {match_id}: {e.stderr}")
            
    total_duration = time.time() - start_time
    if parsed_count > 0:
        print(f"\nDone! Successfully parsed {parsed_count} replays in {total_duration:.1f} seconds.")
    else:
        print("\nAll replays were already parsed. Nothing to do!")

if __name__ == "__main__":
    main()
