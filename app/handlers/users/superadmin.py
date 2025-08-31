from aiogram import types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.users import get_user, get_role
from app.database.business import (
    promote_user_to_admin, demote_admin_to_user, get_admin_list, get_all_feedback_list,
    get_all_movie_categories, create_movie_category, update_movie_category, delete_movie_category,
    get_all_system_settings, set_system_setting
)
from app.buttons.users import superadmin_manage_center_kb, superadmin_action_kb, back_to_main_kb
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN

superadmin_router = Router()


@superadmin_router.callback_query(F.data == "superadmin_manage_center")
async def cb_superadmin_manage_center(cb: types.CallbackQuery):
    """管理中心"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    admins = await get_admin_list()
    admin_count = len([a for a in admins if a.role == ROLE_ADMIN])
    
    text = "🛡️ <b>管理中心</b>\n\n"
    text += f"👮 当前管理员数量：{admin_count}\n\n"
    text += "请选择管理操作："
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=superadmin_manage_center_kb
    )
    await cb.answer()


@superadmin_router.callback_query(F.data == "superadmin_add_admin")
async def cb_superadmin_add_admin(cb: types.CallbackQuery, state: FSMContext):
    """添加管理员"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    await cb.message.edit_caption(
        caption="➕ <b>添加管理员</b>\n\n请输入要提升为管理员的用户ID：",
        reply_markup=superadmin_action_kb
    )
    # 保存消息ID用于后续编辑
    await state.update_data(message_id=cb.message.message_id)
    await state.set_state(Wait.waitAdminUserId)
    await cb.answer()


@superadmin_router.message(StateFilter(Wait.waitAdminUserId))
async def process_admin_user_id(msg: types.Message, state: FSMContext):
    """处理管理员用户ID输入"""
    data = await state.get_data()
    message_id = data.get('message_id')
    
    try:
        user_id = int(msg.text.strip())
    except ValueError:
        # 删除用户消息
        try:
            await msg.delete()
        except:
            pass
        
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption="❌ 用户ID必须是数字，请重新输入：",
                reply_markup=superadmin_action_kb
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
        return
    
    # 删除用户消息
    try:
        await msg.delete()
    except:
        pass
    
    # 检查用户是否存在
    user = await get_user(user_id)
    if not user:
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption="❌ 用户不存在，请检查用户ID是否正确：",
                reply_markup=superadmin_action_kb
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
        return
    
    # 检查用户当前角色
    current_role = await get_role(user_id)
    
    if current_role == ROLE_ADMIN:
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption="❌ 该用户已经是管理员了。",
                reply_markup=back_to_main_kb
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
        await state.clear()
        return
    elif current_role == ROLE_SUPERADMIN:
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption="❌ 该用户是超管，无需提升。",
                reply_markup=back_to_main_kb
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
        await state.clear()
        return
    
    # 保存用户ID到状态并显示确认页面
    await state.update_data(target_user_id=user_id)
    
    user_info = f"用户名: @{user.username or '未设置'}\n昵称: {user.full_name}"
    confirm_text = (
        f"👮 <b>确认提升管理员</b>\n\n"
        f"🆔 用户ID：{user_id}\n"
        f"{user_info}\n\n"
        f"确认要将此用户提升为管理员吗？"
    )
    
    confirm_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ 确认提升", callback_data="confirm_promote_admin"),
                types.InlineKeyboardButton(text="❌ 取消操作", callback_data="superadmin_manage_center")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="superadmin_manage_center"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ]
    )
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=confirm_text,
            reply_markup=confirm_kb
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")


