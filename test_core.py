"""
核心逻辑自动化测试
运行: python -m pytest test_core.py -v
或:   python -m unittest test_core -v
"""

import tempfile
import os
import shutil
import unittest

# 设置隔离的测试数据目录（必须在 import core 之前）
_test_data_dir = tempfile.mkdtemp()
os.environ['DRAFT_PICKER_DATA_DIR'] = _test_data_dir
os.environ.pop('SIMULATION_START_YEAR', None)

import core
from core import (
    load_draft_weights, save_draft_weights, reset_weights,
    is_all_weights_zero, get_current_year, save_current_year,
    increment_year, PseudoRandomPicker, random_lose_player,
    NBA_TEAMS, POSITIONS,
    EARLIEST_DRAFT_YEAR, LATEST_HISTORICAL_DRAFT_YEAR,
    COOL_DOWN_PERIOD, CURRENT_YEAR_FILE, DRAFT_WEIGHTS_FILE,
)
from main import run_draft

# load_dotenv 可能从 .env 加载了 SIMULATION_START_YEAR，需要移除
os.environ.pop('SIMULATION_START_YEAR', None)


def _clean_data_files():
    for f in [CURRENT_YEAR_FILE, DRAFT_WEIGHTS_FILE]:
        if os.path.exists(f):
            os.remove(f)
    # Also clean settings.json for i18n tests
    settings_file = os.path.join(_test_data_dir, "settings.json")
    if os.path.exists(settings_file):
        os.remove(settings_file)


def _available_years(weights):
    return [y for y, d in weights.items() if d['available'] == 1]


def _unavailable_years(weights):
    return [y for y, d in weights.items() if d['available'] == 0]


class TestYearAvailabilityRule(unittest.TestCase):
    """测试年份可用性规则：近20年窗口 (sim_year-20, sim_year] 内不可用"""

    def setUp(self):
        _clean_data_files()
        os.environ.pop('SIMULATION_START_YEAR', None)

    def tearDown(self):
        _clean_data_files()

    def test_sim_year_2026(self):
        """2026年：1980-2006可用，2007-2025不可用"""
        save_current_year(2026)
        weights = load_draft_weights()

        for year in range(1980, 2007):
            self.assertEqual(weights[year]['available'], 1,
                             f"{year}应可用（<= 2026-20=2006）")
        for year in range(2007, 2026):
            self.assertEqual(weights[year]['available'], 0,
                             f"{year}应不可用（在窗口2007-2026内）")

    def test_sim_year_1995_future_drafts_available(self):
        """1995年：1996-2025可用（未来选秀），1980-1995不可用"""
        save_current_year(1995)
        weights = load_draft_weights()

        for year in range(1980, 1996):
            self.assertEqual(weights[year]['available'], 0,
                             f"{year}应不可用（在窗口1976-1995内）")
        for year in range(1996, 2026):
            self.assertEqual(weights[year]['available'], 1,
                             f"{year}应可用（未来选秀，>{1995}）")

    def test_sim_year_2050_all_available(self):
        """2050年：所有1980-2025都可用（全在窗口之前）"""
        save_current_year(2050)
        weights = load_draft_weights()

        for year in range(1980, 2026):
            self.assertEqual(weights[year]['available'], 1,
                             f"{year}应可用（<= 2050-20=2030）")

    def test_sim_year_2000_boundary(self):
        """2000年：1980可用（边界），1981-2000不可用，2001-2025可用"""
        save_current_year(2000)
        weights = load_draft_weights()

        self.assertEqual(weights[1980]['available'], 1,
                         "1980应可用（2000-1980=20，刚好在边界上）")
        for year in range(1981, 2001):
            self.assertEqual(weights[year]['available'], 0,
                             f"{year}应不可用（在窗口内）")
        for year in range(2001, 2026):
            self.assertEqual(weights[year]['available'], 1,
                             f"{year}应可用（未来选秀）")

    def test_available_count_sim_2026(self):
        """2026年应有27个可用年份（1980-2006）"""
        save_current_year(2026)
        weights = load_draft_weights()
        self.assertEqual(len(_available_years(weights)), 27)

    def test_available_count_sim_1995(self):
        """1995年应有30个可用年份（1996-2025）"""
        save_current_year(1995)
        weights = load_draft_weights()
        self.assertEqual(len(_available_years(weights)), 30)


