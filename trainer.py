import os
import time
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import joblib
import gc

DATA_DIR = "C:\\бот\\data"
MODEL_DIR = "C:\\бот\\model"

# Create model directory if it doesn't exist
os.makedirs(MODEL_DIR, exist_ok=True)

def load_dataset():
    manifest_path = "C:\\бот\\new_matches_manifest.txt"
    
    # 1. Read files listed in the manifest if it exists
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest_files = [line.strip() for line in f if line.strip()]
        
        if manifest_files:
            print(f"[MANIFEST] Found {len(manifest_files)} new files in manifest. Filtering data loading strictly to these files...")
            # Ensure the files exist and match our pattern
            csv_files = [f for f in manifest_files if f.endswith('.csv') and os.path.exists(os.path.join(DATA_DIR, f)) and f != 'wards_raw.csv']
        else:
            print("[MANIFEST] Manifest file exists but is empty. Training only on files created in the last 12 hours as new data...")
            # Fallback to files modified in last 12 hours
            now = time.time()
            all_csv = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and f != 'wards_raw.csv']
            csv_files = [f for f in all_csv if now - os.path.getmtime(os.path.join(DATA_DIR, f)) < 12 * 3600]
    else:
        print("[WARNING] Manifest file not found. Falling back to files created in the last 12 hours as new data...")
        # Fallback to files modified in last 12 hours
        now = time.time()
        all_csv = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and f != 'wards_raw.csv']
        csv_files = [f for f in all_csv if now - os.path.getmtime(os.path.join(DATA_DIR, f)) < 12 * 3600]
        
    if not csv_files:
        print("No NEW CSV datasets found matching the manifest or the 12-hour fallback. Exiting training to avoid training on old data.")
        return None
        
    print(f"Found {len(csv_files)} total NEW dataset(s) for training. Loading...")
    
    dfs = []
    for i, f in enumerate(csv_files):
        filepath = os.path.join(DATA_DIR, f)
        try:
            df = pd.read_csv(filepath)
            # Center coordinates by subtracting 8192 (Source 2 grid coordinate offset to map client-side)
            df['hero_x'] = df['hero_x'] - 8192
            df['hero_y'] = df['hero_y'] - 8192
            for j in range(1, 6):
                df[f'creep_{j}_x'] = np.where(df[f'creep_{j}_x'] != 0.0, df[f'creep_{j}_x'] - 8192, 0.0)
                df[f'creep_{j}_y'] = np.where(df[f'creep_{j}_y'] != 0.0, df[f'creep_{j}_y'] - 8192, 0.0)
                
            # Assign match_id from filename
            match_id = int(f.replace('.csv', ''))
            df['match_id'] = match_id
            
            # Downcast to float32/int32 to reduce memory footprint by 50%
            float_cols = df.select_dtypes(include=['float64']).columns
            df[float_cols] = df[float_cols].astype('float32')
            int_cols = df.select_dtypes(include=['int64']).columns
            df[int_cols] = df[int_cols].astype('int32')
            dfs.append(df)
        except Exception as e:
            print(f"Error loading {f}: {e}")
            
        if (i + 1) % 50 == 0:
            print(f"  Loaded {i+1}/{len(csv_files)} files...")
            gc.collect()
            
    print("Concatenating all datasets...")
    full_df = pd.concat(dfs, ignore_index=True)
    del dfs
    gc.collect()
    return full_df

def classify_positions(df):
    print("Classifying player positions (1-5) based on the first 5 minutes...")
    
    # 1. Define list of support heroes (cleaned of underscores to match camelCase CSV format)
    support_heroes = {
        'crystalmaiden', 'lion', 'witchdoctor', 'dazzle', 'shadowshaman',
        'lich', 'oracle', 'disruptor', 'keeperofthelight', 'bane',
        'warlock', 'ancientapparition', 'grimstroke', 'jakiro',
        'skywrathmage', 'treant', 'undying', 'rubick', 'chen', 'wisp',
        'shadowdemon', 'snapfire', 'mirana', 'bountyhunter',
        'nyxassassin', 'spiritbreaker', 'earthspirit', 'tusk',
        'eldertitan', 'techies', 'hoodwink'
    }
    
    df['clean_hero'] = df['hero_name'].str.lower().str.replace('cdota_unit_hero_', '').str.replace('npc_dota_hero_', '')
    df['is_support'] = df['clean_hero'].isin(support_heroes)
    
    # Active laning phase check (seconds between 120 and 300 to exclude pre-game fountain/bounty run bias!)
    first_5 = df[(df['game_time'] >= 120) & (df['game_time'] <= 300)]
    avg_coords = first_5.groupby(['match_id', 'clean_hero'])[['hero_x', 'hero_y']].mean().reset_index()
    
    # Classify team: Radiant is generally x < 0 initially
    avg_coords['is_support'] = avg_coords['clean_hero'].isin(support_heroes)
    avg_coords['is_radiant'] = avg_coords['hero_x'] < 0
    
    # Classify lane using mathematical map diagonal triangles (MID is y approx x, Bottom is x > y, Top is y > x)
    avg_coords['lane'] = 2  # default mid
    
    # Mid lane is close to the diagonal line y = x
    is_mid = np.abs(avg_coords['hero_x'] - avg_coords['hero_y']) < 2200
    
    # Side lanes
    is_bottom = (~is_mid) & (avg_coords['hero_x'] > avg_coords['hero_y'])
    is_top = (~is_mid) & (avg_coords['hero_y'] > avg_coords['hero_x'])
    
    # Safe lane (Radiant bottom, Dire top)
    avg_coords.loc[(avg_coords['is_radiant'] & is_bottom) | (~avg_coords['is_radiant'] & is_top), 'lane'] = 3
    
    # Offlane (Radiant top, Dire bottom)
    avg_coords.loc[(avg_coords['is_radiant'] & is_top) | (~avg_coords['is_radiant'] & is_bottom), 'lane'] = 1
    
    # Assign Position (1-5)
    avg_coords['position'] = 1
    avg_coords.loc[avg_coords['lane'] == 2, 'position'] = 2
    avg_coords.loc[(avg_coords['lane'] == 3) & (avg_coords['is_support']), 'position'] = 5
    avg_coords.loc[(avg_coords['lane'] == 3) & (~avg_coords['is_support']), 'position'] = 1
    avg_coords.loc[(avg_coords['lane'] == 1) & (avg_coords['is_support']), 'position'] = 4
    avg_coords.loc[(avg_coords['lane'] == 1) & (~avg_coords['is_support']), 'position'] = 3
    
    role_map = avg_coords[['match_id', 'clean_hero', 'position']]
    df = df.merge(role_map, on=['match_id', 'clean_hero'], how='left')
    
    df['position'] = df['position'].fillna(1).astype(int)
    print(f"Role distribution:\n{df['position'].value_counts()}")
    return df

