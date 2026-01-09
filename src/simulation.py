from src.agents import RecommenderAgent
from src.environment import BanditEnvironment
from src.logging import DataLogger
from src.analysis import compute_policy_metrics
import numpy as np

class GameSession:
    def __init__(self, num_episodes=1000, output_dir="data", steps_per_episode=20):
        self.env = BanditEnvironment(max_steps=steps_per_episode)
        self.agents = [RecommenderAgent(agent_id=0), RecommenderAgent(agent_id=1)]
        self.current_state = None
        self.current_recommendations = []
        self.episode_count = 0
        self.total_episodes = num_episodes
        self.is_active = False
        self.logger = DataLogger(output_dir=output_dir, max_steps=steps_per_episode)

    def start_game(self):
        """Starts a new game session (resetting everything not persistent if needed, or just starting loop)."""
        self.current_state = self.env.reset()
        self.is_active = True
        self.episode_count = 0
        return self.get_agent_recommendations()

    def get_agent_recommendations(self):
        """Gets recommendations from agents for the current state."""
        self.current_recommendations = []
        for agent in self.agents:
            # State needs to be shape (1,) for the agent
            action = agent.select_action(np.array([self.current_state]))
            self.current_recommendations.append(action)
        return self.current_recommendations

    def process_step(self, human_choice_idx):
        """
        Processes the human's choice, steps the environment, and trains agents.

        Args:
            human_choice_idx (int): 0 or 1, indicating which agent was followed.

        Returns:
            info (dict): Dictionary containing rewards, outcome, and new recommendations.
        """
        if not self.is_active:
            raise ValueError("Game is not active. Call start_game() first.")

        # Capture pre-step state for logging
        current_p = self.current_state

        # 1. Step Environment
        human_reward, agent_rewards, outcome_str, done, next_p = self.env.step(human_choice_idx, self.current_recommendations)

        # Log Step
        self.logger.log_step(
            episode=self.episode_count,
            step=self.env.steps,
            p=current_p,
            recommendations=self.current_recommendations,
            human_choice=human_choice_idx,
            human_reward=human_reward,
            agent_rewards=agent_rewards,
            outcome=outcome_str
        )

        # 2. Train Agents
        for i, agent in enumerate(self.agents):
            agent.store_transition(
                np.array([self.current_state]),
                self.current_recommendations[i],
                agent_rewards[i],
                np.array([next_p]),
                done
            )
            agent.update()

        # 3. Update State
        self.current_state = next_p

        # 4. Handle Episode End
        new_episode_started = False
        metrics = None
        if done:
            # Save Data
            self.logger.save_episode()

            # Compute Analysis
            metrics = compute_policy_metrics(self.agents)

            self.episode_count += 1
            for agent in self.agents:
                agent.update_target_network()

            self.current_state = self.env.reset()
            new_episode_started = True

        # 5. Get New Recommendations (for next step)
        next_recommendations = self.get_agent_recommendations()

        return {
            "human_reward": human_reward,
            "agent_rewards": agent_rewards,
            "outcome": outcome_str,
            "done": done,
            "next_p": self.current_state,
            "recommendations": next_recommendations,
            "new_episode": new_episode_started,
            "episode_count": self.episode_count,
            "metrics": metrics
        }
