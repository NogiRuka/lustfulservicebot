import asyncio

from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command
from loguru import logger

from app.utils.filters import IsBusyFilter, IsCommand
from app.database.users import get_busy, set_busy, get_user
from app.database.users import get_role
from app.buttons.users import (
    get_main_menu_by_role, movie_center_kb, content_center_kb, 
    feedback_center_kb, other_functions_kb, back_to_main_kb
)
from app.buttons.panels import get_panel_for_role
from app.database.business import get_server_stats
from app.utils.group_utils import get_group_member_count
from app.utils.commands_catalog import build_commands_help
from app.config.config import GROUP
from app.utils.group_utils import user_in_group_filter


users_router = Router()


# /start：欢迎与菜单
@users_router.message(CommandStart())
async def start(msg: types.Message):
    # 第一步：检查是否是私聊
    if msg.chat.type != 'private':
        # 在群组中给出更明确的提示
        bot_username = (await msg.bot.get_me()).username
        await msg.reply(
            f"👋 你好！请点击 @{bot_username} 或直接私聊我来使用完整功能。\n\n"
            "🔒 为了保护隐私，主要功能仅在私聊中提供。"
        )
        return
    
    # 第二步：检查是否在设置的群组里（如果设置了GROUP）
    if GROUP:
        is_in_group = await user_in_group_filter(msg.bot, msg.from_user.id)
        if not is_in_group:
            await msg.reply(f"❌ 请先加入群组 @{GROUP} 后再使用机器人功能。")
            return
    
    # 第三步：根据用户ID判断权限显示不同的面板
    role = await get_role(msg.from_user.id)
    title, kb = get_panel_for_role(role)
    
    # 发送带图片的欢迎面板
    welcome_photo = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"
    welcome_text = f"🎉 欢迎使用机器人！\n\n👤 用户角色：{role}\n\n{title}"
    
    await msg.bot.send_photo(
        chat_id=msg.from_user.id,
        photo=welcome_photo,
        caption=welcome_text,
        reply_markup=kb
    )


# /menu：按角色显示面板
@users_router.message(Command("menu"))
async def show_menu(msg: types.Message):
    role = await get_role(msg.from_user.id)
    title, kb = get_panel_for_role(role)
    await msg.bot.send_message(msg.from_user.id, title, reply_markup=kb)


# /commands：按角色显示命令目录
@users_router.message(Command("commands"))
async def show_commands(msg: types.Message):
    role = await get_role(msg.from_user.id)
    catalog = build_commands_help(role)
    await msg.bot.send_message(msg.from_user.id, catalog)


# /role：显示当前账号角色（调试用）
@users_router.message(Command("role"))
async def show_role(msg: types.Message):
    role = await get_role(msg.from_user.id)
    await msg.bot.send_message(msg.from_user.id, f"当前角色：{role}")


# /id：显示当前 Telegram 数字ID（调试用）
@users_router.message(Command("id"))
async def show_id(msg: types.Message):
    await msg.bot.send_message(msg.from_user.id, f"你的聊天ID：{msg.from_user.id}")


# 用户按钮回调处理
@users_router.callback_query(F.data == "user_help")
async def cb_user_help(cb: types.CallbackQuery):
    help_text = (
        "📖 <b>帮助信息</b>\n\n"
        "🤖 这是一个多功能机器人\n"
        "💬 发送任意文本，我会回显给你\n"
        "🔧 使用菜单按钮查看更多功能\n\n"
        "如需返回主菜单，请点击下方按钮。"
    )
    
    # 创建返回按钮
    back_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ]
    )
    
    await cb.message.edit_caption(
        caption=help_text,
        reply_markup=back_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "user_profile")
