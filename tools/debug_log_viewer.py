#!/usr/bin/env python3
"""调试日志查看工具

用于实时查看和分析调试日志文件
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.utils.debug_utils import get_debug_log_file
    from app.config.debug_config import get_current_mode, get_debug_config
except ImportError:
    print("无法导入调试模块，请确保在项目根目录运行此脚本")
    sys.exit(1)

def tail_file(file_path: str, lines: int = 50):
    """显示文件的最后几行
    
    Args:
        file_path: 文件路径
        lines: 显示的行数
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取所有行
            all_lines = f.readlines()
            # 显示最后几行
            for line in all_lines[-lines:]:
                print(line.rstrip())
    except FileNotFoundError:
        print(f"日志文件不存在: {file_path}")
    except Exception as e:
        print(f"读取日志文件失败: {e}")

def follow_file(file_path: str):
    """实时跟踪文件内容（类似tail -f）
    
    Args:
        file_path: 文件路径
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 移动到文件末尾
            f.seek(0, 2)
            
            print(f"正在实时跟踪日志文件: {file_path}")
            print("按 Ctrl+C 停止跟踪")
            print("-" * 80)
            
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.1)
                    
    except FileNotFoundError:
        print(f"日志文件不存在: {file_path}")
    except KeyboardInterrupt:
        print("\n停止跟踪日志文件")
    except Exception as e:
        print(f"跟踪日志文件失败: {e}")

def filter_logs(file_path: str, keyword: str, lines: int = 100):
    """过滤日志内容
    
    Args:
        file_path: 文件路径
        keyword: 过滤关键词
        lines: 最大显示行数
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            count = 0
            for line in f:
                if keyword.lower() in line.lower():
                    print(line.rstrip())
                    count += 1
                    if count >= lines:
                        break
                        
            if count == 0:
                print(f"未找到包含 '{keyword}' 的日志")
            else:
                print(f"\n共找到 {count} 条匹配的日志")
                
    except FileNotFoundError:
        print(f"日志文件不存在: {file_path}")
    except Exception as e:
        print(f"过滤日志失败: {e}")

def show_debug_info():
    """显示当前调试配置信息"""
    print("=== 调试配置信息 ===")
    print(f"当前调试模式: {get_current_mode()}")
    
    config = get_debug_config()
    print(f"调试启用状态: {config.get('enabled', False)}")
    print(f"文件日志启用: {config.get('log_to_file', False)}")
    
    log_file = get_debug_log_file()
    if log_file:
        print(f"日志文件路径: {log_file}")
        
        # 检查文件是否存在
        if os.path.exists(log_file):
            file_size = os.path.getsize(log_file)
            print(f"日志文件大小: {file_size / 1024:.2f} KB")
            print(f"日志文件存在: ✅")
        else:
            print(f"日志文件存在: ❌")
    else:
        print("未配置日志文件")
    
    print("\n=== 调试功能状态 ===")
    features = [
        ('消息ID跟踪', 'message_ids'),
        ('状态信息', 'state_info'),
        ('媒体消息跟踪', 'media_tracking'),
        ('审核流程', 'review_flow'),
        ('主消息跟踪', 'main_message_tracking'),
        ('函数进入/退出', 'function_entry_exit')
    ]
    
    for name, key in features:
        status = "✅" if config.get(f'show_{key}', False) else "❌"
        print(f"{name}: {status}")

def main():
    parser = argparse.ArgumentParser(description='调试日志查看工具')
    parser.add_argument('--file', '-f', help='指定日志文件路径')
    parser.add_argument('--tail', '-t', type=int, default=50, help='显示最后几行（默认50行）')
    parser.add_argument('--follow', action='store_true', help='实时跟踪日志文件')
    parser.add_argument('--filter', help='过滤包含指定关键词的日志')
    parser.add_argument('--info', action='store_true', help='显示调试配置信息')
    
    args = parser.parse_args()
    
    # 显示调试信息
    if args.info:
        show_debug_info()
        return
    
    # 确定日志文件路径
    log_file = args.file or get_debug_log_file()
    
    if not log_file:
        print("错误: 未指定日志文件，且当前配置未启用文件日志")
        print("请使用 --file 参数指定日志文件，或启用调试模式")
        print("\n使用 --info 查看当前调试配置")
        return
    
    print(f"日志文件: {log_file}")
    print(f"调试模式: {get_current_mode()}")
    print("-" * 80)
    
    # 执行相应操作
    if args.follow:
        follow_file(log_file)
    elif args.filter:
        filter_logs(log_file, args.filter, args.tail)
    else:
        tail_file(log_file, args.tail)

if __name__ == '__main__':
    main()