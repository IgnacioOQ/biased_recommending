import { useState } from 'react'
import './Controls.css'
import { API_BASE_URL } from './config'

// TypeScript interfaces
interface SimulationConfig {
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
    cumulative_agent_rewards: number[]
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
    human_choice: number
    agent_correctness: boolean[]
    cumulative_agent_rewards: number[]
}

function Controls() {
    // Configuration state
    // Default config values are now handled by the backend
    const [config] = useState<SimulationConfig>({
        steps_per_episode: 20,
    })

    // Game state
    const [state, setState] = useState<GameState | null>(null)
    const [lastResult, setLastResult] = useState<StepResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [participantName, setParticipantName] = useState('')

    // Start simulation
    const startSimulation = async () => {
        setLoading(true)
        setError(null)
        setLastResult(null)

        try {
            const response = await fetch(`${API_BASE_URL}/api/simulation/init`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    // We rely on backend defaults for RL hyperparameters
                    steps_per_episode: config.steps_per_episode,
                    participant_name: participantName || 'Anonymous',
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
                cumulative_agent_rewards: data.state.cumulative_agent_rewards || [0, 0],
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
            const response = await fetch(`${API_BASE_URL}/api/simulation/${state.session_id}/step`, {
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
                human_choice: result.human_choice,
                agent_correctness: result.agent_correctness,
                cumulative_agent_rewards: result.cumulative_agent_rewards,
            })

            setState(prev => prev ? {
                ...prev,
                current_p: result.next_p,
                recommendations: result.recommendations,
                step: result.done ? 0 : prev.step + 1,
                episode: result.episode_count,
                cumulative_human_reward: prev.cumulative_human_reward + result.human_reward,
                cumulative_agent_rewards: result.cumulative_agent_rewards,
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
            {/* Start Panel - shown when no game is active */}
            {!state && (
                <div className="config-panel">
                    <h2>🎲 Start Experiment</h2>

                    <div className="game-explanation">
                        <p><strong>Welcome to the Recommender System Game!</strong></p>

                        <div className="explanation-section">
                            <h3>🎮 How the Game Works</h3>
                            <ol>
                                <li>The <strong>AI Agents observe a "Coin Bias"</strong> (probability of Heads) for the current step.</li>
                                <li>The Agents give you a recommendation: <strong>RECOMMEND</strong> (bet on Heads) or <strong>NOT RECOMMEND</strong> (bet on Tails).</li>
                                <li><strong>You choose</strong> which agent to trust.</li>
                                <li>A virtual <strong>coin is flipped</strong> based on the hidden bias.</li>
                                <li>If you win (Heads & Recommended, or Tails & Not Recommended), you get <strong>+1 point</strong>.</li>
                            </ol>
                        </div>

                        <div className="explanation-section">
                            <h3>📝 Details</h3>
                            <ul>
                                <li><strong>Length:</strong> Each game (episode) lasts for <strong>20 steps</strong>.</li>
                                <li><strong>Replay:</strong> The agents learn over time! Play multiple episodes to see how they adapt.</li>
                                <li><strong>Goal:</strong> Figure out which agent is smarter and maximize your total score.</li>
                            </ul>
                        </div>
                    </div>

                    <div className="input-group">
                        <label htmlFor="participant-name">Participant Name (Optional)</label>
                        <input
                            id="participant-name"
                            type="text"
                            placeholder="Enter your name"
                            value={participantName}
                            onChange={(e) => setParticipantName(e.target.value)}
                            className="text-input"
                        />
                    </div>

                    <p>Click below to begin the recommendation game.</p>
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

                    {/* Agent Cards */}
                    <div className="agents-container">
                        {[0, 1].map(agentIdx => {
                            const isLastPicked = lastResult?.human_choice === agentIdx
                            const lastCorrect = lastResult?.agent_correctness?.[agentIdx]

                            return (
                                <div key={agentIdx} className={`agent-card ${isLastPicked ? 'picked' : ''}`}>
                                    <div className="agent-header">
                                        <h3>Agent {agentIdx}</h3>
                                        <span className="agent-score">Score: {state.cumulative_agent_rewards[agentIdx].toFixed(1)}</span>
                                    </div>

                                    {renderRecommendation(state.recommendations[agentIdx])}

                                    {lastResult && !lastResult.new_episode && (
                                        <div className={`agent-feedback ${lastCorrect ? 'correct' : 'incorrect'}`}>
                                            Last Rec: {lastCorrect ? '✅ Good' : '❌ Bad'}
                                        </div>
                                    )}

                                    <button
                                        className="choice-button"
                                        onClick={() => makeChoice(agentIdx)}
                                        disabled={loading}
                                    >
                                        {loading ? '⏳' : `Choose Agent ${agentIdx}`}
                                    </button>
                                </div>
                            )
                        })}
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
