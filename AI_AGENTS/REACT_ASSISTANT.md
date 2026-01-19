# React Assistant Guide

> **Purpose:** This document provides AI assistants with guidelines for setting up simulation games as React + FastAPI monorepo projects. Follow this structure to create consistent, maintainable web-based simulations.

---

## Architecture Overview

This template uses a **display-only frontend** pattern where:

- **Backend (Python/FastAPI):** Contains ALL simulation logic, game state, and behavioral logging
- **Frontend (React/TypeScript):** Purely renders state received from backend and captures user input

```
┌─────────────────────────┐        ┌─────────────────────────┐
│    React Frontend       │◄──────►│    Python Backend       │
│    (Display Layer)      │  HTTP  │    (All Game Logic)     │
└─────────────────────────┘        └─────────────────────────┘
         │                                   │
         ▼                                   ▼
   - Render game grid              - Simulation classes
   - Show entities & states        - Agent/Environment logic  
   - Capture user input            - Collision detection
   - Display scores/status         - Behavioral data logging
```

---

## Project Structure Template

```
project_name/
├── backend/                             # Python simulation backend
│   ├── api/                             # FastAPI web layer
│   │   ├── __init__.py                  # Export app and routes
│   │   ├── main.py                      # FastAPI app entry point
│   │   ├── routes.py                    # API endpoint definitions
│   │   └── session.py                   # Session store (in-memory dict)
│   │
│   ├── engine/                          # Core simulation engine (Pydantic models)
│   │   ├── __init__.py                  # Export main classes
│   │   ├── config.py                    # SimulationConfig (hyperparameters)
│   │   ├── model.py                     # Main simulation class (step, get_state)
│   │   └── state.py                     # SimulationState, AgentBelief models
│   │
│   ├── agents.py                        # Agent class(es) - DQN, RL, etc.
│   ├── environment.py                   # Environment/world logic
│   ├── simulation.py                    # Legacy or simple orchestrator
│   ├── analysis.py                      # Policy metrics, evaluation functions
│   ├── logging.py                       # DataLogger for behavioral data
│   └── __init__.py                      # Package init
│
├── frontend/                            # React + TypeScript frontend
│   ├── src/
│   │   ├── main.tsx                     # React entry point
│   │   ├── App.tsx                      # Root component (health check)
│   │   ├── App.css                      # App-level styles
│   │   ├── Controls.tsx                 # Main game UI component
│   │   ├── Controls.css                 # Game UI styles (dark theme)
│   │   ├── index.css                    # Global CSS variables & reset
│   │   └── vite-env.d.ts                # Vite type declarations
│   ├── index.html                       # HTML entry point
│   ├── package.json                     # Node dependencies
│   ├── vite.config.ts                   # Vite configuration
│   ├── tsconfig.json                    # TypeScript configuration
│   └── tsconfig.app.json                # App-specific TS config
│
├── tests/                               # Python unit tests (pytest)
│   ├── test_api.py                      # API endpoint tests
│   ├── test_engine.py                   # Engine/model tests
│   ├── test_mechanics.py                # Core simulation logic tests
│   └── conftest.py                      # Pytest fixtures
│
├── notebooks/                           # Jupyter notebooks for experiments
│   ├── experiment_interface.ipynb       # Interactive experiment UI
│   └── analysis_report.ipynb            # Results visualization
│
├── data/                                # Output data (excluded from git)
│   └── sessions/                        # Exported behavioral logs
│
├── requirements.txt                     # Python dependencies (root level)
├── AGENTS.md                            # Project documentation for AI
├── AGENTS_LOG.md                        # Change log
└── README.md                            # Project overview
```

> **Important:** All Python imports should use the `backend.` prefix (e.g., `from backend.engine import RecommenderSystem`). This requires running the backend from the project root directory.


---

## Step 1: Backend Setup (Python/FastAPI)

### 1.1 Create requirements.txt

```txt
fastapi
uvicorn[standard]
```

Add any simulation-specific dependencies (numpy, etc.) as needed.

### 1.2 Create FastAPI Server (main.py)

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional
import uuid

# Import your simulation package
from simulation_name import Simulation

app = FastAPI()

# CRITICAL: Configure CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active simulation sessions
simulations: dict[str, Simulation] = {}
```

### 1.3 Define Pydantic Models

Use Pydantic `BaseModel` for request/response validation:

```python
class SimulationConfig(BaseModel):
    gridWidth: int
    gridHeight: int
    # Add simulation-specific config fields
    
class StepRequest(BaseModel):
    session_id: str
    action: Literal["up", "down", "left", "right"]  # Define valid actions
