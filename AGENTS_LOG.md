# Agents Log

## Intervention History

### Housekeeping Report (Initial)
**Date:** 2024-05-22
**Summary:** Executed initial housekeeping protocol.
- **Dependency Network:** Mapped imports across `src/`, `tests/`, and `notebooks/`.
- **Tests:** Ran `pytest` on `tests/test_mechanics.py`. All 4 tests passed.

### Bug Fix: Advanced Analysis (Shape Mismatch)
**Date:** 2024-05-22
**Summary:** Fixed RuntimeError in `advanced_experiment_interface.ipynb`.
- **Issue:** `compute_policy_metrics` in `src/analysis.py` passed 1D inputs `(100, 1)` to agents expecting 2D inputs `(100, 2)`.
- **Fix:** Created `src/advanced_analysis.py` with `compute_advanced_policy_metrics`.
- **Details:** The new function constructs inputs as `[p, t]` with `t` fixed at 0 (default).
- **Files Modified:** `src/advanced_simulation.py` updated to use the new analysis function.

### Bug Fix: Notebook NameError
**Date:** 2024-05-22
**Summary:** Fixed NameError in `advanced_experiment_interface.ipynb`.
- **Issue:** The variable `ep_id` was used in a print statement but was undefined in the new JSON saving block.
- **Fix:** Removed the erroneous print statement and cleanup old comments. Validated that the correct logging uses `current_step_info['episode_count']`.

### Bug Fix: Empty Episode History
**Date:** 2024-05-22
**Summary:** Fixed issue where saved JSON history was empty.
- **Issue:** `game.env.episode_history` was being accessed after `env.reset()` was called (which wipes the history).
- **Fix:** Modified `src/advanced_simulation.py` to capture `episode_history` before reset and return it in `process_step` result as `finished_episode_history`.
- **Notebook:** Updated `advanced_experiment_interface.ipynb` to save `current_step_info['finished_episode_history']` instead of the live (reset) environment property.

### Feat: Notebook Layout and Metadata
**Date:** 2024-05-22
**Summary:** Adjusted notebook UI and added data structure metadata.
- **Layout:** Moved the performance plot below the 'Next Step' button in `advanced_experiment_interface.ipynb`.
- **Metadata:** Added `data_structure` key to the JSON output `session_meta` explaining the quintuple format.

### Fix: Robust Notebook Setup
**Date:** 2024-05-22
**Summary:** Updated `advanced_experiment_interface.ipynb` setup cell.
- **Issue:** Potential for nested cloning if setup cell is re-run (`biased_recommending/biased_recommending`).
- **Fix:** Added checks to skip `git clone` if the directory exists and to verify current working directory before switching context. Used the specific working branch for cloning.

### Housekeeping Report (Full Audit)
**Date:** 2024-05-22
**Summary:** Executed full housekeeping protocol including new advanced modules.
- **Dependency Network:** Mapped `src`, `advanced_src`, `tests`, and `notebooks`. Confirmed advanced modules correctly inherit from core modules (`advanced_environment.py` -> `environment.py`, etc.).
- **Tests:** Ran `python -m pytest`.
  - `tests/test_mechanics.py`: 4/4 Passed.
  - `tests/advanced_test_mechanics.py`: 5/5 Passed.
- **Conclusion:** Project state is consistent and functional.

### Feat: Accumulated Accuracy Table
**Date:** 2024-05-22
**Summary:** Added real-time accuracy table to notebook interface.
- **Feature:** Displays True Positive Rate (TPR) and True Negative Rate (TNR) for both agents, accumulated over the session.
- **Layout:** Positioned to the right of the performance plot.

### Feat: Human Proxy Simulation
**Date:** 2024-05-22
**Summary:** Implemented automated proxy simulation.
- **Components:** `HumanProxyAgent`, `ProxySimulation`.
- **Report:** Created `notebooks/proxy_simulation_report.ipynb` featuring plots for Agent Policy Accuracy (vs Unbiased) and Average Human Proxy Reward.

