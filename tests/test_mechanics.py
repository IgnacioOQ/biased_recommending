import unittest
import numpy as np
from src.environment import BanditEnvironment
from src.agents import RecommenderAgent, ReplayBuffer
from src.simulation import GameSession

class TestMechanics(unittest.TestCase):

    def test_environment_mechanics(self):
        env = BanditEnvironment()
        p = env.reset()
        self.assertTrue(0 <= p <= 1)

        # Test Payoff Logic
        # Case 1: Heads (let's force it if possible, or mock, but let's trust statistics or logic for now)
        # We can't easily force random outcomes without seeding or mocking.
        # Let's test the logic by mocking p to 0 (Tails certain) or 1 (Heads certain)

        # Force Heads
        env.p = 1.0
        rec = [1, 0] # Agent 0 recommends, Agent 1 doesn't
        # Human chooses Agent 0 (Rec) -> Should match Heads -> Reward 1
        h_reward, a_rewards, outcome, done, next_p = env.step(0, rec)
        self.assertEqual(outcome, 'Heads')
        self.assertEqual(h_reward, 1)
        self.assertEqual(a_rewards, [1, -1]) # Agent 0 selected

        # Force Tails
        env.p = 0.0
        rec = [1, 0]
        # Human chooses Agent 0 (Rec) -> Mismatch Tails -> Reward 0
        h_reward, a_rewards, outcome, done, next_p = env.step(0, rec)
        self.assertEqual(outcome, 'Tails')
        self.assertEqual(h_reward, 0)
        self.assertEqual(a_rewards, [1, -1])

        # Human chooses Agent 1 (Not Rec) -> Match Tails -> Reward 1
        env.p = 0.0
        h_reward, a_rewards, outcome, done, next_p = env.step(1, rec)
        self.assertEqual(outcome, 'Tails')
        self.assertEqual(h_reward, 1)
        self.assertEqual(a_rewards, [-1, 1])

    def test_agent_mechanics(self):
        agent = RecommenderAgent(agent_id=0)
        state = [0.5]
        action = agent.select_action(state)
        self.assertIn(action, [0, 1])

        # Test Buffer
        agent.store_transition(state, action, 1, [0.6], False)
        self.assertEqual(len(agent.memory), 1)

        # Test Update (needs batch size, so push more)
        for _ in range(agent.batch_size + 1):
             agent.store_transition(state, action, 1, [0.6], False)

        try:
            agent.update()
        except Exception as e:
            self.fail(f"Agent update failed with error: {e}")

    def test_simulation_flow(self):
        game = GameSession()
        initial_recs = game.start_game()
        self.assertEqual(len(initial_recs), 2)

        # Step
        info = game.process_step(human_choice_idx=0)
        self.assertIn('human_reward', info)
        self.assertIn('recommendations', info)
        self.assertEqual(len(info['recommendations']), 2)

if __name__ == '__main__':
    unittest.main()
