from functools import wraps
from aiogram import types
from aiogram.fsm.context import FSMContext
from typing import Callable, Awaitable, Any
from loguru import logger


def require_admin_permission(feature_key: str = "admin_panel_enabled"):
    """
    管理员权限检查装饰器
    
    Args:
        feature_key: 功能开关键名，默认为 admin_panel_enabled
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[[types.CallbackQuery, FSMContext], Awaitable[Any]]):
        @wraps(func)
        async def wrapper(cb: types.CallbackQuery, state: FSMContext, *args, **kwargs):
            # 检查审核功能开关
            from app.database.business import is_feature_enabled
            from app.database.users import get_role
            from app.utils.roles import ROLE_SUPERADMIN
            
            try:
                role = await get_role(cb.from_user.id)
                # 超管不受功能开关限制，普通管理员需要检查开关
                if role != ROLE_SUPERADMIN and not await is_feature_enabled(feature_key):
                    await cb.answer("❌ 审核功能已关闭", show_alert=True)
                    return
                
                # 权限检查通过，执行原函数
                return await func(cb, state, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"权限检查失败: {e}")
                await cb.answer("❌ 权限检查失败，请稍后重试", show_alert=True)
                return
        
        return wrapper
    return decorator


async def check_admin_permission(
    cb: types.CallbackQuery, 
    feature_key: str = "admin_panel_enabled"
) -> bool:
    """
    检查管理员权限的工具函数
    
    Args:
        cb: 回调查询对象
        feature_key: 功能开关键名
    
    Returns:
        bool: 是否有权限
    """
    try:
        from app.database.business import is_feature_enabled
        from app.database.users import get_role
        from app.utils.roles import ROLE_SUPERADMIN
        
        role = await get_role(cb.from_user.id)
        # 超管不受功能开关限制，普通管理员需要检查开关
        if role != ROLE_SUPERADMIN and not await is_feature_enabled(feature_key):
            await cb.answer("❌ 审核功能已关闭", show_alert=True)
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        await cb.answer("❌ 权限检查失败，请稍后重试", show_alert=True)
        return False


def require_role(required_role: str):
    """
    角色权限检查装饰器
    
    Args:
        required_role: 需要的角色 (user/admin/superadmin)
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[[types.CallbackQuery, FSMContext], Awaitable[Any]]):
        @wraps(func)
        async def wrapper(cb: types.CallbackQuery, state: FSMContext, *args, **kwargs):
            try:
                from app.database.users import get_role
                from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN
                
                user_role = await get_role(cb.from_user.id)
                
                # 角色等级检查
                role_levels = {
                    ROLE_USER: 1,
                    ROLE_ADMIN: 2,
                    ROLE_SUPERADMIN: 3
                }
                
                user_level = role_levels.get(user_role, 0)
                required_level = role_levels.get(required_role, 0)
                
                if user_level < required_level:
                    role_names = {
                        ROLE_USER: "普通用户",
                        ROLE_ADMIN: "管理员",
                        ROLE_SUPERADMIN: "超级管理员"
                    }
                    required_name = role_names.get(required_role, "未知角色")
                    await cb.answer(f"❌ 需要 {required_name} 权限", show_alert=True)
                    return
                
                # 权限检查通过，执行原函数
                return await func(cb, state, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"角色权限检查失败: {e}")
                await cb.answer("❌ 权限检查失败，请稍后重试", show_alert=True)
                return
        
        return wrapper
    return decorator


async def check_user_role(cb: types.CallbackQuery, required_role: str) -> bool:
    """
    检查用户角色的工具函数
    
    Args:
        cb: 回调查询对象
        required_role: 需要的角色
    
    Returns:
        bool: 是否有权限
    """
    try:
        from app.database.users import get_role
        from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN
        
        user_role = await get_role(cb.from_user.id)
        
        # 角色等级检查
        role_levels = {
            ROLE_USER: 1,
            ROLE_ADMIN: 2,
            ROLE_SUPERADMIN: 3
        }
        
        user_level = role_levels.get(user_role, 0)
        required_level = role_levels.get(required_role, 0)
        
        if user_level < required_level:
            role_names = {
                ROLE_USER: "普通用户",
                ROLE_ADMIN: "管理员",
                ROLE_SUPERADMIN: "超级管理员"
            }
            required_name = role_names.get(required_role, "未知角色")
            await cb.answer(f"❌ 需要 {required_name} 权限", show_alert=True)
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"角色权限检查失败: {e}")
        await cb.answer("❌ 权限检查失败，请稍后重试", show_alert=True)
        return False


def require_feature_enabled(feature_key: str):
    """
    功能开关检查装饰器
    
    Args:
        feature_key: 功能开关键名
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[[types.CallbackQuery, FSMContext], Awaitable[Any]]):
        @wraps(func)
        async def wrapper(cb: types.CallbackQuery, state: FSMContext, *args, **kwargs):
            try:
                from app.database.business import is_feature_enabled
                
                if not await is_feature_enabled(feature_key):
                    await cb.answer("❌ 该功能已关闭", show_alert=True)
                    return
                
                # 功能开关检查通过，执行原函数
                return await func(cb, state, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"功能开关检查失败: {e}")
                await cb.answer("❌ 功能检查失败，请稍后重试", show_alert=True)
                return
        
        return wrapper
    return decorator


# 组合装饰器：同时检查角色和功能开关
def require_admin_with_feature(feature_key: str = "admin_panel_enabled"):
    """
    组合装饰器：检查管理员权限和功能开关
    
    Args:
        feature_key: 功能开关键名
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[[types.CallbackQuery, FSMContext], Awaitable[Any]]):
        # 先应用角色检查，再应用功能开关检查
        func = require_role("admin")(func)
        func = require_feature_enabled(feature_key)(func)
        return func
    return decorator