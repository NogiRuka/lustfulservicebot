from aiogram import types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from app.database.admin import (
    get_count_of_users,
    get_user_data,
    get_all_users_id,
    remove_user,
)
from app.buttons.admin import admin_panel_kb
from app.utils.states import Wait
from app.database.users import set_role, get_role
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN, ROLE_USER
from app.utils.commands_catalog import build_commands_help
from app.database.business import (
    get_all_feedback_list, reply_user_feedback, review_movie_request, review_content_submission,
    get_all_movie_requests, get_all_content_submissions
)
from app.buttons.users import back_to_main_kb
from app.database.business import is_feature_enabled
from app.utils.panel_utils import get_user_display_link, send_feedback_reply_notification
from app.utils.time_utils import humanize_time
import re

admins_router = Router()


@admins_router.message(Command("panel"))
async def ShowPanel(msg: types.Message):
    # 检查管理员面板开关
    if not await is_feature_enabled("system_enabled"):
        await msg.reply("❌ 系统维护中，暂时无法使用")
        return
    
    if not await is_feature_enabled("admin_panel_enabled"):
        await msg.reply("❌ 管理员面板已关闭")
        return
    
    role = await get_role(msg.from_user.id)
    admin_photo = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"
    admin_text = f"🛡️ 管理员面板\n\n👤 用户角色：{role}\n\n欢迎使用管理员功能，请选择下方按钮进行操作。"
    
    await msg.bot.send_photo(
        chat_id=msg.from_user.id,
        photo=admin_photo,
        caption=admin_text,
        reply_markup=admin_panel_kb
    )


# 面板回调：统计
@admins_router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(cb: types.CallbackQuery):
    users_len = await get_count_of_users()
    # 使用安全编辑函数
    await safe_edit_message(
        cb.message,
        caption=f"📊 <b>用户统计</b>\n\n当前用户总数：{users_len}\n\n点击下方按钮查看更多功能。",
        text=f"当前用户总数：{users_len}",
        reply_markup=admin_panel_kb
    )
    await cb.answer()


# 面板回调：查询提示
@admins_router.callback_query(F.data == "admin_query_user")
async def cb_admin_query_tip(cb: types.CallbackQuery):
    query_text = "🔎 <b>查询用户</b>\n\n请使用命令：/info [chat_id]\n\n示例：/info 123456789"
    try:
        if cb.message.photo:
            await cb.message.edit_caption(caption=query_text, reply_markup=admin_panel_kb)
        else:
            await cb.message.edit_text(query_text, reply_markup=admin_panel_kb)
    except Exception as e:
        # 忽略消息未修改的错误
        if "message is not modified" not in str(e):
            logger.error(f"编辑消息失败: {e}")
    await cb.answer()


# 面板回调：群发公告指引
@admins_router.callback_query(F.data == "admin_announce")
async def cb_admin_announce_tip(cb: types.CallbackQuery, state: FSMContext):
    announce_text = "📢 <b>群发公告</b>\n\n请发送要群发给所有用户的消息（任意类型）\n\n支持文本、图片、视频等各种消息类型。"
    await safe_edit_message(cb.message, caption=announce_text, text=announce_text, reply_markup=admin_panel_kb)
    await state.set_state(Wait.waitAnnounce)
    await cb.answer()


# 面板回调：清理封禁用户（懒方式：实际在群发时自动移除）
@admins_router.callback_query(F.data == "admin_cleanup")
async def cb_admin_cleanup(cb: types.CallbackQuery):
    cleanup_text = "🧹 <b>清理封禁用户</b>\n\n清理功能在群发时自动进行：无法接收的用户会被移除。\n\n这是一个自动化过程，无需手动操作。"
    await safe_edit_message(cb.message, caption=cleanup_text, text=cleanup_text, reply_markup=admin_panel_kb)
    await cb.answer()


# 显示管理员命令
@admins_router.message(Command("commands"))
async def ShowCommands(msg: types.Message):
    role = await get_role(msg.from_user.id)
    await msg.bot.send_message(msg.from_user.id, build_commands_help(role))


# 获取用户总数
@admins_router.message(Command("users"))
async def GetCountOfUsers(msg: types.Message):
    users_len = await get_count_of_users()
    await msg.bot.send_message(msg.from_user.id, "用户总数：" + str(users_len))