@superadmin_router.callback_query(F.data == "superadmin_my_admins")
async def cb_superadmin_my_admins(cb: types.CallbackQuery):
    """我的管理员"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    admins = await get_admin_list()
    admin_users = [a for a in admins if a.role == ROLE_ADMIN]
    
    if not admin_users:
        await cb.message.edit_caption(
            caption="👥 <b>我的管理员</b>\n\n暂无管理员。",
            reply_markup=superadmin_action_kb
        )
    else:
        text = "👥 <b>我的管理员</b>\n\n"
        for i, admin in enumerate(admin_users, 1):
            text += f"{i}. {admin.full_name} (ID: {admin.chat_id})\n"
            text += f"   用户名: @{admin.username or '未设置'}\n"
            text += f"   注册时间: {admin.created_at.strftime('%Y-%m-%d')}\n\n"
        
        text += "💡 使用 /demote [用户ID] 来取消管理员权限"
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=superadmin_action_kb
        )
    
    await cb.answer()


@superadmin_router.callback_query(F.data == "superadmin_manual_reply")
async def cb_superadmin_manual_reply(cb: types.CallbackQuery):
    """人工回复"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    # 获取待处理的反馈
    feedbacks = await get_all_feedback_list()
    pending_feedbacks = [f for f in feedbacks if f.status == "pending"]
    
    text = "🤖 <b>人工回复</b>\n\n"
    
    if not pending_feedbacks:
        text += "暂无待处理的反馈。"
    else:
        text += f"📊 共有 {len(pending_feedbacks)} 条待处理反馈\n\n"
        
        for i, feedback in enumerate(pending_feedbacks[:5], 1):  # 显示前5条
            type_emoji = {
                "bug": "🐛",
                "suggestion": "💡",
                "complaint": "😤",
                "other": "❓"
            }.get(feedback.feedback_type, "❓")
            
            text += f"{i}. {type_emoji} ID:{feedback.id}\n"
            text += f"   用户:{feedback.user_id}\n"
            text += f"   内容:{feedback.content[:60]}{'...' if len(feedback.content) > 60 else ''}\n\n"
        
        if len(pending_feedbacks) > 5:
            text += f"... 还有 {len(pending_feedbacks) - 5} 条待处理\n\n"
        
        text += "💡 使用 /reply [反馈ID] [回复内容] 进行回复"
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=superadmin_action_kb
    )
    await cb.answer()


@superadmin_router.callback_query(F.data == "confirm_promote_admin")
async def cb_confirm_promote_admin(cb: types.CallbackQuery, state: FSMContext):
    """确认提升管理员"""
    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    
    if not target_user_id:
        await cb.answer("❌ 操作失败，请重新尝试", show_alert=True)
        return
    
    # 提升为管理员
    success = await promote_user_to_admin(cb.from_user.id, target_user_id)
    
    if success:
        result_text = f"✅ <b>提升成功！</b>\n\n用户 {target_user_id} 已被提升为管理员。"
        
        # 成功页面按钮
        success_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="➕ 继续添加", callback_data="superadmin_add_admin"),
                    types.InlineKeyboardButton(text="👥 我的管理员", callback_data="superadmin_my_admins")
                ],
                [
                    types.InlineKeyboardButton(text="⬅️ 返回管理中心", callback_data="superadmin_manage_center"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                ]
            ]
        )
        reply_markup = success_kb
    else:
        result_text = "❌ 提升失败，请稍后重试。"
        reply_markup = back_to_main_kb
    
    await cb.message.edit_caption(
        caption=result_text,
        reply_markup=reply_markup
    )
    
    await state.clear()
    await cb.answer()


# 超管命令：取消管理员
@superadmin_router.message(Command("demote"))
async def superadmin_demote_admin(msg: types.Message):
    """取消管理员权限"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可执行此操作")
        return
    
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("用法：/demote [用户ID]")
        return
    
    user_id = int(parts[1])
    
    # 检查目标用户角色
    target_role = await get_role(user_id)
    if target_role != ROLE_ADMIN:
        await msg.reply("❌ 该用户不是管理员")
        return
    
    success = await demote_admin_to_user(msg.from_user.id, user_id)
    
    if success:
        await msg.reply(f"✅ 已取消用户 {user_id} 的管理员权限")
    else:
        await msg.reply("❌ 操作失败，请稍后重试")


# ==================== 类型管理功能 ====================

@superadmin_router.callback_query(F.data == "superadmin_category_manage")
async def cb_superadmin_category_manage(cb: types.CallbackQuery):
    """类型管理主页面"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    categories = await get_all_movie_categories(active_only=False)
    
    text = "📂 <b>类型管理</b>\n\n"
    text += f"📊 当前类型数量：{len(categories)}\n\n"
    
    if categories:
        text += "📋 类型列表：\n"
        for i, category in enumerate(categories[:10], 1):  # 显示前10个
            status = "✅" if category.is_active else "❌"
            text += f"{i}. {status} {category.name}\n"
            text += f"   ID:{category.id} | 创建时间:{category.created_at.strftime('%m-%d %H:%M')}\n\n"
        
        if len(categories) > 10:
            text += f"... 还有 {len(categories) - 10} 个类型\n\n"
    else:
        text += "暂无类型\n\n"
    
    text += "💡 使用命令进行管理：\n"
    text += "/add_category [名称] [描述] - 添加类型\n"
    text += "/edit_category [ID] [名称] [描述] - 编辑类型\n"
    text += "/toggle_category [ID] - 启用/禁用类型\n"
    text += "/delete_category [ID] - 删除类型"
    
    category_manage_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="➕ 添加类型", callback_data="add_category_prompt"),
                types.InlineKeyboardButton(text="🔄 刷新列表", callback_data="superadmin_category_manage")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回管理中心", callback_data="superadmin_manage_center"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=category_manage_kb
    )
    await cb.answer()


