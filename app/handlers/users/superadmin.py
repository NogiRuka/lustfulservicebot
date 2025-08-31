from aiogram import types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.message_utils import safe_edit_message

from app.utils.states import Wait
from app.database.users import get_user, get_role
from app.database.business import (
    promote_user_to_admin, demote_admin_to_user, get_admin_list, get_all_feedback_list,
    get_all_movie_categories, create_movie_category, update_movie_category, delete_movie_category,
    get_all_system_settings, set_system_setting, is_feature_enabled,
    get_all_dev_changelogs, create_dev_changelog, get_dev_changelog_by_id, update_dev_changelog, delete_dev_changelog
)
from app.buttons.users import superadmin_manage_center_kb, superadmin_action_kb, back_to_main_kb
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN

superadmin_router = Router()


@superadmin_router.callback_query(F.data == "superadmin_manage_center")
async def cb_superadmin_manage_center(cb: types.CallbackQuery):
    """管理中心"""
    # 系统总开关由BotStatusMiddleware统一处理，超管拥有特权访问
    
    if not await is_feature_enabled("superadmin_panel_enabled"):
        await cb.answer("❌ 超管面板已关闭", show_alert=True)
        return
    
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    admins = await get_admin_list()
    admin_count = len([a for a in admins if a.role == ROLE_ADMIN])
    
    text = "🛡️ <b>管理中心</b>\n\n"
    text += f"👮 当前管理员数量：{admin_count}\n\n"
    text += "请选择管理操作："
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=superadmin_manage_center_kb
    )
    await cb.answer()


# ==================== 开发日志管理 ====================

@superadmin_router.callback_query(F.data == "dev_changelog_view")
async def cb_dev_changelog_view(cb: types.CallbackQuery):
    """查看开发日志"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    changelogs = await get_all_dev_changelogs()
    
    if not changelogs:
        text = "📋 <b>开发日志</b>\n\n暂无开发日志记录。\n\n💡 使用 /add_changelog 添加新的开发日志"
    else:
        text = "📋 <b>开发日志</b>\n\n"
        text += f"📊 共有 {len(changelogs)} 条记录\n\n"
        
        for i, log in enumerate(changelogs[:10], 1):  # 显示最新10条
            type_emoji = {
                "update": "🔄",
                "bugfix": "🐛",
                "feature": "✨",
                "hotfix": "🚨"
            }.get(log.changelog_type, "📝")
            
            type_text = {
                "update": "更新",
                "bugfix": "修复",
                "feature": "新功能",
                "hotfix": "热修复"
            }.get(log.changelog_type, "其他")
            
            from app.utils.time_utils import humanize_time
            
            text += f"┌─ {i}. {type_emoji} <b>v{log.version}</b>\n"
            text += f"├ 📝 标题：{log.title}\n"
            text += f"├ 🏷️ 类型：{type_text}\n"
            text += f"└ ⏰ 时间：<i>{humanize_time(log.created_at)}</i>\n\n"
        
        if len(changelogs) > 10:
            text += f"... 还有 {len(changelogs) - 10} 条记录\n\n"
        
        text += "💡 管理命令：\n"
        text += "├ /add_changelog - 添加开发日志\n"
        text += "├ /edit_changelog [ID] - 编辑日志\n"
        text += "└ /del_changelog [ID] - 删除日志"
    
    changelog_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🔄 刷新列表", callback_data="dev_changelog_view"),
                types.InlineKeyboardButton(text="➕ 添加日志", callback_data="dev_changelog_add")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回其他功能", callback_data="other_functions"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ]
    )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=changelog_kb
    )
    await cb.answer()


@superadmin_router.callback_query(F.data == "dev_changelog_add")
async def cb_dev_changelog_add(cb: types.CallbackQuery, state: FSMContext):
    """添加开发日志提示"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    text = (
        "➕ <b>添加开发日志</b>\n\n"
        "请使用以下命令格式添加开发日志：\n\n"
        "<code>/add_changelog [版本] [类型] [标题] [内容]</code>\n\n"
        "📋 <b>参数说明</b>：\n"
        "├ 版本：如 1.0.0, 1.2.3\n"
        "├ 类型：update/bugfix/feature/hotfix\n"
        "├ 标题：简短描述\n"
        "└ 内容：详细说明\n\n"
        "💡 <b>示例</b>：\n"
        "<code>/add_changelog 1.0.1 bugfix 修复登录问题 修复了用户登录时的验证错误</code>"
    )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⬅️ 返回日志列表", callback_data="dev_changelog_view"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                ]
            ]
        )
    )
    await cb.answer()


