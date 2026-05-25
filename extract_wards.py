import os
import json
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

RAW_WARDS_PATH = r"C:\бот\data\wards_raw.csv"
OUTPUT_JSON_PATH = r"C:\бот\ward_spots.json"

# Premium pre-defined bootstrap hidden pro MMR ward spots (map coordinates x, y)
# These are top-tier hidden spots in trees, ramps, and cliffs used by pro players
BOOTSTRAP_WARD_SPOTS = [
    # River / Roshan Pit
    {"x": -2300, "y": 1800, "type": "observer", "desc": "Roshan Cliff Hidden"},
    {"x": -600, "y": 1900, "type": "observer", "desc": "River Top Water Trees"},
    {"x": 800, "y": -1900, "type": "observer", "desc": "River Bot Water Trees"},
    {"x": -2800, "y": 900, "type": "sentry", "desc": "Roshan Sentry"},
    
    # Radiant Safe Lane / Jungle
    {"x": 4800, "y": -3800, "type": "observer", "desc": "Rad Safe T1 Behind Trees"},
    {"x": -1700, "y": -4200, "type": "observer", "desc": "Rad Jungle Deep Edge"},
    {"x": -3200, "y": -3800, "type": "observer", "desc": "Rad Jungle High Ground Ramp"},
    {"x": 3500, "y": -6200, "type": "observer", "desc": "Rad Bottom T2 Jungle"},
    
    # Dire Safe Lane / Jungle
    {"x": -4800, "y": 3800, "type": "observer", "desc": "Dire Safe T1 Behind Trees"},
    {"x": 1700, "y": 4200, "type": "observer", "desc": "Dire Jungle Deep Edge"},
    {"x": 3200, "y": 3800, "type": "observer", "desc": "Dire Jungle High Ground Ramp"},
    {"x": -3500, "y": 6200, "type": "observer", "desc": "Dire Top T2 Jungle"},
    
    # Radiant Offlane / Tri-camp
    {"x": -4500, "y": 1200, "type": "observer", "desc": "Rad Offlane Deep Behind Trees"},
    {"x": -6100, "y": -1500, "type": "observer", "desc": "Rad Secret Shop Cliff"},
    
    # Dire Offlane / Tri-camp
    {"x": 4500, "y": -1200, "type": "observer", "desc": "Dire Offlane Deep Behind Trees"},
    {"x": 6100, "y": 1500, "type": "observer", "desc": "Dire Secret Shop Cliff"},
]

def main():
    print("=== Extracting Hidden Pro MMR Ward Spots ===")
    
    ward_spots = list(BOOTSTRAP_WARD_SPOTS)
    
    if os.path.exists(RAW_WARDS_PATH):
        try:
            print(f"Reading raw ward placements from: {RAW_WARDS_PATH}")
            df = pd.read_csv(RAW_WARDS_PATH)
            
            if len(df) > 5:
                # Separate Observer and Sentry wards
                for ward_type in ["CDOTA_NPC_Observer_Ward", "CDOTA_NPC_Sentry_Ward"]:
                    type_str = "observer" if "Observer" in ward_type else "sentry"
                    sub_df = df[df['class_name'] == ward_type]
                    
                    if len(sub_df) < 3:
                        continue
                        
                    # Cluster ward placements using DBSCAN (eps=300 is approx 3 meters)
                    coords = sub_df[['x', 'y']].values
                    clustering = DBSCAN(eps=300, min_samples=2).fit(coords)
                    
                    labels = clustering.labels_
                    unique_labels = set(labels)
                    
                    for label in unique_labels:
                        if label == -1: # Noise
                            continue
                        
                        # Find centroid of the cluster
                        cluster_coords = coords[labels == label]
                        centroid = cluster_coords.mean(axis=0)
                        
                        # Filter out standard obvious high-ground eye pillars
                        # Standard pillars are typically at specific heights or locations
                        # We can calculate distance to typical pillars and exclude if close
                        eye_pillars = [
                            (-3000, -3000), (-4500, 1500), (3000, 3000), (4500, -1500),
                            (-1000, 2500), (1000, -2500)
                        ]
                        
                        is_obvious = False
                        for px, py in eye_pillars:
                            dist = np.sqrt((centroid[0] - px)**2 + (centroid[1] - py)**2)
                            if dist < 450.0:
                                is_obvious = True
                                break
                                
                        if not is_obvious:
                            ward_spots.append({
                                "x": float(centroid[0]),
                                "y": float(centroid[1]),
                                "type": type_str,
                                "desc": f"Pro Hidden {type_str.title()} Spot"
                            })
                            
            print(f"Successfully extracted {len(ward_spots) - len(BOOTSTRAP_WARD_SPOTS)} additional hidden spots.")
        except Exception as e:
            print(f"Error parsing raw wards: {e}")
            
    # Save the consolidated list to JSON
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(ward_spots, f, indent=4)
        
    print(f"Consolidated hidden ward spots successfully saved to: {OUTPUT_JSON_PATH} ({len(ward_spots)} spots total).")

if __name__ == "__main__":
    main()
