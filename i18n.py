"""
Internationalization (i18n) module for 2K Draft Picker.
Supports Chinese (zh) and English (en). Add new languages by extending TRANSLATIONS.
"""

import json
import os
import locale

from core import DATA_DIR

SETTINGS_FILE = str(DATA_DIR / "settings.json")

SUPPORTED_LANGUAGES = ["zh", "en"]

_current_language = "zh"

TRANSLATIONS = {
    "zh": {
        # 菜单/标题
        "app_title": "2K历史选秀年份生成器",
        "menu_header": "===== 2K选秀年份生成器 (当前模拟年份: {sim_year}) =====",
        "menu_run_draft": "1. 进行选秀",
        "menu_reset_all": "2. 重置所有年份",
        "menu_view_years": "3. 查看可用年份",
        "menu_reset_year": "4. 重置当前年份到{reset_year}",
        "menu_quit": "0. 退出程序",
        "menu_prompt": "请输入您的选择 (0-4): ",
        "press_enter": "\n按回车键继续...",

        # 状态显示
        "status_frame": "当前状态",
        "sim_year": "当前模拟年份: {year}",
        "sim_year_loading": "当前模拟年份: 加载中...",
        "available_count": "可用年份数量: {count}",
        "available_count_loading": "可用年份数量: 加载中...",
        "cooling_count": "冷却中年份数量: {count}",
        "cooling_count_loading": "冷却中年份数量: 加载中...",

        # 按钮
        "btn_run_draft": "进行选秀",
        "btn_view_years": "查看可用年份",
        "btn_reset_all": "重置所有",
        "btn_quit": "退出程序",

        # 选秀结果
        "draft_result_frame": "选秀结果",
        "draft_header": "===== 本次选秀年份 =====",
        "selected_year": "选中年份: {year}",
        "year_used_cooldown": "年份 {year} 已被使用，将进入{cooldown}年冷却期（{available_year}年后可再次使用）",
        "players_header": "===== 需要废掉的{count}个球员（按球队英文名A-Z排序）=====",
        "player_line": "{index}. {team} {position} ({team_en})",
        "time_advance": "\n时间推进到: {year}年",

        # 查看年份
        "years_info_frame": "年份信息",
        "available_years_label": "可用年份: {min}-{max} ({detail})",
        "available_years_count": "共{count}个年份",
        "no_available_years": "没有可用年份",
        "available_label": "可用: ",
        "available_years_header": "可用年份:",
        "cooling_label": "冷却中: ",
        "cooling_years_header": "冷却中年份 (冷却期: {cooldown}年):",
        "cooling_year_item": "{year}(还需{remaining}年)",
        "year_summary": "共有 {available} 个可选年份，{cooling} 个冷却中 (冷却期: {cooldown}年)",
        "year_summary_short": "共有 {available} 个可选年份，{cooling} 个冷却中年份",

        # 重置
        "auto_reset": "所有年份都在冷却期或不可用，自动重置所有年份。",
        "auto_reset_title": "自动重置",
        "no_available_title": "没有可用年份",
        "no_available_msg": "当前没有可用的选秀年份！",
        "reset_success": "所有年份的权重和冷却状态已重置.",
        "reset_year_prompt": "请输入起始年份 (直接回车默认{default_year}): ",
        "invalid_year": "输入的年份无效，操作取消。",
        "year_reset_done": "当前模拟年份已重置到{year}年，所有年份权重已重新计算。",
        "reset_after_years": "重置后可用年份 ({year}年):",

        # GUI 重置对话框
        "reset_dialog_title": "设置起始年份",
        "reset_dialog_prompt": "请输入重置后的起始年份：",
        "confirm_reset_title": "确认重置所有数据",
        "confirm_reset_body": (
            "确定要重置所有数据吗？\n\n"
            "当前状态：\n"
            "- 模拟年份：{current_year}年\n"
            "- 重置后将回到：{reset_year}年\n\n"
            "这将执行以下操作：\n"
            "1. 重置所有年份权重和冷却状态\n"
            "2. 清除所有年份的使用记录\n"
            "3. 将模拟年份重置到{reset_year}年\n"
            "4. 根据{reset_year}年重新计算可用年份\n\n"
            "警告：此操作不可撤销！"
        ),
        "reset_success_title": "重置成功",
        "reset_success_body": (
            "所有数据已重置！\n"
            "模拟年份已重置到{reset_year}年。\n"
            "年份权重和冷却状态已清除。"
        ),

        # 退出
        "quit_title": "退出",
        "quit_confirm": "确定要退出程序吗？",
        "goodbye": "再见!",

        # 错误
        "err_draft": "执行选秀时发生错误:\n{error}",
        "err_draft_title": "错误",
        "err_view_years": "查看年份时发生错误:\n{error}",
        "err_reset": "重置所有数据时发生错误:\n{error}",
        "err_draft_fallback": "错误: {error}",
        "err_draft_auto_reset": "可能由于没有可用年份导致错误，自动重置所有年份状态。",
        "invalid_choice": "无效的选择，请重新输入。",

        # 语言
        "language_label": "语言:",

        # 球队显示名
        "teams": {
            "Lakers": "湖人", "Celtics": "凯尔特人", "Warriors": "勇士", "Nets": "篮网",
            "76ers": "76人", "Bucks": "雄鹿", "Suns": "太阳", "Clippers": "快船",
            "Nuggets": "掘金", "Heat": "热火", "Mavericks": "独行侠", "Jazz": "爵士",
            "Knicks": "尼克斯", "Bulls": "公牛", "Hawks": "老鹰", "Raptors": "猛龙",
            "Wizards": "奇才", "Pacers": "步行者", "Hornets": "黄蜂", "Cavaliers": "骑士",
            "Pistons": "活塞", "Magic": "魔术", "Thunder": "雷霆", "Kings": "国王",
            "Timberwolves": "森林狼", "Pelicans": "鹈鹕", "Spurs": "马刺", "Rockets": "火箭",
            "Grizzlies": "灰熊", "Trail Blazers": "开拓者",
        },

        # 位置显示名
        "positions": {
            "PG": "控球后卫", "SG": "得分后卫", "SF": "小前锋", "PF": "大前锋", "C": "中锋",
        },
    },

    "en": {
        # Menu/Title
        "app_title": "2K Historical Draft Year Picker",
        "menu_header": "===== 2K Draft Picker (Current Sim Year: {sim_year}) =====",
        "menu_run_draft": "1. Run Draft",
        "menu_reset_all": "2. Reset All Years",
        "menu_view_years": "3. View Available Years",
        "menu_reset_year": "4. Reset Year to {reset_year}",
        "menu_quit": "0. Quit",
        "menu_prompt": "Enter your choice (0-4): ",
        "press_enter": "\nPress Enter to continue...",

        # Status
        "status_frame": "Current Status",
        "sim_year": "Current Sim Year: {year}",
        "sim_year_loading": "Current Sim Year: Loading...",
        "available_count": "Available Years: {count}",
        "available_count_loading": "Available Years: Loading...",
        "cooling_count": "Cooling Down: {count}",
        "cooling_count_loading": "Cooling Down: Loading...",

        # Buttons
        "btn_run_draft": "Run Draft",
        "btn_view_years": "View Years",
        "btn_reset_all": "Reset All",
        "btn_quit": "Quit",

        # Draft results
        "draft_result_frame": "Draft Result",
        "draft_header": "===== Draft Year Selected =====",
        "selected_year": "Selected Year: {year}",
        "year_used_cooldown": "Year {year} used, entering {cooldown}-year cooldown (available again after {available_year})",
        "players_header": "===== {count} Players to Lose (sorted by team A-Z) =====",
        "player_line": "{index}. {team} {position}",
        "time_advance": "\nTime advanced to: Year {year}",

        # View years
        "years_info_frame": "Year Info",
        "available_years_label": "Available: {min}-{max} ({detail})",
        "available_years_count": "{count} years total",
        "no_available_years": "No available years",
        "available_label": "Available: ",
        "available_years_header": "Available Years:",
        "cooling_label": "Cooling: ",
        "cooling_years_header": "Cooling Down (cooldown: {cooldown} years):",
        "cooling_year_item": "{year} ({remaining}yr left)",
        "year_summary": "Total: {available} available, {cooling} cooling (cooldown: {cooldown} years)",
        "year_summary_short": "Total: {available} available, {cooling} cooling down",

        # Reset
        "auto_reset": "All years in cooldown or unavailable. Auto-resetting all years.",
        "auto_reset_title": "Auto Reset",
        "no_available_title": "No Available Years",
        "no_available_msg": "No draft years available!",
        "reset_success": "All year weights and cooldown status have been reset.",
        "reset_year_prompt": "Enter start year (press Enter for default {default_year}): ",
        "invalid_year": "Invalid year input. Operation cancelled.",
        "year_reset_done": "Sim year reset to {year}. All year weights recalculated.",
        "reset_after_years": "Available years after reset (Year {year}):",

        # GUI reset dialog
        "reset_dialog_title": "Set Start Year",
        "reset_dialog_prompt": "Enter the start year after reset:",
        "confirm_reset_title": "Confirm Full Reset",
        "confirm_reset_body": (
            "Are you sure you want to reset all data?\n\n"
            "Current status:\n"
            "- Sim Year: {current_year}\n"
            "- Will reset to: {reset_year}\n\n"
            "This will:\n"
            "1. Reset all year weights and cooldown status\n"
            "2. Clear all usage records\n"
            "3. Reset sim year to {reset_year}\n"
            "4. Recalculate available years for {reset_year}\n\n"
            "Warning: This cannot be undone!"
        ),
        "reset_success_title": "Reset Successful",
        "reset_success_body": (
            "All data has been reset!\n"
            "Sim year reset to {reset_year}.\n"
            "Year weights and cooldown status cleared."
        ),

        # Quit
        "quit_title": "Quit",
        "quit_confirm": "Are you sure you want to quit?",
        "goodbye": "Goodbye!",

        # Errors
        "err_draft": "Error during draft:\n{error}",
        "err_draft_title": "Error",
        "err_view_years": "Error viewing years:\n{error}",
        "err_reset": "Error resetting data:\n{error}",
        "err_draft_fallback": "Error: {error}",
        "err_draft_auto_reset": "Error may be caused by no available years. Auto-resetting.",
        "invalid_choice": "Invalid choice. Please try again.",

        # Language
        "language_label": "Lang:",

        # Teams (English display = same as ID)
        "teams": {
            "Lakers": "Lakers", "Celtics": "Celtics", "Warriors": "Warriors", "Nets": "Nets",
            "76ers": "76ers", "Bucks": "Bucks", "Suns": "Suns", "Clippers": "Clippers",
            "Nuggets": "Nuggets", "Heat": "Heat", "Mavericks": "Mavericks", "Jazz": "Jazz",
            "Knicks": "Knicks", "Bulls": "Bulls", "Hawks": "Hawks", "Raptors": "Raptors",
            "Wizards": "Wizards", "Pacers": "Pacers", "Hornets": "Hornets", "Cavaliers": "Cavaliers",
            "Pistons": "Pistons", "Magic": "Magic", "Thunder": "Thunder", "Kings": "Kings",
            "Timberwolves": "Timberwolves", "Pelicans": "Pelicans", "Spurs": "Spurs", "Rockets": "Rockets",
            "Grizzlies": "Grizzlies", "Trail Blazers": "Trail Blazers",
        },

        # Positions
        "positions": {
            "PG": "Point Guard", "SG": "Shooting Guard", "SF": "Small Forward",
            "PF": "Power Forward", "C": "Center",
        },
    },
}


