from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from loguru import logger

from app.utils.advanced_browser import (
    AdvancedBrowser, 
    BrowserConfig, 
    TimeField, 
    SortOrder,
    create_browser_for_reviews,
    create_browser_for_feedback,
    create_browser_for_users
)
from app.database.business import (
    get_movie_requests_advanced,
    get_content_submissions_advanced,
    get_user_feedback_advanced,
    get_users_advanced,
    get_admin_actions_advanced
)
from app.utils.filters import HasRole
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN
from app.config import ADMINS_ID, SUPERADMIN_ID

router = Router()

# 创建浏览器实例
request_browser = create_browser_for_reviews(get_movie_requests_advanced)
submission_browser = create_browser_for_reviews(get_content_submissions_advanced)
feedback_browser = create_browser_for_feedback(get_user_feedback_advanced)
user_browser = create_browser_for_users(get_users_advanced)
action_browser = AdvancedBrowser(
    get_admin_actions_advanced,
    BrowserConfig(
        page_size=15,
        sort_field=TimeField.CREATED_AT,
        sort_order=SortOrder.DESC,
        visible_fields=['id', 'action_type', 'description', 'created_at', 'admin_id']
    )
)


@router.message(Command("browse_requests"), HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_ADMIN, ROLE_SUPERADMIN]))
async def browse_requests_command(message: Message):
    """浏览求片请求命令"""
    user_id = str(message.from_user.id)
    
    try:
        # 获取第一页数据
        data = await request_browser.get_page_data(user_id, 1)
        
        # 格式化显示
        text = request_browser.format_page_header(
            "求片请求浏览", 
            data['page_info'], 
            data['config']
        )
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = request_browser.format_item_display(
                item,
                data['config'].visible_fields,
                {
                    'status': lambda x: {'pending': '待审核', 'approved': '已通过', 'rejected': '已拒绝'}.get(x, x),
                    'category_id': lambda x: getattr(item.category, 'name', '未分类') if hasattr(item, 'category') and item.category else '未分类'
                }
            )
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        keyboard = request_browser.create_navigation_keyboard(
            user_id, 
            "browse_requests", 
            data['page_info']
        )
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"浏览求片请求失败: {e}")
        await message.answer("❌ 浏览求片请求失败，请稍后重试")


@router.message(Command("browse_submissions"), HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_ADMIN, ROLE_SUPERADMIN]))
async def browse_submissions_command(message: Message):
    """浏览投稿命令"""
    user_id = str(message.from_user.id)
    
    try:
        # 获取第一页数据
        data = await submission_browser.get_page_data(user_id, 1)
        
        # 格式化显示
        text = submission_browser.format_page_header(
            "投稿内容浏览", 
            data['page_info'], 
            data['config']
        )
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = submission_browser.format_item_display(
                item,
                data['config'].visible_fields,
                {
                    'status': lambda x: {'pending': '待审核', 'approved': '已通过', 'rejected': '已拒绝'}.get(x, x),
                    'category_id': lambda x: getattr(item.category, 'name', '未分类') if hasattr(item, 'category') and item.category else '未分类'
                }
            )
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        keyboard = submission_browser.create_navigation_keyboard(
            user_id, 
            "browse_submissions", 
            data['page_info']
        )
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"浏览投稿失败: {e}")
        await message.answer("❌ 浏览投稿失败，请稍后重试")


@router.message(Command("browse_feedback"), HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_ADMIN, ROLE_SUPERADMIN]))
async def browse_feedback_command(message: Message):
    """浏览反馈命令"""
    user_id = str(message.from_user.id)
    
    try:
        # 获取第一页数据
        data = await feedback_browser.get_page_data(user_id, 1)
        
        # 格式化显示
        text = feedback_browser.format_page_header(
            "用户反馈浏览", 
            data['page_info'], 
            data['config']
        )
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = feedback_browser.format_item_display(
                item,
                data['config'].visible_fields,
                {
                    'status': lambda x: {'pending': '待处理', 'processing': '处理中', 'resolved': '已解决'}.get(x, x),
                    'feedback_type': lambda x: {'bug': '错误报告', 'suggestion': '建议', 'complaint': '投诉', 'other': '其他'}.get(x, x)
                }
            )
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        keyboard = feedback_browser.create_navigation_keyboard(
            user_id, 
            "browse_feedback", 
            data['page_info']
        )
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"浏览反馈失败: {e}")
        await message.answer("❌ 浏览反馈失败，请稍后重试")


