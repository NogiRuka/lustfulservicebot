from aiogram import types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger
from datetime import datetime

from app.utils.message_utils import safe_edit_message
from app.utils.panel_utils import DEFAULT_WELCOME_PHOTO

from app.utils.states import Wait
from app.database.users import get_user, get_role
from app.database.business import (
    promote_user_to_admin, demote_admin_to_user, get_admin_list, get_all_feedback_list,
    get_all_movie_categories, create_movie_category, update_movie_category, delete_movie_category,
    get_all_system_settings, get_system_setting, set_system_setting, is_feature_enabled,
    get_all_dev_changelogs, create_dev_changelog, get_dev_changelog_by_id, update_dev_changelog, delete_dev_changelog
)
from app.buttons.users import superadmin_manage_center_kb, superadmin_action_kb, back_to_main_kb
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN

superadmin_router = Router()


@superadmin_router.callback_query(F.data == "superadmin_manage_center")
async def cb_superadmin_manage_center(cb: types.CallbackQuery):
    """管理中心"""
    # 系统总开关由BotStatusMiddleware统一处理，超管拥有完全特权访问
    
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    # 超管不受任何功能开关限制，拥有完全访问权限
    
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


@superadmin_router.callback_query(F.data == "image_add_new")
async def cb_image_add_new(cb: types.CallbackQuery):
    """添加新图片按钮处理"""
    await cb.answer("💡 请使用命令 /img_add [图片URL] 添加新图片\n示例：/ia https://example.com/image.jpg", show_alert=True)


@superadmin_router.callback_query(F.data == "image_remove_menu")
async def cb_image_remove_menu(cb: types.CallbackQuery):
    """删除图片菜单"""
    await cb.answer("💡 请使用命令 /img_remove [图片URL] 删除图片\n示例：/ir https://example.com/image.jpg", show_alert=True)


@superadmin_router.callback_query(F.data == "image_clear_sessions")
async def cb_image_clear_sessions(cb: types.CallbackQuery):
    """清除会话缓存按钮处理"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    from app.config.image_config import clear_all_sessions, get_image_info
    
    try:
        # 获取清除前的信息
        info_before = get_image_info()
        sessions_before = info_before['active_sessions']
        
        # 清除所有会话
        clear_all_sessions()
        
        await cb.answer(
            f"🧹 会话缓存清除成功！\n清除了 {sessions_before} 个会话\n所有用户下次/start时将重新随机选择图片",
            show_alert=True
        )
        
        # 刷新界面显示
        await cb_superadmin_image_manage(cb)
        
    except Exception as e:
        logger.error(f"清除会话缓存失败: {e}")
        await cb.answer(f"❌ 清除失败：{str(e)}", show_alert=True)


@superadmin_router.message(Command("replies", "r"))
async def view_replies_command(msg: types.Message):
    """查看用户回复"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.edit_text("❌ 仅超管可使用此命令")
        return
    
    from app.database.sent_messages import get_unread_replies, mark_reply_as_read
    
    try:
        # 获取未读回复
        unread_replies = await get_unread_replies(msg.from_user.id)
        
        if not unread_replies:
            await msg.reply(
                "📭 <b>暂无新回复</b>\n\n"
                "💡 当用户回复您的代发消息时，回复会显示在这里。\n\n"
                "使用 /history [用户ID] 查看与特定用户的对话历史"
            )
            return
        
        # 显示未读回复
        text = f"📬 <b>用户回复 ({len(unread_replies)} 条未读)</b>\n\n"
        
        for i, reply in enumerate(unread_replies[:5], 1):  # 最多显示5条
            text += f"<b>{i}. {reply.target_name}</b>\n"
            text += f"🆔 用户ID：{reply.target_id}\n"
            text += f"📤 您的消息：{reply.message_content[:50]}{'...' if len(reply.message_content) > 50 else ''}\n"
            text += f"💬 用户回复：{reply.reply_content[:100]}{'...' if len(reply.reply_content) > 100 else ''}\n"
            text += f"⏰ 回复时间：{reply.replied_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if len(unread_replies) > 5:
            text += f"📝 还有 {len(unread_replies) - 5} 条回复...\n\n"
        
        text += "💡 <b>操作提示</b>：\n"
        text += "├ /mark_read [记录ID] - 标记为已读\n"
        text += "├ /history [用户ID] - 查看对话历史\n"
        text += "└ /su [用户ID] [消息] - 回复用户"
        
        await msg.reply(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"查看回复失败: {e}")
        await msg.reply("❌ 查看回复失败，请稍后重试")