### Feat: Modular Engine Architecture
**Date:** 2026-01-18
**Summary:** Refactored simulation logic into `src/engine/` with Pydantic models.
- **New Files:**
  - `src/engine/config.py`: `SimulationConfig` for all hyperparameters (alpha, beta, num_agents, etc.)
  - `src/engine/state.py`: `SimulationState`, `AgentBelief`, `AgentAccuracy` models
  - `src/engine/model.py`: `RecommenderSystem` class with `step()` and `get_metrics()` methods
  - `tests/test_engine.py`: 16 unit tests for engine module
- **Design:** No matplotlib/plotting in engine - pure computation only
- **Compatibility:** Pydantic v2 with `ConfigDict`, all 21 tests pass
- **Notebook:** `advanced_experiment_interface.ipynb` unchanged for sanity checks

### Feat: FastAPI Wrapper
**Date:** 2026-01-18
**Summary:** Built REST API wrapper for the simulation engine.
- **New Files:**
  - `src/api/session.py`: `SessionStore` singleton for in-memory session management
  - `src/api/routes.py`: 4 endpoints (create, step, state, delete) with 404 error handling
  - `src/api/main.py`: FastAPI app entry point
  - `tests/test_api.py`: 17 unit tests for API module
- **Endpoints:**
  - `POST /api/simulation` - create session with optional config
  - `POST /api/simulation/{session_id}/step?steps=N` - run N steps
  - `GET /api/simulation/{session_id}/state` - get SimulationState
  - `DELETE /api/simulation/{session_id}` - cleanup
- **Dependencies:** Added `fastapi` and `uvicorn[standard]` to requirements.txt
- **Tests:** All 33 tests pass (17 API + 16 engine)

### Housekeeping Report
**Date:** 2026-01-18
**Summary:** Executed full housekeeping protocol.
- **Dependency Network:** Updated to include engine and API modules. Clear layering: core → advanced → engine → API.
- **Tests:** All 38 tests passed in 4.72s.
  - `tests/test_api.py`: 17 passed
  - `tests/test_engine.py`: 16 passed
  - `tests/test_mechanics.py`: 4 passed
  - `tests/test_proxy_simulation.py`: 1 passed
- **Conclusion:** Project state is consistent and functional.

### Feat: React Frontend Implementation
**Date:** 2026-01-19
**Summary:** Added React + TypeScript frontend following REACT_ASSISTANT.md guidelines.
- **Repository Restructure:**
  - Renamed `src/` to `backend/` to match monorepo pattern
  - Updated all Python imports from `src.` to `backend.`
- **Backend Modifications:**
  - Added CORS middleware to `backend/api/main.py` for `localhost:5173`
  - Updated health check to return `{"status": "ok"}`
  - Added `/api/simulation/init` endpoint returning session_id + initial state
- **Frontend Files (`frontend/`):**
  - `App.tsx`: Health check on mount, connection status display
  - `Controls.tsx`: Full game UI with config panel, game display, choice buttons
  - `Controls.css`: Modern dark theme with animations
  - `index.css`: CSS variables and global styles
- **Tech Stack:** Vite + React 18 + TypeScript
- **Commands:**
  - Backend: `python -m uvicorn backend.api.main:app --reload --port 8000`
  - Frontend: `cd frontend && npm run dev`
- **Verification:** Health endpoint returns OK, init endpoint returns valid state

### Housekeeping Report (Post-React Integration)
**Date:** 2026-01-19
**Summary:** Executed full housekeeping protocol following React integration and repository restructure.
- **Dependency Network:** 
  - Validated `src/` to `backend/` rename.
  - Confirmed all internal imports use `backend.` prefix.
  - Frontend acts as a consumer of `backend` APIs.
- **Tests:** Ran `python -m pytest`.
  - `tests/test_api.py`: 17 passed (Updated health check expectation).
  - `tests/test_engine.py`: 16 passed.
  - `tests/test_mechanics.py`: 4 passed.
  - `tests/test_proxy_simulation.py`: 1 passed.
- **Total:** 38 tests passed.
- **Conclusion:** Repository structure successfully migrated. Backend remains fully functional with new folder structure.