@router.message(Command("browse_users"), HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_ADMIN, ROLE_SUPERADMIN]))
async def browse_users_command(message: Message):
    """浏览用户命令"""
    user_id = str(message.from_user.id)
    
    try:
        # 获取第一页数据
        data = await user_browser.get_page_data(user_id, 1)
        
        # 格式化显示
        text = user_browser.format_page_header(
            "用户信息浏览", 
            data['page_info'], 
            data['config']
        )
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = user_browser.format_item_display(
                item,
                data['config'].visible_fields,
                {
                    'role': lambda x: {'user': '普通用户', 'admin': '管理员', 'superadmin': '超级管理员'}.get(x, x)
                }
            )
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        keyboard = user_browser.create_navigation_keyboard(
            user_id, 
            "browse_users", 
            data['page_info']
        )
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"浏览用户失败: {e}")
        await message.answer("❌ 浏览用户失败，请稍后重试")


# ==================== 回调处理器 ====================

@router.callback_query(F.data.startswith("browse_requests_"))
async def handle_requests_browser_callback(callback: CallbackQuery):
    """处理求片浏览回调"""
    await handle_browser_callback(callback, request_browser, "求片请求浏览")


@router.callback_query(F.data.startswith("browse_submissions_"))
async def handle_submissions_browser_callback(callback: CallbackQuery):
    """处理投稿浏览回调"""
    await handle_browser_callback(callback, submission_browser, "投稿内容浏览")


@router.callback_query(F.data.startswith("browse_feedback_"))
async def handle_feedback_browser_callback(callback: CallbackQuery):
    """处理反馈浏览回调"""
    await handle_browser_callback(callback, feedback_browser, "用户反馈浏览")


@router.callback_query(F.data.startswith("browse_users_"))
async def handle_users_browser_callback(callback: CallbackQuery):
    """处理用户浏览回调"""
    await handle_browser_callback(callback, user_browser, "用户信息浏览")


