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
            f"🌟 **欢迎使用 [{BOT_NICKNAME}](https://t.me/{bot_username})**\n💫 请在私聊中使用机器人功能",
            parse_mode="Markdown"
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
        parse_mode="Markdown"
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
    
    welcome_text = f"🎉 欢迎使用机器人！\n\n👤 用户角色：{role}\n\n{title}"
    welcome_photo = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"
    
    # 检查当前消息是否有图片
    if cb.message.photo:
        # 如果有图片，编辑caption
        await cb.message.edit_caption(
            caption=welcome_text,
            reply_markup=kb
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
            reply_markup=kb
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
        parse_mode="Markdown"
    )
    await cb.answer()


@basic_router.callback_query(F.data == "common_server_info")
async def cb_common_server_info(cb: types.CallbackQuery):
    """服务器信息"""
    try:
        stats = await get_server_stats()
        member_count = await get_group_member_count(cb.bot)
        
        info_text = (
            f"🖥️ **服务信息** 🖥️\n\n"
            f"📊 **统计数据**\n"
            f"├ 使用用户: {stats['total_users']}\n"
            f"├ 求片请求: {stats['total_requests']}\n"
            f"└ 内容投稿: {stats['total_submissions']}\n\n"
            f"💫 **感谢您的使用！** 💫"
        )
    except Exception as e:
        logger.error(f"获取服务信息失败: {e}")
        info_text = (
            f"🖥️ <b>服务信息</b>\n\n"
            "❌ 暂时无法获取服务信息，请稍后重试。\n\n"
            "如需返回主菜单，请点击下方按钮。"
        )
    
    await cb.message.edit_caption(
        caption=info_text,
        reply_markup=back_to_main_kb,
        parse_mode="Markdown"
    )
    await cb.answer()


@basic_router.callback_query(F.data == "other_functions")
async def cb_other_functions(cb: types.CallbackQuery):
    """其他功能"""
    await cb.message.edit_caption(
        caption="⚙️ <b>其他功能</b>\n\n请选择您需要的功能：",
        reply_markup=other_functions_kb
    )
    await cb.answer()


# 普通文本消息：防并发回显
@basic_router.message(F.text, IsCommand(), IsBusyFilter())
async def message(msg: types.Message, state: FSMContext):
    """处理普通文本消息"""
    # 检查用户是否处于某个状态中，如果是则不处理
    current_state = await state.get_state()
    if current_state is not None:
        logger.debug(f"用户 {msg.from_user.id} 处于状态 {current_state}，跳过通用消息处理")
        return
    
    await asyncio.sleep(1)
    await msg.reply(
        f"📝 您发送的消息：{msg.text}\n\n"
        "💡 提示：使用 /menu 查看功能菜单"
    )