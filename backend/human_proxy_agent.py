from backend.agents import RecommenderAgent

class HumanProxyAgent(RecommenderAgent):
    def __init__(self, agent_id="human_proxy", input_dim=3, action_dim=2, lr=1e-3, gamma=0.99, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01, buffer_capacity=10000, batch_size=64):
        """
        Initializes the HumanProxyAgent.
        Input vector: [recommendation_1, recommendation_2, time_step]
        Action space: Choose Agent 0 or Agent 1.
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
