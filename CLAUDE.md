# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NBA 2K Draft Year Simulator for "Ultimate League" mode. Helps users strategically randomize historical draft year selections across seasons with a 20-year cooldown mechanism to ensure diversity. UI text and comments are in Chinese.

Two interfaces: CLI (`main.py`) and GUI (`gui_main.py`, tkinter-based).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI version
python main.py

# Run GUI version
python gui_main.py

# Run all unit tests
python -m unittest discover

# Run individual test files
python test_year_logic.py
python test_year_progression.py
python test_reset_functions.py

# Run 50-year simulation
python run_simulation.py

# Build Windows executable
build_exe_updated.bat
```

## Architecture

### Core Logic (duplicated in both main.py and gui_main.py)

Both `main.py` and `gui_main.py` contain their own copies of the core logic — they are not shared via a common module. Changes to game rules or data structures must be applied to both files.

Key components in each:
- **Constants**: `EARLIEST_DRAFT_YEAR` (1980), `LATEST_HISTORICAL_DRAFT_YEAR` (2025), `COOL_DOWN_PERIOD` (20), `NUM_PLAYERS_TO_LOSE` (8)
- **`PseudoRandomPicker`**: Shuffled-list picker that cycles through all items before reshuffling, preventing consecutive duplicates
- **`load_draft_weights()`**: Recalculates availability from scratch each load using two rules: (1) draft year must be >= 20 years older than current sim year, (2) if previously used, 20 years must have passed since last usage
- **`run_draft()`**: Selects a year, picks 8 random team/position pairs, updates state, increments sim year

### State & Data

- **`current_year.json`** and **`draft_weights.json`**: Persisted in `LOCALAPPDATA/2KDraftPicker/` (not the repo root), resolved by `get_app_data_dir()`. The `DRAFT_PICKER_DATA_DIR` env var overrides this location.
- **`.env`**: Sets `SIMULATION_START_YEAR` (default 2026). Loaded via `python-dotenv` from both the app data dir and repo root.
- Auto-reset: When all years enter cooldown, `run_draft()` automatically calls `reset_weights()`.

### Testing

- `test_draft_system.py`: Main unit test suite with `unittest`; also contains 50-year simulation functions used by `run_simulation.py`
- `test_year_logic.py`, `test_year_progression.py`, `test_reset_functions.py`: Focused test scripts for specific subsystems
- Tests use `tempfile` directories and mock environment variables to isolate state from production data

### Build

PyInstaller packages `gui_main.py` into a single Windows `.exe` (windowed mode). Build spec: `2KDraftPicker.spec`. Output goes to `dist/`.
