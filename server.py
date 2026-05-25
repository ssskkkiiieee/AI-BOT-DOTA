import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
try:
    from http.server import ThreadingHTTPServer
except ImportError:
    ThreadingHTTPServer = HTTPServer

import pandas as pd
import numpy as np
import joblib

MODEL_DIR = "C:\\бот\\model"
PORT = 8080

print("Loading trained models...")
model_x_path = os.path.join(MODEL_DIR, "dota_ai_model_x.joblib")
model_y_path = os.path.join(MODEL_DIR, "dota_ai_model_y.joblib")

if not os.path.exists(model_x_path) or not os.path.exists(model_y_path):
    print("Warning: Models not found yet. Make sure training has completed.")
    model_x = None
    model_y = None
else:
    model_x = joblib.load(model_x_path)
    model_y = joblib.load(model_y_path)
    print("Models loaded successfully!")

class PredictionServer(BaseHTTPRequestHandler):
    request_count = 0

    def log_message(self, format, *args):
        PredictionServer.request_count += 1
        print(f"[#{PredictionServer.request_count}] {self.command} {self.path} — {args[0] if args else ''}")

    def do_GET(self):
        global model_x, model_y
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            "status": "online",
            "models_loaded": (model_x is not None and model_y is not None),
            "message": "Dota 2 AI Prediction Server is active. Send POST requests to /predict with state JSON."
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        global model_x, model_y
        
        # Lazy reload models if they weren't loaded at start
        if model_x is None or model_y is None:
            if os.path.exists(model_x_path) and os.path.exists(model_y_path):
                print("Lazy loading trained models...")
                model_x = joblib.load(model_x_path)
                model_y = joblib.load(model_y_path)
                print("Models loaded!")
            else:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Models are still training. Please try again in a few seconds.'}).encode('utf-8'))
                return

        if self.path == '/predict':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                state = json.loads(post_data.decode('utf-8'))
                
                # Extract hero features
                hero_hp_pct = float(state.get('hero_hp_pct', 1.0))
                hero_mana_pct = float(state.get('hero_mana_pct', 1.0))
                
                # Extract and pad creeps list to 5
                creeps = state.get('creeps', [])
                if len(creeps) < 5:
                    creeps = creeps + [{}] * (5 - len(creeps))
                
                # Construct feature dict
                features = {
                    'hero_hp_pct': hero_hp_pct,
                    'hero_mana_pct': hero_mana_pct
                }
                
                for i in range(1, 6):
                    creep = creeps[i-1]
                    features[f'creep_{i}_dx'] = float(creep.get('dx', 0.0))
                    features[f'creep_{i}_dy'] = float(creep.get('dy', 0.0))
                    features[f'creep_{i}_hp_pct'] = float(creep.get('hp_pct', 0.0))
                    features[f'creep_{i}_dist'] = float(creep.get('dist', 0.0))
                    features[f'creep_{i}_team'] = int(creep.get('team', 0))
                
                # Convert to DataFrame with correct column ordering
                columns = [
                    'hero_hp_pct', 'hero_mana_pct',
                    'creep_1_dx', 'creep_1_dy', 'creep_1_hp_pct', 'creep_1_dist', 'creep_1_team',
                    'creep_2_dx', 'creep_2_dy', 'creep_2_hp_pct', 'creep_2_dist', 'creep_2_team',
                    'creep_3_dx', 'creep_3_dy', 'creep_3_hp_pct', 'creep_3_dist', 'creep_3_team',
                    'creep_4_dx', 'creep_4_dy', 'creep_4_hp_pct', 'creep_4_dist', 'creep_4_team',
                    'creep_5_dx', 'creep_5_dy', 'creep_5_hp_pct', 'creep_5_dist', 'creep_5_team'
                ]
                
                df = pd.DataFrame([features], columns=columns)
                
                # Run predictions
                pred_dx = float(model_x.predict(df)[0])
                pred_dy = float(model_y.predict(df)[0])
                
                response = {
                    'dx': pred_dx,
                    'dy': pred_dy
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=ThreadingHTTPServer, handler_class=PredictionServer):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    print(f"=== Dota 2 AI Bot Prediction Server ===")
    print(f"Listening on http://localhost:{PORT}/predict ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print("Stopping server.")

if __name__ == '__main__':
    run()
