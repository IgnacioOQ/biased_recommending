"""
Tests for the engine module.
"""

import unittest

import numpy as np

from src.engine.config import SimulationConfig
from src.engine.model import RecommenderSystem
from src.engine.state import AgentAccuracy, AgentBelief, SimulationState


class TestSimulationConfig(unittest.TestCase):
    """Tests for SimulationConfig Pydantic model."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = SimulationConfig()

        self.assertEqual(config.alpha, 1e-3)
        self.assertEqual(config.beta, 0.99)
        self.assertEqual(config.epsilon, 1.0)
        self.assertEqual(config.num_agents, 2)
        self.assertEqual(config.input_dim, 2)
        self.assertEqual(config.steps_per_episode, 20)

    def test_custom_values(self):
        """Test that custom values are accepted."""
        config = SimulationConfig(
            alpha=0.01, beta=0.95, num_agents=3, steps_per_episode=10
        )

        self.assertEqual(config.alpha, 0.01)
        self.assertEqual(config.beta, 0.95)
        self.assertEqual(config.num_agents, 3)
        self.assertEqual(config.steps_per_episode, 10)

    def test_validation_constraints(self):
        """Test that validation constraints are enforced."""
        # beta (discount) must be <= 1.0
        with self.assertRaises(ValueError):
            SimulationConfig(beta=1.5)

        # num_agents must be >= 1
        with self.assertRaises(ValueError):
            SimulationConfig(num_agents=0)


class TestSimulationState(unittest.TestCase):
    """Tests for SimulationState Pydantic model."""

    def test_default_state(self):
        """Test default state values."""
        state = SimulationState()

        self.assertEqual(state.episode_count, 0)
        self.assertEqual(state.step_count, 0)
        self.assertEqual(state.agent_beliefs, [])
        self.assertEqual(state.cumulative_human_reward, 0.0)

    def test_state_with_values(self):
        """Test state with populated values."""
        beliefs = [
            AgentBelief(agent_id=0, epsilon=0.5, q_values_sample=[1.0, 2.0]),
            AgentBelief(agent_id=1, epsilon=0.3, q_values_sample=[0.5, 1.5]),
        ]
        accuracy = {
            0: AgentAccuracy(tpr=0.8, tnr=0.7, tp=8, rec_count=10, tn=7, not_rec_count=10)
        }

        state = SimulationState(
            episode_count=5,
            step_count=100,
            agent_beliefs=beliefs,
            recommendation_counts={0: 50, 1: 50},
            selection_counts={0: 60, 1: 40},
            cumulative_human_reward=75.0,
            agent_accuracy=accuracy,
        )

        self.assertEqual(state.episode_count, 5)
        self.assertEqual(state.step_count, 100)
        self.assertEqual(len(state.agent_beliefs), 2)
        self.assertEqual(state.cumulative_human_reward, 75.0)

    def test_state_serialization(self):
        """Test that state can be serialized to dict/JSON."""
        state = SimulationState(
            episode_count=1, step_count=20, cumulative_human_reward=10.0
        )

        state_dict = state.model_dump()

        self.assertIsInstance(state_dict, dict)
        self.assertEqual(state_dict["episode_count"], 1)
        self.assertEqual(state_dict["step_count"], 20)


class TestRecommenderSystem(unittest.TestCase):
    """Tests for RecommenderSystem model."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SimulationConfig(steps_per_episode=5)
        self.system = RecommenderSystem(self.config)

    def test_initialization(self):
        """Test that system initializes correctly."""
        self.assertEqual(len(self.system.agents), 2)
        self.assertEqual(self.system.episode_count, 0)
        self.assertEqual(self.system.step_count, 0)
        self.assertFalse(self.system.is_active)

    def test_reset(self):
        """Test reset activates the system."""
        recommendations = self.system.reset()

        self.assertTrue(self.system.is_active)
        self.assertIsNotNone(self.system.current_state)
        self.assertEqual(len(recommendations), 2)
        for r in recommendations:
            self.assertIn(r, [0, 1])

    def test_step_advances_state(self):
        """Test that step advances the simulation."""
        self.system.reset()
        initial_step_count = self.system.step_count

        result = self.system.step(human_choice_idx=0)

        self.assertEqual(self.system.step_count, initial_step_count + 1)
        self.assertIn("human_reward", result)
        self.assertIn("outcome", result)
        self.assertIn("done", result)
        self.assertIn("recommendations", result)

    def test_step_without_reset_raises(self):
        """Test that step without reset raises error."""
        with self.assertRaises(ValueError):
            self.system.step(human_choice_idx=0)

    def test_full_episode(self):
        """Test running a full episode."""
        self.system.reset()

        done = False
        steps = 0
        while not done:
            result = self.system.step(human_choice_idx=0)
            done = result["done"]
            steps += 1

        self.assertEqual(steps, 5)  # steps_per_episode = 5
        self.assertEqual(self.system.episode_count, 1)
        self.assertTrue(result["new_episode"])
        self.assertIsNotNone(result["finished_episode_history"])

    def test_get_metrics_returns_valid_state(self):
        """Test that get_metrics returns valid SimulationState."""
        self.system.reset()
        self.system.step(human_choice_idx=0)
        self.system.step(human_choice_idx=1)

        metrics = self.system.get_metrics()

        self.assertIsInstance(metrics, SimulationState)
        self.assertEqual(metrics.step_count, 2)
        self.assertEqual(len(metrics.agent_beliefs), 2)
        self.assertIn(0, metrics.agent_accuracy)
        self.assertIn(1, metrics.agent_accuracy)

    def test_selection_counts_tracked(self):
        """Test that selection counts are tracked correctly."""
        self.system.reset()
        self.system.step(human_choice_idx=0)
        self.system.step(human_choice_idx=0)
        self.system.step(human_choice_idx=1)

        self.assertEqual(self.system.selection_counts[0], 2)
        self.assertEqual(self.system.selection_counts[1], 1)


class TestNoMatplotlibInEngine(unittest.TestCase):
    """Test that engine module has no matplotlib dependencies."""

    def test_no_matplotlib_import_in_model(self):
        """Verify model.py doesn't import matplotlib."""
        import inspect

        from src.engine import model

        source = inspect.getsource(model)
        # Check for actual imports, not documentation mentions
        self.assertNotIn("import matplotlib", source)
        self.assertNotIn("from matplotlib", source)

    def test_no_matplotlib_import_in_config(self):
        """Verify config.py doesn't import matplotlib."""
        import inspect

        from src.engine import config

        source = inspect.getsource(config)
        self.assertNotIn("import matplotlib", source)
        self.assertNotIn("from matplotlib", source)

    def test_no_matplotlib_import_in_state(self):
        """Verify state.py doesn't import matplotlib."""
        import inspect

        from src.engine import state

        source = inspect.getsource(state)
        self.assertNotIn("import matplotlib", source)
        self.assertNotIn("from matplotlib", source)


if __name__ == "__main__":
    unittest.main()
