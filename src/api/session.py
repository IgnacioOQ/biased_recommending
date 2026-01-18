"""
Session management for simulation instances.

Provides a singleton SessionStore that holds active simulations in memory.
"""

import uuid
from typing import Dict, Optional

from src.engine import RecommenderSystem


class SessionStore:
    """
    Singleton store for active simulation sessions.

    Holds RecommenderSystem instances in memory, keyed by session ID.
    """

    _instance: Optional["SessionStore"] = None

    def __new__(cls) -> "SessionStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions: Dict[str, RecommenderSystem] = {}
        return cls._instance

    def create(self, system: RecommenderSystem) -> str:
        """
        Store a new simulation and return its session ID.

        Args:
            system: The RecommenderSystem instance to store.

        Returns:
            A unique session ID string.
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = system
        return session_id

    def get(self, session_id: str) -> Optional[RecommenderSystem]:
        """
        Retrieve a simulation by session ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The RecommenderSystem if found, None otherwise.
        """
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """
        Remove a simulation from the store.

        Args:
            session_id: The session ID to remove.

        Returns:
            True if the session was found and removed, False otherwise.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list:
        """Return list of active session IDs."""
        return list(self._sessions.keys())

    def clear(self) -> None:
        """Remove all sessions (useful for testing)."""
        self._sessions.clear()


# Global singleton instance
session_store = SessionStore()
