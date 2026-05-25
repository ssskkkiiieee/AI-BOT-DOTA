import os
import time
import datetime
import subprocess

PIPELINE_SCRIPT = r"C:\бот\run_pipeline.py"
RESEARCH_SCRIPT = r"C:\бот\web_researcher.py"
LOG_FILE = r"C:\бот\pipeline_runner.log"

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [RUNNER] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def main():
    log_message("=== STARTING DOTA 2 AI DUAL CONTINUOUS LEARNING RUNNER ===")
    log_message("This runner will run forever, recursively searching the web and retraining models simultaneously.")
    
    run_interval = 60  # Continuous mode: sleep only 60 seconds between learning loops
    iteration = 0
    
    while True:
        iteration += 1
        log_message(f"--- Launching Continuous Learning Loop Iteration #{iteration} ---")
        
        # 1. First trigger Internet Meta Crawler
        log_message("Executing web crawler: web_researcher.py...")
        try:
            subprocess.run(["python", RESEARCH_SCRIPT], check=True)
            log_message("Internet intelligence successfully refreshed!")
        except Exception as e:
            log_message(f"[ERROR] Web crawler failed: {e}")
            
        # 2. Trigger ML Replay Parser pipeline (1600 matches)
        log_message("Executing pipeline: run_pipeline.py 1600...")
        try:
            process = subprocess.run(["python", PIPELINE_SCRIPT, "1600"], capture_output=True, text=True, check=True)
            log_message("Pipeline executed successfully!")
            log_message(f"Pipeline stdout: {process.stdout[-500:]}")
        except subprocess.CalledProcessError as e:
            log_message(f"[ERROR] Pipeline failed with code {e.returncode}!")
            log_message(f"[ERROR] stderr: {e.stderr}")
        except Exception as e:
            log_message(f"[ERROR] Pipeline runner encountered exception: {e}")
            
        log_message(f"Iteration completed! Next cycle scheduled in 2 hours ({run_interval} seconds)...")
        time.sleep(run_interval)

if __name__ == "__main__":
    main()