class TestCooldownAfterUse(unittest.TestCase):
    """测试使用后的冷却期"""

    def setUp(self):
        _clean_data_files()
        os.environ.pop('SIMULATION_START_YEAR', None)

    def tearDown(self):
        _clean_data_files()

    def test_used_year_blocked(self):
        """刚使用的年份不可用"""
        save_current_year(2026)
        weights = load_draft_weights()
        self.assertEqual(weights[1990]['available'], 1)

        weights[1990]['last_used_year'] = 2026
        save_draft_weights(weights)

        weights = load_draft_weights()
        self.assertEqual(weights[1990]['available'], 0)

    def test_cooldown_expires_at_20(self):
        """冷却期满20年后恢复可用"""
        save_current_year(2026)
        weights = load_draft_weights()
        weights[1990]['last_used_year'] = 2026
        save_draft_weights(weights)

        save_current_year(2046)
        weights = load_draft_weights()
        self.assertEqual(weights[1990]['available'], 1,
                         "冷却期满（2046-2026=20），应可用")

    def test_cooldown_not_expired_at_19(self):
        """冷却期未满时仍不可用"""
        save_current_year(2026)
        weights = load_draft_weights()
        weights[1990]['last_used_year'] = 2026
        save_draft_weights(weights)

        save_current_year(2045)
        weights = load_draft_weights()
        self.assertEqual(weights[1990]['available'], 0,
                         "冷却期未满（2045-2026=19<20），应不可用")

    def test_multiple_cooldowns(self):
        """多个年份各自独立冷却"""
        save_current_year(2026)
        weights = load_draft_weights()
        weights[1985]['last_used_year'] = 2026
        weights[1990]['last_used_year'] = 2030
        save_draft_weights(weights)

        save_current_year(2046)
        weights = load_draft_weights()
        self.assertEqual(weights[1985]['available'], 1, "1985冷却期满")
        self.assertEqual(weights[1990]['available'], 0, "1990冷却期未满（2046-2030=16）")


class TestResetWeights(unittest.TestCase):
    """测试重置功能"""

    def setUp(self):
        _clean_data_files()
        os.environ.pop('SIMULATION_START_YEAR', None)

    def tearDown(self):
        _clean_data_files()

    def test_reset_clears_usage(self):
        """重置后清除使用记录"""
        save_current_year(2026)
        weights = load_draft_weights()
        weights[1990]['last_used_year'] = 2026
        weights[1990]['available'] = 0
        save_draft_weights(weights)

        result = reset_weights()
        self.assertIsNone(result[1990]['last_used_year'])
        self.assertEqual(result[1990]['available'], 1)

    def test_reset_recalculates_for_current_year(self):
        """重置后根据当前模拟年份重新计算"""
        save_current_year(1995)
        result = reset_weights()

        for year in range(1980, 1996):
            self.assertEqual(result[year]['available'], 0)
        for year in range(1996, 2026):
            self.assertEqual(result[year]['available'], 1)

    def test_reset_persists_to_file(self):
        """重置结果写入文件"""
        save_current_year(2026)
        reset_weights()

        weights = load_draft_weights()
        self.assertEqual(weights[1990]['available'], 1)
        self.assertIsNone(weights[1990]['last_used_year'])


class TestYearPersistence(unittest.TestCase):
    """测试年份持久化"""

    def setUp(self):
        _clean_data_files()
        os.environ.pop('SIMULATION_START_YEAR', None)

    def tearDown(self):
        _clean_data_files()

    def test_save_and_load(self):
        save_current_year(2030)
        self.assertEqual(get_current_year(), 2030)

    def test_increment(self):
        save_current_year(2026)
        result = increment_year()
        self.assertEqual(result, 2027)
        self.assertEqual(get_current_year(), 2027)

    def test_default_year(self):
        """无文件且无环境变量时返回默认值"""
        year = get_current_year()
        self.assertEqual(year, core.INITIAL_SIMULATION_YEAR)


class TestIsAllWeightsZero(unittest.TestCase):
    def test_all_zero(self):
        weights = {
            1980: {'available': 0, 'last_used_year': 2020},
            1981: {'available': 0, 'last_used_year': 2021},
        }
        self.assertTrue(is_all_weights_zero(weights))

    def test_not_all_zero(self):
        weights = {
            1980: {'available': 1, 'last_used_year': None},
            1981: {'available': 0, 'last_used_year': 2021},
        }
        self.assertFalse(is_all_weights_zero(weights))


class TestPseudoRandomPicker(unittest.TestCase):
    def test_covers_all_items_per_round(self):
        """每轮覆盖所有项"""
        items = ['A', 'B', 'C', 'D']
        picker = PseudoRandomPicker(items)
        round1 = [picker.pick() for _ in range(4)]
        self.assertEqual(sorted(round1), sorted(items))
        round2 = [picker.pick() for _ in range(4)]
        self.assertEqual(sorted(round2), sorted(items))

    def test_single_item(self):
        picker = PseudoRandomPicker(['X'])
        for _ in range(5):
            self.assertEqual(picker.pick(), 'X')

    def test_does_not_modify_original(self):
        items = [1, 2, 3]
        picker = PseudoRandomPicker(items)
        [picker.pick() for _ in range(10)]
        self.assertEqual(items, [1, 2, 3])


