import numpy as np
from src.environment import BanditEnvironment

class AdvancedBanditEnvironment(BanditEnvironment):
    def __init__(self, max_steps=20):
        super().__init__(max_steps=max_steps)
        self.episode_history = {0: [], 1: []}

    def reset(self):
        """Resets the environment and returns the initial observation."""
        super().reset()
        self.episode_history = {0: [], 1: []}
        return self.construct_observation(self.p, self.steps)

    def construct_observation(self, p, t):
        """Constructs an observation vector [p, t]."""
        return np.array([p, t], dtype=np.float32)

    def step(self, human_choice_idx, agent_recommendations):
        """
        Executes a step and returns the next observation.
        """
        # Capture the observation *before* the step logic increments time (conceptually)
        # However, the base class 'step' increments self.steps.
        # We need to return the *next* observation.

        human_reward, agent_rewards, outcome_str, done, next_p = super().step(human_choice_idx, agent_recommendations)

        # Construct the next observation
        # self.steps has already been incremented by super().step()
        next_observation = self.construct_observation(next_p, self.steps)

        return human_reward, agent_rewards, outcome_str, done, next_observation

    def store_transition(self, agent_id, state, action, reward, next_state, done):
        """Stores a transition quintuple for a specific agent."""
        if agent_id not in self.episode_history:
            self.episode_history[agent_id] = []

        self.episode_history[agent_id].append((state, action, reward, next_state, done))