# 查询指定用户
@admins_router.message(Command("info"))
async def GetUserData(msg: types.Message):
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.bot.send_message(msg.from_user.id, "用法：/info [chat_id]")
        return
    chat_id = parts[1]

    current_user = await get_user_data(int(chat_id))

    if not current_user:
        await msg.bot.send_message(msg.from_user.id, "未找到该用户")
        return

    message = f"""
<b>用户名：</b> {current_user.username}
<b>昵称：</b> {current_user.full_name}
<b>聊天ID：</b> {current_user.chat_id}
<b>创建时间：</b> {current_user.created_at.strftime("%Y-%m-%d %H:%M:%S")}
<b>最后活跃：</b> {current_user.last_activity_at.strftime("%Y-%m-%d %H:%M:%S")}
    """

    await msg.bot.send_message(msg.from_user.id, message)


# 群发公告
@admins_router.message(Command("announce"))
async def Announce(msg: types.Message, state: FSMContext):
    await msg.bot.send_message(msg.from_user.id, "请发送要群发给所有用户的消息（任意类型）")
    await state.set_state(Wait.waitAnnounce)


@admins_router.message(StateFilter(Wait.waitAnnounce))
async def ConfirmAnnounce(msg: types.Message, state: FSMContext):
    all_users_id = await get_all_users_id()

    users_len = len(all_users_id)

    active_users = 0
    inactive_users = 0

    await msg.reply(f"开始向 {users_len} 位用户群发…")

    for chat_id in all_users_id:
        try:
            await msg.bot.copy_message(chat_id, msg.from_user.id, msg.message_id)
            active_users += 1
        except Exception as e:
            inactive_users += 1
            remove_user(chat_id)

    await msg.bot.send_message(
        msg.from_user.id,
        f"<b>发送完成</b>\n💚成功：{active_users}\n💔已移除：{inactive_users}",
    )
    await state.clear()


# ==================== 管理员专用功能 ====================

@admins_router.callback_query(F.data == "admin_feedback_browse")
async def cb_admin_feedback_browse(cb: types.CallbackQuery):
    """反馈浏览"""
    feedbacks = await get_all_feedback_list()
    
    if not feedbacks:
        await cb.message.edit_caption(
            caption="👀 <b>反馈浏览</b>\n\n暂无用户反馈。",
            reply_markup=back_to_main_kb
        )
    else:
        text = "👀 <b>反馈浏览</b>\n\n"
        pending_count = sum(1 for f in feedbacks if f.status == "pending")
        text += f"📊 总计 {len(feedbacks)} 条反馈，{pending_count} 条待处理\n\n"
        
        for i, feedback in enumerate(feedbacks[:15], 1):  # 最多显示15条
            status_emoji = {
                "pending": "⏳",
                "processing": "🔄", 
                "resolved": "✅"
            }.get(feedback.status, "❓")
            
            status_text = {
                "pending": "待处理",
                "processing": "处理中", 
                "resolved": "已解决"
            }.get(feedback.status, "未知")
            
            type_emoji = {
                "bug": "🐛",
                "suggestion": "💡",
                "complaint": "😤",
                "other": "❓"
            }.get(feedback.feedback_type, "❓")
            
            type_text = {
                "bug": "Bug反馈",
                "suggestion": "建议反馈",
                "complaint": "投诉反馈",
                "other": "其他反馈"
            }.get(feedback.feedback_type, "未知类型")
            
            # 获取用户显示链接
            user_display = await get_user_display_link(feedback.user_id)
            
            # 美化的卡片式布局
            content_preview = feedback.content[:40] + ('...' if len(feedback.content) > 40 else '')
            text += f"┌─ {i}. {type_emoji} {status_emoji} <b>ID:{feedback.id}</b>\n"
            text += f"├ 👤 用户：{user_display}\n"
            text += f"├ ⏰ 时间：<i>{humanize_time(feedback.created_at)}</i>\n"
            text += f"├ 📂 类型：{type_emoji} {type_text}\n"
            text += f"├ 🏷️ 状态：<code>{status_text}</code>\n"
            text += f"└ 📄 内容：{content_preview}\n\n"
        
        if len(feedbacks) > 15:
            text += f"... 还有 {len(feedbacks) - 15} 条记录\n\n"
        
        text += "💡 使用 /reply [反馈ID] [回复内容] 来回复反馈"
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=back_to_main_kb
        )
    
    await cb.answer()