```

### 1.4 Required API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check - frontend uses this to verify backend is running |
| `/simulation/init` | POST | Initialize new game, returns `session_id` and initial `state` |
| `/simulation/step` | POST | Process user action, return updated `state` |
| `/simulation/state/{id}` | GET | Get current game state |
| `/simulation/tick/{id}` | POST | (Optional) Advance simulation without user input (for continuous mode) |
| `/simulation/export/{id}` | GET | (Optional) Export behavioral data for ML training |

### 1.5 Health Check Endpoint

```python
@app.get("/health")
def health_check():
    return {"status": "ok"}
```

### 1.6 Simulation Init Endpoint

```python
@app.post("/simulation/init")
def init_simulation(config: SimulationConfig):
    session_id = str(uuid.uuid4())
    
    simulation = Simulation.create(
        session_id=session_id,
        grid_width=config.gridWidth,
        grid_height=config.gridHeight,
        # Pass other config parameters
    )
    
    simulations[session_id] = simulation
    
    return {
        "session_id": session_id,
        "state": simulation.get_state(),
    }
```

### 1.7 Step Endpoint

```python
@app.post("/simulation/step")
def simulation_step(request: StepRequest):
    if request.session_id not in simulations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    simulation = simulations[request.session_id]
    new_state = simulation.step(request.action)
    
    return {"state": new_state}
```

### 1.8 Simulation Class Structure

Create a simulation package with this pattern:

```python
# simulation_name/simulation.py
class Simulation:
    def __init__(self, session_id: str, agent, environment):
        self.session_id = session_id
        self.agent = agent
        self.environment = environment
        self.game_over = False
        self.score = 0
        self.history = []  # For behavioral logging
    
    @classmethod
    def create(cls, session_id: str, grid_width: int, grid_height: int, **kwargs):
        """Factory method to create simulation with all components."""
        agent = Agent(x=0, y=0)
        environment = Environment(width=grid_width, height=grid_height)
        return cls(session_id, agent, environment)
    
    def step(self, action: str) -> dict:
        """Process one simulation step."""
        # 1. Log the action
        self.history.append({"action": action, "state": self.get_state()})
        
        # 2. Move agent
        self.agent.move(action)
        
        # 3. Update environment
        self.environment.step()
        
        # 4. Check win/lose conditions
        if self.environment.check_collision(self.agent.x, self.agent.y):
            self.game_over = True
        
        # 5. Update score
        self.score += 1
        
        return self.get_state()
    
    def get_state(self) -> dict:
        """Return JSON-serializable game state for frontend."""
        return {
            "session_id": self.session_id,
            "agent": {"x": self.agent.x, "y": self.agent.y},
            "environment": {
                "width": self.environment.width,
                "height": self.environment.height,
                "obstacles": [{"x": o.x, "y": o.y} for o in self.environment.obstacles],
            },
            "game_over": self.game_over,
            "score": self.score,
        }
```

---

## Step 2: Frontend Setup (Vite + React + TypeScript)

### 2.1 Initialize Vite Project

```bash
cd project_name
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

### 2.2 package.json Dependencies

Ensure these are present:

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "~5.6.2",
    "vite": "^6.0.5"
  }
}
```

### 2.3 App.tsx Pattern

The root component should:
1. Check backend health on mount
2. Display connection status
3. Conditionally render game UI when healthy

```tsx
import { useState, useEffect } from 'react'
import Controls from './Controls'
import './App.css'

function App() {
    const [health, setHealth] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetch('http://localhost:8000/health')
            .then(res => res.json())
            .then(data => setHealth(data.status))
            .catch(err => setError(err.message))
    }, [])

    return (
        <div className="app-container">
            <h1>Simulation Name</h1>
            
            <div className="status-card">
                <p>Backend Status: {
                    error ? <span className="error">{error}</span> :
                    health ? <span className="success">{health}</span> :
                    <span>Loading...</span>
                }</p>
            </div>
            
            {health === 'ok' && <Controls />}
        </div>
    )
}

export default App
```

### 2.4 Controls.tsx Pattern

The main game component should:

1. **Define TypeScript interfaces** for state and config
2. **Manage state** with `useState` hooks
3. **Initialize simulation** via POST to `/simulation/init`
4. **Handle user actions** via POST to `/simulation/step`
5. **Render game grid** by mapping backend state to visual elements
6. **Support continuous mode** (optional) using `useEffect` + `setInterval`

```tsx
import { useState, useEffect, useRef } from 'react'
import './Controls.css'

type SimulationMode = 'step' | 'continuous'

interface SimulationConfig {
    gridWidth: number
    gridHeight: number
    obstacleCount: number
}

interface Position {
    x: number
    y: number
}

