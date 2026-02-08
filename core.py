"""
Shared core logic for 2K Draft Picker.
Both main.py (CLI) and gui_main.py (GUI) import from this module.
"""

import random
import json
import os
from pathlib import Path
from dotenv import load_dotenv


def get_app_data_dir() -> Path:
    override = os.environ.get("DRAFT_PICKER_DATA_DIR")
    if override:
        base_dir = Path(override)
    else:
        base_dir = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home())
        base_dir = base_dir / "2KDraftPicker"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


DATA_DIR = get_app_data_dir()
load_dotenv(DATA_DIR / ".env")
load_dotenv()

# --- Constants ---
CURRENT_YEAR_FILE = str(DATA_DIR / "current_year.json")
DRAFT_WEIGHTS_FILE = str(DATA_DIR / "draft_weights.json")
INITIAL_SIMULATION_YEAR = 2026
EARLIEST_DRAFT_YEAR = 1980
LATEST_HISTORICAL_DRAFT_YEAR = 2025
COOL_DOWN_PERIOD = 20
NUM_PLAYERS_TO_LOSE = 8

# Internal IDs — display names are in i18n.py
NBA_TEAMS = [
    "Lakers", "Celtics", "Warriors", "Nets", "76ers", "Bucks", "Suns", "Clippers", "Nuggets", "Heat",
    "Mavericks", "Jazz", "Knicks", "Bulls", "Hawks", "Raptors", "Wizards", "Pacers", "Hornets", "Cavaliers",
    "Pistons", "Magic", "Thunder", "Kings", "Timberwolves", "Pelicans", "Spurs", "Rockets", "Grizzlies", "Trail Blazers"
]
POSITIONS = ["PG", "SG", "SF", "PF", "C"]


# --- Helper Classes ---
class PseudoRandomPicker:
    def __init__(self, items):
        self.original_items = list(items)
        self.items = []
        self.shuffle()
        self.index = 0

    def shuffle(self):
        self.items = list(self.original_items)
        random.shuffle(self.items)
        self.index = 0

    def pick(self):
        if self.index >= len(self.items):
            self.shuffle()
        item = self.items[self.index]
        self.index += 1
        return item


# --- Core Logic Functions ---
def random_lose_player(team_picker, position_picker):
    random_team = team_picker.pick()
    random_position = position_picker.pick()
    return random_team, random_position


def get_current_year():
    """
    获取当前年份.
    优先级: current_year.json > 环境变量 SIMULATION_START_YEAR > 默认值.
    文件优先，这样年份可以正常推进。
    """
    # 1. 首先尝试从文件读取
    if os.path.exists(CURRENT_YEAR_FILE):
        try:
            with open(CURRENT_YEAR_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                year = data.get('current_year')
                if year is not None:
                    return year
        except (json.JSONDecodeError, IOError):
            pass

    # 2. 如果文件无效或不存在，尝试从环境变量获取
    start_year_from_env = os.environ.get('SIMULATION_START_YEAR')
    if start_year_from_env:
        try:
            year = int(start_year_from_env)
            save_current_year(year)
            return year
        except ValueError:
            pass

    # 3. 如果都不行，使用默认年份并创建文件
    save_current_year(INITIAL_SIMULATION_YEAR)
    return INITIAL_SIMULATION_YEAR


def save_current_year(year):
    try:
        with open(CURRENT_YEAR_FILE, 'w', encoding='utf-8') as f:
            json.dump({'current_year': year}, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def increment_year():
    current_year = get_current_year()
    new_year = current_year + 1
    save_current_year(new_year)
    return new_year


def load_draft_weights():
    current_sim_year = get_current_year()
    draft_weights = {}

    raw_loaded_weights = {}
    if os.path.exists(DRAFT_WEIGHTS_FILE):
        try:
            with open(DRAFT_WEIGHTS_FILE, 'r', encoding='utf-8') as f:
                raw_loaded_weights = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    for year_to_check in range(EARLIEST_DRAFT_YEAR, LATEST_HISTORICAL_DRAFT_YEAR + 1):
        year_str = str(year_to_check)
        last_used_sim_year = raw_loaded_weights.get(year_str, {}).get('last_used_year')

        is_available = True
        if current_sim_year - COOL_DOWN_PERIOD < year_to_check <= current_sim_year:
            is_available = False
        elif last_used_sim_year is not None and \
             current_sim_year - last_used_sim_year < COOL_DOWN_PERIOD:
            is_available = False

        draft_weights[year_to_check] = {
            'available': 1 if is_available else 0,
            'last_used_year': last_used_sim_year
        }

    return draft_weights


def save_draft_weights(weights):
    weights_to_save = {str(year): data for year, data in weights.items()}
    try:
        with open(DRAFT_WEIGHTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(weights_to_save, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def reset_weights():
    current_sim_year = get_current_year()
    weights = {}
    for year_to_check in range(EARLIEST_DRAFT_YEAR, LATEST_HISTORICAL_DRAFT_YEAR + 1):
        is_age_eligible = (year_to_check <= current_sim_year - COOL_DOWN_PERIOD or year_to_check > current_sim_year)
        weights[year_to_check] = {
            'available': 1 if is_age_eligible else 0,
            'last_used_year': None
        }
    save_draft_weights(weights)
    return weights


def is_all_weights_zero(weights):
    return all(data['available'] == 0 for data in weights.values())
