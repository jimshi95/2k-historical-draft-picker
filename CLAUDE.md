# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NBA 2K Draft Year Simulator for "Ultimate League" mode. Helps users strategically randomize historical draft year selections across seasons with a 20-year cooldown mechanism to ensure diversity. Supports Chinese and English via i18n.

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
python -m unittest test_core -v

# Build Windows executable
build.bat
```

## Architecture

### Module Structure

- **`core.py`** — Shared core logic (single source of truth). Both `main.py` and `gui_main.py` import from here.
- **`i18n.py`** — Internationalization module. Translations dict, language detection, `t()` function.
- **`main.py`** — CLI interface. Imports core + i18n, no duplicated logic.
- **`gui_main.py`** — GUI interface (tkinter). Imports core + i18n, includes language switcher.
- **`test_core.py`** — Unit tests for core logic and i18n.

### Core Logic (`core.py`)

Key components:
- **Constants**: `EARLIEST_DRAFT_YEAR` (1980), `LATEST_HISTORICAL_DRAFT_YEAR` (2025), `COOL_DOWN_PERIOD` (20), `NUM_PLAYERS_TO_LOSE` (8)
- **`NBA_TEAMS`**: English team IDs (e.g., `"Lakers"`, `"Celtics"`). Display names come from `i18n.py`.
- **`POSITIONS`**: Internal IDs (`"PG"`, `"SG"`, `"SF"`, `"PF"`, `"C"`). Display names come from `i18n.py`.
- **`PseudoRandomPicker`**: Shuffled-list picker that cycles through all items before reshuffling
- **`load_draft_weights()`**: Recalculates availability from scratch each load using two rules: (1) draft year must be >= 20 years older than current sim year, (2) if previously used, 20 years must have passed since last usage
- **`get_current_year()`**: Priority: file > env var > default

### i18n (`i18n.py`)

- **`TRANSLATIONS`** dict with `"zh"` and `"en"` keys, including teams/positions display names
- **`detect_language()`**: Priority: `DRAFT_PICKER_LANG` env var > `settings.json` > OS locale > default `zh`
- **`set_language(lang)`**: Switch language and persist to `settings.json`
- **`t(key, **kwargs)`**: Get translated string with `{placeholder}` formatting. Returns dict for `"teams"`/`"positions"` keys.
- To add a new language: add entry to `SUPPORTED_LANGUAGES` and `TRANSLATIONS` dict

### State & Data

- **`current_year.json`** and **`draft_weights.json`**: Persisted in `LOCALAPPDATA/2KDraftPicker/`, resolved by `get_app_data_dir()`. The `DRAFT_PICKER_DATA_DIR` env var overrides this location.
- **`settings.json`**: Language preference, stored in the same data dir.
- **`.env`**: Sets `SIMULATION_START_YEAR` (default 2026). Loaded via `python-dotenv` from both the app data dir and repo root.
- Auto-reset: When all years enter cooldown, `run_draft()` automatically calls `reset_weights()`.

### Testing

- `test_core.py`: Unit tests covering core logic, draft flow, and i18n key consistency
- Tests use `tempfile` directories and mock environment variables to isolate state from production data

### Build

PyInstaller packages `gui_main.py` into a single Windows `.exe` (windowed mode). Build spec: `2KDraftPicker.spec`. Output goes to `dist/`.
