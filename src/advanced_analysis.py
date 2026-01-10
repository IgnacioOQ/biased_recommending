import numpy as np
import torch

def compute_advanced_policy_metrics(agents, time_step=0):
    """
    Computes differences between learned policies and the unbiased policy for advanced agents.
    Unbiased Policy: Recommend (1) if p > 0.5, else Not Recommend (0).

    Since Advanced Agents observe [p, t], we fix t to a specific value (default 0)
    to compute metrics across the p-grid.
    """
    # Grid of p values
    p_grid = np.linspace(0, 1, 100)

    # Construct input states: [p, t]
    # Shape should be (100, 2)
    t_column = np.full((100, 1), time_step)
    p_column = p_grid.reshape(-1, 1)
    states_np = np.hstack([p_column, t_column]).astype(np.float32)

    metrics = {}

    for agent in agents:
        agent_id = agent.agent_id

        # Get Agent Actions
        actions = []

        with torch.no_grad():
            # Convert to tensor. Shape (100, 2)
            states = torch.FloatTensor(states_np).to(agent.device)

            # Forward pass
            q_values = agent.policy_net(states) # (100, 2)
            actions = q_values.argmax(dim=1).cpu().numpy()

        unbiased_actions = (p_grid > 0.5).astype(int)

        # 1. Accuracy (Agreement %)
        agreement = (actions == unbiased_actions)
        accuracy = np.mean(agreement)

        # 2. Simple Disagreement Count
        disagreement_count = np.sum(~agreement)

        metrics[f"agent_{agent_id}"] = {
            "accuracy": float(accuracy),
            "disagreement_count": int(disagreement_count),
            "disagreement_rate": float(1.0 - accuracy),
            "analyzed_at_time_step": time_step
        }

    return metrics
