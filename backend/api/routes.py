"""
API routes for simulation management.
"""

from typing import Any, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.engine import RecommenderSystem, SimulationConfig, SimulationState
from backend.api.session import session_store


def _convert_numpy_types(obj: Any) -> Any:
    """Recursively convert numpy types to Python native types."""
    if isinstance(obj, dict):
        return {_convert_numpy_types(k): _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        converted = [_convert_numpy_types(item) for item in obj]
        return converted  # Return as list for JSON compatibility
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj


router = APIRouter(prefix="/api", tags=["simulation"])


class CreateSessionResponse(BaseModel):
    """Response model for session creation."""

    session_id: str
    message: str = "Session created successfully"


class InitResponse(BaseModel):
    """Response model for simulation init (REACT_ASSISTANT pattern)."""

    session_id: str
    state: dict


class StepRequest(BaseModel):
    """Request model for step endpoint."""

    human_choice_idx: int = 0


class StepResponse(BaseModel):
    """Response model for step endpoint."""

    steps_executed: int
    final_result: dict


class DeleteResponse(BaseModel):
    """Response model for session deletion."""

    message: str
    session_id: str


@router.post("/simulation/init", response_model=InitResponse)
def init_simulation(config: Optional[SimulationConfig] = None) -> InitResponse:
    """
    Initialize a new simulation session and return initial state.

    This follows the REACT_ASSISTANT.md pattern for frontend consumption.
    Returns session_id plus initial state with recommendations.

    Args:
        config: Optional SimulationConfig. Uses defaults if not provided.

    Returns:
        InitResponse with session_id and initial state.
    """
    if config is None:
        config = SimulationConfig()

    system = RecommenderSystem(config)
    recommendations = system.reset()  # Returns initial recommendations

    session_id = session_store.create(system)

    # Build initial state for frontend
    # The current_state is an observation array [p, t]
    initial_state = {
        "current_p": float(system.current_state[0]),  # p from observation
        "current_t": int(system.current_state[1]),    # t from observation
        "recommendations": [int(r) for r in recommendations],
        "episode": system.episode_count,
        "step": int(system.env.steps),
        "game_over": False,
        "cumulative_human_reward": 0.0,
    }

    return InitResponse(session_id=session_id, state=initial_state)


@router.post("/simulation", response_model=CreateSessionResponse)
def create_simulation(config: Optional[SimulationConfig] = None) -> CreateSessionResponse:
    """
    Create a new simulation session.

    Args:
        config: Optional SimulationConfig. Uses defaults if not provided.

    Returns:
        CreateSessionResponse with the new session_id.
    """
    if config is None:
        config = SimulationConfig()

    system = RecommenderSystem(config)
    system.reset()  # Initialize the simulation

    session_id = session_store.create(system)

    return CreateSessionResponse(session_id=session_id)


@router.post("/simulation/{session_id}/step", response_model=StepResponse)
def run_step(
    session_id: str,
    request: StepRequest,
    steps: int = Query(default=1, ge=1, le=1000, description="Number of steps to run"),
) -> StepResponse:
    """
    Run step(s) on a simulation.

    Args:
        session_id: The session ID.
        request: StepRequest with human_choice_idx.
        steps: Number of steps to execute (query param, default=1).

    Returns:
        StepResponse with number of steps executed and final result.

    Raises:
        404: If session_id is not found.
    """
    system = session_store.get(session_id)
    if system is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    result = None
    for _ in range(steps):
        result = system.step(request.human_choice_idx)

    # Convert numpy types for JSON serialization
    converted_result = _convert_numpy_types(result) if result else {}
    return StepResponse(steps_executed=steps, final_result=converted_result)


@router.get("/simulation/{session_id}/state", response_model=SimulationState)
def get_state(session_id: str) -> SimulationState:
    """
    Get the current state of a simulation.

    Args:
        session_id: The session ID.

    Returns:
        SimulationState snapshot.

    Raises:
        404: If session_id is not found.
    """
    system = session_store.get(session_id)
    if system is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return system.get_metrics()


@router.delete("/simulation/{session_id}", response_model=DeleteResponse)
def delete_simulation(session_id: str) -> DeleteResponse:
    """
    Delete a simulation session.

    Args:
        session_id: The session ID to delete.

    Returns:
        DeleteResponse confirming deletion.

    Raises:
        404: If session_id is not found.
    """
    deleted = session_store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return DeleteResponse(message="Session deleted successfully", session_id=session_id)
