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

admins_router = Router()


@admins_router.message(Command("panel"))
async def ShowPanel(msg: types.Message):
    await msg.bot.send_message(msg.from_user.id, "管理员面板：", reply_markup=admin_panel_kb)


# 面板回调：统计
@admins_router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(cb: types.CallbackQuery):
    users_len = await get_count_of_users()
    await cb.message.edit_text(f"当前用户总数：{users_len}", reply_markup=admin_panel_kb)
    await cb.answer()


# 面板回调：查询提示
@admins_router.callback_query(F.data == "admin_query_user")
async def cb_admin_query_tip(cb: types.CallbackQuery):
    await cb.message.edit_text("请使用命令：/info <chat_id>", reply_markup=admin_panel_kb)
    await cb.answer()


# 面板回调：群发公告指引
@admins_router.callback_query(F.data == "admin_announce")
async def cb_admin_announce_tip(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text("请发送要群发给所有用户的消息（任意类型）", reply_markup=admin_panel_kb)
    await state.set_state(Wait.waitAnnounce)
    await cb.answer()


# 面板回调：清理封禁用户（懒方式：实际在群发时自动移除）
@admins_router.callback_query(F.data == "admin_cleanup")
async def cb_admin_cleanup(cb: types.CallbackQuery):
    await cb.message.edit_text("清理功能在群发时自动进行：无法接收的用户会被移除。", reply_markup=admin_panel_kb)
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
        await msg.bot.send_message(msg.from_user.id, "用法：/info <chat_id>")
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


# 仅超管：升为管理员
@admins_router.message(Command("promote"))
async def PromoteToAdmin(msg: types.Message):
    caller_role = await get_role(msg.from_user.id)
    if caller_role != ROLE_SUPERADMIN:
        await msg.bot.send_message(msg.from_user.id, "仅超管可执行此操作。")
        return

    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.bot.send_message(msg.from_user.id, "用法：/promote <chat_id>")
        return
    target_id = int(parts[1])
    ok = await set_role(target_id, ROLE_ADMIN)
    if ok:
        await msg.bot.send_message(msg.from_user.id, f"已将 {target_id} 设为管理员。")
    else:
        await msg.bot.send_message(msg.from_user.id, "操作失败，请稍后重试。")


# 仅超管：取消管理员
@admins_router.message(Command("demote"))
async def DemoteFromAdmin(msg: types.Message):
    caller_role = await get_role(msg.from_user.id)
    if caller_role != ROLE_SUPERADMIN:
        await msg.bot.send_message(msg.from_user.id, "仅超管可执行此操作。")
        return

    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.bot.send_message(msg.from_user.id, "用法：/demote <chat_id>")
        return
    target_id = int(parts[1])
    ok = await set_role(target_id, ROLE_USER)
    if ok:
        await msg.bot.send_message(msg.from_user.id, f"已将 {target_id} 设为普通用户。")
    else:
        await msg.bot.send_message(msg.from_user.id, "操作失败，请稍后重试。")