@superadmin_router.message(Command("history", "h"))
async def view_history_command(msg: types.Message):
    """查看与特定用户的对话历史"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply(
            "用法：/history [用户ID] 或 /h [用户ID]\n"
            "示例：/h 123456789"
        )
        return
    
    try:
        user_id = int(parts[1])
    except ValueError:
        await msg.reply("❌ 用户ID必须是数字")
        return
    
    from app.database.sent_messages import get_conversation_history
    from app.database.users import get_user
    
    try:
        # 获取用户信息
        user_info = await get_user(user_id)
        user_name = user_info.full_name if user_info else f"用户{user_id}"
        
        # 获取对话历史
        history = await get_conversation_history(msg.from_user.id, user_id, limit=10)
        
        if not history:
            await msg.reply(
                f"📭 <b>与 {user_name} 暂无对话记录</b>\n\n"
                f"💡 使用 /su {user_id} [消息内容] 开始对话"
            )
            return
        
        text = f"💬 <b>与 {user_name} 的对话历史</b>\n\n"
        
        for i, record in enumerate(reversed(history), 1):  # 按时间正序显示
            status_emoji = {
                "sent": "📤",
                "replied": "💬",
                "failed": "❌"
            }.get(record.status, "📤")
            
            text += f"<b>{i}. {status_emoji} {record.sent_at.strftime('%m-%d %H:%M')}</b>\n"
            text += f"📤 您：{record.message_content[:80]}{'...' if len(record.message_content) > 80 else ''}\n"
            
            if record.reply_content:
                text += f"💬 {user_name}：{record.reply_content[:80]}{'...' if len(record.reply_content) > 80 else ''}\n"
                text += f"⏰ 回复于：{record.replied_at.strftime('%m-%d %H:%M')}\n"
            
            text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += f"💡 使用 /su {user_id} [消息] 继续对话"
        
        await msg.reply(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"查看对话历史失败: {e}")
        await msg.reply("❌ 查看对话历史失败，请稍后重试")


@superadmin_router.message(Command("mark_read", "mr"))
async def mark_read_command(msg: types.Message):
    """标记回复为已读"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply(
            "用法：/mark_read [记录ID] 或 /mr [记录ID]\n"
            "示例：/mr 123"
        )
        return
    
    try:
        record_id = int(parts[1])
    except ValueError:
        await msg.reply("❌ 记录ID必须是数字")
        return
    
    from app.database.sent_messages import mark_reply_as_read
    
    try:
        success = await mark_reply_as_read(record_id)
        
        if success:
            await msg.reply(f"✅ 记录 #{record_id} 已标记为已读")
        else:
            await msg.reply(f"❌ 记录 #{record_id} 不存在或已经是已读状态")
            
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        await msg.reply("❌ 标记已读失败，请稍后重试")
        
        # 刷新界面显示
        await cb_superadmin_image_manage(cb)
        
    except Exception as e:
        logger.error(f"清除会话缓存失败: {e}")
        await cb.answer(f"❌ 清除失败：{str(e)}", show_alert=True)


@superadmin_router.callback_query(F.data == "image_test_random")
async def cb_image_test_random(cb: types.CallbackQuery):
    """测试随机图片按钮处理"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    from app.config.image_config import get_random_image
    
    try:
        # 获取随机图片
        random_image = get_random_image()
        
        # 发送测试图片
        test_text = (
            f"🎲 <b>随机图片测试</b>\n\n"
            f"🎯 <b>随机选择的图片</b>：\n{random_image}\n\n"
            f"⏰ <b>测试时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"💡 <b>说明</b>：这就是用户/start时可能看到的图片"
        )
        
        await cb.bot.send_photo(
            chat_id=cb.from_user.id,
            photo=random_image,
            caption=test_text,
            parse_mode="HTML"
        )
        
        await cb.answer("🎲 随机图片测试已发送！")
        
    except Exception as e:
        logger.error(f"测试随机图片失败: {e}")
        await cb.answer(f"❌ 测试失败：{str(e)}", show_alert=True)


# ==================== 功能开关切换 ====================

@superadmin_router.callback_query(F.data.startswith("toggle_"))
async def cb_toggle_feature(cb: types.CallbackQuery):
    """切换功能开关"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    # 提取功能名称
    feature_key = cb.data.replace("toggle_", "")
    
    # 获取当前状态
    current_value = await get_system_setting(feature_key)
    if current_value is None:
        await cb.answer("❌ 功能不存在", show_alert=True)
        return
    
    # 切换状态
    current_enabled = current_value.lower() in ["true", "1", "yes", "on"]
    new_value = "false" if current_enabled else "true"
    
    # 更新设置
    success = await set_system_setting(
        feature_key, 
        new_value, 
        "boolean", 
        f"功能开关 - {feature_key}", 
        cb.from_user.id
    )
    
    if success:
        # 获取功能名称（按优先级排序）
        feature_names = {
            "bot_enabled": "🤖 机器人开关",
            "movie_request_enabled": "🎬 求片开关",
            "content_submit_enabled": "📝 投稿开关",
            "feedback_enabled": "💬 反馈开关",
            "admin_panel_enabled": "👮 审核开关",
            "dev_changelog_enabled": "📋 开发日志开关",
            "system_enabled": "🌐 系统总开关",
            "page_size": "📄 每页显示条数"
        }
        
        feature_name = feature_names.get(feature_key, feature_key)
        status_text = "启用" if new_value == "true" else "禁用"
        
        await cb.answer(f"✅ {feature_name} 已{status_text}", show_alert=True)
        
        # 刷新页面
        await cb_superadmin_system_settings(cb)
    else:
        await cb.answer("❌ 设置更新失败", show_alert=True)


# ==================== 开发日志管理 ====================