async def handle_browser_callback(callback: CallbackQuery, browser: AdvancedBrowser, title: str):
    """通用浏览器回调处理"""
    user_id = str(callback.from_user.id)
    callback_data = callback.data
    
    try:
        if "_set_page_size" in callback_data:
            # 设置每页条数
            prefix = callback_data.split("_set_page_size")[0]
            keyboard = browser.create_page_size_keyboard(prefix)
            await callback.message.edit_text(
                "📊 选择每页显示条数：",
                reply_markup=keyboard
            )
            await callback.answer()
            return
            
        elif "_page_size_" in callback_data:
            # 设置具体页面大小
            try:
                page_size_str = callback_data.split("_page_size_")[1]
                page_size = int(page_size_str)
                browser.update_config(user_id, page_size=page_size)
                data = await browser.get_page_data(user_id, 1)
            except (ValueError, IndexError) as e:
                logger.error(f"解析页面大小失败: {callback_data}, 错误: {e}")
                await callback.answer("❌ 页面大小设置失败")
                return
            
        elif "_page_" in callback_data:
            # 页面跳转
            try:
                page_str = callback_data.split("_page_")[1]
                page = int(page_str)
                data = await browser.get_page_data(user_id, page)
            except (ValueError, IndexError) as e:
                logger.error(f"解析页面号失败: {callback_data}, 错误: {e}")
                await callback.answer("❌ 页面跳转失败")
                return
            
        elif "_settings" in callback_data:
            # 显示设置
            keyboard = browser.create_settings_keyboard(user_id, callback_data.split("_settings")[0])
            await callback.message.edit_text(
                f"⚙️ {title} - 浏览设置\n\n请选择要修改的设置项：",
                reply_markup=keyboard
            )
            await callback.answer()
            return
            
        elif "_refresh" in callback_data:
            # 刷新当前页
            data = await browser.get_page_data(user_id)
            
        elif "_toggle_sort_order" in callback_data:
            # 切换排序顺序
            state = browser.get_user_state(user_id)
            new_order = SortOrder.DESC if state.config.sort_order == SortOrder.ASC else SortOrder.ASC
            browser.update_config(user_id, sort_order=new_order)
            data = await browser.get_page_data(user_id, 1)
            
        elif "_set_sort_field" in callback_data:
            # 设置排序字段
            prefix = callback_data.split("_set_sort_field")[0]
            keyboard = browser.create_sort_field_keyboard(prefix)
            await callback.message.edit_text(
                "📅 选择排序字段：",
                reply_markup=keyboard
            )
            await callback.answer()
            return
            
        elif "_sort_field_" in callback_data:
            # 设置具体排序字段
            field_value = callback_data.split("_sort_field_")[1]
            field = TimeField(field_value)
            browser.update_config(user_id, sort_field=field)
            data = await browser.get_page_data(user_id, 1)
            
        elif "_set_fields" in callback_data:
            # 设置显示字段
            prefix = callback_data.split("_set_fields")[0]
            state = browser.get_user_state(user_id)
            keyboard = browser.create_visible_fields_keyboard(prefix, state.config.visible_fields)
            await callback.message.edit_text(
                "🏷️ 选择显示字段：",
                reply_markup=keyboard
            )
            await callback.answer()
            return
            
        elif "_toggle_field_" in callback_data:
            # 切换字段显示状态
            field_name = callback_data.split("_toggle_field_")[1]
            state = browser.get_user_state(user_id)
            current_fields = state.config.visible_fields.copy() if state.config.visible_fields else ['id', 'title', 'status', 'created_at']
            
            if field_name in current_fields:
                # 移除字段（但至少保留一个字段）
                if len(current_fields) > 1:
                    current_fields.remove(field_name)
            else:
                # 添加字段
                current_fields.append(field_name)
            
            browser.update_config(user_id, visible_fields=current_fields)
            
            # 更新键盘显示
            prefix = callback_data.split("_toggle_field_")[0]
            keyboard = browser.create_visible_fields_keyboard(prefix, current_fields)
            await callback.message.edit_text(
                "🏷️ 选择显示字段：",
                reply_markup=keyboard
            )
            await callback.answer()
            return
            
        elif "_back_to_" in callback_data:
            # 返回操作
            if "_back_to_browse" in callback_data:
                data = await browser.get_page_data(user_id)
            elif "_back_to_settings" in callback_data:
                prefix = callback_data.split("_back_to_settings")[0]
                keyboard = browser.create_settings_keyboard(user_id, prefix)
                await callback.message.edit_text(
                    f"⚙️ {title} - 浏览设置\n\n请选择要修改的设置项：",
                    reply_markup=keyboard
                )
                await callback.answer()
                return
            else:
                data = await browser.get_page_data(user_id)
        else:
            # 默认刷新
            data = await browser.get_page_data(user_id)
        
        # 更新消息内容
        text = browser.format_page_header(title, data['page_info'], data['config'])
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = browser.format_item_display(item, data['config'].visible_fields)
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        prefix = callback_data.split("_")[0] + "_" + callback_data.split("_")[1]
        keyboard = browser.create_navigation_keyboard(user_id, prefix, data['page_info'])
        
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except Exception as edit_error:
            # 处理消息内容相同的错误
            if "message is not modified" in str(edit_error):
                # 消息内容相同，无需更新，直接回应
                pass
            else:
                # 其他编辑错误，重新抛出
                raise edit_error
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"处理浏览器回调失败: {e}")
        if "message is not modified" in str(e):
            await callback.answer("📄 页面内容无变化")
        else:
            await callback.answer("❌ 操作失败，请稍后重试")