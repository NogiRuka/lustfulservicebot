import asyncio
from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.filters import IsBusyFilter, IsCommand
from app.database.users import get_busy, set_busy, get_user, get_role
from app.buttons.users import (
    get_main_menu_by_role, other_functions_kb, back_to_main_kb
)
from app.buttons.panels import get_panel_for_role
from app.database.business import get_server_stats
from app.utils.group_utils import get_group_member_count, user_in_group_filter
from app.utils.commands_catalog import build_commands_help
from app.config.config import GROUP, BOT_NICKNAME
from app.utils.panel_utils import create_welcome_panel_text, create_info_panel_text, DEFAULT_WELCOME_PHOTO

basic_router = Router()


# /start：欢迎与菜单
@basic_router.message(CommandStart())
async def start(msg: types.Message):
    # 第一步：检查是否是私聊
    if msg.chat.type != 'private':
        # 在群组中给出更明确的提示
        bot_username = (await msg.bot.get_me()).username
        await msg.reply(
            f"🌟 <b>欢迎使用 <a href='https://t.me/{bot_username}'>{BOT_NICKNAME}</a></b>\n💫 请在私聊中使用机器人功能",
            parse_mode="HTML"
        )
        return
    
    # 第二步：检查是否在设置的群组里（如果设置了GROUP）
    if GROUP:
        is_in_group = await user_in_group_filter(msg.bot, msg.from_user.id)
        if not is_in_group:
            await msg.reply(
                f"❌ 您需要先加入群组 @{GROUP} 才能使用此机器人。\n\n"
                "请加入群组后再次尝试。"
            )
            return
    
    # 第三步：获取用户角色并显示对应面板
    role = await get_role(msg.from_user.id)
    title, kb = get_panel_for_role(role)
    
    # 使用复用的面板样式函数
    welcome_text = create_welcome_panel_text(title, role)
    welcome_photo = DEFAULT_WELCOME_PHOTO
    
    await msg.bot.send_photo(
        chat_id=msg.from_user.id,
        photo=welcome_photo,
        caption=welcome_text,
        reply_markup=kb,
        parse_mode="HTML"
    )


@basic_router.callback_query(F.data == "user_toggle_busy")
async def cb_user_toggle_busy(cb: types.CallbackQuery):
    """切换忙碌状态"""
    current_busy = await get_busy(cb.from_user.id)
    new_busy = not current_busy
    await set_busy(cb.from_user.id, new_busy)
    
    status_text = "忙碌" if new_busy else "空闲"
    toggle_text = (
        f"🔁 <b>状态切换</b>\n\n"
        f"当前状态：{status_text}\n\n"
        "如需返回主菜单，请点击下方按钮。"
    )
    
    back_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ]
    )
    
    await cb.message.edit_caption(
        caption=toggle_text,
        reply_markup=back_kb
    )
    await cb.answer(f"状态已切换为: {status_text}")


@basic_router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(cb: types.CallbackQuery):
    role = await get_role(cb.from_user.id)
    title, kb = get_panel_for_role(role)
    
    # 使用复用的面板样式函数
    welcome_text = create_welcome_panel_text(title, role)
    welcome_photo = DEFAULT_WELCOME_PHOTO
    
    # 检查当前消息是否有图片
    if cb.message.photo:
        # 如果有图片，编辑caption
        await cb.message.edit_caption(
            caption=welcome_text,
            reply_markup=kb,
            parse_mode="HTML"
        )
    else:
        # 如果没有图片，删除当前消息并发送新的带图片消息
        try:
            await cb.message.delete()
        except:
            pass  # 忽略删除失败的错误
        
        await cb.bot.send_photo(
            chat_id=cb.from_user.id,
            photo=welcome_photo,
            caption=welcome_text,
            reply_markup=kb,
            parse_mode="HTML"
        )
    
    await cb.answer()


@basic_router.callback_query(F.data == "common_my_info")
async def cb_common_my_info(cb: types.CallbackQuery):
    """我的信息"""
    user = await get_user(cb.from_user.id)
    role = await get_role(cb.from_user.id)
    
    # 使用复用的面板样式函数
    user_info = {
        'username': cb.from_user.username,
        'full_name': cb.from_user.full_name,
        'user_id': cb.from_user.id,
        'role': role,
        'created_at': user.created_at.strftime('%Y年%m月%d日 %H:%M') if user else '未知',
        'last_activity_at': user.last_activity_at.strftime('%Y年%m月%d日 %H:%M') if user and user.last_activity_at else '未知'
    }
    info_text = create_info_panel_text(user_info)
    
    await cb.message.edit_caption(
        caption=info_text,
        reply_markup=back_to_main_kb,
        parse_mode="HTML"
    )
    await cb.answer()


@basic_router.callback_query(F.data == "common_server_info")
async def cb_common_server_info(cb: types.CallbackQuery):
    """服务器信息"""
    try:
        stats = await get_server_stats()
        member_count = await get_group_member_count(cb.bot)
        
        info_text = (
            f"🖥️ <b>服务信息</b> 🖥️\n\n"
            f"📊 <b>统计数据</b>\n"
            f"├ 使用用户: {stats['total_users']}\n"
            f"├ 求片请求: {stats['total_requests']}\n"
            f"└ 内容投稿: {stats['total_submissions']}\n\n"
            f"💫 <b>感谢您的使用！</b> 💫"
        )
    except Exception as e:
        logger.error(f"获取服务信息失败: {e}")
        info_text = (
            f"🖥️ <b>服务信息</b> 🖥️\n\n"
            "❌ 暂时无法获取服务信息，请稍后重试。\n\n"
            "如需返回主菜单，请点击下方按钮。"
        )
    
    await cb.message.edit_caption(
        caption=info_text,
        reply_markup=back_to_main_kb,
        parse_mode="HTML"
    )
    await cb.answer()


