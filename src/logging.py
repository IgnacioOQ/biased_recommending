import uuid
import json
import os
import numpy as np
from datetime import datetime

class DataLogger:
    def __init__(self, output_dir="data", max_steps=20, session_id=None):
        if session_id:
            self.session_id = session_id
        else:
            self.session_id = f"sessionid_{uuid.uuid4()}"
        self.output_dir = output_dir
        self.episode_buffer = []
        self.max_steps = max_steps

        # Initialize session file structure
        self.session_filepath = os.path.join(self.output_dir, f"{self.session_id}.json")
        self.session_data = {
            "session_meta": {
                "session_id": self.session_id,
                "total_number_of_steps_in_episode": self.max_steps,
                "start_time": datetime.now().isoformat()
            },
            "episodes": []
        }

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Create the initial session file
        self._write_session_file()

    def _write_session_file(self):
        with open(self.session_filepath, 'w') as f:
            json.dump(self.session_data, f, indent=4)

    def log_step(self, episode, step, p, recommendations, human_choice, human_reward, agent_rewards, outcome):
        entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "episode": episode,
            "step": step,
            "p": float(p),
            "recommendations": [int(r) for r in recommendations],
            "human_choice": int(human_choice),
            "human_reward": float(human_reward),
            "agent_rewards": [float(r) for r in agent_rewards],
            "outcome": outcome
        }
        self.episode_buffer.append(entry)

    def save_episode(self):
        if not self.episode_buffer:
            return

        # Load existing data (to be safe in case of manual edits or parallel processes, though unlikely here)
        # For this single-process notebook flow, we can just update our memory struct and write.
        if os.path.exists(self.session_filepath):
            with open(self.session_filepath, 'r') as f:
                self.session_data = json.load(f)

        # Append current episode
        self.session_data["episodes"].append(self.episode_buffer)

        # Update file
        self._write_session_file()

        self.episode_buffer = [] # Clear buffer
