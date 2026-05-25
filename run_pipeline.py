import os
import sys
import time
import bz2
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "deb3dc65-2e3a-4c9e-9d16-bce6ff480468"
DATA_DIR = "C:\\бот\\data"
MODEL_DIR = "C:\\бот\\model"
PARSER_EXE = "C:\\бот\\parser\\parser.exe"
TRAINER_SCRIPT = "C:\\бот\\trainer.py"
MAX_WORKERS = 4  # Sweet spot for parallel downloading and parsing without disk congestion

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_json_explorer(sql_query):
    url = f"https://api.opendota.com/api/explorer?sql={sql_query}&api_key={API_KEY}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        if 'rows' in data:
            return data['rows']
    except Exception as e:
        print(f"Error executing SQL Explorer query: {e}")
    return None

def download_file(url, filepath, match_id):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    out_file.write(chunk)
        return True
    except Exception as e:
        print(f"[Match {match_id}] Error downloading: {e}")
        return False

def decompress_bz2(source_path, dest_path, match_id):
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
        print(f"[Match {match_id}] Error decompressing: {e}")
        return False

def ensure_replay_salt(match):
    if match.get('cluster') is not None and match.get('replay_salt') is not None:
        return True
        
    match_id = match['match_id']
    
    # Try OpenDota first
    try:
        url = f"https://api.opendota.com/api/matches/{match_id}?api_key={API_KEY}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            cluster = data.get('cluster')
            replay_salt = data.get('replay_salt')
            if cluster is not None and replay_salt is not None:
                match['cluster'] = int(cluster)
                match['replay_salt'] = int(replay_salt)
                print(f"[Match {match_id}] Discovered metadata via OpenDota: cluster={cluster}, salt={replay_salt}")
                return True
    except Exception as e:
        pass
        
    # Try Stratz API as fallback
    try:
        url = f"https://api.stratz.com/api/v1/match/{match_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            cluster = data.get('clusterId')
            replay_salt = data.get('replaySalt')
            if cluster is not None and replay_salt is not None:
                match['cluster'] = int(cluster)
                match['replay_salt'] = int(replay_salt)
                print(f"[Match {match_id}] Discovered metadata via Stratz API: cluster={cluster}, salt={replay_salt}")
                return True
    except Exception as e:
        pass
        
    return False

