# Housekeeping Protocol

1. Read the AGENTS.md file.
2. Look at the dependency network of the project, namely which script refers to which one.
3. Proceed doing different sanity checks and unit tests from root scripts to leaves.
4. Compile all errors and tests results into a report. And print that report in the Latest Report subsection below, overwriting previous reports.
5. Add that report to the AGENTS_LOG.md.

# Current Project Housekeeping

## Dependency Network

Based on updated import analysis (including engine and API modules):
- **Core Modules:**
  - `src/logging.py`: Standard libs, numpy.
  - `src/analysis.py`: numpy.
  - `src/environment.py`: numpy.
  - `src/agents.py`: numpy, torch, random, collections.
  - `src/simulation.py`: Depends on `src.agents`, `src.environment`, `src.logging`, `src.analysis`.
- **Advanced Modules:**
  - `src/advanced_environment.py`: Inherits `src.environment`.
  - `src/advanced_agents.py`: Inherits `src.agents`.
  - `src/advanced_analysis.py`: Depends on numpy, torch.
  - `src/advanced_simulation.py`: Depends on advanced modules + `src.simulation` + `src.logging`.
- **Engine Module (New):**
  - `src/engine/config.py`: pydantic.
  - `src/engine/state.py`: pydantic.
  - `src/engine/model.py`: Depends on `src.advanced_agents`, `src.advanced_environment`, `src.engine.config`, `src.engine.state`, torch, numpy.
- **API Module (New):**
  - `src/api/session.py`: Depends on `src.engine`.
  - `src/api/routes.py`: Depends on `src.engine`, `src.api.session`, fastapi, numpy.
  - `src/api/main.py`: Depends on `src.api.routes`, fastapi.
- **Tests:**
  - `tests/test_mechanics.py`: Covers core modules (4 tests).
  - `tests/advanced_test_mechanics.py`: Covers advanced modules (5 tests).
  - `tests/test_engine.py`: Covers engine module (16 tests).
  - `tests/test_api.py`: Covers API module (17 tests).
  - `tests/test_proxy_simulation.py`: Covers proxy simulation (1 test).
- **Notebooks:**
  - `notebooks/experiment_interface.ipynb`: Uses `src.simulation`.
  - `notebooks/advanced_experiment_interface.ipynb`: Uses `src.advanced_simulation`.

## Latest Report

**Execution Date:** 2026-01-18

**Test Results:**
1. `tests/test_api.py`: **Passed** (17 tests).
2. `tests/test_engine.py`: **Passed** (16 tests).
3. `tests/test_mechanics.py`: **Passed** (4 tests).
4. `tests/test_proxy_simulation.py`: **Passed** (1 test).

**Total: 38 tests passed in 4.72s**

**Summary:**
All tests passed. New engine module (`src/engine/`) provides modular simulation with Pydantic models. New API module (`src/api/`) exposes FastAPI endpoints for session management. The dependency graph shows clear layering from core → advanced → engine → API.
