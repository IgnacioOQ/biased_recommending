"""
Tests for the API module.
"""

import unittest

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.session import session_store


class TestAPI(unittest.TestCase):
    """Tests for the FastAPI endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        cls.client = TestClient(app)

    def setUp(self):
        """Clear session store before each test."""
        session_store.clear()

    def test_health_check(self):
        """Test health endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_create_simulation_default_config(self):
        """Test creating simulation with default config."""
        response = self.client.post("/api/simulation")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("session_id", data)
        self.assertEqual(data["message"], "Session created successfully")

    def test_create_simulation_custom_config(self):
        """Test creating simulation with custom config."""
        config = {"alpha": 0.01, "beta": 0.95, "steps_per_episode": 10}
        response = self.client.post("/api/simulation", json=config)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("session_id", data)

    def test_get_state(self):
        """Test getting simulation state."""
        # Create session
        create_resp = self.client.post("/api/simulation")
        session_id = create_resp.json()["session_id"]

        # Get state
        response = self.client.get(f"/api/simulation/{session_id}/state")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("episode_count", data)
        self.assertIn("step_count", data)
        self.assertIn("agent_beliefs", data)

    def test_get_state_not_found(self):
        """Test 404 when session not found."""
        response = self.client.get("/api/simulation/nonexistent-id/state")
        self.assertEqual(response.status_code, 404)

    def test_run_step(self):
        """Test running a step."""
        # Create session
        create_resp = self.client.post("/api/simulation")
        session_id = create_resp.json()["session_id"]

        # Run step
        response = self.client.post(
            f"/api/simulation/{session_id}/step", json={"human_choice_idx": 0}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["steps_executed"], 1)
        self.assertIn("final_result", data)
        self.assertIn("human_reward", data["final_result"])

    def test_run_multiple_steps(self):
        """Test running multiple steps."""
        # Create session
        create_resp = self.client.post("/api/simulation")
        session_id = create_resp.json()["session_id"]

        # Run 5 steps
        response = self.client.post(
            f"/api/simulation/{session_id}/step?steps=5", json={"human_choice_idx": 1}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["steps_executed"], 5)

    def test_run_step_not_found(self):
        """Test 404 when step on nonexistent session."""
        response = self.client.post(
            "/api/simulation/nonexistent-id/step", json={"human_choice_idx": 0}
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_simulation(self):
        """Test deleting a simulation."""
        # Create session
        create_resp = self.client.post("/api/simulation")
        session_id = create_resp.json()["session_id"]

        # Delete
        response = self.client.delete(f"/api/simulation/{session_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Session deleted successfully")

        # Verify deleted
        get_resp = self.client.get(f"/api/simulation/{session_id}/state")
        self.assertEqual(get_resp.status_code, 404)

    def test_delete_not_found(self):
        """Test 404 when deleting nonexistent session."""
        response = self.client.delete("/api/simulation/nonexistent-id")
        self.assertEqual(response.status_code, 404)

    def test_full_workflow(self):
        """Test complete create->step->state->delete workflow."""
        # Create
        create_resp = self.client.post(
            "/api/simulation", json={"steps_per_episode": 5}
        )
        session_id = create_resp.json()["session_id"]

        # Run steps until episode ends
        for _ in range(5):
            step_resp = self.client.post(
                f"/api/simulation/{session_id}/step", json={"human_choice_idx": 0}
            )
            self.assertEqual(step_resp.status_code, 200)

        # Check state
        state_resp = self.client.get(f"/api/simulation/{session_id}/state")
        data = state_resp.json()
        self.assertEqual(data["step_count"], 5)
        self.assertEqual(data["episode_count"], 1)

        # Delete
        del_resp = self.client.delete(f"/api/simulation/{session_id}")
        self.assertEqual(del_resp.status_code, 200)


class TestSessionStore(unittest.TestCase):
    """Tests for the SessionStore singleton."""

    def setUp(self):
        """Clear store before each test."""
        session_store.clear()

    def test_singleton(self):
        """Test that SessionStore is a singleton."""
        from src.api.session import SessionStore

        store1 = SessionStore()
        store2 = SessionStore()
        self.assertIs(store1, store2)

    def test_create_and_get(self):
        """Test creating and retrieving a session."""
        from src.engine import RecommenderSystem, SimulationConfig

        system = RecommenderSystem(SimulationConfig())
        session_id = session_store.create(system)

        retrieved = session_store.get(session_id)
        self.assertIs(retrieved, system)

    def test_get_nonexistent(self):
        """Test getting nonexistent session returns None."""
        result = session_store.get("nonexistent")
        self.assertIsNone(result)

    def test_delete(self):
        """Test deleting a session."""
        from src.engine import RecommenderSystem, SimulationConfig

        system = RecommenderSystem(SimulationConfig())
        session_id = session_store.create(system)

        deleted = session_store.delete(session_id)
        self.assertTrue(deleted)
        self.assertIsNone(session_store.get(session_id))

    def test_delete_nonexistent(self):
        """Test deleting nonexistent session returns False."""
        deleted = session_store.delete("nonexistent")
        self.assertFalse(deleted)

    def test_list_sessions(self):
        """Test listing session IDs."""
        from src.engine import RecommenderSystem, SimulationConfig

        sys1 = RecommenderSystem(SimulationConfig())
        sys2 = RecommenderSystem(SimulationConfig())

        id1 = session_store.create(sys1)
        id2 = session_store.create(sys2)

        sessions = session_store.list_sessions()
        self.assertIn(id1, sessions)
        self.assertIn(id2, sessions)
        self.assertEqual(len(sessions), 2)


if __name__ == "__main__":
    unittest.main()
