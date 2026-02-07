"""
2K Historical Draft Picker - GUI Version
基于 tkinter 的图形界面版本
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import random
import json
import os
import sys
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
    优先级: current_year.json > 环境变量 SIMULATION_START_YEAR > 默认值.
    修改为文件优先级更高，这样年份可以正常推进
    """
    # 1. 首先尝试从文件读取
    if os.path.exists(CURRENT_YEAR_FILE):
        try:
            with open(CURRENT_YEAR_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                year = data.get('current_year')
                if year is not None:
                    return year
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取年份文件 '{CURRENT_YEAR_FILE}' 出错: {e}. 将尝试环境变量.")

    # 2. 如果文件无效或不存在，尝试从环境变量获取
    start_year_from_env = os.environ.get('SIMULATION_START_YEAR')
    if start_year_from_env:
        try:
            year = int(start_year_from_env)
            # 保存到文件，以便后续使用
            save_current_year(year)
            return year
        except ValueError:
            print(f"环境变量 'SIMULATION_START_YEAR' 的值 '{start_year_from_env}' 不是一个有效的年份. 将忽略.")

    # 3. 如果都不行，使用默认年份并创建文件
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
        # 规则1: 选秀年份不能在当前模拟年份的近20年范围内
        if current_sim_year - COOL_DOWN_PERIOD < year_to_check <= current_sim_year:
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
    except IOError as e:
        print(f"保存权重文件 '{DRAFT_WEIGHTS_FILE}' 出错: {e}")

def reset_weights():
    """重置所有年份的权重和冷却状态."""
    current_sim_year = get_current_year()
    weights = {}
    for year_to_check in range(EARLIEST_DRAFT_YEAR, LATEST_HISTORICAL_DRAFT_YEAR + 1):
        # 选秀年份不能在近20年窗口内
        is_age_eligible = (year_to_check <= current_sim_year - COOL_DOWN_PERIOD or year_to_check > current_sim_year)
        weights[year_to_check] = {
            'available': 1 if is_age_eligible else 0,
            'last_used_year': None  # 重置使用记录
        }
    save_draft_weights(weights)
    return weights

def is_all_weights_zero(weights):
    """检查是否所有权重都为0"""
    return all(data['available'] == 0 for data in weights.values())

def get_team_english_name(chinese_name, team_mapping_dict):
    """根据中文名获取英文名."""
    return team_mapping_dict.get(chinese_name, chinese_name)

# --- GUI Application ---
class DraftApp:
    def __init__(self, root):
        self.root = root
        self.root.title("2K历史选秀年份生成器")
        self.root.geometry("800x600")
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="2K历史选秀年份生成器", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # 状态显示
        self.status_frame = ttk.LabelFrame(main_frame, text="当前状态", padding="10")
        self.status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.year_label = ttk.Label(self.status_frame, text="当前模拟年份: 加载中...")
        self.year_label.grid(row=0, column=0, sticky=tk.W)
        
        self.available_label = ttk.Label(self.status_frame, text="可用年份数量: 加载中...")
        self.available_label.grid(row=1, column=0, sticky=tk.W)
        
        self.cooling_label = ttk.Label(self.status_frame, text="冷却中年份数量: 加载中...")
        self.cooling_label.grid(row=2, column=0, sticky=tk.W)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        # 按钮布局
        self.run_draft_btn = ttk.Button(button_frame, text="进行选秀", 
                                         command=self.run_draft, width=15)
        self.run_draft_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.view_years_btn = ttk.Button(button_frame, text="查看可用年份", 
                                         command=self.view_available_years, width=15)
        self.view_years_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.reset_all_btn = ttk.Button(button_frame, text="重置所有", 
                                        command=self.reset_all, width=15)
        self.reset_all_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.quit_btn = ttk.Button(button_frame, text="退出程序", 
                                   command=self.quit_app, width=15)
        self.quit_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # 结果显示区域
        self.result_frame = ttk.LabelFrame(main_frame, text="选秀结果", padding="10")
        self.result_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建滚动文本框
        self.result_text = scrolledtext.ScrolledText(self.result_frame, 
                                                     height=15, 
                                                     width=70,
                                                     font=('Courier New', 10))
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 年份信息显示
        self.years_frame = ttk.LabelFrame(main_frame, text="年份信息", padding="10")
        self.years_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.years_info = ttk.Label(self.years_frame, text="")
        self.years_info.grid(row=0, column=0, sticky=tk.W)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=1)
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)
        
    def update_display(self):
        """更新显示状态"""
        current_year = get_current_year()
        self.year_label.config(text=f"当前模拟年份: {current_year}")
        
        weights = load_draft_weights()
        available_years = [year for year, data in weights.items() if data['available'] == 1]
        cooling_years = [year for year, data in weights.items() 
                        if data['available'] == 0 and data['last_used_year'] is not None]
        
        self.available_label.config(text=f"可用年份数量: {len(available_years)}")
        self.cooling_label.config(text=f"冷却中年份数量: {len(cooling_years)}")
        
        # 更新年份信息
        if available_years:
            years_text = f"可用年份: {min(available_years)}-{max(available_years)} "
            if len(available_years) <= 10:
                years_text += f"({', '.join(map(str, sorted(available_years)))})"
            else:
                years_text += f"(共{len(available_years)}个年份)"
        else:
            years_text = "没有可用年份"
        
        self.years_info.config(text=years_text)
        
    def run_draft(self):
        """执行选秀流程"""
        try:
            current_sim_year = get_current_year()
            
            draft_weights = load_draft_weights()
            
            if is_all_weights_zero(draft_weights):
                messagebox.showinfo("自动重置", "所有年份都在冷却期或不可用，自动重置所有年份。")
                draft_weights = reset_weights()
            
            available_years = [year for year, data in draft_weights.items() if data['available'] == 1]
            
            if not available_years:
                messagebox.showwarning("没有可用年份", "当前没有可用的选秀年份！")
                return
            
            team_picker = PseudoRandomPicker(NBA_TEAMS)
            position_picker = PseudoRandomPicker(POSITIONS)
            year_picker = PseudoRandomPicker(available_years)
            
            selected_year = year_picker.pick()
            
            # 更新权重
            draft_weights[selected_year]['available'] = 0
            draft_weights[selected_year]['last_used_year'] = current_sim_year
            save_draft_weights(draft_weights)
            
            # 选择球员
            selected_players = []
            for _ in range(NUM_PLAYERS_TO_LOSE):
                team, position = random_lose_player(team_picker, position_picker)
                selected_players.append((team, position))
            
            # 按英文名排序
            selected_players.sort(key=lambda x: get_team_english_name(x[0], TEAM_MAPPING))
            
            # 显示结果
            result_text = f"===== 本次选秀年份 =====\n"
            result_text += f"选中年份: {selected_year}\n\n"
            result_text += f"年份 {selected_year} 已被使用，将进入{COOL_DOWN_PERIOD}年冷却期 "
            result_text += f"（{current_sim_year + COOL_DOWN_PERIOD}年后可再次使用）\n\n"
            
            result_text += f"===== 需要废掉的{NUM_PLAYERS_TO_LOSE}个球员（按球队英文名A-Z排序）=====\n"
            for i, (team, position) in enumerate(selected_players):
                result_text += f"{i+1}. {team} {position} ({get_team_english_name(team, TEAM_MAPPING)})\n"
            
            # 时间推进
            new_sim_year = increment_year()
            result_text += f"\n时间推进到: {new_sim_year}年\n"
            
            # 更新显示区域
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)
            
            # 更新状态显示
            self.update_display()
            
        except Exception as e:
            messagebox.showerror("错误", f"执行选秀时发生错误:\n{str(e)}")
    
    def view_available_years(self):
        """查看可用年份"""
        try:
            weights = load_draft_weights()
            current_sim_year = get_current_year()
            
            available_years = []
            cooling_years = []
            
            for year, data in sorted(weights.items()):
                if data['available'] == 1:
                    available_years.append(str(year))
                elif data['last_used_year'] is not None:
                    remaining_years = COOL_DOWN_PERIOD - (current_sim_year - data['last_used_year'])
                    if remaining_years > 0:
                        cooling_years.append(f"{year}(还需{remaining_years}年)")
            
            result_text = f"当前模拟年份: {current_sim_year}\n\n"
            result_text += "可用年份:\n"
            if available_years:
                result_text += ", ".join(available_years) + "\n"
            else:
                result_text += "没有可用年份\n"
            
            if cooling_years:
                result_text += f"\n冷却中年份 (冷却期: {COOL_DOWN_PERIOD}年):\n"
                result_text += ", ".join(cooling_years) + "\n"
            
            result_text += f"\n共有 {len(available_years)} 个可选年份，{len(cooling_years)} 个冷却中年份"
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)
            
        except Exception as e:
            messagebox.showerror("错误", f"查看年份时发生错误:\n{str(e)}")
    
    def reset_all(self):
        """重置所有 - 完整重置"""
        try:
            current_year = get_current_year()
            default_reset_year = int(os.environ.get('SIMULATION_START_YEAR', INITIAL_SIMULATION_YEAR))

            reset_year = simpledialog.askinteger(
                "设置起始年份",
                f"请输入重置后的起始年份：",
                initialvalue=default_reset_year,
                parent=self.root
            )

            if reset_year is None:
                return

            confirm_message = (
                f"确定要重置所有数据吗？\n\n"
                f"当前状态：\n"
                f"- 模拟年份：{current_year}年\n"
                f"- 重置后将回到：{reset_year}年\n\n"
                f"这将执行以下操作：\n"
                f"1. 重置所有年份权重和冷却状态\n"
                f"2. 清除所有年份的使用记录\n"
                f"3. 将模拟年份重置到{reset_year}年\n"
                f"4. 根据{reset_year}年重新计算可用年份\n\n"
                f"警告：此操作不可撤销！"
            )

            if messagebox.askyesno("确认重置所有数据", confirm_message):
                # 重置权重
                weights = reset_weights()
                
                # 重置年份
                save_current_year(reset_year)
                
                messagebox.showinfo("重置成功", 
                    f"所有数据已重置！\n"
                    f"模拟年份已重置到{reset_year}年。\n"
                    f"年份权重和冷却状态已清除。")
                
                # 更新显示
                self.update_display()
                
                # 显示可用年份
                available_years = [year for year, data in weights.items() if data['available'] == 1]
                
                years_text = f"重置后可用年份 ({reset_year}年):\n"
                if available_years:
                    years_text += ", ".join(map(str, sorted(available_years)))
                else:
                    years_text += "没有可用年份"
                    
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, years_text)
                
        except Exception as e:
            messagebox.showerror("错误", f"重置所有数据时发生错误:\n{str(e)}")
    
    def quit_app(self):
        """退出程序"""
        if messagebox.askyesno("退出", "确定要退出程序吗？"):
            self.root.destroy()

def main():
    root = tk.Tk()
    app = DraftApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
