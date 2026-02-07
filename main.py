import random
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# --- Constants ---
CURRENT_YEAR_FILE = 'current_year.json'
DRAFT_WEIGHTS_FILE = 'draft_weights.json'
INITIAL_SIMULATION_YEAR = 2026
EARLIEST_DRAFT_YEAR = 1980
# This constant defines the upper limit for years considered in draft_weights.json
# It's not necessarily the current simulation year but the latest historical draft class year
# we might have rules for (e.g. for initial population of draft_weights.json).
# Given the original code, 2025 was used as latest_year in load_draft_weights.
LATEST_HISTORICAL_DRAFT_YEAR = 2025
COOL_DOWN_PERIOD = 20
NUM_PLAYERS_TO_LOSE = 8

TEAM_MAPPING = {
    "老鹰": "Hawks", "凯尔特人": "Celtics", "篮网": "Nets", "黄蜂": "Hornets",
    "公牛": "Bulls", "骑士": "Cavaliers", "独行侠": "Mavericks", "掘金": "Nuggets",
    "活塞": "Pistons", "勇士": "Warriors", "火箭": "Rockets", "步行者": "Pacers",
    "快船": "Clippers", "湖人": "Lakers", "灰熊": "Grizzlies", "热火": "Heat",
    "雄鹿": "Bucks", "森林狼": "Timberwolves", "鹈鹕": "Pelicans", "尼克斯": "Knicks",
    "雷霆": "Thunder", "魔术": "Magic", "76人": "76ers", "太阳": "Suns",
    "开拓者": "Trail Blazers", "国王": "Kings", "马刺": "Spurs", "猛龙": "Raptors",
    "爵士": "Jazz", "奇才": "Wizards"
}

NBA_TEAMS = [
    "湖人", "凯尔特人", "勇士", "篮网", "76人", "雄鹿", "太阳", "快船", "掘金", "热火",
    "独行侠", "爵士", "尼克斯", "公牛", "老鹰", "猛龙", "奇才", "步行者", "黄蜂", "骑士",
    "活塞", "魔术", "雷霆", "国王", "森林狼", "鹈鹕", "马刺", "火箭", "灰熊", "开拓者"
]
POSITIONS = ["控球后卫", "得分后卫", "小前锋", "大前锋", "中锋"]

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
    """随机选择一支球队和一个位置"""
    random_team = team_picker.pick()
    random_position = position_picker.pick()
    return random_team, random_position

