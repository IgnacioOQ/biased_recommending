import numpy as np
from src.agents import RecommenderAgent

class AdvancedRecommenderAgent(RecommenderAgent):
    def __init__(self, agent_id, input_dim=2, action_dim=2, lr=1e-3, gamma=0.99, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01, buffer_capacity=10000, batch_size=64):
        """
        Initializes the AdvancedRecommenderAgent with input_dim=2 (default) to handle [p, t] observations.
        """
        super().__init__(
            agent_id=agent_id,
            input_dim=input_dim,
            action_dim=action_dim,
            lr=lr,
            gamma=gamma,
            epsilon=epsilon,
            epsilon_decay=epsilon_decay,
            epsilon_min=epsilon_min,
            buffer_capacity=buffer_capacity,
            batch_size=batch_size
        )