def fetch_matches_from_providers(target_count):
    discovered = []
    
    # Provider 1: OpenDota SQL Explorer (Paginating chunk size of 500 to prevent database timeouts)
    print("Discovering matches from Provider 1: OpenDota SQL Explorer...")
    chunk_size = 500
    for offset in range(0, target_count + 1000, chunk_size):
        sql_query = f"SELECT match_id, cluster, replay_salt FROM matches ORDER BY match_id DESC LIMIT {chunk_size} OFFSET {offset}"
        rows = fetch_json_explorer(sql_query)
        if rows:
            valid_chunk_count = 0
            for r in rows:
                if r.get('match_id') and r.get('cluster') is not None and r.get('replay_salt') is not None:
                    discovered.append({
                        'match_id': int(r['match_id']),
                        'cluster': int(r['cluster']),
                        'replay_salt': int(r['replay_salt'])
                    })
                    valid_chunk_count += 1
            print(f"  Paginator: Discovered {valid_chunk_count} valid matches in chunk (offset {offset}).")
            if len(discovered) >= target_count + 500:
                break
            time.sleep(1) # Polite gap between requests
        else:
            break
    print(f"Provider 1: Discovered {len(discovered)} valid matches total after paginated filtering.")
    
    # Provider 2: OpenDota Public ProMatches endpoint (Fallback / Complement)
    if len(discovered) < target_count:
        print("Discovering matches from Provider 2: OpenDota /proMatches endpoint...")
        try:
            url = f"https://api.opendota.com/api/proMatches?api_key={API_KEY}"
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                pro_matches = resp.json()
                for pm in pro_matches:
                    match_id = pm.get('match_id')
                    if match_id:
                        discovered.append({
                            'match_id': int(match_id),
                            'cluster': None,
                            'replay_salt': None
                        })
                print(f"Provider 2: Added {len(pro_matches)} pro match candidates.")
        except Exception as e:
            print(f"Error querying Provider 2: {e}")
            
    # Provider 3: Stratz API GraphQL (Professional / High MMR)
    if len(discovered) < target_count:
        print("Discovering matches from Provider 3: Stratz GraphQL...")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            query = """
            query {
              matches(leagueId: 1, take: 100) {
                id
                clusterId
                replaySalt
              }
            }
            """
            resp = requests.post("https://api.stratz.com/graphql", json={"query": query}, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                matches = data.get('data', {}).get('matches', [])
                for m in matches:
                    if m.get('id') and m.get('clusterId') and m.get('replaySalt'):
                        discovered.append({
                            'match_id': int(m['id']),
                            'cluster': int(m['clusterId']),
                            'replay_salt': int(m['replaySalt'])
                        })
                print(f"Provider 3: Discovered {len(matches)} matches via Stratz.")
        except Exception as e:
            print(f"Error querying Provider 3: {e}")
            
    # Remove duplicates preserving order
    seen = set()
    unique_matches = []
    for m in discovered:
        if m['match_id'] not in seen:
            seen.add(m['match_id'])
            unique_matches.append(m)
            
    return unique_matches

def process_match(match, index, total):
    match_id = match['match_id']
    csv_path = os.path.join(DATA_DIR, f"{match_id}.csv")
    
    # Check if already processed
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 100:
        return f"Match {match_id} already exists."
        
    print(f"[{index}/{total}] Starting Match ID: {match_id}")
    
    # Ensure we have replay salt and cluster (dynamic on-demand metadata recovery)
    if not ensure_replay_salt(match):
        return f"Match {match_id} failed: could not resolve replay salt or cluster."
        
    cluster = match['cluster']
    replay_salt = match['replay_salt']
    
    compressed_filepath = os.path.join(DATA_DIR, f"{match_id}.dem.bz2")
    decompressed_filepath = os.path.join(DATA_DIR, f"{match_id}.dem")
    
    try:
        # 1. Download bz2 from Valve CDN
        replay_url = f"http://replay{cluster}.valve.net/570/{match_id}_{replay_salt}.dem.bz2"
        if not download_file(replay_url, compressed_filepath, match_id):
            return f"Match {match_id} download failed."
            
        # 2. Decompress bz2
        if not decompress_bz2(compressed_filepath, decompressed_filepath, match_id):
            return f"Match {match_id} decompression failed."
            
        # 3. Parse dem file using Go parser
        parse_start = time.time()
        subprocess.run([PARSER_EXE, "-file", decompressed_filepath], capture_output=True, text=True, check=True)
        parse_duration = time.time() - parse_start
        return f"Match {match_id} successfully parsed in {parse_duration:.1f}s."
        
    except subprocess.CalledProcessError as e:
        return f"Match {match_id} parsing failed: {e.stderr}"
    except Exception as e:
        return f"Match {match_id} failed with error: {e}"
    finally:
        # Guarantee immediate clean deletion of temporary files to save space!
        if os.path.exists(compressed_filepath):
            try: os.remove(compressed_filepath)
            except: pass
        if os.path.exists(decompressed_filepath):
            try: os.remove(decompressed_filepath)
            except: pass

def main():
    print("=== Dota 2 AI Bot Parallel Data Pipeline Coordinator ===")
    
    target_count = 1600
    if len(sys.argv) > 1:
        try:
            target_count = int(sys.argv[1])
        except ValueError:
            pass
            
    print(f"Target matches to parse: {target_count}")
    
    manifest_path = "C:\\бот\\new_matches_manifest.txt"
    # Clear manifest at the start of the execution to ensure only new data is trained
    with open(manifest_path, "w") as f:
        f.write("")
    
    # Query pro matches with multi-provider discovery
    matches = fetch_matches_from_providers(target_count)
    if not matches:
        print("Failed to retrieve matches from any API provider.")
        return
        
    print(f"Retrieved {len(matches)} total candidate matches.")
    
    # Filter out already parsed ones
    to_process = []
    for match in matches:
        csv_path = os.path.join(DATA_DIR, f"{match['match_id']}.csv")
        if not (os.path.exists(csv_path) and os.path.getsize(csv_path) > 100):
            to_process.append(match)
            if len(to_process) >= target_count:
                break
                
    print(f"Found {len(to_process)} matches that need to be processed.")
    if not to_process:
        print("All matches already parsed!")
        # Trigger ML model training even if no new matches, trainer will handle empty manifest safely
        print("\n=== Launching Model Training ===")
        training_start = time.time()
        try:
            subprocess.run(["python", "-u", TRAINER_SCRIPT], check=True)
            print(f"Model training completed in {time.time() - training_start:.1f} seconds.")
        except Exception as e:
            print(f"Training failed: {e}")
        return

    # Process in parallel using a ThreadPoolExecutor
    print(f"Starting ThreadPoolExecutor with {MAX_WORKERS} parallel workers...")
    completed_count = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_match, match, i + 1, len(to_process)): match for i, match in enumerate(to_process)}
        
        for future in as_completed(futures):
            result = future.result()
            print(f"[Pipeline Log] {result}")
            match_item = futures[future]
            if "successfully parsed" in result:
                completed_count += 1
                csv_filename = f"{match_item['match_id']}.csv"
                # Record to manifest
                with open(manifest_path, "a") as f:
                    f.write(csv_filename + "\n")
            elif "already exists" in result:
                completed_count += 1
            
            # Print periodic progress
            elapsed = time.time() - start_time
            print(f"--- Progress: {completed_count}/{len(to_process)} matches complete | Elapsed Time: {elapsed/60:.1f}m ---")
            
    print(f"\nSuccessfully gathered and parsed {completed_count} datasets in {time.time() - start_time:.1f} seconds!")
    
    # 4. Trigger ML model training
    print("\n=== Launching Model Training on New Datasets ===")
    training_start = time.time()
    try:
        subprocess.run(["python", "-u", TRAINER_SCRIPT], check=True)
        print(f"Model training completed in {time.time() - training_start:.1f} seconds.")
    except Exception as e:
        print(f"Training failed: {e}")

if __name__ == "__main__":
    main()