interface SimulationState {
    session_id: string
    agent: Position
    environment: {
        width: number
        height: number
        obstacles: Position[]
    }
    game_over: boolean
    score: number
}

function Controls() {
    // Configuration state
    const [config, setConfig] = useState<SimulationConfig>({
        gridWidth: 10,
        gridHeight: 10,
        obstacleCount: 3,
    })
    
    // Simulation state
    const [state, setState] = useState<SimulationState | null>(null)
    const [mode, setMode] = useState<SimulationMode | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    
    // Continuous mode interval
    const intervalRef = useRef<number | null>(null)
    
    // Start simulation
    const startSimulation = async (selectedMode: SimulationMode) => {
        setLoading(true)
        setError(null)
        
        try {
            const response = await fetch('http://localhost:8000/simulation/init', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    gridWidth: config.gridWidth,
                    gridHeight: config.gridHeight,
                    obstacleCount: config.obstacleCount,
                }),
            })
            
            const data = await response.json()
            setState(data.state)
            setMode(selectedMode)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start')
        } finally {
            setLoading(false)
        }
    }
    
    // Handle user action
    const moveAgent = async (direction: 'up' | 'down' | 'left' | 'right') => {
        if (!state || state.game_over) return
        
        try {
            const response = await fetch('http://localhost:8000/simulation/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: state.session_id,
                    action: direction,
                }),
            })
            
            const data = await response.json()
            setState(data.state)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to step')
        }
    }
    
    // Continuous mode: auto-tick
    useEffect(() => {
        if (mode === 'continuous' && state && !state.game_over) {
            intervalRef.current = window.setInterval(async () => {
                const response = await fetch(
                    `http://localhost:8000/simulation/tick/${state.session_id}`,
                    { method: 'POST' }
                )
                const data = await response.json()
                setState(data.state)
            }, 500)
        }
        
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [mode, state?.session_id, state?.game_over])
    
    // Render grid
    const renderGrid = () => {
        if (!state) return null
        
        const cells = []
        for (let y = 0; y < state.environment.height; y++) {
            for (let x = 0; x < state.environment.width; x++) {
                const isAgent = state.agent.x === x && state.agent.y === y
                const isObstacle = state.environment.obstacles.some(
                    o => o.x === x && o.y === y
                )
                
                let cellClass = 'grid-cell'
                if (isAgent) cellClass += ' agent'
                if (isObstacle) cellClass += ' obstacle'
                
                cells.push(
                    <div key={`${x}-${y}`} className={cellClass} />
                )
            }
        }
        
        return (
            <div 
                className="grid"
                style={{
                    gridTemplateColumns: `repeat(${state.environment.width}, 1fr)`
                }}
            >
                {cells}
            </div>
        )
    }
    
    return (
        <div className="controls-container">
            {/* Config UI, Start buttons, Grid, Arrow controls */}
            {renderGrid()}
        </div>
    )
}

export default Controls
```

### 2.5 CSS Grid Rendering

```css
.grid {
    display: grid;
    gap: 2px;
    background: #1a1a2e;
    padding: 10px;
    border-radius: 8px;
}

.grid-cell {
    width: 30px;
    height: 30px;
    background: #16213e;
    border-radius: 4px;
}

.grid-cell.agent {
    background: #00ff88;
}

.grid-cell.obstacle {
    background: #ff4444;
}

.grid-cell.goal {
    background: #4488ff;
}
```

---

## Step 3: Running the Application

### 3.1 Start Backend (Terminal 1)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`

### 3.2 Start Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

### 3.3 Verify Connection

1. Open `http://localhost:5173` in browser
2. Health status should display "ok" in green
3. Game controls should appear

---

## Key Concepts for AI Assistants

### CORS Configuration

**Problem:** Browser blocks requests from `localhost:5173` to `localhost:8000` (different ports).

**Solution:** FastAPI must explicitly allow the frontend origin:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Session Management

- Each game is identified by a unique `session_id` (UUID)
- Backend stores active sessions in a dictionary
- Frontend stores `session_id` in React state
- All subsequent requests include `session_id`

### State Pattern

The backend `get_state()` method returns a **JSON-serializable dictionary** with:
- All entity positions (agents, obstacles, goals)
- Grid dimensions
- Game status (game_over, won, score)
- Any other data the frontend needs to render

Frontend **never computes game logic** — it only:
1. Sends user actions to backend
2. Receives new state
3. Renders the state

### Continuous vs Step Mode

| Mode | User Experience | Implementation |
|------|-----------------|----------------|
| **Step** | Turn-based, user controls pace | Only call `/simulation/step` on user input |
| **Continuous** | Real-time, auto-advancing | Use `setInterval` to call `/simulation/tick` every N ms |

---

## Checklist for New Simulations