@superadmin_router.message(Command("add_changelog"))
async def superadmin_add_changelog_cmd(msg: types.Message):
    """添加开发日志命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=4)
    if len(parts) < 5:
        await msg.reply(
            "用法：/add_changelog [版本] [类型] [标题] [内容]\n\n"
            "类型支持：update/bugfix/feature/hotfix\n"
            "示例：/add_changelog 1.0.1 bugfix 修复登录问题 修复了用户登录时的验证错误"
        )
        return
    
    version = parts[1]
    changelog_type = parts[2].lower()
    title = parts[3]
    content = parts[4]
    
    if changelog_type not in ["update", "bugfix", "feature", "hotfix"]:
        await msg.reply("❌ 类型必须是：update/bugfix/feature/hotfix")
        return
    
    success = await create_dev_changelog(version, title, content, changelog_type, msg.from_user.id)
    
    if success:
        await msg.reply(f"✅ 开发日志已添加\n\n📋 版本：{version}\n🏷️ 类型：{changelog_type}\n📝 标题：{title}")
    else:
        await msg.reply("❌ 添加开发日志失败")


@superadmin_router.message(Command("edit_changelog"))
async def superadmin_edit_changelog_cmd(msg: types.Message):
    """编辑开发日志命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=5)
    if len(parts) < 6:
        await msg.reply(
            "用法：/edit_changelog [ID] [版本] [类型] [标题] [内容]\n\n"
            "类型支持：update/bugfix/feature/hotfix\n"
            "示例：/edit_changelog 1 1.0.2 bugfix 修复登录问题 修复了用户登录时的验证错误"
        )
        return
    
    try:
        changelog_id = int(parts[1])
    except ValueError:
        await msg.reply("❌ ID必须是数字")
        return
    
    version = parts[2]
    changelog_type = parts[3].lower()
    title = parts[4]
    content = parts[5]
    
    if changelog_type not in ["update", "bugfix", "feature", "hotfix"]:
        await msg.reply("❌ 类型必须是：update/bugfix/feature/hotfix")
        return
    
    success = await update_dev_changelog(changelog_id, version, title, content, changelog_type)
    
    if success:
        await msg.reply(f"✅ 开发日志已更新\n\n🆔 ID：{changelog_id}\n📋 版本：{version}\n🏷️ 类型：{changelog_type}\n📝 标题：{title}")
    else:
        await msg.reply("❌ 更新开发日志失败，请检查ID是否正确")


