"""
Engine module for recommender system simulation.

Provides a modular, computation-only architecture for running simulations
without UI or plotting dependencies.
"""

from backend.engine.config import SimulationConfig
from backend.engine.state import SimulationState, AgentBelief
from backend.engine.model import RecommenderSystem

__all__ = [
    "SimulationConfig",
    "SimulationState",
    "AgentBelief",
    "RecommenderSystem",
]
