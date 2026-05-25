import os
import sys
import time
import bz2
import requests

API_KEY = "deb3dc65-2e3a-4c9e-9d16-bce6ff480468"
DATA_DIR = "C:\\бот\\data"

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_json_explorer(sql_query):
    url = f"https://api.opendota.com/api/explorer?sql={sql_query}&api_key={API_KEY}"
    print(f"Executing SQL Explorer query...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if 'rows' in data:
            return data['rows']
        else:
            print("Explorer response format is invalid.")
            return None
    except Exception as e:
        print(f"Error executing SQL Explorer query: {e}")
        return None

def download_file(url, filepath):
    print(f"Downloading replay from: {url}")
    print(f"Saving to: {filepath}")
    
    start_time = time.time()
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.2f}% ({downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB)", end="", flush=True)
                    else:
                        print(f"\rDownloaded: {downloaded / (1024*1024):.1f} MB", end="", flush=True)
            print()
            
        duration = time.time() - start_time
        print(f"Download completed in {duration:.1f} seconds.")
        return True
    except Exception as e:
        print(f"\nError downloading file: {e}")
        return False

def decompress_bz2(source_path, dest_path):
    print(f"Decompressing {source_path} to {dest_path}...")
    start_time = time.time()
    try:
        with bz2.BZ2File(source_path, 'rb') as source, open(dest_path, 'wb') as dest:
            # Read in 1MB chunks
            buffer_size = 1024 * 1024
            while True:
                chunk = source.read(buffer_size)
                if not chunk:
                    break
                dest.write(chunk)
        duration = time.time() - start_time
        print(f"Decompression completed in {duration:.1f} seconds.")
        # Delete the compressed bz2 file to save disk space
        if os.path.exists(source_path):
            os.remove(source_path)
            print("Removed temporary compressed .bz2 file.")
        return True
    except Exception as e:
        print(f"Error during decompression: {e}")
        return False

def main():
    print("=== Dota 2 Replay Downloader ===")
    
    # Query recently recorded professional matches that have replay metadata (cluster, replay_salt)
    sql_query = "SELECT match_id, cluster, replay_salt FROM matches WHERE leagueid > 0 AND replay_salt IS NOT NULL ORDER BY match_id DESC LIMIT 100"
    
    matches = fetch_json_explorer(sql_query)
    if not matches:
        print("No matches found in database.")
        return
    
    print(f"Found {len(matches)} professional matches with replay metadata.")
    
    downloaded_count = 0
    max_downloads = 1
    
    if len(sys.argv) > 1:
        try:
            max_downloads = int(sys.argv[1])
        except ValueError:
            pass
            
    print(f"Attempting to download up to {max_downloads} replay(s)...")
    
    for match in matches:
        match_id = match['match_id']
        cluster = match['cluster']
        replay_salt = match['replay_salt']
        
        # Construct the direct Valve CDN replay URL
        replay_url = f"http://replay{cluster}.valve.net/570/{match_id}_{replay_salt}.dem.bz2"
        
        compressed_filepath = os.path.join(DATA_DIR, f"{match_id}.dem.bz2")
        decompressed_filepath = os.path.join(DATA_DIR, f"{match_id}.dem")
        
        # Skip if already downloaded
        if os.path.exists(decompressed_filepath):
            print(f"Replay for match {match_id} already exists locally.")
            downloaded_count += 1
            if downloaded_count >= max_downloads:
                break
            continue
            
        print(f"\nProcessing Match ID: {match_id}")
        
        # Download and decompress directly from Valve CDN
        if download_file(replay_url, compressed_filepath):
            if decompress_bz2(compressed_filepath, decompressed_filepath):
                print(f"Successfully downloaded and extracted replay for Match {match_id}!")
                downloaded_count += 1
                if downloaded_count >= max_downloads:
                    break
            else:
                # Clean up if bz2 decompression failed
                if os.path.exists(compressed_filepath):
                    os.remove(compressed_filepath)
        
        # Minor sleep to be safe
        time.sleep(1)
        
    if downloaded_count == 0:
        print("\nCould not download any replays.")
    else:
        print(f"\nDone! Successfully downloaded {downloaded_count} replays to: {DATA_DIR}")

if __name__ == "__main__":
    main()