@superadmin_router.callback_query(F.data == "dev_changelog_view")
async def cb_dev_changelog_view(cb: types.CallbackQuery):
    """查看开发日志"""
    # 检查开发日志功能开关
    if not await is_feature_enabled("dev_changelog_enabled"):
        await cb.answer("❌ 开发日志功能已关闭", show_alert=True)
        return
    
    role = await get_role(cb.from_user.id)
    # 所有用户都可以查看开发日志（如果功能启用）
    
    changelogs = await get_all_dev_changelogs()
    
    if not changelogs:
        text = "📋 <b>开发日志</b>\n\n暂无开发日志记录。"
        if role == ROLE_SUPERADMIN:
            text += "\n\n💡 使用 /add_changelog 添加新的开发日志"
    else:
        text = "📋 <b>开发日志</b>\n\n"
        text += f"📊 共有 {len(changelogs)} 条记录\n\n"
        
        # 创建开发日志按钮列表
        changelog_buttons = []
        
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
            
            # 处理版本号显示，避免重复的v
            version_display = log.version if log.version.startswith('v') else f"v{log.version}"
            text += f"┌─ {i}. {type_emoji} <b>{version_display}</b>\n"
            text += f"├ 📝 标题：{log.title}\n"
            text += f"├ 🏷️ 类型：{type_text}\n"
            text += f"└ ⏰ 时间：<i>{humanize_time(log.created_at)}</i>\n\n"
            
            # 添加查看详情按钮
            changelog_buttons.append(
                types.InlineKeyboardButton(
                    text=f"📖 查看 {version_display}",
                    callback_data=f"dev_changelog_detail_{log.id}"
                )
            )
        
        if len(changelogs) > 10:
            text += f"... 还有 {len(changelogs) - 10} 条记录\n\n"
        
        if role == ROLE_SUPERADMIN:
            text += "💡 管理命令：\n"
            text += "├ /add_changelog - 添加开发日志\n"
            text += "├ /edit_changelog [ID] - 编辑日志\n"
            text += "└ /del_changelog [ID] - 删除日志"
    
    # 根据用户角色显示不同的按钮
    keyboard_rows = []
    
    # 如果有开发日志，添加查看详情按钮（每行2个）
    if changelogs:
        for i in range(0, len(changelog_buttons), 2):
            row = changelog_buttons[i:i+2]
            keyboard_rows.append(row)
    
    # 添加功能按钮
    if role == ROLE_SUPERADMIN:
        keyboard_rows.extend([
            [
                types.InlineKeyboardButton(text="🔄 刷新列表", callback_data="dev_changelog_view"),
                types.InlineKeyboardButton(text="➕ 添加日志", callback_data="dev_changelog_add")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回其他功能", callback_data="other_functions"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ])
    else:
        keyboard_rows.extend([
            [
                types.InlineKeyboardButton(text="🔄 刷新列表", callback_data="dev_changelog_view")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回其他功能", callback_data="other_functions"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ])
    
    changelog_kb = types.InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=changelog_kb
    )
    await cb.answer()


@superadmin_router.callback_query(F.data.startswith("dev_changelog_detail_"))
async def cb_dev_changelog_detail(cb: types.CallbackQuery):
    """查看开发日志详细内容"""
    # 检查开发日志功能开关
    if not await is_feature_enabled("dev_changelog_enabled"):
        await cb.answer("❌ 开发日志功能已关闭", show_alert=True)
        return
    
    # 提取日志ID
    changelog_id = int(cb.data.split("_")[-1])
    
    # 获取日志详情
    changelog = await get_dev_changelog_by_id(changelog_id)
    
    if not changelog:
        await cb.answer("❌ 开发日志不存在", show_alert=True)
        return
    
    # 构建详细内容
    type_emoji = {
        "update": "🔄",
        "bugfix": "🐛",
        "feature": "✨",
        "hotfix": "🚨"
    }.get(changelog.changelog_type, "📝")
    
    type_text = {
        "update": "更新",
        "bugfix": "修复",
        "feature": "新功能",
        "hotfix": "热修复"
    }.get(changelog.changelog_type, "其他")
    
    from app.utils.time_utils import humanize_time
    from app.utils.markdown_utils import format_changelog_content
    
    # 处理版本号显示，避免重复的v
    version_display = changelog.version if changelog.version.startswith('v') else f"v{changelog.version}"
    
    # 转换Markdown内容为HTML
    formatted_content = format_changelog_content(changelog.content)
    
    text = f"{type_emoji} <b>开发日志详情</b>\n\n"
    text += f"📋 <b>版本</b>：{version_display}\n"
    text += f"📝 <b>标题</b>：{changelog.title}\n"
    text += f"🏷️ <b>类型</b>：{type_text}\n"
    text += f"⏰ <b>发布时间</b>：{humanize_time(changelog.created_at)}\n\n"
    text += f"📄 <b>详细内容</b>：\n\n{formatted_content}"
    
    # 创建返回按钮
    role = await get_role(cb.from_user.id)
    
    if role == ROLE_SUPERADMIN:
        detail_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✏️ 编辑", callback_data=f"dev_changelog_edit_{changelog.id}"),
                    types.InlineKeyboardButton(text="🗑️ 删除", callback_data=f"dev_changelog_delete_{changelog.id}")
                ],
                [
                    types.InlineKeyboardButton(text="⬅️ 返回日志列表", callback_data="dev_changelog_view"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                ]
            ]
        )
    else:
        detail_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⬅️ 返回日志列表", callback_data="dev_changelog_view"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                ]
            ]
        )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=detail_kb
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


@superadmin_router.callback_query(F.data == "superadmin_image_manage")
async def cb_superadmin_image_manage(cb: types.CallbackQuery):
    """图片管理界面 - 显示数据库中的所有图片"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    from app.config.image_config import get_image_info
    from app.database.image_library import get_all_images, get_image_stats
    
    try:
        # 获取随机池信息
        pool_info = get_image_info()
        
        # 获取数据库图片统计
        db_stats = await get_image_stats()
        
        # 获取最近的图片
        recent_images = await get_all_images(limit=5)
        
        text = "🖼️ <b>图片管理中心</b>\n\n"
        text += "📊 <b>统计信息</b>：\n"
        text += f"├ 随机池图片：{pool_info['total_images']} 张\n"
        text += f"├ 数据库图片：{db_stats['total_images']} 张\n"
        text += f"├ 活跃会话：{pool_info['active_sessions']} 个\n"
        text += f"└ 总使用次数：{db_stats['total_usage']} 次\n\n"
        
        if recent_images:
            text += "🎯 <b>最近添加的图片</b>：\n"
            for i, img in enumerate(recent_images[:3], 1):
                # 截断URL显示
                display_url = img.image_url[:40] + "..." if len(img.image_url) > 40 else img.image_url
                text += f"{i}. {display_url}\n"
                text += f"   📅 {img.added_at.strftime('%m-%d %H:%M')} | 🔢 使用{img.usage_count}次\n"
            
            if len(recent_images) > 3:
                text += f"... 还有 {len(recent_images) - 3} 张图片\n"
        else:
            text += "📝 <b>暂无图片记录</b>\n"
        
        text += "\n💡 <b>功能</b>：图片池与数据库管理\n"
        text += "⚡ <b>命令</b>：/img_info 查看详情"
        
        # 创建图片管理按钮
        image_manage_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="➕ 添加图片", callback_data="image_add_new"),
                    types.InlineKeyboardButton(text="🗑️ 删除图片", callback_data="image_remove_menu"),
                ],
                [
                    types.InlineKeyboardButton(text="📋 查看所有图片", callback_data="image_view_all"),
                    types.InlineKeyboardButton(text="📊 详细统计", callback_data="image_stats_detail"),
                ],
                [
                    types.InlineKeyboardButton(text="🧹 清除会话缓存", callback_data="image_clear_sessions"),
                    types.InlineKeyboardButton(text="🎲 测试随机图片", callback_data="image_test_random"),
                ],
                [
                    types.InlineKeyboardButton(text="⬅️ 返回管理中心", callback_data="superadmin_manage_center"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
                ],
            ]
        )
        
        await safe_edit_message(
            cb.message,
            caption=text,
            reply_markup=image_manage_kb
        )
        await cb.answer()
        
    except Exception as e:
        logger.error(f"图片管理界面加载失败: {e}")
        await cb.answer("❌ 加载图片管理界面失败", show_alert=True)


@superadmin_router.callback_query(F.data == "image_view_all")
async def cb_image_view_all(cb: types.CallbackQuery):
    """查看所有图片"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    from app.database.image_library import get_all_images
    
    try:
        images = await get_all_images(limit=20)
        
        if not images:
            await cb.answer("📝 暂无图片记录", show_alert=True)
            return
        
        text = "📋 <b>所有图片列表</b>\n\n"
        
        for i, img in enumerate(images, 1):
            # 截断URL显示
            display_url = img.image_url[:50] + "..." if len(img.image_url) > 50 else img.image_url
            status = "🟢" if img.is_active else "🔴"
            text += f"{i}. {status} {display_url}\n"
            text += f"   📅 {img.added_at.strftime('%Y-%m-%d %H:%M')} | 🔢 使用{img.usage_count}次\n"
            if img.description:
                text += f"   📝 {img.description[:30]}...\n" if len(img.description) > 30 else f"   📝 {img.description}\n"
            text += "\n"
        
        if len(images) == 20:
            text += "... 仅显示前20张图片\n\n"
        
        text += "💡 🟢=活跃 🔴=禁用"
        
        # 创建返回按钮
        back_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⬅️ 返回图片管理", callback_data="superadmin_image_manage"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
                ],
            ]
        )
        
        await safe_edit_message(
            cb.message,
            caption=text,
            reply_markup=back_kb
        )
        await cb.answer()
        
    except Exception as e:
        logger.error(f"查看所有图片失败: {e}")
        await cb.answer("❌ 查看图片列表失败", show_alert=True)