# 管理员命令：回复反馈
@admins_router.message(Command("reply"))
async def admin_reply_feedback(msg: types.Message):
    """回复用户反馈"""
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.reply("用法：/reply [反馈ID] [回复内容]")
        return
    
    try:
        feedback_id = int(parts[1])
    except ValueError:
        await msg.reply("反馈ID必须是数字")
        return
    
    reply_content = parts[2]
    
    # 先获取反馈信息
    feedbacks = await get_all_feedback_list()
    feedback = next((f for f in feedbacks if f.id == feedback_id), None)
    
    if not feedback:
        await msg.reply("❌ 反馈不存在")
        return
    
    success = await reply_user_feedback(feedback_id, msg.from_user.id, reply_content)
    
    if success:
        # 发送通知给用户
        await send_feedback_reply_notification(msg.bot, feedback.user_id, feedback_id, reply_content)
        
        # 发送成功消息给管理员
        success_msg = await msg.reply(f"✅ 已回复反馈 {feedback_id}，用户已收到通知")
        
        # 删除命令消息和成功消息（延迟删除）
        try:
            await msg.delete()
            # 3秒后删除成功消息
            import asyncio
            await asyncio.sleep(3)
            await success_msg.delete()
        except Exception as e:
            from loguru import logger
            logger.warning(f"删除消息失败: {e}")
    else:
        await msg.reply("❌ 回复失败，请检查反馈ID是否正确")


# 管理员命令：向用户发送消息
@admins_router.message(Command("message"))
async def admin_message_user(msg: types.Message):
    """向特定项目的用户发送消息"""
    parts = msg.text.split(maxsplit=3)
    if len(parts) < 4:
        await msg.reply(
            "用法：/message [类型] [ID] [消息内容]\n\n"
            "类型支持：\n"
            "• movie - 求片\n"
            "• content - 投稿\n"
            "• feedback - 反馈\n\n"
            "示例：/message movie 123 您的求片已处理完成"
        )
        return
    
    item_type = parts[1].lower()
    try:
        item_id = int(parts[2])
    except ValueError:
        await msg.reply("❌ ID必须是数字")
        return
    
    message_content = parts[3]
    
    # 根据类型获取对应的项目和用户信息
    user_id = None
    item_title = None
    
    if item_type == "movie":
        requests = await get_all_movie_requests()
        item = next((r for r in requests if r.id == item_id), None)
        if item:
            user_id = item.user_id
            item_title = item.title
            type_name = "求片"
    elif item_type == "content":
        submissions = await get_all_content_submissions()
        item = next((s for s in submissions if s.id == item_id), None)
        if item:
            user_id = item.user_id
            item_title = item.title
            type_name = "投稿"
    elif item_type == "feedback":
        feedbacks = await get_all_feedback_list()
        item = next((f for f in feedbacks if f.id == item_id), None)
        if item:
            user_id = item.user_id
            item_title = f"反馈#{item_id}"
            type_name = "反馈"
    else:
        await msg.reply("❌ 不支持的类型，请使用 movie、content 或 feedback")
        return
    
    if not user_id:
        await msg.reply(f"❌ {type_name} ID {item_id} 不存在")
        return
    
    # 发送消息给用户
    try:
        notification_text = (
            f"📨 <b>管理员消息</b> 📨\n\n"
            f"📋 <b>关于</b>：{type_name} - {item_title}\n"
            f"🆔 <b>ID</b>：{item_id}\n\n"
            f"💬 <b>消息内容</b>：\n{message_content}\n\n"
            f"📝 如有疑问，请联系管理员。"
        )
        
        await msg.bot.send_message(
            chat_id=user_id,
            text=notification_text,
            parse_mode="HTML"
        )
        
        # 发送成功消息给管理员
        success_msg = await msg.reply(f"✅ 消息已发送给用户（{type_name} #{item_id}）")
        
        # 删除命令消息和成功消息（延迟删除）
        try:
            await msg.delete()
            # 3秒后删除成功消息
            import asyncio
            await asyncio.sleep(3)
            await success_msg.delete()
        except Exception as e:
            from loguru import logger
            logger.warning(f"删除消息失败: {e}")
            
    except Exception as e:
        from loguru import logger
        logger.error(f"发送消息失败: {e}")
        await msg.reply("❌ 发送消息失败，请检查用户是否存在")


