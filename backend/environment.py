import numpy as np

class BanditEnvironment:
    def __init__(self, max_steps=20):
        self.p = None
        self.steps = 0
        self.max_steps = max_steps

    def reset(self):
        self.steps = 0
        self.p = self.get_p()
        return self.p

    def get_p(self):
        """Generates a new probability p uniform in [0, 1]."""
        return np.random.uniform(0, 1)

    def step(self, human_choice_idx, agent_recommendations):
        """
        Executes a step in the environment.

        Args:
            human_choice_idx (int): The index of the agent selected by the human (0 or 1).
            agent_recommendations (list): List of recommendations from agents [rec_0, rec_1].
                                          1 = Recommend, 0 = Not Recommend.

        Returns:
            human_reward (int): Payoff for the human.
            agent_rewards (list): Payoff for the agents [+1 if selected, -1 otherwise].
            outcome (str): 'Heads' or 'Tails'.
            done (bool): Whether the episode is finished.
        """
        self.steps += 1

        # 1. Nature draws coin outcome based on p
        # Note: p is generated at the start of the step logic (effectively)
        # but in this flow, p was generated for the *current* observation.
        # Now we realize the outcome based on that p.
        is_heads = np.random.random() < self.p
        outcome_str = 'Heads' if is_heads else 'Tails'

        # 2. Determine Human Payoff
        # Logic:
        # Heads + Recommend (+1)
        # Tails + Not Recommend (+1)
        # Else 0

        selected_recommendation = agent_recommendations[human_choice_idx]

        human_reward = 0
        if is_heads and selected_recommendation == 1:
            human_reward = 1
        elif not is_heads and selected_recommendation == 0:
            human_reward = 1
        else:
            human_reward = 0

        # 3. Determine Agent Payoff
        # +1 if selected, -1 if not
        agent_rewards = []
        for i in range(len(agent_recommendations)):
            if i == human_choice_idx:
                agent_rewards.append(1)
            else:
                agent_rewards.append(-1)

        # 4. Check if done
        done = self.steps >= self.max_steps

        # 5. Generate new p for next step (if not done, or even if done, just to update state)
        if not done:
            self.p = self.get_p()

        return human_reward, agent_rewards, outcome_str, done, self.p