@basic_router.callback_query(F.data == "other_functions")
async def cb_other_functions(cb: types.CallbackQuery):
    """其他功能"""
    from app.database.users import get_role
    from app.utils.roles import ROLE_SUPERADMIN
    
    role = await get_role(cb.from_user.id)
    
    # 所有用户都可以查看开发日志
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🔁 切换忙碌状态", callback_data="user_toggle_busy"),
                types.InlineKeyboardButton(text="📖 帮助信息", callback_data="user_help"),
            ],
            [
                types.InlineKeyboardButton(text="🗑️ 清空记录", callback_data="clear_chat_history"),
                types.InlineKeyboardButton(text="📋 开发日志", callback_data="dev_changelog_view"),
            ],
            [
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
            ],
        ]
    )
    
    await cb.message.edit_caption(
        caption="⚙️ <b>其他功能</b>\n\n请选择您需要的功能：",
        reply_markup=kb
    )
    await cb.answer()


@basic_router.callback_query(F.data == "user_help")
async def cb_user_help(cb: types.CallbackQuery):
    """帮助信息"""
    await cb.answer("📖 暂无帮助信息", show_alert=True)


@basic_router.callback_query(F.data == "clear_chat_history")
async def cb_clear_chat_history(cb: types.CallbackQuery):
    """清空聊天记录"""
    try:
        # 获取当前聊天中的所有消息并删除
        chat_id = cb.from_user.id
        
        # 尝试删除最近的消息（Telegram API限制，只能删除最近48小时内的消息）
        # 这里我们尝试删除最近100条消息
        deleted_count = 0
        for i in range(100):
            try:
                # 从当前消息ID开始向前删除
                message_id = cb.message.message_id - i
                if message_id > 0:
                    await cb.bot.delete_message(chat_id=chat_id, message_id=message_id)
                    deleted_count += 1
            except Exception:
                # 忽略删除失败的消息（可能已经被删除或超出时间限制）
                continue
        
        # 发送确认消息
        await cb.bot.send_message(
            chat_id=chat_id,
            text=f"🗑️ <b>清空完成</b>\n\n已尝试清理聊天记录\n删除了 {deleted_count} 条消息\n\n💡 <i>注：由于Telegram限制，只能删除最近48小时内的消息</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await cb.answer(f"❌ 清空失败: {str(e)}", show_alert=True)
    
    await cb.answer("🗑️ 正在清空聊天记录...")


# 普通文本消息：处理用户回复反馈
@basic_router.message(F.text, IsCommand(), IsBusyFilter())
async def message(msg: types.Message, state: FSMContext):
    """处理普通文本消息"""
    # 检查用户是否处于某个状态中，如果是则不处理
    current_state = await state.get_state()
    if current_state is not None:
        logger.debug(f"用户 {msg.from_user.id} 处于状态 {current_state}，跳过通用消息处理")
        return
    
    # 处理用户回复反馈的消息
    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        # 检查回复的消息是否是反馈回复通知
        if "反馈回复通知" in msg.reply_to_message.text:
            await handle_user_feedback_reply(msg)
            return
    
    # 其他普通消息暂不处理
    logger.debug(f"用户 {msg.from_user.id} 发送了普通消息，暂不处理")


async def handle_user_feedback_reply(msg: types.Message):
    """处理用户回复反馈的消息"""
    try:
        # 从回复的消息中提取反馈ID
        reply_text = msg.reply_to_message.text
        import re
        feedback_id_match = re.search(r'反馈ID：(\d+)', reply_text)
        
        if not feedback_id_match:
            await msg.reply("❌ 无法识别反馈ID，请直接回复反馈通知消息")
            return
        
        feedback_id = int(feedback_id_match.group(1))
        user_reply = msg.text
        
        # 获取用户信息
        from app.utils.panel_utils import get_user_display_link
        user_display = await get_user_display_link(msg.from_user.id)
        
        # 构建转发给管理员的消息
        admin_notification = (
            f"💬 <b>用户反馈回复</b> 💬\n\n"
            f"🆔 <b>反馈ID</b>：{feedback_id}\n"
            f"👤 <b>用户</b>：{user_display}\n"
            f"📝 <b>用户回复</b>：\n{user_reply}\n\n"
            f"💡 <b>回复方式</b>：/rp {feedback_id} [回复内容]"
        )
        
        # 发送给所有管理员和超管
        from app.database.business import get_admin_list
        from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN
        from app.database.users import get_user
        
        admins = await get_admin_list()
        
        # 获取超管ID
        from app.config import SUPERADMIN_ID
        if SUPERADMIN_ID:
            try:
                await msg.bot.send_message(
                    chat_id=SUPERADMIN_ID,
                    text=admin_notification,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"发送消息给超管失败: {e}")
        
        # 发送给所有管理员
        for admin in admins:
            try:
                await msg.bot.send_message(
                    chat_id=admin.chat_id,
                    text=admin_notification,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"发送消息给管理员 {admin.chat_id} 失败: {e}")
        
        # 给用户发送确认消息
        await msg.reply(
            f"✅ 您的回复已转达给管理员\n\n"
            f"🆔 反馈ID：{feedback_id}\n"
            f"📝 回复内容：{user_reply}\n\n"
            f"💡 管理员会尽快处理您的回复"
        )
        
    except Exception as e:
        logger.error(f"处理用户反馈回复失败: {e}")
        await msg.reply("❌ 处理回复失败，请稍后重试或联系管理员")
    