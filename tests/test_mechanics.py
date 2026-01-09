import unittest
import numpy as np
import os
import shutil
import json
from src.environment import BanditEnvironment
from src.agents import RecommenderAgent, ReplayBuffer
from src.simulation import GameSession
from src.logging import DataLogger
from src.analysis import compute_policy_metrics

class TestMechanics(unittest.TestCase):

    def test_environment_mechanics(self):
        env = BanditEnvironment()
        p = env.reset()
        self.assertTrue(0 <= p <= 1)

        # Payoff Logic Test
        env.p = 1.0
        rec = [1, 0]
        h_reward, a_rewards, outcome, done, next_p = env.step(0, rec)
        self.assertEqual(outcome, 'Heads')
        self.assertEqual(h_reward, 1)
        self.assertEqual(a_rewards, [1, -1]) # Agent 0 selected

    def test_agent_mechanics(self):
        agent = RecommenderAgent(agent_id=0)
        state = [0.5]
        action = agent.select_action(state)
        self.assertIn(action, [0, 1])

        agent.store_transition(state, action, 1, [0.6], False)
        self.assertEqual(len(agent.memory), 1)

    def test_simulation_flow_and_logging(self):
        test_dir = "test_data"
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

        game = GameSession(output_dir=test_dir)
        game.start_game()

        # Run one episode (20 steps)
        for _ in range(21): # +1 to trigger done
            info = game.process_step(human_choice_idx=0)
            if info['done']:
                break

        # Check if file created
        files = os.listdir(test_dir)
        self.assertTrue(len(files) > 0)
        self.assertTrue(files[0].endswith(".json"))

        # Check content
        with open(os.path.join(test_dir, files[0]), 'r') as f:
            data = json.load(f)
            self.assertIn("session_meta", data)
            self.assertIn("episodes", data)
            self.assertTrue(len(data["episodes"]) > 0)

            # Check first step of first episode
            first_step = data["episodes"][0][0]
            self.assertIn("session_id", first_step)
            self.assertIn("p", first_step)
            self.assertIn("outcome", first_step)

        # Cleanup
        shutil.rmtree(test_dir)

    def test_analysis_metrics(self):
        agents = [RecommenderAgent(agent_id=0)]
        metrics = compute_policy_metrics(agents)
        self.assertIn("agent_0", metrics)
        self.assertIn("disagreement_rate", metrics["agent_0"])

if __name__ == '__main__':
    unittest.main()