@superadmin_router.callback_query(F.data == "image_stats_detail")
async def cb_image_stats_detail(cb: types.CallbackQuery):
    """查看详细统计"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    from app.database.image_library import get_image_stats
    from app.config.image_config import get_image_info
    
    try:
        db_stats = await get_image_stats()
        pool_info = get_image_info()
        
        text = "📊 <b>图片系统详细统计</b>\n\n"
        
        text += "🗄️ <b>数据库统计</b>：\n"
        text += f"├ 总图片数：{db_stats['total_images']} 张\n"
        text += f"├ 活跃图片：{db_stats['active_images']} 张\n"
        text += f"├ 禁用图片：{db_stats['inactive_images']} 张\n"
        text += f"└ 总使用次数：{db_stats['total_usage']} 次\n\n"
        
        text += "🎲 <b>随机池统计</b>：\n"
        text += f"├ 池中图片：{pool_info['total_images']} 张\n"
        text += f"├ 活跃会话：{pool_info['active_sessions']} 个\n"
        text += f"└ 系统描述：{pool_info['description']}\n\n"
        
        if db_stats['recent_images']:
            text += "🕐 <b>最近添加</b>：\n"
            for img in db_stats['recent_images'][:3]:
                display_url = img['image_url'][:30] + "..." if len(img['image_url']) > 30 else img['image_url']
                text += f"├ {display_url}\n"
                text += f"│   📅 {img['added_at']} | 🔢 {img['usage_count']}次\n"
            text += "\n"
        
        avg_usage = db_stats['total_usage'] / db_stats['total_images'] if db_stats['total_images'] > 0 else 0
        text += f"📈 <b>平均使用次数</b>：{avg_usage:.1f} 次/图片\n"
        
        # 创建返回按钮
        back_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⬅️ 返回图片管理", callback_data="superadmin_image_manage"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
                ],
            ]
        )
        
        await safe_edit_message(
            cb.message,
            caption=text,
            reply_markup=back_kb
        )
        await cb.answer()
        
    except Exception as e:
        logger.error(f"查看详细统计失败: {e}")
        await cb.answer("❌ 获取统计信息失败", show_alert=True)


@superadmin_router.callback_query(F.data == "superadmin_manual_reply")
async def cb_superadmin_manual_reply(cb: types.CallbackQuery):
    """代发消息功能"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    text = "🤖 <b>代发消息与回复追踪</b>\n\n"
    text += "通过机器人代替您发送消息到指定目标，并自动追踪用户回复\n\n"
    text += "📋 <b>发送命令</b>：\n\n"
    text += "🔹 <b>发送给用户</b>：\n"
    text += "   /send_user [用户ID] [消息内容] 或 /su [用户ID] [消息内容]\n"
    text += "   示例：/su 123456789 您好！\n\n"
    text += "🔹 <b>发送到频道</b>：\n"
    text += "   /send_channel [频道ID] [消息内容] 或 /sc [频道ID] [消息内容]\n"
    text += "   示例：/sc @mychannel 公告内容\n\n"
    text += "🔹 <b>发送到群组</b>：\n"
    text += "   /send_group [群组ID] [消息内容] 或 /sg [群组ID] [消息内容]\n"
    text += "   示例：/sg -1001234567890 群组消息\n\n"
    text += "📬 <b>回复追踪命令</b>：\n\n"
    text += "🔹 <b>查看回复</b>：\n"
    text += "   /replies 或 /r - 查看用户回复\n\n"
    text += "🔹 <b>对话历史</b>：\n"
    text += "   /history [用户ID] 或 /h [用户ID] - 查看对话记录\n"
    text += "   示例：/h 123456789\n\n"
    text += "🔹 <b>标记已读</b>：\n"
    text += "   /mark_read [记录ID] 或 /mr [记录ID] - 标记回复为已读\n\n"
    text += "💡 <b>功能特点</b>：\n"
    text += "├ 📨 发送给用户的消息会自动提示可回复\n"
    text += "├ 💬 用户回复会自动记录并通知管理员\n"
    text += "├ 📋 支持查看完整对话历史\n"
    text += "├ 🔔 新回复会实时通知所有管理员\n"
    text += "└ 📊 支持已读/未读状态管理\n\n"
    text += "💡 <b>使用提示</b>：\n"
    text += "├ 用户ID：数字格式，如 123456789\n"
    text += "├ 频道ID：@频道名 或 -100开头的数字\n"
    text += "├ 群组ID：-100开头的数字\n"
    text += "└ 消息支持HTML格式和Markdown格式\n\n"
    text += "⚠️ <b>注意</b>：请谨慎使用此功能，确保消息内容合适"
    
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