def get_current_year():
    """
    获取当前年份.
    优先级: 环境变量 SIMULATION_START_YEAR > current_year.json > 默认值.
    """
    # 1. 尝试从环境变量获取
    start_year_from_env = os.environ.get('SIMULATION_START_YEAR')
    if start_year_from_env:
        try:
            return int(start_year_from_env)
        except ValueError:
            print(f"环境变量 'SIMULATION_START_YEAR' 的值 '{start_year_from_env}' 不是一个有效的年份. 将忽略.")

    # 2. 如果环境变量无效或未设置，尝试从文件读取
    if os.path.exists(CURRENT_YEAR_FILE):
        try:
            with open(CURRENT_YEAR_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('current_year', INITIAL_SIMULATION_YEAR)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取年份文件 '{CURRENT_YEAR_FILE}' 出错: {e}. 返回默认年份 {INITIAL_SIMULATION_YEAR}.")
            return INITIAL_SIMULATION_YEAR

    # 3. 如果文件不存在，创建初始年份文件并返回默认年份
    save_current_year(INITIAL_SIMULATION_YEAR)
    return INITIAL_SIMULATION_YEAR

def save_current_year(year):
    """保存当前年份到文件."""
    try:
        with open(CURRENT_YEAR_FILE, 'w', encoding='utf-8') as f:
            json.dump({'current_year': year}, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"保存年份文件 '{CURRENT_YEAR_FILE}' 出错: {e}")

def increment_year():
    """递增当前年份"""
    current_year = get_current_year()
    new_year = current_year + 1
    save_current_year(new_year)
    return new_year

def load_draft_weights():
    """
    从文件加载选秀年份权重.
    如果文件不存在或无效, 则会根据当前年份和规则生成默认权重.
    始终确保返回的权重对于当前 current_year 是最新的.
    """
    current_sim_year = get_current_year()
    draft_weights = {}
    
    raw_loaded_weights = {}
    if os.path.exists(DRAFT_WEIGHTS_FILE):
        try:
            with open(DRAFT_WEIGHTS_FILE, 'r', encoding='utf-8') as f:
                raw_loaded_weights = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载权重文件 '{DRAFT_WEIGHTS_FILE}' 出错: {e}. 将基于规则重新计算.")
            # 继续执行，以便基于规则填充 draft_weights

    for year_to_check in range(EARLIEST_DRAFT_YEAR, LATEST_HISTORICAL_DRAFT_YEAR + 1):
        year_str = str(year_to_check)
        # 从加载的数据中获取该年份最后使用信息，如果不存在则为 None
        last_used_sim_year = raw_loaded_weights.get(year_str, {}).get('last_used_year')

        is_available = True
        # 规则1: 选秀年份必须至少比当前模拟年份早 COOL_DOWN_PERIOD 年
        if current_sim_year - year_to_check < COOL_DOWN_PERIOD:
            is_available = False
        # 规则 2: 如果使用过，必须已过冷却期
        elif last_used_sim_year is not None and \
             current_sim_year - last_used_sim_year < COOL_DOWN_PERIOD:
            is_available = False
        
        draft_weights[year_to_check] = {
            'available': 1 if is_available else 0,
            'last_used_year': last_used_sim_year
        }
            
    return draft_weights

def save_draft_weights(weights):
    """保存选秀年份权重到文件，年份键将转为字符串."""
    weights_to_save = {str(year): data for year, data in weights.items()}
    try:
        with open(DRAFT_WEIGHTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(weights_to_save, f, ensure_ascii=False, indent=2)
        print(f"权重已保存到 {DRAFT_WEIGHTS_FILE}")
    except IOError as e:
        print(f"保存权重文件 '{DRAFT_WEIGHTS_FILE}' 出错: {e}")

def print_draft_weights(weights):
    """打印当前的选秀年份权重"""
    current_sim_year = get_current_year()
    print(f"\n当前模拟年份: {current_sim_year}")
    print("当前可选的年份:")    
    
    available_years = []
    cooling_years = []
    
    for year, data in sorted(weights.items()):
        if data['available'] == 1:
            available_years.append(str(year))
        elif data['last_used_year'] is not None:
            remaining_years = COOL_DOWN_PERIOD - (current_sim_year - data['last_used_year'])
            if remaining_years > 0:
                cooling_years.append(f"{year}(还需{remaining_years}年)")
    
    if available_years:
        print("可用: " + ", ".join(available_years))
    else:
        print("没有可选的年份")
    
    if cooling_years:
        print("冷却中: " + ", ".join(cooling_years))
    
    print(f"共有 {len(available_years)} 个可选年份，{len(cooling_years)} 个冷却中 (冷却期: {COOL_DOWN_PERIOD}年)")


def reset_weights():
    """重置所有年份的权重和冷却状态."""
    current_sim_year = get_current_year()
    weights = {}
    for year_to_check in range(EARLIEST_DRAFT_YEAR, LATEST_HISTORICAL_DRAFT_YEAR + 1):
        # 年份是否达到基础的可选年龄 (20年规则)
        is_age_eligible = (current_sim_year - year_to_check >= COOL_DOWN_PERIOD)
        weights[year_to_check] = {
            'available': 1 if is_age_eligible else 0,
            'last_used_year': None  # 重置使用记录
        }
    save_draft_weights(weights)
    print("所有年份的权重和冷却状态已重置.")
    return weights

def is_all_weights_zero(weights):
    """检查是否所有权重都为0"""
    return all(data['available'] == 0 for data in weights.values())

def get_team_english_name(chinese_name, team_mapping_dict): # Renamed to avoid conflict
    """根据中文名获取英文名."""
    return team_mapping_dict.get(chinese_name, chinese_name) # Use passed dict

def show_menu():
    """显示主菜单."""
    current_sim_year = get_current_year()
    # 决定重置年份的显示值
    reset_year = os.environ.get('SIMULATION_START_YEAR') or INITIAL_SIMULATION_YEAR
    print(f"\n===== 2K选秀年份生成器 (当前模拟年份: {current_sim_year}) =====")
    print("1. 进行选秀")
    print("2. 重置所有年份")
    print("3. 查看可用年份")
    print(f"4. 重置当前年份到{reset_year}")
    print("0. 退出程序")
    choice = input(f"请输入您的选择 (0-4): ")
    return choice
    

def run_draft(team_map, teams_list, pos_list): # Renamed params
    """执行选秀流程."""
    current_sim_year = get_current_year()
    
    draft_weights = load_draft_weights()
    
    if is_all_weights_zero(draft_weights):
        print("所有年份都在冷却期或不可用，自动重置所有年份。")
        draft_weights = reset_weights()
    
    available_years = [year for year, data in draft_weights.items() if data['available'] == 1]
    
    if not available_years:
        print("没有可用的年份！")
        return
    
    team_picker = PseudoRandomPicker(teams_list)
    position_picker = PseudoRandomPicker(pos_list)
    year_picker = PseudoRandomPicker(available_years)
    
    try:
        selected_year = year_picker.pick()
        print(f"\n===== 本次选秀年份 =====")
        print(f"选中年份: {selected_year}")
        
        draft_weights[selected_year]['available'] = 0
        draft_weights[selected_year]['last_used_year'] = current_sim_year # Use current_sim_year
        print(f"年份 {selected_year} 已被使用，将进入{COOL_DOWN_PERIOD}年冷却期 "
              f"（{current_sim_year + COOL_DOWN_PERIOD}年后可再次使用）") # Use constant
        
        print(f"\n===== 需要废掉的{NUM_PLAYERS_TO_LOSE}个球员（按球队英文名A-Z排序）=====") # Use constant
        selected_players = []
        for _ in range(NUM_PLAYERS_TO_LOSE): # Use constant
            team, position = random_lose_player(team_picker, position_picker)
            selected_players.append((team, position))
        
        selected_players.sort(key=lambda x: get_team_english_name(x[0], team_map)) # Use passed team_map
        
        for i, (team, position) in enumerate(selected_players):
            print(f"{i+1}. {team} {position} ({get_team_english_name(team, team_map)})") # Use passed team_map
        # 正确的注释缩进
        # 保存更新后的权重
        save_draft_weights(draft_weights)
        
        new_sim_year = increment_year()
        print(f"\n时间推进到: {new_sim_year}年")
        
        print_draft_weights(draft_weights)
        
    except ValueError as e: # Should be IndexError if available_years is empty and pick is attempted
        print(f"错误: {e}") # but available_years is checked above.
        print("可能由于没有可用年份导致错误，自动重置所有年份状态。")
        reset_weights()

def main():
    # 使用全局定义的常量
    # team_mapping, nba_teams, positions
    while True:
        choice = show_menu()
        
        if choice == '1':
            run_draft(TEAM_MAPPING, NBA_TEAMS, POSITIONS) # Pass constants
            input("\n按回车键继续...")
        elif choice == '2':
            reset_weights()
            print_draft_weights(load_draft_weights()) # Show updated weights
            input("\n按回车键继续...")
        elif choice == '3':
            print_draft_weights(load_draft_weights())
            input("\n按回车键继续...")
        elif choice == '4':
            # 始终从 get_current_year 的逻辑源头获取重置年份
            reset_year = int(os.environ.get('SIMULATION_START_YEAR', INITIAL_SIMULATION_YEAR))
            save_current_year(reset_year) 
            print(f"当前模拟年份已重置到{reset_year}年.")
            input("\n按回车键继续...")
        elif choice == '0':
            print("再见!")
            sys.exit(0)
        else:
            print("无效的选择，请重新输入。")

if __name__ == '__main__':
    main()
