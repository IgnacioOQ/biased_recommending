import numpy as np
from src.simulation import GameSession
from src.advanced_environment import AdvancedBanditEnvironment
from src.advanced_agents import AdvancedRecommenderAgent
from src.logging import DataLogger
from src.advanced_analysis import compute_advanced_policy_metrics

class AdvancedGameSession(GameSession):
    def __init__(self, num_episodes=1000, output_dir="data", steps_per_episode=20):
        super().__init__(num_episodes, output_dir, steps_per_episode)
        # Override environment with AdvancedBanditEnvironment
        self.env = AdvancedBanditEnvironment(max_steps=steps_per_episode)
        # Override agents with AdvancedRecommenderAgent
        self.agents = [AdvancedRecommenderAgent(agent_id=0), AdvancedRecommenderAgent(agent_id=1)]
        # Re-initialize logger to match the session parameters (optional, but good for safety)
        self.logger = DataLogger(output_dir=output_dir, max_steps=steps_per_episode)

    def start_game(self):
        """Starts a new game session using advanced logic."""
        # env.reset() now returns [p, t]
        self.current_state = self.env.reset()
        self.is_active = True
        self.episode_count = 0
        return self.get_agent_recommendations()

    def get_agent_recommendations(self):
        """Gets recommendations from agents for the current state (which is [p, t])."""
        self.current_recommendations = []
        for agent in self.agents:
            # State is already a numpy array [p, t], but select_action expects shape (1, input_dim) usually?
            # RecommenderAgent.select_action does: state = torch.FloatTensor(state).unsqueeze(0)
            # If self.current_state is shape (2,), unsqueeze(0) makes it (1, 2), which matches input_dim=2.
            action = agent.select_action(self.current_state)
            self.current_recommendations.append(action)
        return self.current_recommendations

    def process_step(self, human_choice_idx):
        """
        Processes the step with advanced observation and storage logic.
        """
        if not self.is_active:
            raise ValueError("Game is not active. Call start_game() first.")

        # Capture pre-step state (Observation at t)
        current_observation = self.current_state
        # For logging, we might want just p? The logger expects 'p'.
        # current_observation is [p, t].
        current_p = current_observation[0]

        # 1. Step Environment
        # The advanced env returns next_observation instead of next_p
        human_reward, agent_rewards, outcome_str, done, next_observation = self.env.step(human_choice_idx, self.current_recommendations)

        # Log Step
        self.logger.log_step(
            episode=self.episode_count,
            step=self.env.steps, # This is t+1 (1-based)
            p=current_p,
            recommendations=self.current_recommendations,
            human_choice=human_choice_idx,
            human_reward=human_reward,
            agent_rewards=agent_rewards,
            outcome=outcome_str
        )

        # 2. Store Transitions and Train Agents
        for i, agent in enumerate(self.agents):
            # Store in Environment History (The requirement: "stores all the cuadruples")
            # Quintuple: (State, Action, Reward, Next_State, Done)
            self.env.store_transition(
                agent_id=i,
                state=current_observation,
                action=self.current_recommendations[i],
                reward=agent_rewards[i],
                next_state=next_observation,
                done=done
            )

            # Update Agent's Internal Memory and Train
            agent.store_transition(
                current_observation,
                self.current_recommendations[i],
                agent_rewards[i],
                next_observation,
                done
            )
            agent.update()

        # 3. Update State
        self.current_state = next_observation

        # 4. Handle Episode End
        new_episode_started = False
        metrics = None
        if done:
            self.logger.save_episode()
            metrics = compute_advanced_policy_metrics(self.agents)
            self.episode_count += 1
            for agent in self.agents:
                agent.update_target_network()

            # Reset Env
            self.current_state = self.env.reset()
            new_episode_started = True

        # 5. Get New Recommendations
        next_recommendations = self.get_agent_recommendations()

        return {
            "human_reward": human_reward,
            "agent_rewards": agent_rewards,
            "outcome": outcome_str,
            "done": done,
            "next_p": self.current_state[0], # Return p for UI/Compatibility
            "recommendations": next_recommendations,
            "new_episode": new_episode_started,
            "episode_count": self.episode_count,
            "metrics": metrics
        }
