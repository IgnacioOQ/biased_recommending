import uuid
import json
import os
import numpy as np
from datetime import datetime

class DataLogger:
    def __init__(self, output_dir="data"):
        self.session_id = f"sessionid_{uuid.uuid4()}"
        self.output_dir = output_dir
        self.episode_buffer = []

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

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

        # Filename: session_episode_timestamp.json
        episode_num = self.episode_buffer[0]['episode']
        filename = f"{self.session_id}_ep{episode_num}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(self.episode_buffer, f, indent=4)

        self.episode_buffer = [] # Clear buffer
