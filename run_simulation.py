#!/usr/bin/env python3
"""
50年选秀模拟测试运行器
支持日志记录、历史查看和结果比较
"""

import sys
import os
from test_draft_system import (
    run_fifty_year_simulation_with_logging,
    view_log_history, 
    compare_two_logs
)

def show_menu():
    """显示主菜单"""
    print("\n===== 50年选秀模拟测试管理器 =====")
    print("1. 运行新的50年模拟测试 (带日志记录)")
    print("2. 查看历史日志记录")
    print("3. 比较两次测试结果")
    print("4. 查看logs目录")
    print("0. 退出")
    return input("请选择操作 (0-4): ").strip()

def main():
    """主程序"""
    while True:
        choice = show_menu()
        
        if choice == '1':
            print("\n开始运行50年模拟测试...")
            try:
                log_file, summary_file = run_fifty_year_simulation_with_logging()
                print(f"\n[DONE] 测试完成!")
                print(f"📄 详细日志: {log_file}")
                print(f"📋 汇总报告: {summary_file}")
            except Exception as e:
                print(f"[ERROR] 运行过程中出现错误: {e}")
        
        elif choice == '2':
            view_log_history()
        
        elif choice == '3':
            print("\n请输入要比较的两个时间戳 (格式: YYYYMMDD_HHMMSS)")
            timestamp1 = input("第一个时间戳: ").strip()
            timestamp2 = input("第二个时间戳: ").strip()
            
            if timestamp1 and timestamp2:
                compare_two_logs(timestamp1, timestamp2)
            else:
                print("❌ 请输入有效的时间戳")
        
        elif choice == '4':
            if os.path.exists('logs'):
                print("\n===== logs 目录内容 =====")
                files = os.listdir('logs')
                if files:
                    for file in sorted(files):
                        print(f"  {file}")
                else:
                    print("  (目录为空)")
            else:
                print("logs 目录不存在")
        
        elif choice == '0':
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == '__main__':
    main()