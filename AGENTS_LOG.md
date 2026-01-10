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