When setting up a new simulation project, ensure:

- [ ] `requirements.txt` includes `fastapi` and `uvicorn[standard]`
- [ ] CORS middleware allows `http://localhost:5173`
- [ ] `/health` endpoint returns `{"status": "ok"}`
- [ ] `/simulation/init` creates session and returns initial state
- [ ] `/simulation/step` processes actions and returns new state
- [ ] `get_state()` returns JSON-serializable dict with all render data
- [ ] Frontend checks health before showing game UI
- [ ] TypeScript interfaces match backend state structure
- [ ] Grid rendering uses CSS Grid with dynamic `gridTemplateColumns`
- [ ] Error handling for network failures
- [ ] Loading states during API calls

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| CORS error in browser | Missing or wrong CORS config | Add correct `allow_origins` in FastAPI |
| Health check fails | Backend not running | Start backend first on port 8000 |
| `uvicorn` not found | Not in PATH | Use `python -m uvicorn` instead |
| State not updating | Missing `setState` call | Ensure fetch response updates state |
| Grid not rendering | Missing CSS Grid setup | Check `gridTemplateColumns` matches width |
| Continuous mode doesn't stop | Interval not cleared | Return cleanup in `useEffect` |

---

## Behavioral Data Logging

For ML training, log all user actions:

```python
# In Simulation class
self.history.append({
    "step": len(self.history),
    "action": action,
    "state_before": previous_state,
    "state_after": new_state,
    "reward": calculated_reward,
})

def export_behavioral_data(self, filepath: str):
    import json
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(self.history, f, indent=2)
    return self.history
```

### 4.1 Single-File Session Logging (Recommended)

Instead of separate files per episode, maintain a single JSON file per session. This prevents clutter and makes data analysis easier.

**Structure (`data/sessions/{session_id}.json`):**
```json
{
  "session_id": "uuid",
  "participant_name": "User Input",
  "start_time": "2024-03-20T10:00:00.123+00:00",
  "config": { ... },
  "episodes": {
    "0": [ ...steps... ],
    "1": [ ...steps... ]
  }
}
```

**Implementation Tip:**
Use `datetime.datetime.now().astimezone().isoformat()` for `start_time` to preserve time zone information, which is critical for multi-region studies.

---

## Summary

This architecture cleanly separates concerns:

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| **Backend** | Python + FastAPI | All game logic, state management, ML logging |
| **API** | REST + JSON | Stateless request/response communication |
| **Frontend** | React + TypeScript | Display rendering, user input capture |

AI assistants should use this pattern when helping users create web-based simulations for ML training, game prototypes, or educational tools.

---

## Step 4: Cloud Deployment (Render & Vercel)

For production deployment, use **Render** for the Python backend and **Vercel** for the React frontend.

### 4.1 Prerequisites

- GitHub Account (project must be in a repository)
- Render Account (for backend)
- Vercel Account (for frontend)

### 4.2 Preparation: Environment Variables

**Code Refactoring Required Before Deployment:**
1.  **Backend (`main.py`):** Update CORS to allow production origins.
    ```python
    origins = [
        "http://localhost:5173",
        "https://your-project.vercel.app" # Add Vercel URL after deployment
    ]
    # Optionally use os.getenv("FRONTEND_URL")
    ```
2.  **Frontend:** Replace hardcoded `http://localhost:8000` with `import.meta.env.VITE_API_URL`.
    - Create `.env.production` file:
      ```
      VITE_API_URL=https://your-project-backend.onrender.com
      ```

### 4.3 Backend Deployment (Render.com)

1.  **Create Service:**
    - Dashboard -> New + -> **Web Service**
    - Connect GitHub repository
2.  **Configure Settings:**
    - **Name:** `project-backend`
    - **Runtime:** Python 3
    - **Build Command:** `pip install -r requirements.txt`
    - **Start Command:** `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
    - **Environment Variables:**
        - `PYTHON_VERSION`: `3.10.0` (or matching your local version)
3.  **Deploy:** Click "Create Web Service".
4.  **Copy URL:** (e.g., `https://project-backend.onrender.com`).

### 4.4 Frontend Deployment (Vercel)

1.  **Create Project:**
    - Dashboard -> **Add New...** -> **Project**
    - Import GitHub repository
2.  **Configure Project:**
    - **Root Directory:** Edit -> Select `frontend` folder
    - **Framework Preset:** Vite
    - **Environment Variables:**
        - `VITE_API_URL`: `https://project-backend.onrender.com` (No trailing slash)
3.  **Deploy:** Click "Deploy".
4.  **Update Backend CORS:**
    - Update `backend/api/main.py` with the new Vercel domain.
    - Push changes to GitHub to trigger Render redeploy.

