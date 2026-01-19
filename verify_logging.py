import requests
import json
import os
import sys

BASE_URL = "http://localhost:8000/api"

def test_simulation_flow():
    print("1. Initializing simulation...")
    response = requests.post(f"{BASE_URL}/simulation/init", json={"steps_per_episode": 5})
    if response.status_code != 200:
        print(f"FAILED: Init response {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    session_id = data["session_id"]
    print(f"   Session ID: {session_id}")

    print("2. Running episode...")
    step_count = 0
    done = False
    
    while not done:
        # Always choose agent 0
        resp = requests.post(
            f"{BASE_URL}/simulation/{session_id}/step",
            json={"human_choice_idx": 0}
        )
        res_data = resp.json()
        final_result = res_data["final_result"]
        done = final_result["done"]
        step_count += 1
        print(f"   Step {step_count}: done={done}")
        
        if step_count > 10:
            print("FAILED: Episode didn't finish in expected steps")
            sys.exit(1)

    print("3. Verifying log file...")
    log_path = os.path.join("data", "sessions", session_id, "episode_0.json") # First episode is 0
    
    if not os.path.exists(log_path):
        print(f"FAILED: Log file not found at {log_path}")
        # List dir to see what happened
        print(f"Current dir: {os.getcwd()}")
        if os.path.exists(os.path.join("data", "sessions", session_id)):
            print("Dir exists, but file missing.")
        sys.exit(1)
        
    with open(log_path, 'r') as f:
        log_data = json.load(f)
        
    print(f"   Log file found with {len(log_data)} entries.")
    
    # Verify tuple structure in first entry
    entry = log_data[0]
    required_keys = ["t", "p", "rec_agent_0", "rec_agent_1", "human_choice", 
                     "agent_0_payoff", "agent_1_payoff", "outcome", "human_payoff", 
                     "t_next", "done"]
    
    missing = [k for k in required_keys if k not in entry]
    if missing:
        print(f"FAILED: Missing keys in log: {missing}")
        sys.exit(1)
        
    print("SUCCESS: Full flow and logging verified!")

if __name__ == "__main__":
    test_simulation_flow()
