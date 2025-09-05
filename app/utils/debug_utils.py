from loguru import logger
from typing import Any, Dict, Optional
from aiogram import types
from aiogram.fsm.context import FSMContext
from app.config.debug_config import (
    is_debug_enabled, should_show_feature, get_current_mode, get_debug_config
)
import os
from pathlib import Path

# 初始化文件日志
def _init_file_logging():
    """初始化文件日志配置"""
    config = get_debug_config()
    
    if config.get('log_to_file', False) and config.get('log_file_path'):
        log_file_path = config['log_file_path']
        
        # 确保日志目录存在
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 移除现有的文件处理器（如果有）
        logger.remove()
        
        # 添加控制台输出
        logger.add(
            lambda msg: print(msg, end=""),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
            level="DEBUG"
        )
        
        # 添加文件输出
        logger.add(
            log_file_path,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation=config.get('max_file_size', '10MB'),
            retention=config.get('backup_count', 5),
            compression="zip",
            encoding="utf-8"
        )
        
        logger.info(f"调试文件日志已启用: {log_file_path}")

# 在模块加载时初始化文件日志
_init_file_logging()

def debug_log(message: str, **kwargs):
    """调试日志函数
    
    Args:
        message: 日志消息
        **kwargs: 额外的调试信息
    """
    if is_debug_enabled():
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        log_message = f"🔍 DEBUG [{get_current_mode().upper()}]: {message}"
        if extra_info:
            log_message += f" | {extra_info}"
        logger.debug(log_message)

def debug_message_info(cb: types.CallbackQuery, prefix: str = ""):
    """调试消息信息
    
    Args:
        cb: 回调查询对象
        prefix: 日志前缀
    """
    if is_debug_enabled() and should_show_feature('message_ids'):
        message_id = cb.message.message_id if cb.message else "None"
        chat_id = cb.message.chat.id if cb.message else "None"
        user_id = cb.from_user.id
        callback_data = cb.data
        
        debug_log(
            f"{prefix}消息信息",
            message_id=message_id,
            chat_id=chat_id,
            user_id=user_id,
            callback_data=callback_data
        )

async def debug_state_info(state: FSMContext, prefix: str = ""):
    """调试状态信息
    
    Args:
        state: FSM状态对象
        prefix: 日志前缀
    """
    if is_debug_enabled() and should_show_feature('state_info'):
        try:
            data = await state.get_data()
            current_state = await state.get_state()
            
            # 提取关键信息
            main_message_id = data.get('main_message_id')
            message_id = data.get('message_id')
            sent_media_ids = data.get('sent_media_ids', [])
            review_type = data.get('review_type')
            review_id = data.get('review_id')
            
            debug_log(
                f"{prefix}状态信息",
                current_state=current_state,
                main_message_id=main_message_id,
                message_id=message_id,
                sent_media_count=len(sent_media_ids),
                review_type=review_type,
                review_id=review_id
            )
        except Exception as e:
            debug_log(f"{prefix}状态信息获取失败", error=str(e))

def debug_main_message_tracking(action: str, old_id: Optional[int] = None, new_id: Optional[int] = None, **kwargs):
    """调试主消息ID跟踪
    
    Args:
        action: 操作类型
        old_id: 旧的消息ID
        new_id: 新的消息ID
        **kwargs: 额外信息
    """
    if is_debug_enabled() and should_show_feature('main_message_tracking'):
        debug_info = {
            "action": action,
            "old_main_id": old_id,
            "new_main_id": new_id
        }
        debug_info.update(kwargs)
        
        debug_log("📍 主消息ID跟踪", **debug_info)

def debug_media_message_tracking(action: str, message_ids: list = None, **kwargs):
    """调试媒体消息跟踪
    
    Args:
        action: 操作类型
        message_ids: 消息ID列表
        **kwargs: 额外信息
    """
    if is_debug_enabled() and should_show_feature('media_tracking'):
        debug_info = {
            "action": action,
            "media_count": len(message_ids) if message_ids else 0,
            "media_ids": message_ids[:5] if message_ids else []  # 只显示前5个ID
        }
        debug_info.update(kwargs)
        
        debug_log("📱 媒体消息跟踪", **debug_info)

def debug_review_flow(step: str, **kwargs):
    """调试审核流程
    
    Args:
        step: 流程步骤
        **kwargs: 额外信息
    """
    if is_debug_enabled() and should_show_feature('review_flow'):
        debug_log(f"🔄 审核流程: {step}", **kwargs)

def debug_error(error_type: str, error_msg: str, **kwargs):
    """调试错误信息
    
    Args:
        error_type: 错误类型
        error_msg: 错误消息
        **kwargs: 额外信息
    """
    if is_debug_enabled():  # 错误信息总是显示（如果调试启用）
        debug_info = {
            "error_type": error_type,
            "error_msg": error_msg
        }
        debug_info.update(kwargs)
        
        debug_log("❌ 错误", **debug_info)

def set_debug_mode(mode: str):
    """设置调试模式
    
    Args:
        mode: 调试模式 ('development', 'testing', 'production')
    """
    from app.config.debug_config import set_debug_mode as config_set_debug_mode
    config_set_debug_mode(mode)
    
    # 重新初始化文件日志
    _init_file_logging()
    
    debug_log(f"调试模式已设置为: {mode}")

def get_debug_log_file() -> Optional[str]:
    """获取当前调试日志文件路径
    
    Returns:
        日志文件路径，如果未启用文件日志则返回None
    """
    config = get_debug_config()
    if config.get('log_to_file', False):
        return config.get('log_file_path')
    return None

def enable_file_logging(log_file_path: str = None):
    """启用文件日志
    
    Args:
        log_file_path: 自定义日志文件路径（可选）
    """
    config = get_debug_config()
    if log_file_path:
        config['log_file_path'] = log_file_path
    config['log_to_file'] = True
    
    _init_file_logging()
    debug_log(f"文件日志已启用: {config.get('log_file_path')}")

def disable_file_logging():
    """禁用文件日志"""
    config = get_debug_config()
    config['log_to_file'] = False
    
    # 重新配置为仅控制台输出
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    debug_log("文件日志已禁用")

def get_debug_mode() -> str:
    """获取当前调试模式
    
    Returns:
        当前调试模式
    """
    return get_current_mode()

# 装饰器：自动添加函数调试信息
def debug_function(func_name: str = None):
    """函数调试装饰器
    
    Args:
        func_name: 函数名称（可选）
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if is_debug_enabled() and should_show_feature('function_entry_exit'):
                name = func_name or func.__name__
                debug_log(f"🚀 进入函数: {name}")
                try:
                    result = await func(*args, **kwargs)
                    debug_log(f"✅ 函数完成: {name}")
                    return result
                except Exception as e:
                    debug_error("函数执行错误", str(e), function=name)
                    raise
            else:
                return await func(*args, **kwargs)
        return wrapper
    return decorator