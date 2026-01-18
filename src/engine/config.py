"""
Simulation configuration using Pydantic for validation.
"""

from pydantic import BaseModel, ConfigDict, Field


class SimulationConfig(BaseModel):
    """
    Configuration for all simulation hyperparameters.

    Uses Pydantic for validation and type coercion.
    """

    # Agent hyperparameters
    alpha: float = Field(default=1e-3, description="Learning rate", ge=0.0)
    beta: float = Field(
        default=0.99, description="Discount factor (gamma)", ge=0.0, le=1.0
    )
    epsilon: float = Field(
        default=1.0, description="Initial exploration rate", ge=0.0, le=1.0
    )
    epsilon_decay: float = Field(
        default=0.995, description="Epsilon decay per episode", ge=0.0, le=1.0
    )
    epsilon_min: float = Field(
        default=0.01, description="Minimum epsilon", ge=0.0, le=1.0
    )

    # Architecture
    num_agents: int = Field(default=2, description="Number of recommender agents", ge=1)
    input_dim: int = Field(default=2, description="Observation dimension [p, t]", ge=1)
    action_dim: int = Field(default=2, description="Action space size", ge=1)

    # Training
    buffer_capacity: int = Field(default=10000, description="Replay buffer size", ge=1)
    batch_size: int = Field(default=64, description="Training batch size", ge=1)

    # Environment
    steps_per_episode: int = Field(
        default=20, description="Max steps per episode", ge=1
    )

    model_config = ConfigDict(validate_assignment=True)
