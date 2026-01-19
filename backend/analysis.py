import numpy as np

def compute_policy_metrics(agents):
    """
    Computes differences between learned policies and the unbiased policy.
    Unbiased Policy: Recommend (1) if p > 0.5, else Not Recommend (0).
    """
    # Grid of p values
    p_grid = np.linspace(0, 1, 100)

    metrics = {}

    for agent in agents:
        agent_id = agent.agent_id

        # Get Agent Actions
        # agent.select_action usually takes a single state or batch?
        # Our current select_action does: state (numpy array) -> tensor -> argmax
        # Let's batch process

        actions = []
        q_values_list = []

        # We need to access the network directly for batch efficiency or loop
        # For simplicity and robustness given current agent code, we loop or modify agent to accept batch
        # Agent select_action expects shape (1,) for single inference usually, or (batch, 1)
        # Let's try batching:
        import torch
        with torch.no_grad():
            states = torch.FloatTensor(p_grid).unsqueeze(1).to(agent.device)
            q_values = agent.policy_net(states) # (100, 2)
            actions = q_values.argmax(dim=1).cpu().numpy()
            q_vals = q_values.cpu().numpy()

        unbiased_actions = (p_grid > 0.5).astype(int)

        # 1. Accuracy (Agreement %)
        agreement = (actions == unbiased_actions)
        accuracy = np.mean(agreement)

        # 2. Simple Disagreement Count
        disagreement_count = np.sum(~agreement)

        # 3. MSE (Mean Squared Error) ?
        # MSE is typically between predicted values and target values.
        # Here we don't have "true Q values" easily without solving the MDP.
        # But the user asked for "MSE".
        # Perhaps MSE between the policy action (0/1) and the optimal action (0/1)? That's (1-Accuracy).
        # Or maybe MSE of the Q-values? But we don't have ground truth Q-values.
        # Let's interpret "MSE" as Mean Squared Error between the agent's probability of recommending
        # (which is 0 or 1 for deterministic policy) vs the unbiased policy (0 or 1).
        # This is effectively same as (1-Accuracy) for binary 0/1.
        # Let's stick to Disagreement Rate (1-Accuracy) as the error metric.

        metrics[f"agent_{agent_id}"] = {
            "accuracy": float(accuracy),
            "disagreement_count": int(disagreement_count),
            "disagreement_rate": float(1.0 - accuracy)
        }

    return metrics