# ==================== 随机图片管理命令 ====================

@superadmin_router.message(Command("img_info", "ii"))
async def img_info_command(msg: types.Message):
    """查看图片池信息"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    from app.config.image_config import get_image_info, IMAGE_LIST
    
    info = get_image_info()
    
    text = "🖼️ <b>随机图片池信息</b>\n\n"
    text += f"📊 <b>图片总数</b>：{info['total_images']} 张\n"
    text += f"👥 <b>活跃会话</b>：{info['active_sessions']} 个\n"
    text += f"📝 <b>说明</b>：{info['description']}\n\n"
    
    text += "🎯 <b>图片列表</b>：\n"
    for i, img_url in enumerate(IMAGE_LIST, 1):
        text += f"{i}. {img_url}\n\n"
    
    await msg.reply(text, parse_mode="HTML")


@superadmin_router.message(Command("img_add", "ia"))
async def img_add_command(msg: types.Message):
    """添加图片到随机池并保存到数据库"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply(
            "用法：/img_add [图片URL] 或 /ia [图片URL]\n"
            "示例：/ia https://example.com/image.jpg"
        )
        return
    
    image_url = parts[1]
    
    from app.config.image_config import add_image
    from app.database.image_library import save_image_url
    
    try:
        # 添加到随机池
        pool_success = add_image(image_url)
        
        # 保存到数据库
        db_record = await save_image_url(
            image_url=image_url,
            added_by=msg.from_user.id,
            description=f"通过命令添加到随机图片池"
        )
        
        if pool_success or db_record:
            status_text = ""
            if pool_success and db_record:
                status_text = "✅ 图片已添加到随机池并保存到数据库"
            elif pool_success:
                status_text = "✅ 图片已添加到随机池（数据库中已存在）"
            elif db_record:
                status_text = "✅ 图片已保存到数据库（随机池中已存在）"
            
            await msg.reply(
                f"<b>{status_text}</b>\n\n"
                f"🎯 <b>图片URL</b>：\n{image_url}\n\n"
                f"⏰ <b>添加时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"💡 <b>提示</b>：图片已加入系统，用户下次/start时可能随机到此图片",
                parse_mode="HTML"
            )
        else:
            await msg.reply("⚠️ 图片已存在于系统中")
        
    except Exception as e:
        logger.error(f"添加图片失败: {e}")
        await msg.reply(f"❌ 添加图片失败：{str(e)}")


