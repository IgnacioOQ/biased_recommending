"""
Simulation state models using Pydantic.

Captures the exact snapshot of the system (agent beliefs, item popularity).
"""

from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class AgentBelief(BaseModel):
    """
    Captures the belief state of a single agent.
    """

    agent_id: int
    epsilon: float = Field(description="Current exploration rate")
    q_values_sample: List[float] = Field(
        default_factory=list, description="Q-values for sample states"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentAccuracy(BaseModel):
    """
    Accuracy metrics for an agent (TPR/TNR).
    """

    tpr: float = Field(default=0.0, description="True Positive Rate (TP/Rec)")
    tnr: float = Field(default=0.0, description="True Negative Rate (TN/NotRec)")
    tp: int = Field(default=0, description="True positives")
    rec_count: int = Field(default=0, description="Total recommendations")
    tn: int = Field(default=0, description="True negatives")
    not_rec_count: int = Field(default=0, description="Total not-recommendations")


class SimulationState(BaseModel):
    """
    Captures the exact snapshot of the simulation system.

    Includes agent beliefs, item popularity (recommendation counts),
    and performance metrics.
    """

    # Episode tracking
    episode_count: int = Field(default=0, description="Number of completed episodes")
    step_count: int = Field(default=0, description="Total steps taken")

    # Agent beliefs
    agent_beliefs: List[AgentBelief] = Field(
        default_factory=list, description="Belief state for each agent"
    )

    # Item popularity (recommendation counts)
    recommendation_counts: Dict[int, int] = Field(
        default_factory=dict, description="agent_id -> times action=1 (recommend)"
    )
    selection_counts: Dict[int, int] = Field(
        default_factory=dict, description="agent_id -> times selected by human"
    )

    # Performance metrics
    cumulative_human_reward: float = Field(
        default=0.0, description="Total human reward accumulated"
    )
    agent_accuracy: Dict[int, AgentAccuracy] = Field(
        default_factory=dict, description="Accuracy metrics per agent"
    )

    # New metrics for UI
    episode_reward: int = Field(default=0, description="Reward in current episode")
    average_reward: float = Field(default=0.0, description="Average reward per episode")
    agent_successes: List[int] = Field(
        default_factory=list, description="Count of correct predictions per agent in current episode"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)