@superadmin_router.callback_query(F.data == "add_category_prompt")
async def cb_add_category_prompt(cb: types.CallbackQuery, state: FSMContext):
    """添加类型提示"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    await cb.message.edit_caption(
        caption="➕ <b>添加类型</b>\n\n请输入类型名称：",
        reply_markup=superadmin_action_kb
    )
    
    await state.set_state(Wait.waitCategoryName)
    await cb.answer()


@superadmin_router.message(StateFilter(Wait.waitCategoryName))
async def process_category_name(msg: types.Message, state: FSMContext):
    """处理类型名称输入"""
    category_name = msg.text.strip()
    
    if not category_name:
        await msg.reply("类型名称不能为空，请重新输入：")
        return
    
    # 创建类型
    success = await create_movie_category(
        name=category_name,
        description=f"由超管创建的类型：{category_name}",
        creator_id=msg.from_user.id
    )
    
    if success:
        result_text = f"✅ <b>类型创建成功！</b>\n\n📂 类型名称：{category_name}\n\n类型已添加到系统中。"
    else:
        result_text = "❌ 创建失败，类型名称可能已存在。"
    
    # 删除用户输入的消息
    try:
        await msg.delete()
    except:
        pass
    
    # 发送结果消息
    await msg.answer_photo(
        photo="https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true",
        caption=result_text,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="➕ 继续添加", callback_data="add_category_prompt"),
                    types.InlineKeyboardButton(text="📂 类型管理", callback_data="superadmin_category_manage")
                ],
                [
                    types.InlineKeyboardButton(text="⬅️ 返回管理中心", callback_data="superadmin_manage_center"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                ]
            ]
        )
    )
    
    await state.clear()


# ==================== 系统设置功能 ====================

@superadmin_router.callback_query(F.data == "superadmin_system_settings")
async def cb_superadmin_system_settings(cb: types.CallbackQuery):
    """系统设置主页面"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    settings = await get_all_system_settings()
    
    text = "⚙️ <b>系统设置</b>\n\n"
    text += f"📊 当前设置数量：{len(settings)}\n\n"
    
    if settings:
        text += "📋 主要设置：\n"
        important_keys = [
            "system_enabled", "movie_request_enabled", "content_submit_enabled", 
            "feedback_enabled", "admin_panel_enabled", "superadmin_panel_enabled"
        ]
        
        for setting in settings:
            if setting.setting_key in important_keys:
                status = "✅" if setting.setting_value.lower() in ["true", "1", "yes", "on"] else "❌"
                text += f"{status} {setting.setting_key}: {setting.setting_value}\n"
        
        text += "\n💡 使用命令进行管理：\n"
        text += "/set_setting [键名] [值] - 设置功能开关\n"
        text += "/toggle_feature [功能名] - 快速切换功能\n"
        text += "/view_settings - 查看所有设置"
    else:
        text += "暂无设置\n\n"
        text += "💡 系统将使用默认设置"
    
    settings_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🔄 刷新设置", callback_data="superadmin_system_settings"),
                types.InlineKeyboardButton(text="📋 查看全部", callback_data="view_all_settings")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回管理中心", callback_data="superadmin_manage_center"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=settings_kb
    )
    await cb.answer()


@superadmin_router.callback_query(F.data == "view_all_settings")
async def cb_view_all_settings(cb: types.CallbackQuery):
    """查看所有系统设置"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    settings = await get_all_system_settings()
    
    text = "📋 <b>所有系统设置</b>\n\n"
    
    if settings:
        for i, setting in enumerate(settings[:15], 1):  # 显示前15个
            status = "✅" if setting.is_active else "❌"
            text += f"{i}. {status} {setting.setting_key}\n"
            text += f"   值: {setting.setting_value}\n"
            text += f"   类型: {setting.setting_type}\n"
            if setting.description:
                text += f"   说明: {setting.description}\n"
            text += "\n"
        
        if len(settings) > 15:
            text += f"... 还有 {len(settings) - 15} 个设置\n\n"
    else:
        text += "暂无设置"
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⬅️ 返回设置", callback_data="superadmin_system_settings"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                ]
            ]
        )
    )
    await cb.answer()