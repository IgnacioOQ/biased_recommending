"""
API module for the simulation engine.

Provides REST endpoints for managing simulation sessions.
"""

from backend.api.main import app
from backend.api.session import SessionStore

__all__ = ["app", "SessionStore"]
