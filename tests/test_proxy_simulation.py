import unittest
import os
import shutil
import numpy as np
from src.proxy_simulation import ProxySimulation

class TestProxySimulation(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_proxy_data"
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_run_simulation(self):
        """Test that the proxy simulation runs for a few episodes without error and saves data."""
        sim = ProxySimulation(num_episodes=2, output_dir=self.output_dir, steps_per_episode=5)
        sim.run()

        # Check if files created
        files = os.listdir(self.output_dir)
        json_files = [f for f in files if f.endswith('.json')]
        self.assertTrue(len(json_files) >= 1) # Should have history file + session log file

        # Check history file content
        history_file = [f for f in json_files if "proxy_simulation_history" in f][0]
        import json
        with open(os.path.join(self.output_dir, history_file), 'r') as f:
            data = json.load(f)

        self.assertIn("episodes", data)
        self.assertEqual(len(data["episodes"]), 2)

        # Check structure
        ep0 = data["episodes"][0]
        self.assertIn("recommenders", ep0)
        self.assertIn("human_proxy", ep0)
        self.assertEqual(len(ep0["human_proxy"]), 5) # 5 steps

        # Check Human Input Dimensions [r1, r2, t]
        # JSON loads as list
        first_obs = ep0["human_proxy"][0][0]
        self.assertEqual(len(first_obs), 3)

if __name__ == '__main__':
    unittest.main()