async def cb_user_profile(cb: types.CallbackQuery):
    user = await get_user(cb.from_user.id)
    role = await get_role(cb.from_user.id)
    
    profile_text = (
        f"🙋 <b>我的信息</b>\n\n"
        f"👤 用户名: {cb.from_user.username or '未设置'}\n"
        f"📝 昵称: {cb.from_user.full_name}\n"
        f"🆔 ID: {cb.from_user.id}\n"
        f"🎭 角色: {role}\n\n"
        "如需返回主菜单，请点击下方按钮。"
    )
    
    back_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ]
    )
    
    await cb.message.edit_caption(
        caption=profile_text,
        reply_markup=back_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "user_toggle_busy")
async def cb_user_toggle_busy(cb: types.CallbackQuery):
    current_busy = await get_busy(cb.from_user.id)
    new_busy = not current_busy
    await set_busy(cb.from_user.id, new_busy)
    
    status_text = "忙碌" if new_busy else "空闲"
    toggle_text = (
        f"🔁 <b>状态切换</b>\n\n"
        f"当前状态: {status_text}\n\n"
        "忙碌状态下，机器人将不会处理你的消息。\n\n"
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


@users_router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(cb: types.CallbackQuery):
    role = await get_role(cb.from_user.id)
    title, kb = get_panel_for_role(role)
    
    welcome_text = f"🎉 欢迎使用机器人！\n\n👤 用户角色：{role}\n\n{title}"
    
    await cb.message.edit_caption(
        caption=welcome_text,
        reply_markup=kb
    )
    await cb.answer()


# ==================== 公共功能模块 ====================

@users_router.callback_query(F.data == "common_my_info")
async def cb_common_my_info(cb: types.CallbackQuery):
    """我的信息"""
    user = await get_user(cb.from_user.id)
    role = await get_role(cb.from_user.id)
    
    info_text = (
        f"🙋 <b>我的信息</b>\n\n"
        f"👤 用户名: {cb.from_user.username or '未设置'}\n"
        f"📝 昵称: {cb.from_user.full_name}\n"
        f"🆔 用户ID: {cb.from_user.id}\n"
        f"🎭 角色: {role}\n"
        f"📅 注册时间: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user else '未知'}\n"
        f"⏰ 最后活跃: {user.last_activity_at.strftime('%Y-%m-%d %H:%M:%S') if user and user.last_activity_at else '未知'}\n\n"
        "如需返回主菜单，请点击下方按钮。"
    )
    
    await cb.message.edit_caption(
        caption=info_text,
        reply_markup=back_to_main_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "common_server_info")
async def cb_common_server_info(cb: types.CallbackQuery):
    """服务器信息"""
    stats = await get_server_stats()
    group_members = await get_group_member_count(cb.bot)
    
    server_text = (
        f"🖥️ <b>服务器信息</b>\n\n"
        f"👥 总用户数: {stats.get('total_users', 0)}\n"
        f"👮 管理员数: {stats.get('total_admins', 0)}\n"
        f"🎬 求片总数: {stats.get('total_requests', 0)}\n"
        f"⏳ 待审求片: {stats.get('pending_requests', 0)}\n"
        f"📝 投稿总数: {stats.get('total_submissions', 0)}\n"
        f"⏳ 待审投稿: {stats.get('pending_submissions', 0)}\n"
        f"💬 反馈总数: {stats.get('total_feedback', 0)}\n"
        f"⏳ 待处理反馈: {stats.get('pending_feedback', 0)}\n"
    )
    
    if group_members > 0:
        server_text += f"🏠 群组成员: {group_members}\n"
    
    server_text += "\n如需返回主菜单，请点击下方按钮。"
    
    await cb.message.edit_caption(
        caption=server_text,
        reply_markup=back_to_main_kb
    )
    await cb.answer()


# ==================== 功能中心导航 ====================

@users_router.callback_query(F.data == "movie_center")
async def cb_movie_center(cb: types.CallbackQuery):
    """求片中心"""
    center_text = (
        f"🎬 <b>求片中心</b>\n\n"
        "欢迎来到求片中心！\n\n"
        "🎬 开始求片 - 提交新的求片请求\n"
        "📋 我的求片 - 查看我的求片记录\n\n"
        "请选择您需要的功能："
    )
    
    await cb.message.edit_caption(
        caption=center_text,
        reply_markup=movie_center_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "content_center")
async def cb_content_center(cb: types.CallbackQuery):
    """内容投稿中心"""
    center_text = (
        f"📝 <b>内容投稿中心</b>\n\n"
        "欢迎来到内容投稿中心！\n\n"
        "📝 开始投稿 - 提交新的内容投稿\n"
        "📋 我的投稿 - 查看我的投稿记录\n\n"
        "请选择您需要的功能："
    )
    
    await cb.message.edit_caption(
        caption=center_text,
        reply_markup=content_center_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "feedback_center")
async def cb_feedback_center(cb: types.CallbackQuery):
    """用户反馈中心"""
    center_text = (
        f"💬 <b>用户反馈中心</b>\n\n"
        "欢迎来到用户反馈中心！\n\n"
        "🐛 Bug反馈 - 报告程序错误\n"
        "💡 建议反馈 - 提出改进建议\n"
        "😤 投诉反馈 - 投诉相关问题\n"
        "❓ 其他反馈 - 其他类型反馈\n"
        "📋 我的反馈 - 查看反馈记录\n\n"
        "请选择反馈类型："
    )
    
    await cb.message.edit_caption(
        caption=center_text,
        reply_markup=feedback_center_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "other_functions")
async def cb_other_functions(cb: types.CallbackQuery):
    """其他功能"""
    functions_text = (
        f"⚙️ <b>其他功能</b>\n\n"
        "这里是一些额外的实用功能：\n\n"
        "🔁 切换忙碌状态 - 控制消息处理\n"
        "📖 帮助信息 - 查看使用帮助\n\n"
        "请选择您需要的功能："
    )
    
    await cb.message.edit_caption(
        caption=functions_text,
        reply_markup=other_functions_kb
    )
    await cb.answer()


# 普通文本消息：防并发回显
@users_router.message(F.text, IsCommand(), IsBusyFilter())
async def message(msg: types.Message):
    if await get_busy(msg.from_user.id):
        await msg.bot.send_message(msg.from_user.id, "请稍候，我正在处理你的上一个请求…")
        await asyncio.sleep(5)
        return

    try:
        await set_busy(msg.from_user.id, True)
        await msg.bot.send_message(msg.from_user.id, f"你发送了：{msg.text}")
    except Exception as e:
        logger.error(e)
    finally:
        await set_busy(msg.from_user.id, False)


# 处理内联菜单：帮助
@users_router.callback_query(F.data == "user_help")
async def cb_user_help(cb: types.CallbackQuery):
    await cb.message.edit_text(
        "<b>🤖 机器人帮助</b>\n- 发送任意文本，我会回显给你\n- 使用内联菜单查看更多功能",
        reply_markup=main_menu_kb,
    )
    await cb.answer()


# 处理内联菜单：我的信息
@users_router.callback_query(F.data == "user_profile")
async def cb_user_profile(cb: types.CallbackQuery):
    user = await get_user(cb.from_user.id)
    if not user:
        await cb.message.edit_text("未找到你的信息，稍后再试。", reply_markup=main_menu_kb)
    else:
        msg = (
            f"<b>用户名：</b> {user.username}\n"
            f"<b>昵称：</b> {user.full_name}\n"
            f"<b>聊天ID：</b> {user.chat_id}\n"
            f"<b>忙碌状态：</b> {'是' if user.is_busy else '否'}\n"
        )
        await cb.message.edit_text(msg, reply_markup=main_menu_kb)
    await cb.answer()


# 处理内联菜单：切换忙碌
@users_router.callback_query(F.data == "user_toggle_busy")
async def cb_toggle_busy(cb: types.CallbackQuery):
    current = await get_busy(cb.from_user.id)
    await set_busy(cb.from_user.id, not current)
    await cb.message.edit_text(
        f"忙碌状态已设置为：{'是' if not current else '否'}",
        reply_markup=main_menu_kb,
    )
    await cb.answer()
