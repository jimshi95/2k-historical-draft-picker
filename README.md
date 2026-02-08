# 2K 选秀年份模拟器 / 2K Draft Year Simulator

这是一个用于模拟 NBA 2K 游戏中"终极联盟"模式下，如何策略性地选择历史选秀名单的工具。它可以帮助用户在多个赛季中实现选秀年份的随机化选择，同时通过智能的冷却机制，确保了长周期内的多样性和趣味性。

A tool for NBA 2K's "Ultimate League" mode that helps strategically randomize historical draft year selections across seasons with a 20-year cooldown mechanism for diversity.

## 核心功能 / Core Features

- **智能随机选秀 / Smart Random Draft**: 从可用的历史年份池中（1980-2025年），根据规则随机选择一个选秀年份。
- **20年窗口规则 / 20-Year Window Rule**: 当前模拟年份前20年以内的年份不可选。
- **动态冷却机制 / Dynamic Cooldown**: 已被选中的年份会进入一个20年的冷却期。
- **多语言支持 / i18n**: 支持中文和英文，自动检测系统语言，可手动切换。
- **状态持久化 / State Persistence**:
    - 数据文件存储在 `%LOCALAPPDATA%\2KDraftPicker\` 目录下，可通过环境变量 `DRAFT_PICKER_DATA_DIR` 自定义。
    - 语言偏好保存在 `settings.json` 中。

## 安装指南 / Installation

1.  **克隆代码库**
    ```bash
    git clone <your-repository-url>
    cd <repository-name>
    ```

2.  **创建并激活虚拟环境**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置起始年份 (可选)**
    在项目根目录的 `.env` 文件中设置：
    ```
    SIMULATION_START_YEAR=2026
    ```

## 如何使用 / Usage

### 语言切换 / Language Switching

语言自动检测优先级：
1. 环境变量 `DRAFT_PICKER_LANG` (`zh` 或 `en`)
2. `settings.json` 中保存的用户偏好
3. 操作系统 locale
4. 默认中文

```bash
# 强制英文 / Force English
set DRAFT_PICKER_LANG=en
python main.py

# 强制中文 / Force Chinese
set DRAFT_PICKER_LANG=zh
python main.py
```

GUI 版本可在界面右上角下拉框切换语言。

### 运行 GUI 版本（推荐）

```bash
python gui_main.py
```

或双击 `2KDraftPicker.bat` 启动。

### 运行 CLI 版本

```bash
python main.py
```

## 测试 / Testing

```bash
python -m unittest test_core -v
```

测试覆盖：
- 20年窗口可用性规则
- 使用后冷却期
- 重置功能
- 年份持久化
- 伪随机选择器
- 完整选秀流程
- i18n 翻译 key 一致性、语言切换、球队/位置覆盖

## 构建可执行文件 / Build

```bash
build.bat
```

构建成功后生成 `dist\2KDraftPicker.exe`。

## 项目结构 / Project Structure

```
.
├── core.py             # 共享核心逻辑 / Shared core logic
├── i18n.py             # 国际化模块 / i18n module (zh/en)
├── main.py             # CLI 版本 / CLI interface
├── gui_main.py         # GUI 版本 / GUI interface (tkinter)
├── test_core.py        # 自动化测试 / Unit tests
├── .env                # 环境变量配置 / Environment config
├── requirements.txt    # 项目依赖 / Dependencies
├── build.bat           # 构建脚本 / Build script
└── 2KDraftPicker.bat   # GUI 启动器 / GUI launcher
```
