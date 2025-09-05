"""调试配置模块

用于控制调试信息的显示和隐藏
"""

import os
from typing import Dict, Any

# 从环境变量读取调试模式设置，默认为开发模式
DEBUG_MODE = os.getenv('DEBUG_MODE', 'development').lower()

# 调试配置
DEBUG_CONFIG = {
    'development': {
        'enabled': True,
        'log_level': 'DEBUG',
        'show_message_ids': True,
        'show_state_info': True,
        'show_media_tracking': True,
        'show_review_flow': True,
        'show_main_message_tracking': True,
        'show_function_entry_exit': True
    },
    'testing': {
        'enabled': True,
        'log_level': 'INFO',
        'show_message_ids': True,
        'show_state_info': False,
        'show_media_tracking': True,
        'show_review_flow': True,
        'show_main_message_tracking': True,
        'show_function_entry_exit': False
    },
    'production': {
        'enabled': False,
        'log_level': 'WARNING',
        'show_message_ids': False,
        'show_state_info': False,
        'show_media_tracking': False,
        'show_review_flow': False,
        'show_main_message_tracking': False,
        'show_function_entry_exit': False
    }
}

def get_debug_config() -> Dict[str, Any]:
    """获取当前调试配置
    
    Returns:
        当前模式的调试配置
    """
    return DEBUG_CONFIG.get(DEBUG_MODE, DEBUG_CONFIG['development'])

def is_debug_enabled() -> bool:
    """检查调试模式是否启用
    
    Returns:
        是否启用调试模式
    """
    return get_debug_config()['enabled']

def should_show_feature(feature: str) -> bool:
    """检查是否应该显示特定的调试功能
    
    Args:
        feature: 功能名称
        
    Returns:
        是否应该显示该功能
    """
    config = get_debug_config()
    return config.get(f'show_{feature}', False)

def set_debug_mode(mode: str):
    """设置调试模式
    
    Args:
        mode: 调试模式 ('development', 'testing', 'production')
    """
    global DEBUG_MODE
    if mode in DEBUG_CONFIG:
        DEBUG_MODE = mode
        print(f"调试模式已设置为: {mode}")
    else:
        print(f"无效的调试模式: {mode}")
        print(f"可用模式: {list(DEBUG_CONFIG.keys())}")

def get_current_mode() -> str:
    """获取当前调试模式
    
    Returns:
        当前调试模式
    """
    return DEBUG_MODE

# 快捷函数
def enable_debug():
    """启用调试模式"""
    set_debug_mode('development')

def disable_debug():
    """禁用调试模式"""
    set_debug_mode('production')

def set_testing_mode():
    """设置为测试模式"""
    set_debug_mode('testing')

# 打印当前配置（仅在启动时）
if __name__ == "__main__":
    print(f"当前调试模式: {DEBUG_MODE}")
    print(f"调试配置: {get_debug_config()}")