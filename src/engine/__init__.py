"""
Engine module for recommender system simulation.

Provides a modular, computation-only architecture for running simulations
without UI or plotting dependencies.
"""

from src.engine.config import SimulationConfig
from src.engine.state import SimulationState, AgentBelief
from src.engine.model import RecommenderSystem

__all__ = [
    "SimulationConfig",
    "SimulationState",
    "AgentBelief",
    "RecommenderSystem",
]
