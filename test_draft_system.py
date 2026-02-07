import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch
from main import (
    load_draft_weights, save_draft_weights, reset_weights, 
    is_all_weights_zero, get_current_year, PseudoRandomPicker,
    get_team_english_name, random_lose_player
)
import datetime

class TestDraftSystem(unittest.TestCase):
    
    def setUp(self):
        """每个测试前的准备工作"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        """每个测试后的清理工作"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_load_draft_weights_default(self):
        """测试默认权重加载"""
        weights = load_draft_weights()
        
        # 检查年份范围
        self.assertIn(1980, weights)
        self.assertIn(2025, weights)
        
        # 检查1980-2005年可用，2006-2025年不可用
        for year in range(1980, 2007):
            self.assertEqual(weights[year]['available'], 1, f"年份 {year} 应该可用")
        
        for year in range(2007, 2027):
            self.assertEqual(weights[year]['available'], 0, f"年份 {year} 应该不可用")
    
    def test_save_and_load_weights(self):
        """测试权重保存和加载"""
        test_weights = {
            1995: {'available': 0, 'last_used_year': 2025},
            2000: {'available': 1, 'last_used_year': None}
        }
        
        # 保存权重
        save_draft_weights(test_weights)
        
        # 加载权重
        with open('draft_weights.json', 'r', encoding='utf-8') as f:
            loaded_weights = json.load(f)
        
        self.assertEqual(loaded_weights['1995']['available'], 0)
        self.assertEqual(loaded_weights['1995']['last_used_year'], 2025)
        self.assertEqual(loaded_weights['2000']['available'], 1)
        self.assertIsNone(loaded_weights['2000']['last_used_year'])
    
    def test_reset_weights(self):
        """测试权重重置功能"""
        # 先创建一个有使用记录的权重文件
        test_weights = {
            1995: {'available': 0, 'last_used_year': 2025}
        }
        save_draft_weights(test_weights)
        
        # 重置权重
        reset_weights_result = reset_weights()
        
        # 验证重置后的状态
        self.assertEqual(reset_weights_result[1995]['available'], 1)
        self.assertIsNone(reset_weights_result[1995]['last_used_year'])
    
    def test_is_all_weights_zero(self):
        """测试检查所有权重是否为0的功能"""
        # 全部为0的情况
        all_zero_weights = {
            1980: {'available': 0, 'last_used_year': 2025},
            1981: {'available': 0, 'last_used_year': 2025}
        }
        self.assertTrue(is_all_weights_zero(all_zero_weights))
        
        # 部分为1的情况
        partial_weights = {
            1980: {'available': 1, 'last_used_year': None},
            1981: {'available': 0, 'last_used_year': 2025}
        }
        self.assertFalse(is_all_weights_zero(partial_weights))
    
    def test_pseudo_random_picker(self):
        """测试伪随机选择器"""
        items = ['A', 'B', 'C']
        picker = PseudoRandomPicker(items)
        
        # 测试选择8次，应该包含重复但不会连续重复
        results = []
        for _ in range(8):
            results.append(picker.pick())
        
        # 验证所有项都会被选到
        unique_results = set(results)
        self.assertEqual(len(unique_results), 3)
        
        # 验证结果都在原始列表中
        for result in results:
            self.assertIn(result, items)
    
    def test_team_english_name_mapping(self):
        """测试球队中英文名映射"""
        team_mapping = {
            "湖人": "Lakers",
            "勇士": "Warriors",
            "公牛": "Bulls"
        }
        
        self.assertEqual(get_team_english_name("湖人", team_mapping), "Lakers")
        self.assertEqual(get_team_english_name("勇士", team_mapping), "Warriors")
        self.assertEqual(get_team_english_name("不存在的队", team_mapping), "不存在的队")
    
    def test_random_lose_player(self):
        """测试随机选择球员功能"""
        teams = ["湖人", "勇士", "公牛"]
        positions = ["控球后卫", "得分后卫", "小前锋"]
        
        team_picker = PseudoRandomPicker(teams)
        position_picker = PseudoRandomPicker(positions)
        
        # 测试多次选择
        for _ in range(10):
            team, position = random_lose_player(team_picker, position_picker)
            self.assertIn(team, teams)
            self.assertIn(position, positions)
    
    def test_cooling_period_logic(self):
        """测试冷却期逻辑"""
        # 模拟一个年份在2020年被使用，现在是2025年
        weights = {
            1995: {'available': 0, 'last_used_year': 2020},  # 冷却期5年，还需15年
            1990: {'available': 0, 'last_used_year': 2005},  # 冷却期已过20年
            2000: {'available': 1, 'last_used_year': None}   # 未使用
        }
        
        # 保存到文件
        save_draft_weights(weights)
        
        # 重新加载，应该自动更新冷却状态
        loaded_weights = load_draft_weights()
        
        # 1995年仍在冷却期
        self.assertEqual(loaded_weights[1995]['available'], 0)
        
        # 1990年冷却期已过，应该重新可用
        self.assertEqual(loaded_weights[1990]['available'], 1)
        
        # 2000年保持可用
        self.assertEqual(loaded_weights[2000]['available'], 1)
    
    def test_twenty_year_rule(self):
        """测试20年规则"""
        current_year = get_current_year()  # 2025
        
        weights = load_draft_weights()
        
        # 验证2005年及之前的年份可用
        for year in range(1980, 2007):
            if weights[year]['last_used_year'] is None:
                self.assertEqual(weights[year]['available'], 1, 
                               f"年份 {year} 应该可用（距离当前年份 {current_year - year} 年）")
        
        # 验证2006年及之后的年份不可用
        for year in range(2007, 2027):
            self.assertEqual(weights[year]['available'], 0, 
                           f"年份 {year} 应该不可用（距离当前年份 {current_year - year} 年）")
    
    def test_year_usage_and_cooling(self):
        """测试年份使用和冷却的完整流程"""
        weights = load_draft_weights()
        
        # 使用1995年
        weights[1995]['available'] = 0
        weights[1995]['last_used_year'] = 2025
        
        save_draft_weights(weights)
        
        # 重新加载
        loaded_weights = load_draft_weights()
        
        # 验证1995年进入冷却期
        self.assertEqual(loaded_weights[1995]['available'], 0)
        self.assertEqual(loaded_weights[1995]['last_used_year'], 2025)