def feature_engineering(df):
    print("Performing feature engineering...")
    
    # Calculate future movement target offset after 10 rows (~333ms)
    df['next_x'] = df.groupby('hero_name')['hero_x'].shift(-10)
    df['next_y'] = df.groupby('hero_name')['hero_y'].shift(-10)
    
    df['label_dx'] = df['next_x'] - df['hero_x']
    df['label_dy'] = df['next_y'] - df['hero_y']
    
    df = df.dropna(subset=['label_dx', 'label_dy'])
    
    features = []
    
    # Hero features
    features.append(df['hero_hp'] / df['hero_max_hp'])
    hero_mana_pct = np.where(df['hero_max_mana'] > 0, df['hero_mana'] / df['hero_max_mana'], 0.0)
    features.append(pd.Series(hero_mana_pct, index=df.index))
    
    # Relative creep features
    for i in range(1, 6):
        creep_x = df[f'creep_{i}_x']
        creep_y = df[f'creep_{i}_y']
        
        creep_dx = np.where(creep_x != 0.0, creep_x - df['hero_x'], 0.0)
        creep_dy = np.where(creep_y != 0.0, creep_y - df['hero_y'], 0.0)
        
        creep_hp_pct = np.where(df[f'creep_{i}_max_hp'] > 0, df[f'creep_{i}_hp'] / df[f'creep_{i}_max_hp'], 0.0)
        
        features.extend([
            pd.Series(creep_dx, name=f'creep_{i}_dx', index=df.index),
            pd.Series(creep_dy, name=f'creep_{i}_dy', index=df.index),
            pd.Series(creep_hp_pct, name=f'creep_{i}_hp_pct', index=df.index),
            df[f'creep_{i}_dist'],
            df[f'creep_{i}_team']
        ])
        
    X = pd.concat(features, axis=1)
    X.columns = [
        'hero_hp_pct', 'hero_mana_pct',
        'creep_1_dx', 'creep_1_dy', 'creep_1_hp_pct', 'creep_1_dist', 'creep_1_team',
        'creep_2_dx', 'creep_2_dy', 'creep_2_hp_pct', 'creep_2_dist', 'creep_2_team',
        'creep_3_dx', 'creep_3_dy', 'creep_3_hp_pct', 'creep_3_dist', 'creep_3_team',
        'creep_4_dx', 'creep_4_dy', 'creep_4_hp_pct', 'creep_4_dist', 'creep_4_team',
        'creep_5_dx', 'creep_5_dy', 'creep_5_hp_pct', 'creep_5_dist', 'creep_5_team'
    ]
    
    X['position'] = df['position']
    y_dx = df['label_dx']
    y_dy = df['label_dy']
    
    return X, y_dx, y_dy

def main():
    print("=== Dota 2 5-Position AI Model Trainer ===")
    
    df = load_dataset()
    if df is None or len(df) == 0:
        return
        
    # 1. Perform Role Classification
    df = classify_positions(df)
    
    # 2. Extract Features and Labels
    X, y_dx, y_dy = feature_engineering(df)
    del df
    gc.collect()
    
    # 3. Train models for each Position (1-5) separately!
    for pos in range(1, 6):
        print(f"\n--- Training Position {pos} Models ---")
        pos_mask = X['position'] == pos
        
        X_pos = X[pos_mask].drop(columns=['position'])
        y_dx_pos = y_dx[pos_mask]
        y_dy_pos = y_dy[pos_mask]
        
        print(f"Dataset size for Position {pos}: {len(X_pos)} samples")
        if len(X_pos) < 100:
            print(f"Skipping Position {pos} due to insufficient samples.")
            continue
            
        # Model iteration count: 80 Iterations is perfect and fast for 5 concurrent models
        print(f"Training Position {pos} X Model...")
        model_x = HistGradientBoostingRegressor(max_iter=80, random_state=42)
        model_x.fit(X_pos, y_dx_pos)
        
        print(f"Training Position {pos} Y Model...")
        model_y = HistGradientBoostingRegressor(max_iter=80, random_state=42)
        model_y.fit(X_pos, y_dy_pos)
        
        # Save models
        model_x_path = os.path.join(MODEL_DIR, f"dota_ai_model_x_pos{pos}.joblib")
        model_y_path = os.path.join(MODEL_DIR, f"dota_ai_model_y_pos{pos}.joblib")
        
        joblib.dump(model_x, model_x_path)
        joblib.dump(model_y, model_y_path)
        
        print(f"Saved Position {pos} models successfully.")
        
    print("\n=== All position-specific models successfully trained! ===")

if __name__ == "__main__":
    main()
