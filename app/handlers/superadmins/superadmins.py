from aiogram import types, Router
from aiogram.filters import Command

from app.database.users import set_role, get_role
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN, ROLE_USER


superadmins_router = Router()


@superadmins_router.message(Command("promote"))
async def PromoteToAdmin(msg: types.Message):
    # 仅超管可用
    caller_role = await get_role(msg.from_user.id)
    if caller_role != ROLE_SUPERADMIN:
        await msg.bot.send_message(msg.from_user.id, "仅超管可执行此操作。")
        return

    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.bot.send_message(msg.from_user.id, "用法：/promote [chat_id]")
        return
    target_id = int(parts[1])
    ok = await set_role(target_id, ROLE_ADMIN)
    if ok:
        await msg.bot.send_message(msg.from_user.id, f"已将 {target_id} 设为管理员。")
    else:
        await msg.bot.send_message(msg.from_user.id, "操作失败，请稍后重试。")


@superadmins_router.message(Command("demote"))
async def DemoteFromAdmin(msg: types.Message):
    caller_role = await get_role(msg.from_user.id)
    if caller_role != ROLE_SUPERADMIN:
        await msg.bot.send_message(msg.from_user.id, "仅超管可执行此操作。")
        return

    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.bot.send_message(msg.from_user.id, "用法：/demote [chat_id]")
        return
    target_id = int(parts[1])
    ok = await set_role(target_id, ROLE_USER)
    if ok:
        await msg.bot.send_message(msg.from_user.id, f"已将 {target_id} 设为普通用户。")
    else:
        await msg.bot.send_message(msg.from_user.id, "操作失败，请稍后重试。")