def run_integration_test():
    """运行集成测试"""
    print("===== 集成测试开始 =====")
    
    # 测试完整的选秀流程
    weights = load_draft_weights()
    available_years = [year for year, data in weights.items() if data['available'] == 1]
    
    print(f"可用年份数量: {len(available_years)}")
    print(f"可用年份范围: {min(available_years)} - {max(available_years)}")
    
    # 测试球队和位置选择
    teams = ["湖人", "勇士", "公牛"]
    positions = ["控球后卫", "得分后卫"]
    
    team_picker = PseudoRandomPicker(teams)
    position_picker = PseudoRandomPicker(positions)
    
    print("\n测试球员选择:")
    for i in range(5):
        team, position = random_lose_player(team_picker, position_picker)
        print(f"{i+1}. {team} {position}")
    
    print("\n===== 集成测试完成 =====")

def run_fifty_year_simulation():
    """运行50年的选秀模拟测试"""
    print("===== 开始50年选秀模拟测试 =====")
    
    # 球队中英文名映射
    team_mapping = {
        "老鹰": "Hawks",
        "凯尔特人": "Celtics", 
        "篮网": "Nets",
        "黄蜂": "Hornets",
        "公牛": "Bulls",
        "骑士": "Cavaliers",
        "独行侠": "Mavericks",
        "掘金": "Nuggets",
        "活塞": "Pistons",
        "勇士": "Warriors",
        "火箭": "Rockets",
        "步行者": "Pacers",
        "快船": "Clippers",
        "湖人": "Lakers",
        "灰熊": "Grizzlies",
        "热火": "Heat",
        "雄鹿": "Bucks",
        "森林狼": "Timberwolves",
        "鹈鹕": "Pelicans",
        "尼克斯": "Knicks",
        "雷霆": "Thunder",
        "魔术": "Magic",
        "76人": "76ers",
        "太阳": "Suns",
        "开拓者": "Trail Blazers",
        "国王": "Kings",
        "马刺": "Spurs",
        "猛龙": "Raptors",
        "爵士": "Jazz",
        "奇才": "Wizards"
    }
    
    nba_teams = [
        "湖人", "凯尔特人", "勇士", "篮网", "76人",
        "雄鹿", "太阳", "快船", "掘金", "热火",
        "独行侠", "爵士", "尼克斯", "公牛", "老鹰",
        "猛龙", "奇才", "步行者", "黄蜂", "骑士",
        "活塞", "魔术", "雷霆", "国王", "森林狼",
        "鹈鹕", "马刺", "火箭", "灰熊", "开拓者"
    ]
    
    positions = [
        "控球后卫", "得分后卫", "小前锋", "大前锋", "中锋"
    ]
    
    # 重置权重，从干净状态开始
    reset_weights()
    
    simulation_results = []
    year_usage_stats = {}
    
    # 模拟50年
    for simulation_year in range(2026, 2076):
        print(f"\n模拟年份: {simulation_year}")
        
        # 动态更新当前年份（模拟时间推移）
        original_get_current_year = globals()['get_current_year']
        globals()['get_current_year'] = lambda: simulation_year
        
        try:
            # 加载当前权重状态
            draft_weights = load_draft_weights()
            
            # 检查是否所有权重都为0
            if is_all_weights_zero(draft_weights):
                print(f"  年份 {simulation_year}: 所有年份都在冷却期，自动重置")
                draft_weights = reset_weights()
            
            # 获取可用年份
            available_years = [year for year, data in draft_weights.items() if data['available'] == 1]
            
            if not available_years:
                result = {
                    'simulation_year': simulation_year,
                    'status': '无可用年份',
                    'selected_year': None,
                    'available_years_count': 0,
                    'available_years': [],
                    'players': []
                }
            else:
                # 创建选择器
                team_picker = PseudoRandomPicker(nba_teams)
                position_picker = PseudoRandomPicker(positions)
                year_picker = PseudoRandomPicker(available_years)
                
                # 选择年份
                selected_year = year_picker.pick()
                
                # 选择8个球员
                selected_players = []
                for _ in range(8):
                    team, position = random_lose_player(team_picker, position_picker)
                    selected_players.append({
                        'team': team,
                        'position': position,
                        'team_english': get_team_english_name(team, team_mapping)
                    })
                
                # 按英文名排序
                selected_players.sort(key=lambda x: x['team_english'])
                
                # 更新权重（标记为已使用）
                draft_weights[selected_year]['available'] = 0
                draft_weights[selected_year]['last_used_year'] = simulation_year
                save_draft_weights(draft_weights)
                
                # 统计年份使用情况
                if selected_year not in year_usage_stats:
                    year_usage_stats[selected_year] = []
                year_usage_stats[selected_year].append(simulation_year)
                
                result = {
                    'simulation_year': simulation_year,
                    'status': '成功',
                    'selected_year': selected_year,
                    'available_years_count': len(available_years),
                    'available_years': sorted(available_years),
                    'players': selected_players
                }
                
                print(f"  选中年份: {selected_year} (可用年份: {len(available_years)}个)")
        
        except Exception as e:
            result = {
                'simulation_year': simulation_year,
                'status': f'错误: {str(e)}',
                'selected_year': None,
                'available_years_count': 0,
                'available_years': [],
                'players': []
            }
            print(f"  发生错误: {e}")
        
        finally:
            # 恢复原始的get_current_year函数
            globals()['get_current_year'] = original_get_current_year
        
        simulation_results.append(result)
    
    # 保存详细结果到文件
    results_data = {
        'simulation_info': {
            'start_year': 2026,
            'end_year': 2075,
            'total_years': 50,
            'simulation_date': '2025-05-31'
        },
        'year_usage_statistics': year_usage_stats,
        'detailed_results': simulation_results
    }
    
    with open('fifty_year_simulation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    # 生成统计报告
    generate_simulation_report(results_data)
    
    print(f"\n===== 50年模拟测试完成 =====")
    print(f"详细结果已保存到: fifty_year_simulation_results.json")
    print(f"统计报告已保存到: simulation_report.txt")

def create_log_entry(simulation_results, year_usage_stats):
    """创建一个日志条目"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建logs目录
    import os
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 保存详细结果
    log_filename = f'logs/simulation_{timestamp}.json'
    results_data = {
        'simulation_info': {
            'start_year': 2026,
            'end_year': 2075,
            'total_years': 50,
            'simulation_date': datetime.datetime.now().isoformat(),
            'timestamp': timestamp
        },
        'year_usage_statistics': year_usage_stats,
        'detailed_results': simulation_results
    }
    
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    # 创建简短的汇总报告
    summary_filename = f'logs/summary_{timestamp}.txt'
    create_summary_log(summary_filename, results_data)
    
    # 更新主日志索引
    update_log_index(timestamp, log_filename, summary_filename)
    
    return log_filename, summary_filename

def create_summary_log(filename, results_data):
    """创建简短的汇总日志"""
    simulation_results = results_data['detailed_results']
    year_usage_stats = results_data['year_usage_statistics']
    
    lines = []
    lines.append(f"模拟测试汇总报告 - {results_data['simulation_info']['simulation_date']}")
    lines.append("=" * 60)
    
    # 基本统计
    successful_drafts = [r for r in simulation_results if r['status'] == '成功']
    lines.append(f"总模拟年数: 50年")
    lines.append(f"成功选秀: {len(successful_drafts)}次")
    lines.append(f"成功率: {len(successful_drafts)/len(simulation_results)*100:.1f}%")
    lines.append("")
    
    # 年份使用频率
    lines.append("年份使用频率:")
    if year_usage_stats:
        usage_counts = [(year, len(times)) for year, times in year_usage_stats.items()]
        usage_counts.sort(key=lambda x: x[1], reverse=True)
        for year, count in usage_counts[:10]:  # 显示前10个最常用的年份
            lines.append(f"  {year}: {count}次")
    lines.append("")
    
    # 球队统计
    team_counts = {}
    for result in successful_drafts:
        for player in result['players']:
            team = player['team']
            team_counts[team] = team_counts.get(team, 0) + 1
    
    lines.append("球队被选中次数 (前5名):")
    sorted_teams = sorted(team_counts.items(), key=lambda x: x[1], reverse=True)
    for team, count in sorted_teams[:5]:
        lines.append(f"  {team}: {count}次")
    
    lines.append("=" * 60)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def update_log_index(timestamp, log_file, summary_file):
    """更新日志索引文件"""
    index_file = 'logs/log_index.txt'
    
    # 读取现有索引
    entries = []
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            entries = f.readlines()
    
    # 添加新条目
    new_entry = f"{timestamp} | {log_file} | {summary_file}\n"
    entries.append(new_entry)
    
    # 保持最近100条记录
    if len(entries) > 100:
        entries = entries[-100:]
    
    # 写回索引文件
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("时间戳 | 详细日志文件 | 汇总文件\n")
        f.write("=" * 80 + "\n")
        f.writelines(entries)

def run_fifty_year_simulation_with_logging():
    """运行50年模拟测试并记录日志"""
    print("===== 开始50年选秀模拟测试 (带日志记录) =====")
    
    # 球队中英文名映射
    team_mapping = {
        "老鹰": "Hawks", "凯尔特人": "Celtics", "篮网": "Nets", "黄蜂": "Hornets",
        "公牛": "Bulls", "骑士": "Cavaliers", "独行侠": "Mavericks", "掘金": "Nuggets",
        "活塞": "Pistons", "勇士": "Warriors", "火箭": "Rockets", "步行者": "Pacers",
        "快船": "Clippers", "湖人": "Lakers", "灰熊": "Grizzlies", "热火": "Heat",
        "雄鹿": "Bucks", "森林狼": "Timberwolves", "鹈鹕": "Pelicans", "尼克斯": "Knicks",
        "雷霆": "Thunder", "魔术": "Magic", "76人": "76ers", "太阳": "Suns",
        "开拓者": "Trail Blazers", "国王": "Kings", "马刺": "Spurs", "猛龙": "Raptors",
        "爵士": "Jazz", "奇才": "Wizards"
    }
    
    nba_teams = [
        "湖人", "凯尔特人", "勇士", "篮网", "76人", "雄鹿", "太阳", "快船", "掘金", "热火",
        "独行侠", "爵士", "尼克斯", "公牛", "老鹰", "猛龙", "奇才", "步行者", "黄蜂", "骑士",
        "活塞", "魔术", "雷霆", "国王", "森林狼", "鹈鹕", "马刺", "火箭", "灰熊", "开拓者"
    ]
    
    positions = ["控球后卫", "得分后卫", "小前锋", "大前锋", "中锋"]
    
    # 重置权重，从干净状态开始
    reset_weights()
    
    simulation_results = []
    year_usage_stats = {}
    
    # 模拟50年
    for simulation_year in range(2026, 2076):
        print(f"模拟年份: {simulation_year} ({simulation_year-2024}/50)")
        
        # 动态更新当前年份（模拟时间推移）
        original_get_current_year = globals()['get_current_year']
        globals()['get_current_year'] = lambda: simulation_year
        
        try:
            # 加载当前权重状态
            draft_weights = load_draft_weights()
            
            # 获取可用年份
            available_years = [year for year, data in draft_weights.items() if data['available'] == 1]
            
            if not available_years:
                print(f"  年份 {simulation_year}: 没有可用的年份，等待冷却期结束")
                result = {
                    'simulation_year': simulation_year,
                    'status': '无可用年份',
                    'selected_year': None,
                    'available_years_count': 0,
                    'available_years': [],
                    'players': []
                }
            else:
                # 创建选择器
                team_picker = PseudoRandomPicker(nba_teams)
                position_picker = PseudoRandomPicker(positions)
                year_picker = PseudoRandomPicker(available_years)
                
                # 选择年份
                selected_year = year_picker.pick()
                
                # 选择8个球员
                selected_players = []
                for _ in range(8):
                    team, position = random_lose_player(team_picker, position_picker)
                    selected_players.append({
                        'team': team,
                        'position': position,
                        'team_english': get_team_english_name(team, team_mapping)
                    })
                
                # 按英文名排序
                selected_players.sort(key=lambda x: x['team_english'])
                
                # 更新权重（标记为已使用）
                draft_weights[selected_year]['available'] = 0
                draft_weights[selected_year]['last_used_year'] = simulation_year
                save_draft_weights(draft_weights)
                
                # 统计年份使用情况
                if selected_year not in year_usage_stats:
                    year_usage_stats[selected_year] = []
                year_usage_stats[selected_year].append(simulation_year)
                
                result = {
                    'simulation_year': simulation_year,
                    'status': '成功',
                    'selected_year': selected_year,
                    'available_years_count': len(available_years),
                    'available_years': sorted(available_years),
                    'players': selected_players
                }
                
                print(f"  选中年份: {selected_year} (可用年份: {len(available_years)}个)")
        
        except Exception as e:
            result = {
                'simulation_year': simulation_year,
                'status': f'错误: {str(e)}',
                'selected_year': None,
                'available_years_count': 0,
                'available_years': [],
                'players': []
            }
            print(f"  发生错误: {e}")
        
        finally:
            # 恢复原始的get_current_year函数
            globals()['get_current_year'] = original_get_current_year
        
        simulation_results.append(result)
    
    # 创建日志条目
    log_file, summary_file = create_log_entry(simulation_results, year_usage_stats)
    
    print(f"\n===== 50年模拟测试完成 =====")
    print(f"详细日志已保存到: {log_file}")
    print(f"汇总报告已保存到: {summary_file}")
    print(f"日志索引: logs/log_index.txt")
    
    return log_file, summary_file

def view_log_history():
    """查看历史日志记录"""
    index_file = 'logs/log_index.txt'
    
    if not os.path.exists(index_file):
        print("还没有日志记录")
        return
    
    print("\n===== 历史日志记录 =====")
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)

def compare_two_logs(timestamp1, timestamp2):
    """比较两次运行的结果"""
    log1_file = f'logs/simulation_{timestamp1}.json'
    log2_file = f'logs/simulation_{timestamp2}.json'
    
    if not os.path.exists(log1_file) or not os.path.exists(log2_file):
        print("找不到指定的日志文件")
        return
    
    # 读取两个日志文件
    with open(log1_file, 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    
    with open(log2_file, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    
    print(f"\n===== 日志比较: {timestamp1} vs {timestamp2} =====")
    
    # 比较年份使用统计
    stats1 = data1['year_usage_statistics']
    stats2 = data2['year_usage_statistics']
    
    print("年份使用次数对比:")
    all_years = set(stats1.keys()) | set(stats2.keys())
    for year in sorted(all_years):
        count1 = len(stats1.get(year, []))
        count2 = len(stats2.get(year, []))
        if count1 != count2:
            print(f"  {year}: {count1} -> {count2} ({'+'if count2>count1 else ''}{count2-count1})")
    
    # 比较球队统计
    def get_team_stats(data):
        team_counts = {}
        for result in data['detailed_results']:
            if result['status'] == '成功':
                for player in result['players']:
                    team = player['team']
                    team_counts[team] = team_counts.get(team, 0) + 1
        return team_counts
    
    teams1 = get_team_stats(data1)
    teams2 = get_team_stats(data2)
    
    print("\n球队被选中次数变化 (前10名):")
    all_teams = set(teams1.keys()) | set(teams2.keys())
    team_changes = []
    for team in all_teams:
        count1 = teams1.get(team, 0)
        count2 = teams2.get(team, 0)
        if count1 != count2:
            team_changes.append((team, count1, count2, count2-count1))
    
    team_changes.sort(key=lambda x: abs(x[3]), reverse=True)
    for team, count1, count2, diff in team_changes[:10]:
        print(f"  {team}: {count1} -> {count2} ({'+'if diff>0 else ''}{diff})")

# ...existing code...