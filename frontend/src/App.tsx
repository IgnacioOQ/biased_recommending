import { useState, useEffect } from 'react'
import Controls from './Controls'
import './App.css'
import { API_BASE_URL } from './config'

function App() {
  const [health, setHealth] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then(res => res.json())
      .then(data => setHealth(data.status))
      .catch(err => setError(err.message))
  }, [])

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🎰 Biased Recommender Experiment</h1>
        <p className="subtitle">Testing how recommender systems can exploit human biases</p>
      </header>

      <div className="status-card">
        <span className="status-label">Backend Status:</span>
        {error ? (
          <span className="status error">❌ {error}</span>
        ) : health ? (
          <span className="status success">✅ {health}</span>
        ) : (
          <span className="status loading">⏳ Connecting...</span>
        )}
      </div>

      {health === 'ok' && <Controls />}

      {!health && !error && (
        <div className="loading-hint">
          <p>Make sure the backend is running:</p>
          <code>python -m uvicorn src.api.main:app --reload --port 8000</code>
        </div>
      )}
    </div>
  )
}

export default App
