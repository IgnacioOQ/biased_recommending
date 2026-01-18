"""
API module for the simulation engine.

Provides REST endpoints for managing simulation sessions.
"""

from src.api.main import app
from src.api.session import SessionStore

__all__ = ["app", "SessionStore"]
