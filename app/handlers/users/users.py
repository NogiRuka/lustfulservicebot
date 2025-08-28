import asyncio

from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command
from loguru import logger

from app.utils.filters import IsBusyFilter, IsCommand
from app.database.users import get_busy, set_busy, get_user
from app.database.users import get_role
from app.buttons.users import main_menu_kb
from app.buttons.panels import get_panel_for_role
from app.utils.commands_catalog import build_commands_help


users_router = Router()


# /start：欢迎与菜单
@users_router.message(IsBusyFilter(), CommandStart())
async def start(msg: types.Message):
    role = await get_role(msg.from_user.id)
    title, kb = get_panel_for_role(role)
    await msg.bot.send_message(msg.from_user.id, title, reply_markup=kb)


# /help：帮助信息
@users_router.message(Command("help"))
async def help_handler(msg: types.Message):
    help_message = (
        "<b>🤖 机器人帮助</b>\n"
        "- 发送任意文本，我会回显给你\n"
        "- 使用内联菜单查看更多功能"
    )
    await msg.bot.send_message(msg.from_user.id, help_message)


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
