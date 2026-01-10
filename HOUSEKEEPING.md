# Housekeeping Protocol

1. Read the AGENTS.md file.
2. Look at the dependency network of the project, namely which script refers to which one.
3. Proceed doing different sanity checks and unit tests from root scripts to leaves.
4. Add that report to the AGENTS_LOG.md
5. Compile all errors and tests results into a report. And print that report in the Latest Report subsection below, overwriting previous reports.

# Current Project Housekeeping

## Dependency Network

Based on import analysis:
- `src/logging.py`: Imports standard libraries (uuid, json, os, datetime) and numpy.
- `src/analysis.py`: Imports numpy.
- `src/environment.py`: Imports numpy.
- `src/agents.py`: Imports numpy, torch (nn, optim), random, collections.deque.
- `src/simulation.py`: Depends on `src.agents`, `src.environment`, `src.logging`, `src.analysis`, and numpy.
- `tests/test_mechanics.py`: Depends on all `src` modules (`agents`, `environment`, `simulation`, `logging`, `analysis`) and standard libraries/numpy.
- `notebooks/`: Imports `src` modules via `simulation.py` (based on typical usage patterns, confirmed by `simulation.py` dependencies).

## Latest Report

```
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
plugins: anyio-4.12.1
collected 4 items

tests/test_mechanics.py ....                                             [100%]

============================== 4 passed in 2.22s ===============================
```