class TestRunDraft(unittest.TestCase):
    """测试完整选秀流程"""

    def setUp(self):
        _clean_data_files()
        os.environ.pop('SIMULATION_START_YEAR', None)

    def tearDown(self):
        _clean_data_files()

    def test_draft_increments_year(self):
        save_current_year(2026)
        run_draft()
        self.assertEqual(get_current_year(), 2027)

    def test_draft_marks_one_year_used(self):
        save_current_year(2026)
        run_draft()

        weights = load_draft_weights()
        used = [y for y, d in weights.items() if d['last_used_year'] == 2026]
        self.assertEqual(len(used), 1)

    def test_draft_selects_valid_year(self):
        """选中的年份应在可用范围内"""
        save_current_year(2026)
        run_draft()

        weights = load_draft_weights()
        used = [y for y, d in weights.items() if d['last_used_year'] == 2026]
        self.assertEqual(len(used), 1)
        selected = used[0]
        # 选中的年份应在 1980-2006 范围内（2026年的可用范围）
        self.assertGreaterEqual(selected, 1980)
        self.assertLessEqual(selected, 2006)

    def test_consecutive_drafts(self):
        """连续选秀不会出错"""
        save_current_year(2026)
        for i in range(5):
            run_draft()
        self.assertEqual(get_current_year(), 2031)

        weights = load_draft_weights()
        used_count = sum(1 for d in weights.values() if d['last_used_year'] is not None)
        self.assertEqual(used_count, 5)


class TestRandomLosePlayer(unittest.TestCase):
    def test_returns_valid_team_and_position(self):
        teams = ["Lakers", "Warriors", "Bulls"]
        positions = ["PG", "SG", "SF"]
        tp = PseudoRandomPicker(teams)
        pp = PseudoRandomPicker(positions)

        for _ in range(20):
            team, pos = random_lose_player(tp, pp)
            self.assertIn(team, teams)
            self.assertIn(pos, positions)


class TestWeightsPersistence(unittest.TestCase):
    """测试权重文件的保存和加载"""

    def setUp(self):
        _clean_data_files()
        os.environ.pop('SIMULATION_START_YEAR', None)

    def tearDown(self):
        _clean_data_files()

    def test_save_and_reload_preserves_usage(self):
        save_current_year(2026)
        weights = load_draft_weights()
        weights[1995]['last_used_year'] = 2026
        save_draft_weights(weights)

        reloaded = load_draft_weights()
        self.assertEqual(reloaded[1995]['last_used_year'], 2026)

    def test_load_without_file_creates_defaults(self):
        """无文件时生成默认权重"""
        save_current_year(2026)
        weights = load_draft_weights()
        self.assertIn(1980, weights)
        self.assertIn(2025, weights)
        self.assertEqual(len(weights), LATEST_HISTORICAL_DRAFT_YEAR - EARLIEST_DRAFT_YEAR + 1)


class TestI18n(unittest.TestCase):
    """测试 i18n 模块"""

    def test_all_keys_consistent(self):
        """zh and en should have the same set of keys"""
        from i18n import TRANSLATIONS
        zh_keys = set(TRANSLATIONS["zh"].keys())
        en_keys = set(TRANSLATIONS["en"].keys())
        self.assertEqual(zh_keys, en_keys,
                         f"Missing keys: zh-en={zh_keys-en_keys}, en-zh={en_keys-zh_keys}")

    def test_t_returns_string(self):
        from i18n import t, set_language
        set_language("zh")
        result = t("app_title")
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "app_title")

    def test_t_with_kwargs(self):
        from i18n import t, set_language
        set_language("en")
        result = t("sim_year", year=2026)
        self.assertIn("2026", result)

    def test_t_returns_dict_for_teams(self):
        from i18n import t, set_language
        set_language("zh")
        teams = t("teams")
        self.assertIsInstance(teams, dict)
        self.assertEqual(teams["Lakers"], "湖人")

    def test_language_switch(self):
        from i18n import t, set_language
        set_language("zh")
        zh_title = t("app_title")
        set_language("en")
        en_title = t("app_title")
        self.assertNotEqual(zh_title, en_title)

    def test_teams_coverage(self):
        """All NBA_TEAMS should be in both language team dicts"""
        from i18n import TRANSLATIONS
        for lang in ["zh", "en"]:
            teams = TRANSLATIONS[lang]["teams"]
            for team in NBA_TEAMS:
                self.assertIn(team, teams, f"{team} missing in {lang} teams")

    def test_positions_coverage(self):
        """All POSITIONS should be in both language position dicts"""
        from i18n import TRANSLATIONS
        for lang in ["zh", "en"]:
            positions = TRANSLATIONS[lang]["positions"]
            for pos in POSITIONS:
                self.assertIn(pos, positions, f"{pos} missing in {lang} positions")

    def test_detect_language_env_var(self):
        from i18n import detect_language
        os.environ["DRAFT_PICKER_LANG"] = "en"
        try:
            self.assertEqual(detect_language(), "en")
        finally:
            os.environ.pop("DRAFT_PICKER_LANG", None)

    def test_detect_language_invalid_env(self):
        from i18n import detect_language
        os.environ["DRAFT_PICKER_LANG"] = "fr"
        try:
            # Should fall through to next priority
            lang = detect_language()
            self.assertIn(lang, ["zh", "en"])
        finally:
            os.environ.pop("DRAFT_PICKER_LANG", None)


if __name__ == '__main__':
    unittest.main()
