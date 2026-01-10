import unittest
import numpy as np
from src.advanced_environment import AdvancedBanditEnvironment
from src.advanced_agents import AdvancedRecommenderAgent
from src.advanced_simulation import AdvancedGameSession

class TestAdvancedMechanics(unittest.TestCase):
    def setUp(self):
        self.env = AdvancedBanditEnvironment(max_steps=5)
        self.agent = AdvancedRecommenderAgent(agent_id=0, input_dim=2)
        self.session = AdvancedGameSession(num_episodes=2, steps_per_episode=5)

    def test_environment_initialization(self):
        """Test that the environment initializes with correct history structure."""
        self.assertEqual(self.env.episode_history, {0: [], 1: []})
        obs = self.env.reset()
        self.assertEqual(obs.shape, (2,))
        self.assertEqual(obs[1], 0) # Initial time step is 0

    def test_observation_construction(self):
        """Test that construct_observation returns [p, t]."""
        p = 0.5
        t = 10
        obs = self.env.construct_observation(p, t)
        self.assertTrue(np.array_equal(obs, np.array([0.5, 10], dtype=np.float32)))

    def test_step_and_storage(self):
        """Test stepping the environment and manually storing transitions."""
        obs = self.env.reset()
        next_obs = self.env.construct_observation(0.8, 1)

        self.env.store_transition(0, obs, 1, 1.0, next_obs, False)

        history = self.env.episode_history[0]
        self.assertEqual(len(history), 1)
        state, action, reward, n_state, done = history[0]

        self.assertTrue(np.array_equal(state, obs))
        self.assertEqual(action, 1)
        self.assertEqual(reward, 1.0)
        self.assertTrue(np.array_equal(n_state, next_obs))
        self.assertFalse(done)

    def test_agent_input_dimension(self):
        """Test that the agent accepts the new input dimension."""
        state = np.array([0.5, 0], dtype=np.float32)
        action = self.agent.select_action(state)
        self.assertIn(action, [0, 1])

    def test_simulation_loop(self):
        """Test the full simulation loop for a few steps."""
        self.session.start_game()

        # Step 1
        result = self.session.process_step(human_choice_idx=0)
        self.assertFalse(result['done'])

        # Verify environment history in the session
        self.assertEqual(len(self.session.env.episode_history[0]), 1)
        self.assertEqual(len(self.session.env.episode_history[1]), 1)

        # Verify transition content
        transition = self.session.env.episode_history[0][0]
        # State should be [p, 0]
        self.assertEqual(transition[0][1], 0)
        # Next State should be [new_p, 1]
        self.assertEqual(transition[3][1], 1)

if __name__ == '__main__':
    unittest.main()
