import numpy as np
import os
import json
import uuid
from datetime import datetime
from backend.advanced_environment import AdvancedBanditEnvironment
from backend.advanced_agents import AdvancedRecommenderAgent
from backend.human_proxy_agent import HumanProxyAgent
from backend.logging import DataLogger
from backend.advanced_analysis import compute_advanced_policy_metrics

# Helper for JSON serialization
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class ProxySimulation:
    def __init__(self, num_episodes=1000, output_dir="data", steps_per_episode=20, session_id=None):
        self.output_dir = output_dir
        self.num_episodes = num_episodes
        self.steps_per_episode = steps_per_episode

        # Environment
        self.env = AdvancedBanditEnvironment(max_steps=steps_per_episode)

        # Agents
        self.recommenders = [
            AdvancedRecommenderAgent(agent_id=0),
            AdvancedRecommenderAgent(agent_id=1)
        ]
        self.human_proxy = HumanProxyAgent()

        # Logging
        self.session_id = session_id if session_id else f"sessionid_{uuid.uuid4()}"
        self.logger = DataLogger(output_dir=output_dir, max_steps=steps_per_episode, session_id=self.session_id)

        # Human Proxy History Buffer (per episode)
        self.human_proxy_history = []

        # Metrics History
        self.metrics_history = []

        # Human Rewards History
        self.human_reward_history = []

        # Session Data Storage (Growing JSON)
        self.history_filepath = os.path.join(output_dir, f"proxy_simulation_history_{self.session_id}.json")
        self._init_history_file()

    def _init_history_file(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        initial_data = {
            "session_meta": {
                "session_id": self.session_id,
                "type": "ProxySimulation",
                "start_time": datetime.now().isoformat(),
                "steps_per_episode": self.steps_per_episode,
                "data_structure_recommenders": "Dict {agent_id: [(State [p, t], Action, Reward, Next_State [p, t+1], Done)]}",
                "data_structure_human": "List [(State [r0, r1, t, success_0, success_1], Action, Reward, Next_State [...], Done)]"
            },
            "episodes": []
        }
        with open(self.history_filepath, 'w') as f:
            json.dump(initial_data, f, indent=4, cls=NumpyEncoder)

    def _save_episode_history(self, env_history, human_history):
        """Appends the episode's history to the JSON file."""
        if os.path.exists(self.history_filepath):
            with open(self.history_filepath, 'r') as f:
                data = json.load(f)
        else:
            return # Should exist from init

        episode_entry = {
            "recommenders": env_history,
            "human_proxy": human_history
        }
        data["episodes"].append(episode_entry)

        with open(self.history_filepath, 'w') as f:
            json.dump(data, f, indent=4, cls=NumpyEncoder)

    def run(self):
        print(f"Starting Proxy Simulation (Session {self.session_id})...")

        for episode in range(self.num_episodes):
            obs = self.env.reset() # [p, t=0]
            done = False
            self.human_proxy_history = []
            
            # Track successful recommendations per agent in this episode
            # Success = recommendation matched coin outcome (Recommend+Heads or NotRecommend+Tails)
            success_counts = [0, 0]

            # Initial Recommendations
            # Recommenders observe [p, 0]
            current_recs = [agent.select_action(obs) for agent in self.recommenders]

            while not done:
                current_p = obs[0]
                current_t = obs[1]

                # 1. Human Proxy Observation
                # Vector: [rec_0, rec_1, t, success_0, success_1]
                human_obs = np.array([current_recs[0], current_recs[1], current_t, success_counts[0], success_counts[1]], dtype=np.float32)

                # 2. Human Proxy Action
                human_choice = self.human_proxy.select_action(human_obs)

                # 3. Environment Step
                human_reward, agent_rewards, outcome_str, done, next_obs = self.env.step(human_choice, current_recs)
                
                # 3.5 Update Success Counts based on coin outcome
                # Success = Recommend(1) + Heads, or NotRecommend(0) + Tails
                is_heads = (outcome_str == 'Heads')
                for i, rec in enumerate(current_recs):
                    if (rec == 1 and is_heads) or (rec == 0 and not is_heads):
                        success_counts[i] += 1

                # 4. Get Next Recommendations (for Next State of Human)
                # Next Recommender Obs: next_obs [p', t+1]
                # If done, next_recs might not matter, but we need them for the tuple (S, A, R, S', Done)
                next_recs = [0, 0] # Placeholder
                if not done:
                    next_recs = [agent.select_action(next_obs) for agent in self.recommenders]

                next_human_obs = np.array([next_recs[0], next_recs[1], next_obs[1], success_counts[0], success_counts[1]], dtype=np.float32)

                # 5. Store/Train Recommenders
                # They observe [p, t], act, get reward, next is [p', t+1]
                for i, agent in enumerate(self.recommenders):
                    # Store in Env History
                    self.env.store_transition(
                        i, obs, current_recs[i], agent_rewards[i], next_obs, done
                    )
                    # Train
                    agent.store_transition(obs, current_recs[i], agent_rewards[i], next_obs, done)
                    agent.update()

                # 6. Store Human Proxy Transition
                self.human_proxy.store_transition(human_obs, human_choice, human_reward, next_human_obs, done)
                self.human_proxy_history.append((human_obs, human_choice, human_reward, next_human_obs, done))

                # 7. Logging
                self.logger.log_step(
                    episode=episode,
                    step=self.env.steps, # t+1
                    p=current_p,
                    recommendations=current_recs,
                    human_choice=human_choice,
                    human_reward=human_reward,
                    agent_rewards=agent_rewards,
                    outcome=outcome_str
                )

                # Update state
                obs = next_obs
                current_recs = next_recs

            # End of Episode
            self.logger.save_episode()

            # Train Human Proxy (at end of episode)
            # The agent typically updates from buffer. We can loop updates or just call update() once?
            # User said: "train during simulation, at the end of each episode".
            # Standard DQN update samples a batch. To learn effectively, we might want multiple updates?
            # Or just one update per episode step?
            # I'll call update() a few times or proportional to length?
            # Let's just call update() once per episode for now, or match steps?
            # Recommenders updated 20 times. Let's update Human Proxy 20 times?
            # Or just once. I'll stick to 1 update call per episode to match "at the end".
            # Actually, standard DQN usually trains every step. If we only train at end, we should probably loop.
            # I will loop `steps_per_episode` times to give it equivalent gradient steps.
            for _ in range(self.steps_per_episode):
                self.human_proxy.update()

            # Update Target Networks
            for agent in self.recommenders:
                agent.update_target_network()
            self.human_proxy.update_target_network()

            # Save History
            self._save_episode_history(self.env.episode_history, self.human_proxy_history)

            # Compute and Store Metrics
            metrics = compute_advanced_policy_metrics(self.recommenders)
            self.metrics_history.append(metrics)

            # Compute Human Rewards
            # history is list of (obs, choice, reward, next_obs, done)
            rewards = [step[2] for step in self.human_proxy_history]
            avg_reward = np.mean(rewards) if rewards else 0.0
            self.human_reward_history.append(avg_reward)

            if (episode + 1) % 10 == 0:
                print(f"Episode {episode+1}/{self.num_episodes} completed.")

        return {
            "metrics": self.metrics_history,
            "human_rewards": self.human_reward_history
        }

if __name__ == "__main__":
    sim = ProxySimulation(num_episodes=5, output_dir="data")
    sim.run()