@superadmin_router.message(Command("del_changelog"))
async def superadmin_delete_changelog_cmd(msg: types.Message):
    """删除开发日志命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.reply("用法：/del_changelog [ID]\n\n示例：/del_changelog 1")
        return
    
    try:
        changelog_id = int(parts[1])
    except ValueError:
        await msg.reply("❌ ID必须是数字")
        return
    
    # 先获取日志信息用于确认
    changelog = await get_dev_changelog_by_id(changelog_id)
    if not changelog:
        await msg.reply("❌ 找不到指定的开发日志")
        return
    
    success = await delete_dev_changelog(changelog_id)
    
    if success:
        await msg.reply(f"✅ 开发日志已删除\n\n🆔 ID：{changelog_id}\n📋 版本：{changelog.version}\n📝 标题：{changelog.title}")
    else:
        await msg.reply("❌ 删除开发日志失败")


@superadmin_router.callback_query(F.data == "superadmin_add_admin")
async def cb_superadmin_add_admin(cb: types.CallbackQuery, state: FSMContext):
    """添加管理员"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    await safe_edit_message(
        cb.message,
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
        await safe_edit_message(
            cb.message,
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
        
        await safe_edit_message(
            cb.message,
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
        
        text += "💡 使用 /rp [反馈ID] [回复内容] 进行回复"
    
    await safe_edit_message(
        cb.message,
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
    
    await safe_edit_message(
        cb.message,
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


# ==================== 快速操作命令 ====================

@superadmin_router.message(Command("add_category"))
async def superadmin_add_category_cmd(msg: types.Message):
    """添加类型命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.strip().split(maxsplit=2)
    if len(parts) < 2:
        await msg.reply("用法：/add_category [名称] [描述]\n示例：/add_category 科幻片 科幻类型的电影")
        return
    
    name = parts[1]
    description = parts[2] if len(parts) > 2 else f"由超管创建的类型：{name}"
    
    success = await create_movie_category(
        name=name,
        description=description,
        creator_id=msg.from_user.id
    )
    
    if success:
        await msg.reply(f"✅ 成功添加类型：{name}")
    else:
        await msg.reply("❌ 添加失败，类型名称可能已存在")


@superadmin_router.message(Command("edit_category"))
async def superadmin_edit_category_cmd(msg: types.Message):
    """编辑类型命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.strip().split(maxsplit=3)
    if len(parts) < 3:
        await msg.reply("用法：/edit_category [ID] [新名称] [新描述]\n示例：/edit_category 1 动作片 动作类型的电影")
        return
    
    try:
        category_id = int(parts[1])
        name = parts[2]
        description = parts[3] if len(parts) > 3 else None
    except ValueError:
        await msg.reply("❌ 类型ID必须是数字")
        return
    
    success = await update_movie_category(
        category_id=category_id,
        name=name,
        description=description
    )
    
    if success:
        await msg.reply(f"✅ 成功编辑类型 ID:{category_id}")
    else:
        await msg.reply("❌ 编辑失败，请检查类型ID是否正确")


@superadmin_router.message(Command("toggle_category"))
async def superadmin_toggle_category_cmd(msg: types.Message):
    """切换类型状态命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("用法：/toggle_category [ID]\n示例：/toggle_category 1")
        return
    
    category_id = int(parts[1])
    
    # 获取当前状态
    category = await get_movie_category_by_id(category_id)
    if not category:
        await msg.reply("❌ 类型不存在")
        return
    
    new_status = not category.is_active
    success = await update_movie_category(
        category_id=category_id,
        is_active=new_status
    )
    
    if success:
        status_text = "启用" if new_status else "禁用"
        await msg.reply(f"✅ 已{status_text}类型：{category.name}")
    else:
        await msg.reply("❌ 操作失败")


@superadmin_router.message(Command("delete_category"))
async def superadmin_delete_category_cmd(msg: types.Message):
    """删除类型命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("用法：/delete_category [ID]\n示例：/delete_category 1")
        return
    
    category_id = int(parts[1])
    
    # 获取类型信息
    category = await get_movie_category_by_id(category_id)
    if not category:
        await msg.reply("❌ 类型不存在")
        return
    
    success = await delete_movie_category(category_id)
    
    if success:
        await msg.reply(f"✅ 已删除类型：{category.name}")
    else:
        await msg.reply("❌ 删除失败，可能有求片记录关联此类型")


@superadmin_router.message(Command("set_setting"))
async def superadmin_set_setting_cmd(msg: types.Message):
    """设置系统配置命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.strip().split(maxsplit=2)
    if len(parts) != 3:
        await msg.reply("用法：/set_setting [键名] [值]\n示例：/set_setting movie_request_enabled true")
        return
    
    setting_key = parts[1]
    setting_value = parts[2]
    
    success = await set_system_setting(
        setting_key=setting_key,
        setting_value=setting_value,
        updater_id=msg.from_user.id
    )
    
    if success:
        await msg.reply(f"✅ 已设置 {setting_key} = {setting_value}")
    else:
        await msg.reply("❌ 设置失败")


@superadmin_router.message(Command("toggle_feature"))
async def superadmin_toggle_feature_cmd(msg: types.Message):
    """快速切换功能开关命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.strip().split()
    if len(parts) != 2:
        await msg.reply("用法：/toggle_feature [功能名]\n示例：/toggle_feature movie_request_enabled")
        return
    
    feature_key = parts[1]
    
    # 获取当前状态
    current_value = await get_system_setting(feature_key, "false")
    new_value = "false" if current_value.lower() in ["true", "1", "yes", "on"] else "true"
    
    success = await set_system_setting(
        setting_key=feature_key,
        setting_value=new_value,
        updater_id=msg.from_user.id
    )
    
    if success:
        status_text = "启用" if new_value == "true" else "禁用"
        await msg.reply(f"✅ 已{status_text}功能：{feature_key}")
    else:
        await msg.reply("❌ 切换失败")


@superadmin_router.message(Command("view_settings"))
async def superadmin_view_settings_cmd(msg: types.Message):
    """查看所有设置命令"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    settings = await get_all_system_settings()
    
    if not settings:
        await msg.reply("暂无系统设置")
        return
    
    text = "⚙️ <b>系统设置列表</b>\n\n"
    
    for i, setting in enumerate(settings[:20], 1):  # 显示前20个
        status = "✅" if setting.is_active else "❌"
        text += f"{i}. {status} {setting.setting_key}: {setting.setting_value}\n"
    
    if len(settings) > 20:
        text += f"\n... 还有 {len(settings) - 20} 个设置"
    
    await msg.reply(text, parse_mode="HTML")


# ==================== 类型管理功能 ====================

@superadmin_router.callback_query(F.data == "superadmin_category_manage")
async def cb_superadmin_category_manage(cb: types.CallbackQuery):
    """类型管理主页面"""
    await cb_superadmin_category_manage_page(cb, 1)


@superadmin_router.callback_query(F.data.startswith("category_manage_page_"))
async def cb_superadmin_category_manage_page(cb: types.CallbackQuery, page: int = None):
    """类型管理分页"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    # 提取页码
    if page is None:
        page = extract_page_from_callback(cb.data, "category_manage")
    
    categories = await get_all_movie_categories(active_only=False)
    paginator = Paginator(categories, page_size=5)
    page_info = paginator.get_page_info(page)
    page_items = paginator.get_page_items(page)
    
    # 构建页面内容
    text = format_page_header("📂 <b>类型管理</b>", page_info)
    
    if page_items:
        text += "📋 类型列表：\n"
        start_num = (page - 1) * paginator.page_size + 1
        for i, category in enumerate(page_items, start_num):
            status = "✅" if category.is_active else "❌"
            text += f"{i}. {status} {category.name}\n"
            text += f"   ID:{category.id} | 创建:{category.created_at.strftime('%m-%d %H:%M')}\n"
            text += f"   /edit_category {category.id} | /toggle_category {category.id}\n\n"
    
    text += "💡 快速命令：\n"
    text += "/add_category [名称] [描述] - 添加类型\n"
    text += "/delete_category [ID] - 删除类型"
    
    # 创建分页键盘
    extra_buttons = [
        [
            types.InlineKeyboardButton(text="➕ 添加类型", callback_data="add_category_prompt"),
            types.InlineKeyboardButton(text="🔄 刷新", callback_data="superadmin_category_manage")
        ],
        [
            types.InlineKeyboardButton(text="⬅️ 返回管理中心", callback_data="superadmin_manage_center"),
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
        ]
    ]
    
    keyboard = paginator.create_pagination_keyboard(
        page, "category_manage", extra_buttons
    )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=keyboard
    )
    await cb.answer()


@superadmin_router.callback_query(F.data == "add_category_prompt")
async def cb_add_category_prompt(cb: types.CallbackQuery, state: FSMContext):
    """添加类型提示"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    await safe_edit_message(
        cb.message,
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
    
    text = "⚙️ <b>系统设置中心</b> ⚙️\n\n"
    text += f"📊 <b>设置概览</b>：共 {len(settings)} 项配置\n\n"
    
    if settings:
        text += "🔧 <b>核心功能开关</b>\n"
        important_keys = {
            "bot_enabled": "🤖 机器人总开关",
            "system_enabled": "🌐 系统总开关", 
            "movie_request_enabled": "🎬 求片功能", 
            "content_submit_enabled": "📝 投稿功能",
            "feedback_enabled": "💬 反馈功能", 
            "admin_panel_enabled": "👮 管理面板", 
            "superadmin_panel_enabled": "🛡️ 超管面板"
        }
        
        for setting in settings:
            if setting.setting_key in important_keys:
                status = "✅ 启用" if setting.setting_value.lower() in ["true", "1", "yes", "on"] else "❌ 禁用"
                name = important_keys[setting.setting_key]
                text += f"├ {name}：{status}\n"
        
        text += "\n💡 <b>管理命令</b>：\n"
        text += "├ /set_setting [键名] [值] - 设置功能开关\n"
        text += "├ /toggle_feature [功能名] - 快速切换功能\n"
        text += "└ /view_settings - 查看所有设置"
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
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=settings_kb
    )
    await cb.answer()


@superadmin_router.callback_query(F.data == "view_all_settings")
async def cb_view_all_settings(cb: types.CallbackQuery):
    """查看所有系统设置"""
    await cb_view_all_settings_page(cb, 1)


@superadmin_router.callback_query(F.data.startswith("settings_page_"))
async def cb_view_all_settings_page(cb: types.CallbackQuery, page: int = None):
    """系统设置分页"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    # 提取页码
    if page is None:
        page = extract_page_from_callback(cb.data, "settings")
    
    settings = await get_all_system_settings()
    paginator = Paginator(settings, page_size=8)
    page_info = paginator.get_page_info(page)
    page_items = paginator.get_page_items(page)
    
    # 构建页面内容
    text = format_page_header("📋 <b>所有系统设置</b>", page_info)
    
    if page_items:
        start_num = (page - 1) * paginator.page_size + 1
        for i, setting in enumerate(page_items, start_num):
            status = "✅" if setting.is_active else "❌"
            text += f"{i}. {status} {setting.setting_key}\n"
            text += f"   值: {setting.setting_value} | 类型: {setting.setting_type}\n"
            if setting.description:
                text += f"   说明: {setting.description}\n"
            text += f"   /set_setting {setting.setting_key} [新值]\n\n"
    
    text += "💡 快速命令：\n"
    text += "/toggle_feature [功能名] - 快速切换功能"
    
    # 创建分页键盘
    extra_buttons = [
        [
            types.InlineKeyboardButton(text="🔄 刷新", callback_data="view_all_settings"),
            types.InlineKeyboardButton(text="⬅️ 返回设置", callback_data="superadmin_system_settings")
        ],
        [
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
        ]
    ]
    
    keyboard = paginator.create_pagination_keyboard(
        page, "settings", extra_buttons
    )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=keyboard
    )
    await cb.answer()