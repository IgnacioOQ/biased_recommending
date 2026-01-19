"""
RecommenderSystem class - the core simulation model.

Extracted from advanced_experiment_interface.ipynb/AdvancedGameSession.
Contains only computation logic, no plotting/matplotlib.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import torch
import json
import os
import time
import datetime

from backend.advanced_agents import AdvancedRecommenderAgent
from backend.advanced_environment import AdvancedBanditEnvironment
from backend.engine.config import SimulationConfig
from backend.engine.state import AgentAccuracy, AgentBelief, SimulationState


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
        self.cumulative_agent_rewards: List[float] = [0.0] * config.num_agents

        # Accuracy tracking (TPR/TNR per agent)
        # Accuracy tracking (TPR/TNR per agent)
        self.agent_stats: Dict[int, Dict[str, int]] = {
            i: {"tp": 0, "rec_count": 0, "tn": 0, "not_rec_count": 0}
            for i in range(config.num_agents)
        }

        # New Metric Tracking
        self.session_reward: int = 0
        self.episode_reward: int = 0
        self.agent_successes: List[int] = [0] * config.num_agents

        # Session and Logging
        self.session_id: Optional[str] = None
        self.participant_name: str = "Anonymous"
        self.current_episode_history: List[Dict] = []
        
    def set_session_id(self, session_id: str):
        """Set the session ID for data logging."""
        self.session_id = session_id

    def set_participant_name(self, name: str):
        """Set the participant name for data logging."""
        self.participant_name = name

    def reset(self) -> List[int]:
        """
        Reset for new episode/session.

        Returns:
            List of initial agent recommendations.
        """
        self.current_state = self.env.reset()
        self.is_active = True
        self.cumulative_agent_rewards = [0.0] * self.config.num_agents
        
        # Reset episode-specific metrics
        self.episode_reward = 0
        self.agent_successes = [0] * self.config.num_agents
        
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
        
        # Update metric trackers
        self.episode_reward += human_reward
        self.session_reward += human_reward

        # Update recommendation counts and accuracy stats
        # Also determine 'correctness' for UI display
        agent_correctness = []  # True if recommendation was 'good' (Rec=1 => Heads, Rec=0 => Tails)
        outcome_is_success = outcome_str == "Heads"
        
        for aid in range(self.config.num_agents):
            action = self.current_recommendations[aid]
            # Track cumulative reward
            self.cumulative_agent_rewards[aid] += agent_rewards[aid]
            
            is_correct = False
            if action == 1:  # Recommend
                self.recommendation_counts[aid] += 1
                self.agent_stats[aid]["rec_count"] += 1
                if outcome_is_success:
                    self.agent_stats[aid]["tp"] += 1
                    is_correct = True
            else:  # Not Recommend
                self.agent_stats[aid]["not_rec_count"] += 1
                if not outcome_is_success:  # Tails = success for not-recommend
                    self.agent_stats[aid]["tn"] += 1
                    is_correct = True
            agent_correctness.append(is_correct)

            # Track successes for this episode
            if is_correct:
                self.agent_successes[aid] += 1

        # -------------------------------------------------------
        # Behavioral Logging (Requested Tuple)
        # -------------------------------------------------------
        # Tuple: (t, p, rec1, rec2, choice, payoffs, outcome, human_payoff, t_next, done)
        step_record = {
            "t": int(current_observation[1]),
            "p": float(current_observation[0]),
            "rec_agent_0": int(self.current_recommendations[0]),
            "rec_agent_1": int(self.current_recommendations[1]),
            "human_choice": int(human_choice_idx),
            "agent_0_payoff": float(agent_rewards[0]),
            "agent_1_payoff": float(agent_rewards[1]),
            "outcome": outcome_str,
            "human_payoff": float(human_reward),
            "t_next": int(next_observation[1]),
            "done": bool(done)
        }
        self.current_episode_history.append(step_record)

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
            # Save detailed log for this episode
            self._save_episode_log()
            self.current_episode_history = []  # Reset for next episode
            # Capture history before reset
            finished_episode_history = self.env.episode_history

            self.episode_count += 1
            for agent in self.agents:
                agent.update_target_network()

            # Reset environment
            self.current_state = self.env.reset()
            self.cumulative_agent_rewards = [0.0] * self.config.num_agents
            
            # Reset episode metrics
            self.episode_reward = 0
            self.agent_successes = [0] * self.config.num_agents
            new_episode_started = True

        # Get new recommendations
        next_recommendations = self._get_recommendations()

        return {
            "human_reward": human_reward,
            "agent_rewards": agent_rewards,
            "cumulative_agent_rewards": self.cumulative_agent_rewards,
            "agent_correctness": agent_correctness,
            "human_choice": human_choice_idx,
            "outcome": outcome_str,
            "done": done,
            "next_p": self.current_state[0],
            "recommendations": next_recommendations,
            "new_episode": new_episode_started,
            "episode_count": self.episode_count,
            "finished_episode_history": finished_episode_history,
            
            # New Metrics for Step Result
            "episode_reward": self.episode_reward,
            "average_reward": self.session_reward / max(1, self.episode_count) if self.episode_count > 0 else 0.0,
            "agent_successes": self.agent_successes,
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
            
            # New Metrics
            episode_reward=self.episode_reward,
            average_reward=self.session_reward / max(1, self.episode_count) if self.episode_count > 0 else 0.0,
            agent_successes=self.agent_successes,
        )

    def _save_episode_log(self):
        """
        Saves/Updates session log with current episode history.
        
        Target file: data/sessions/{session_id}.json
        Structure:
        {
            "session_id": "...",
            "participant_name": "...",
            "config": {...},
            "episodes": {
                "0": [...],
                "1": [...]
            }
        }
        """
        if not self.session_id:
            print("Warning: No session_id set, cannot save behavioral log.")
            return

        # Ensure directory exists
        base_dir = os.path.join("data", "sessions")
        os.makedirs(base_dir, exist_ok=True)
        
        filepath = os.path.join(base_dir, f"{self.session_id}.json")
        
        # Load existing data or create new structure
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    session_data = json.load(f)
            except Exception as e:
                print(f"Error reading existing log: {e}. Creating new.")
                session_data = self._create_new_session_data()
        else:
            session_data = self._create_new_session_data()
            
        # Update with current episode
        episode_key = str(self.episode_count)
        session_data["episodes"][episode_key] = self.current_episode_history
        
        # Write back
        try:
            with open(filepath, "w") as f:
                json.dump(session_data, f, indent=2)
            print(f"Updated session log at {filepath}")
        except Exception as e:
            print(f"Error saving session log: {e}")

    def _create_new_session_data(self) -> Dict:
        """Helper to create initial session data structure."""
        return {
            "session_id": self.session_id,
            "participant_name": self.participant_name,
            "start_time": datetime.datetime.now().astimezone().isoformat(),
            "config": self.config.model_dump() if hasattr(self.config, "model_dump") else self.config.dict(),
            "episodes": {}
        }