@superadmin_router.message(Command("img_remove", "ir"))
async def img_remove_command(msg: types.Message):
    """从随机池和数据库中移除图片"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply(
            "用法：/img_remove [图片URL] 或 /ir [图片URL]\n"
            "示例：/ir https://example.com/image.jpg"
        )
        return
    
    image_url = parts[1]
    
    from app.config.image_config import remove_image
    from app.database.image_library import delete_image_by_url
    
    try:
        # 从随机池中移除
        pool_success = remove_image(image_url)
        
        # 从数据库中删除
        db_success = await delete_image_by_url(image_url)
        
        if pool_success or db_success:
            status_text = ""
            if pool_success and db_success:
                status_text = "✅ 图片已从随机池和数据库中移除"
            elif pool_success:
                status_text = "✅ 图片已从随机池中移除（数据库中不存在）"
            elif db_success:
                status_text = "✅ 图片已从数据库中删除（随机池中不存在）"
            
            await msg.reply(
                f"🗑️ <b>{status_text}</b>\n\n"
                f"🎯 <b>移除的图片</b>：\n{image_url}\n\n"
                f"⏰ <b>移除时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"💡 <b>提示</b>：使用该图片的用户会话已自动切换到其他图片",
                parse_mode="HTML"
            )
        else:
            await msg.reply("⚠️ 图片不存在或无法移除（随机池至少需要保留一张图片）")
        
    except Exception as e:
        logger.error(f"移除图片失败: {e}")
        await msg.reply(f"❌ 移除图片失败：{str(e)}")


@superadmin_router.message(Command("img_clear", "ic"))
async def img_clear_command(msg: types.Message):
    """清除所有用户会话图片缓存"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    from app.config.image_config import clear_all_sessions, get_image_info
    
    try:
        # 获取清除前的信息
        info_before = get_image_info()
        sessions_before = info_before['active_sessions']
        
        # 清除所有会话
        clear_all_sessions()
        
        await msg.reply(
            f"🧹 <b>会话缓存清除成功</b>\n\n"
            f"📊 <b>清除的会话数</b>：{sessions_before} 个\n"
            f"⏰ <b>清除时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"💡 <b>提示</b>：所有用户下次/start时将重新随机选择图片",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"清除会话缓存失败: {e}")
        await msg.reply(f"❌ 清除会话缓存失败：{str(e)}")


# ==================== 代发消息功能 ====================

@superadmin_router.message(Command("send_user", "su"))
async def send_user_message(msg: types.Message):
    """发送消息给指定用户"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        usage_text = (
            "用法：/send_user [用户ID] [消息内容] 或 /su [用户ID] [消息内容]\n"
            "示例：/su 123456789 您好！这是来自管理员的消息"
        )
        try:
            await msg.edit_text(usage_text)
        except Exception:
            await msg.reply(usage_text)
        return
    
    try:
        user_id = int(parts[1])
    except ValueError:
        error_text = "❌ 用户ID必须是数字"
        try:
            await msg.edit_text(error_text)
        except Exception:
            await msg.reply(error_text)
        return
    
    message_content = parts[2]
    
    try:
        # 获取用户信息用于显示
        from app.database.users import get_user
        user_info = await get_user(user_id)
        target_name = user_info.full_name if user_info else f"用户{user_id}"
        
        # 发送消息给目标用户（只发送纯净的消息内容）
        sent_msg = await msg.bot.send_message(
            chat_id=user_id,
            text=message_content,
            parse_mode="HTML"
        )
        
        # 记录发送的消息
        from app.database.sent_messages import create_sent_message_record
        record_id = await create_sent_message_record(
            admin_id=msg.from_user.id,
            target_type="user",
            target_id=user_id,
            target_name=target_name,
            message_content=message_content,
            sent_message_id=sent_msg.message_id,
            status="sent"
        )
        
        # 尝试编辑原始命令消息，如果失败则回复
        success_text = (
            f"✅ <b>消息发送成功</b>\n\n"
            f"📤 <b>目标用户</b>：{target_name} ({user_id})\n"
            f"📝 <b>消息内容</b>：{message_content[:100]}{'...' if len(message_content) > 100 else ''}\n"
            f"🆔 <b>记录ID</b>：{record_id}\n\n"
            f"⏰ <b>发送时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"💡 <b>提示</b>：使用 /replies 查看用户回复"
        )
        
        try:
            await msg.edit_text(success_text, parse_mode="HTML")
        except Exception as edit_error:
            # 如果编辑失败（如带图片的消息），则回复
            await msg.reply(success_text, parse_mode="HTML")
        
    except Exception as e:
        # 记录失败的消息
        from app.database.sent_messages import create_sent_message_record
        await create_sent_message_record(
            admin_id=msg.from_user.id,
            target_type="user",
            target_id=user_id,
            target_name=f"用户{user_id}",
            message_content=message_content,
            status="failed"
        )
        
        # 尝试编辑原始命令消息，如果失败则回复
        error_text = (
            f"❌ <b>消息发送失败</b>\n\n"
            f"📤 <b>目标用户</b>：{user_id}\n"
            f"❌ <b>错误信息</b>：{str(e)}\n\n"
            f"💡 <b>可能原因</b>：\n"
            f"├ 用户ID不存在\n"
            f"├ 用户已屏蔽机器人\n"
            f"├ 用户未启动过机器人\n"
            f"└ 消息格式有误"
        )
        
        try:
            await msg.edit_text(error_text, parse_mode="HTML")
        except Exception as edit_error:
            # 如果编辑失败（如带图片的消息），则回复
            await msg.reply(error_text, parse_mode="HTML")


@superadmin_router.message(Command("send_channel", "sc"))
async def send_channel_message(msg: types.Message):
    """发送消息到指定频道"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.edit_text("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.edit_text(
            "用法：/send_channel [频道ID] [消息内容] 或 /sc [频道ID] [消息内容]\n"
            "示例：/sc @mychannel 这是频道公告\n"
            "或：/sc -1001234567890 这是频道公告"
        )
        return
    
    channel_id = parts[1]
    message_content = parts[2]
    
    # 处理频道ID格式
    if channel_id.startswith('@'):
        target_id = channel_id
    else:
        try:
            target_id = int(channel_id)
        except ValueError:
            await msg.edit_text("❌ 频道ID格式错误，应为 @频道名 或数字ID")
            return
    
    try:
        # 发送消息到目标频道
        sent_msg = await msg.bot.send_message(
            chat_id=target_id,
            text=message_content,
            parse_mode="HTML"
        )
        
        # 编辑原始命令消息显示成功确认
        await msg.edit_text(
            f"✅ <b>频道消息发送成功</b>\n\n"
            f"📢 <b>目标频道</b>：{channel_id}\n"
            f"📝 <b>消息内容</b>：{message_content[:100]}{'...' if len(message_content) > 100 else ''}\n"
            f"🔗 <b>消息链接</b>：{sent_msg.link if hasattr(sent_msg, 'link') else '无'}\n\n"
            f"⏰ <b>发送时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await msg.edit_text(
            f"❌ <b>频道消息发送失败</b>\n\n"
            f"📢 <b>目标频道</b>：{channel_id}\n"
            f"❌ <b>错误信息</b>：{str(e)}\n\n"
            f"💡 <b>可能原因</b>：\n"
            f"├ 频道ID不存在\n"
            f"├ 机器人不是频道管理员\n"
            f"├ 没有发送消息权限\n"
            f"└ 消息格式有误",
            parse_mode="HTML"
        )


@superadmin_router.message(Command("send_group", "sg"))
async def send_group_message(msg: types.Message):
    """发送消息到指定群组"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.edit_text("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.edit_text(
            "用法：/send_group [群组ID] [消息内容] 或 /sg [群组ID] [消息内容]\n"
            "示例：/sg -1001234567890 这是群组通知"
        )
        return
    
    try:
        group_id = int(parts[1])
    except ValueError:
        await msg.edit_text("❌ 群组ID必须是数字（通常以-100开头）")
        return
    
    message_content = parts[2]
    
    try:
        # 发送消息到目标群组
        sent_msg = await msg.bot.send_message(
            chat_id=group_id,
            text=message_content,
            parse_mode="HTML"
        )
        
        # 编辑原始命令消息显示成功确认
        await msg.edit_text(
            f"✅ <b>群组消息发送成功</b>\n\n"
            f"👥 <b>目标群组</b>：{group_id}\n"
            f"📝 <b>消息内容</b>：{message_content[:100]}{'...' if len(message_content) > 100 else ''}\n"
            f"🆔 <b>消息ID</b>：{sent_msg.message_id}\n\n"
            f"⏰ <b>发送时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await msg.edit_text(
            f"❌ <b>群组消息发送失败</b>\n\n"
            f"👥 <b>目标群组</b>：{group_id}\n"
            f"❌ <b>错误信息</b>：{str(e)}\n\n"
            f"💡 <b>可能原因</b>：\n"
            f"├ 群组ID不存在\n"
            f"├ 机器人不在群组中\n"
            f"├ 没有发送消息权限\n"
            f"└ 消息格式有误",
            parse_mode="HTML"
        )


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
    
    from app.config.config import CATEGORY_PAGE_SIZE
    categories = await get_all_movie_categories(active_only=False)
    paginator = Paginator(categories, page_size=CATEGORY_PAGE_SIZE)
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
        photo=DEFAULT_WELCOME_PHOTO,
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
        # 按优先级分组显示
        text += "🔥 <b>【优先级1】核心功能开关</b>\n"
        core_switches = {
            "bot_enabled": "🤖 机器人开关",
            "movie_request_enabled": "🎬 求片开关", 
            "content_submit_enabled": "📝 投稿开关",
            "feedback_enabled": "💬 反馈开关",
            "admin_panel_enabled": "👮 审核开关",
            "dev_changelog_enabled": "📋 开发日志开关"
        }
        
        for setting in settings:
            if setting.setting_key in core_switches:
                status = "✅ 启用" if setting.setting_value.lower() in ["true", "1", "yes", "on"] else "❌ 禁用"
                name = core_switches[setting.setting_key]
                text += f"├ {name}：{status}\n"
        
        text += "\n⚙️ <b>【优先级2】系统配置项</b>\n"
        config_items = {
            "page_size": "📄 每页显示条数",
            "system_enabled": "🌐 系统总开关"
        }
        
        for setting in settings:
            if setting.setting_key in config_items:
                name = config_items[setting.setting_key]
                text += f"├ {name}：{setting.setting_value}\n"
        
        text += "\n💡 <b>快捷命令</b>：\n"
        text += "├ /toggle_feature [功能名] - 快速切换开关\n"
        text += "├ /set_setting [键名] [值] - 修改配置项\n"
        text += "└ /view_settings - 查看所有设置"
    else:
        text += "暂无设置\n\n"
        text += "💡 系统将使用默认设置"
    
    # 创建功能开关按钮（按优先级排序）
    toggle_buttons = []
    if settings:
        # 获取当前设置状态
        setting_dict = {s.setting_key: s.setting_value.lower() in ["true", "1", "yes", "on"] for s in settings}
        
        # 第一行：机器人开关（最高优先级）
        row1 = []
        if "bot_enabled" in setting_dict:
            status = "🟢" if setting_dict["bot_enabled"] else "🔴"
            row1.append(types.InlineKeyboardButton(text=f"{status} 机器人", callback_data="toggle_bot_enabled"))
        if row1:
            toggle_buttons.append(row1)
        
        # 第二行：求片和投稿开关
        row2 = []
        if "movie_request_enabled" in setting_dict:
            status = "🟢" if setting_dict["movie_request_enabled"] else "🔴"
            row2.append(types.InlineKeyboardButton(text=f"{status} 求片", callback_data="toggle_movie_request_enabled"))
        if "content_submit_enabled" in setting_dict:
            status = "🟢" if setting_dict["content_submit_enabled"] else "🔴"
            row2.append(types.InlineKeyboardButton(text=f"{status} 投稿", callback_data="toggle_content_submit_enabled"))
        if row2:
            toggle_buttons.append(row2)
        
        # 第三行：反馈和审核开关
        row3 = []
        if "feedback_enabled" in setting_dict:
            status = "🟢" if setting_dict["feedback_enabled"] else "🔴"
            row3.append(types.InlineKeyboardButton(text=f"{status} 反馈", callback_data="toggle_feedback_enabled"))
        if "admin_panel_enabled" in setting_dict:
            status = "🟢" if setting_dict["admin_panel_enabled"] else "🔴"
            row3.append(types.InlineKeyboardButton(text=f"{status} 审核", callback_data="toggle_admin_panel_enabled"))
        if row3:
            toggle_buttons.append(row3)
        
        # 第四行：开发日志开关
        row4 = []
        if "dev_changelog_enabled" in setting_dict:
            status = "🟢" if setting_dict["dev_changelog_enabled"] else "🔴"
            row4.append(types.InlineKeyboardButton(text=f"{status} 开发日志", callback_data="toggle_dev_changelog_enabled"))
        if row4:
            toggle_buttons.append(row4)
    
    # 添加管理按钮
    toggle_buttons.extend([
        [
            types.InlineKeyboardButton(text="🔄 刷新设置", callback_data="superadmin_system_settings"),
            types.InlineKeyboardButton(text="📋 查看全部", callback_data="view_all_settings")
        ],
        [
            types.InlineKeyboardButton(text="⬅️ 返回管理中心", callback_data="superadmin_manage_center"),
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
        ]
    ])
    
    settings_kb = types.InlineKeyboardMarkup(inline_keyboard=toggle_buttons)
    
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
    
    from app.config.config import SETTINGS_PAGE_SIZE
    settings = await get_all_system_settings()
    paginator = Paginator(settings, page_size=SETTINGS_PAGE_SIZE)
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