def _load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def detect_language():
    """
    Detect language by priority:
    1. DRAFT_PICKER_LANG env var
    2. settings.json user preference
    3. OS locale
    4. Default: zh
    """
    # 1. Env var
    env_lang = os.environ.get("DRAFT_PICKER_LANG")
    if env_lang and env_lang in SUPPORTED_LANGUAGES:
        return env_lang

    # 2. settings.json
    settings = _load_settings()
    saved_lang = settings.get("language")
    if saved_lang and saved_lang in SUPPORTED_LANGUAGES:
        return saved_lang

    # 3. OS locale
    try:
        os_locale = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
        if os_locale.startswith("zh") or os_locale.startswith("Chinese"):
            return "zh"
        elif os_locale.startswith("en") or os_locale.startswith("English"):
            return "en"
    except Exception:
        pass

    # 4. Default
    return "zh"


def set_language(lang):
    """Set the current language and persist to settings.json."""
    global _current_language
    if lang in SUPPORTED_LANGUAGES:
        _current_language = lang
        settings = _load_settings()
        settings["language"] = lang
        _save_settings(settings)


def get_language():
    """Get the current language code."""
    return _current_language


def t(key, **kwargs):
    """
    Get translated string for the current language.
    Supports {named_placeholder} formatting via kwargs.
    For dict values (teams, positions), returns the dict directly.
    """
    lang_dict = TRANSLATIONS.get(_current_language, TRANSLATIONS["zh"])
    value = lang_dict.get(key)
    if value is None:
        # Fallback to zh
        value = TRANSLATIONS["zh"].get(key, key)
    if isinstance(value, str) and kwargs:
        return value.format(**kwargs)
    return value


# Initialize language on import
_current_language = detect_language()
