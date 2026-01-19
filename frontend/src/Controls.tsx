import { useState } from 'react'
import './Controls.css'

// TypeScript interfaces
interface SimulationConfig {
    alpha: number
    beta: number
    epsilon: number
    epsilon_decay: number
    epsilon_min: number
    steps_per_episode: number
}

interface GameState {
    session_id: string
    current_p: number
    current_t: number
    recommendations: number[]
    episode: number
    step: number
    game_over: boolean
    cumulative_human_reward: number
}

interface StepResult {
    human_reward: number
    agent_rewards: number[]
    outcome: string
    done: boolean
    new_episode: boolean
    recommendations: number[]
    current_p: number
    step: number
    episode: number
}

function Controls() {
    // Configuration state
    const [config, setConfig] = useState<SimulationConfig>({
        alpha: 0.001,
        beta: 0.99,
        epsilon: 1.0,
        epsilon_decay: 0.995,
        epsilon_min: 0.01,
        steps_per_episode: 20,
    })

    // Game state
    const [state, setState] = useState<GameState | null>(null)
    const [lastResult, setLastResult] = useState<StepResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Start simulation
    const startSimulation = async () => {
        setLoading(true)
        setError(null)
        setLastResult(null)

        try {
            const response = await fetch('http://localhost:8000/api/simulation/init', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    alpha: config.alpha,
                    beta: config.beta,
                    epsilon: config.epsilon,
                    epsilon_decay: config.epsilon_decay,
                    epsilon_min: config.epsilon_min,
                    steps_per_episode: config.steps_per_episode,
                }),
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }

            const data = await response.json()
            setState({
                session_id: data.session_id,
                current_p: data.state.current_p,
                current_t: data.state.current_t,
                recommendations: data.state.recommendations,
                episode: data.state.episode,
                step: data.state.step,
                game_over: false,
                cumulative_human_reward: 0,
            })
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start simulation')
        } finally {
            setLoading(false)
        }
    }

    // Make a choice
    const makeChoice = async (agentIndex: number) => {
        if (!state) return
        setLoading(true)
        setError(null)

        try {
            const response = await fetch(`http://localhost:8000/api/simulation/${state.session_id}/step`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    human_choice_idx: agentIndex,
                }),
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }

            const data = await response.json()
            const result = data.final_result

            setLastResult({
                human_reward: result.human_reward,
                agent_rewards: result.agent_rewards,
                outcome: result.outcome,
                done: result.done,
                new_episode: result.new_episode,
                recommendations: result.recommendations,
                current_p: result.next_p,
                step: result.done ? 0 : state.step + 1,
                episode: result.episode_count,
            })

            setState(prev => prev ? {
                ...prev,
                current_p: result.next_p,
                recommendations: result.recommendations,
                step: result.done ? 0 : prev.step + 1,
                episode: result.episode_count,
                cumulative_human_reward: prev.cumulative_human_reward + result.human_reward,
            } : null)

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to process step')
        } finally {
            setLoading(false)
        }
    }

    // Render recommendation badge
    const renderRecommendation = (action: number) => {
        if (action === 1) {
            return <span className="recommendation recommend">✓ RECOMMEND</span>
        } else {
            return <span className="recommendation not-recommend">✗ NOT RECOMMEND</span>
        }
    }

    return (
        <div className="controls-container">
            {/* Configuration Panel - shown when no game is active */}
            {!state && (
                <div className="config-panel">
                    <h2>⚙️ Configuration</h2>
                    <div className="config-grid">
                        <div className="config-item">
                            <label>Learning Rate (α)</label>
                            <input
                                type="number"
                                step="0.0001"
                                min="0"
                                max="1"
                                value={config.alpha}
                                onChange={e => setConfig(prev => ({ ...prev, alpha: parseFloat(e.target.value) }))}
                            />
                        </div>
                        <div className="config-item">
                            <label>Discount Factor (β)</label>
                            <input
                                type="number"
                                step="0.01"
                                min="0"
                                max="1"
                                value={config.beta}
                                onChange={e => setConfig(prev => ({ ...prev, beta: parseFloat(e.target.value) }))}
                            />
                        </div>
                        <div className="config-item">
                            <label>Initial Epsilon (ε)</label>
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="1"
                                value={config.epsilon}
                                onChange={e => setConfig(prev => ({ ...prev, epsilon: parseFloat(e.target.value) }))}
                            />
                        </div>
                        <div className="config-item">
                            <label>Steps per Episode</label>
                            <input
                                type="number"
                                step="1"
                                min="1"
                                max="100"
                                value={config.steps_per_episode}
                                onChange={e => setConfig(prev => ({ ...prev, steps_per_episode: parseInt(e.target.value) }))}
                            />
                        </div>
                    </div>
                    <button
                        className="start-button"
                        onClick={startSimulation}
                        disabled={loading}
                    >
                        {loading ? '⏳ Starting...' : '🚀 Start Experiment'}
                    </button>
                </div>
            )}

            {/* Game Display - shown when game is active */}
            {state && (
                <div className="game-panel">
                    {/* Progress Bar */}
                    <div className="progress-bar">
                        <div className="progress-info">
                            <span>Episode: {state.episode + 1}</span>
                            <span>Step: {state.step + 1} / {config.steps_per_episode}</span>
                            <span className="reward">Total Reward: {state.cumulative_human_reward}</span>
                        </div>
                        <div className="progress-track">
                            <div
                                className="progress-fill"
                                style={{ width: `${((state.step + 1) / config.steps_per_episode) * 100}%` }}
                            />
                        </div>
                    </div>

                    {/* Current P Value */}
                    <div className="p-display">
                        <h3>Current Probability (p)</h3>
                        <div className="p-value">{state.current_p.toFixed(3)}</div>
                        <div className="p-bar">
                            <div
                                className="p-fill"
                                style={{ width: `${state.current_p * 100}%` }}
                            />
                        </div>
                        <p className="p-hint">
                            {state.current_p >= 0.5
                                ? '📈 p ≥ 0.5: Unbiased policy would RECOMMEND'
                                : '📉 p < 0.5: Unbiased policy would NOT RECOMMEND'}
                        </p>
                    </div>

                    {/* Agent Cards */}
                    <div className="agents-container">
                        {[0, 1].map(agentIdx => (
                            <div key={agentIdx} className="agent-card">
                                <h3>Agent {agentIdx}</h3>
                                {renderRecommendation(state.recommendations[agentIdx])}
                                <button
                                    className="choice-button"
                                    onClick={() => makeChoice(agentIdx)}
                                    disabled={loading}
                                >
                                    {loading ? '⏳' : `Choose Agent ${agentIdx}`}
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Last Result */}
                    {lastResult && (
                        <div className={`result-panel ${lastResult.human_reward > 0 ? 'win' : 'lose'}`}>
                            <div className="result-outcome">
                                {lastResult.outcome === 'Heads' ? '🪙 HEADS' : '🪙 TAILS'}
                            </div>
                            <div className="result-rewards">
                                <span className={`reward ${lastResult.human_reward > 0 ? 'positive' : 'zero'}`}>
                                    Your Reward: {lastResult.human_reward > 0 ? '+1' : '0'}
                                </span>
                                <span className="agent-rewards">
                                    Agent 0: {lastResult.agent_rewards[0] > 0 ? '+1' : '-1'} |
                                    Agent 1: {lastResult.agent_rewards[1] > 0 ? '+1' : '-1'}
                                </span>
                            </div>
                            {lastResult.new_episode && (
                                <div className="new-episode-notice">
                                    ✨ New Episode Started!
                                </div>
                            )}
                        </div>
                    )}

                    {/* Reset Button */}
                    <button
                        className="reset-button"
                        onClick={() => { setState(null); setLastResult(null); }}
                    >
                        🔄 New Experiment
                    </button>
                </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="error-panel">
                    ⚠️ {error}
                </div>
            )}
        </div>
    )
}

export default Controls
