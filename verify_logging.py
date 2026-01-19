import requests
import json
import os
import sys

BASE_URL = "http://localhost:8000/api"

def test_simulation_flow():
    print("1. Initializing simulation...")
    # New payload with participant_name
    payload = {
        "steps_per_episode": 5,
        "participant_name": "TestUser"
    }
    response = requests.post(f"{BASE_URL}/simulation/init", json=payload)
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
    # New log path: data/sessions/{session_id}.json
    log_path = os.path.join("data", "sessions", f"{session_id}.json")
    
    if not os.path.exists(log_path):
        print(f"FAILED: Log file not found at {log_path}")
        # List dir to see what happened
        print(f"Current dir: {os.getcwd()}")
        sys.exit(1)
        
    with open(log_path, 'r') as f:
        log_data = json.load(f)
        
    # Check top-level structure
    if log_data["session_id"] != session_id:
        print("FAILED: Session ID mismatch in log")
        sys.exit(1)
    if log_data["participant_name"] != "TestUser":
        print(f"FAILED: Participant name mismatch. Got {log_data.get('participant_name')}")
        sys.exit(1)
    
    episodes = log_data.get("episodes", {})
    if "0" not in episodes:
         print("FAILED: Episode 0 not found in log")
         sys.exit(1)

    episode_data = episodes["0"]
    print(f"   Log file found. Episode 0 has {len(episode_data)} entries.")
    
    # Verify tuple structure in first entry
    entry = episode_data[0]
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
