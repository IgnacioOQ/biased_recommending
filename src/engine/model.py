"""
RecommenderSystem class - the core simulation model.

Extracted from advanced_experiment_interface.ipynb/AdvancedGameSession.
Contains only computation logic, no plotting/matplotlib.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import torch

from src.advanced_agents import AdvancedRecommenderAgent
from src.advanced_environment import AdvancedBanditEnvironment
from src.engine.config import SimulationConfig
from src.engine.state import AgentAccuracy, AgentBelief, SimulationState


class RecommenderSystem:
    """
    Core simulation model for the recommender system experiment.

    Manages the environment and agents, providing step-by-step simulation
    with state tracking. No plotting/UI code - pure computation only.
    """

    def __init__(self, config: SimulationConfig):
        """
        Initialize using SimulationConfig.

        Args:
            config: SimulationConfig with all hyperparameters.
        """
        self.config = config

        # Initialize environment
        self.env = AdvancedBanditEnvironment(max_steps=config.steps_per_episode)

        # Initialize agents
        self.agents: List[AdvancedRecommenderAgent] = [
            AdvancedRecommenderAgent(
                agent_id=i,
                input_dim=config.input_dim,
                action_dim=config.action_dim,
                lr=config.alpha,
                gamma=config.beta,
                epsilon=config.epsilon,
                epsilon_decay=config.epsilon_decay,
                epsilon_min=config.epsilon_min,
                buffer_capacity=config.buffer_capacity,
                batch_size=config.batch_size,
            )
            for i in range(config.num_agents)
        ]

        # State tracking
        self.episode_count: int = 0
        self.step_count: int = 0
        self.current_state: Optional[np.ndarray] = None
        self.current_recommendations: List[int] = []
        self.is_active: bool = False

        # Popularity/selection tracking
        self.recommendation_counts: Dict[int, int] = {
            i: 0 for i in range(config.num_agents)
        }
        self.selection_counts: Dict[int, int] = {i: 0 for i in range(config.num_agents)}

        # Reward tracking
        self.cumulative_human_reward: float = 0.0

        # Accuracy tracking (TPR/TNR per agent)
        self.agent_stats: Dict[int, Dict[str, int]] = {
            i: {"tp": 0, "rec_count": 0, "tn": 0, "not_rec_count": 0}
            for i in range(config.num_agents)
        }

    def reset(self) -> List[int]:
        """
        Reset for new episode/session.

        Returns:
            List of initial agent recommendations.
        """
        self.current_state = self.env.reset()
        self.is_active = True
        return self._get_recommendations()

    def _get_recommendations(self) -> List[int]:
        """
        Get recommendations from all agents for current state.

        Returns:
            List of actions (0 or 1) from each agent.
        """
        self.current_recommendations = []
        for agent in self.agents:
            action = agent.select_action(self.current_state)
            self.current_recommendations.append(action)
        return self.current_recommendations

    def step(self, human_choice_idx: int) -> Dict[str, Any]:
        """
        Advance the simulation by one tick.

        Args:
            human_choice_idx: Index of the agent selected by the human (0 or 1).

        Returns:
            Dict with step results (no plotting, just data):
                - human_reward: int payoff for human
                - agent_rewards: list of agent payoffs
                - outcome: 'Heads' or 'Tails'
                - done: bool if episode finished
                - next_p: float probability for next step
                - recommendations: list of next step recommendations
                - new_episode: bool if new episode started
                - episode_count: current episode number
                - finished_episode_history: episode history if done, else None
        """
        if not self.is_active:
            raise ValueError("Simulation is not active. Call reset() first.")

        # Capture pre-step state
        current_observation = self.current_state
        current_p = current_observation[0]

        # Step environment
        human_reward, agent_rewards, outcome_str, done, next_observation = (
            self.env.step(human_choice_idx, self.current_recommendations)
        )

        # Update tracking
        self.step_count += 1
        self.cumulative_human_reward += human_reward
        self.selection_counts[human_choice_idx] += 1

        # Update recommendation counts and accuracy stats
        outcome_is_success = outcome_str == "Heads"
        for aid in range(self.config.num_agents):
            action = self.current_recommendations[aid]
            if action == 1:  # Recommend
                self.recommendation_counts[aid] += 1
                self.agent_stats[aid]["rec_count"] += 1
                if outcome_is_success:
                    self.agent_stats[aid]["tp"] += 1
            else:  # Not Recommend
                self.agent_stats[aid]["not_rec_count"] += 1
                if not outcome_is_success:  # Tails = success for not-recommend
                    self.agent_stats[aid]["tn"] += 1

        # Store transitions and train agents
        for i, agent in enumerate(self.agents):
            # Store in environment history
            self.env.store_transition(
                agent_id=i,
                state=current_observation,
                action=self.current_recommendations[i],
                reward=agent_rewards[i],
                next_state=next_observation,
                done=done,
            )

            # Update agent's internal memory and train
            agent.store_transition(
                current_observation,
                self.current_recommendations[i],
                agent_rewards[i],
                next_observation,
                done,
            )
            agent.update()

        # Update state
        self.current_state = next_observation

        # Handle episode end
        new_episode_started = False
        finished_episode_history = None

        if done:
            # Capture history before reset
            finished_episode_history = self.env.episode_history

            self.episode_count += 1
            for agent in self.agents:
                agent.update_target_network()

            # Reset environment
            self.current_state = self.env.reset()
            new_episode_started = True

        # Get new recommendations
        next_recommendations = self._get_recommendations()

        return {
            "human_reward": human_reward,
            "agent_rewards": agent_rewards,
            "outcome": outcome_str,
            "done": done,
            "next_p": self.current_state[0],
            "recommendations": next_recommendations,
            "new_episode": new_episode_started,
            "episode_count": self.episode_count,
            "finished_episode_history": finished_episode_history,
        }

    def get_metrics(self) -> SimulationState:
        """
        Returns current SimulationState snapshot.

        Returns:
            SimulationState with current agent beliefs, popularity, and metrics.
        """
        # Build agent beliefs
        agent_beliefs = []
        for agent in self.agents:
            # Sample Q-values at a few representative states
            sample_states = [
                np.array([0.25, 0], dtype=np.float32),  # Low p, start
                np.array([0.50, 10], dtype=np.float32),  # Mid p, mid episode
                np.array([0.75, 0], dtype=np.float32),  # High p, start
            ]
            q_values_sample = []
            with torch.no_grad():
                for state in sample_states:
                    state_tensor = (
                        torch.FloatTensor(state).unsqueeze(0).to(agent.device)
                    )
                    q_vals = agent.policy_net(state_tensor)
                    q_values_sample.extend(q_vals.cpu().numpy().flatten().tolist())

            agent_beliefs.append(
                AgentBelief(
                    agent_id=agent.agent_id,
                    epsilon=agent.epsilon,
                    q_values_sample=q_values_sample,
                )
            )

        # Build accuracy metrics
        agent_accuracy = {}
        for aid, stats in self.agent_stats.items():
            tpr = stats["tp"] / stats["rec_count"] if stats["rec_count"] > 0 else 0.0
            tnr = (
                stats["tn"] / stats["not_rec_count"]
                if stats["not_rec_count"] > 0
                else 0.0
            )
            agent_accuracy[aid] = AgentAccuracy(
                tpr=tpr,
                tnr=tnr,
                tp=stats["tp"],
                rec_count=stats["rec_count"],
                tn=stats["tn"],
                not_rec_count=stats["not_rec_count"],
            )

        return SimulationState(
            episode_count=self.episode_count,
            step_count=self.step_count,
            agent_beliefs=agent_beliefs,
            recommendation_counts=dict(self.recommendation_counts),
            selection_counts=dict(self.selection_counts),
            cumulative_human_reward=self.cumulative_human_reward,
            agent_accuracy=agent_accuracy,
        )
