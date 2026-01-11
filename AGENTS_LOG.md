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

### Housekeeping Report (Full Audit)
**Date:** 2026-01-11
**Summary:** Executed full housekeeping protocol.
- **Dependency Network:** Re-mapped imports. Confirmed structure remains consistent with previous reports.
- **Tests:** Ran `python -m pytest`.
  - `tests/test_mechanics.py`: 4/4 Passed.
  - `tests/advanced_test_mechanics.py`: 5/5 Passed.
- **File System Check:** Noted absence of `src/human_proxy_agent.py` and `src/proxy_simulation.py` (mentioned in memories/context) from the current file system.
- **Conclusion:** Core and Advanced components are functional.
