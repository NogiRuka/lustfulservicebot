from aiogram import types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from utils.filters import IsAdmin, ChatTypeFilter
from bot import bot, router
from config import ADMINS_ID
from database.admin import (
    get_count_of_users,
    get_user_data,
    get_all_users_id,
    remove_user,
)
from buttons.admin import cancel_btn, clear_btn
from utils.states import Wait


@router.message(
    ChatTypeFilter(chat_type=["private"]), IsAdmin(ADMINS_ID), F.text == "Cancel 🚫"
)
async def Cancel(msg: types.Message, state: FSMContext):
    await bot.send_message(msg.from_user.id, "Canceled", reply_markup=clear_btn)
    await state.clear()


# Show all admin commands
@router.message(
    ChatTypeFilter(chat_type=["private"]), Command("commands"), IsAdmin(ADMINS_ID)
)
async def ShowCommands(msg: types.Message):
    message = """
<b>Users data</b>
/users
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>Export user data</b>
/info <code>chat_id</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>Announce</b>
/announce 
"""

    await bot.send_message(msg.from_user.id, message)


# Get count of users
@router.message(
    ChatTypeFilter(chat_type=["private"]), Command("users"), IsAdmin(ADMINS_ID)
)
async def GetCountOfUsers(msg: types.Message):
    users_len = await get_count_of_users()

    await bot.send_message(msg.from_user.id, "Users length: " + str(users_len))


# Get
@router.message(
    ChatTypeFilter(chat_type=["private"]), Command("info"), IsAdmin(ADMINS_ID)
)
async def GetUserData(msg: types.Message):
    chat_id = msg.text.replace("/info ", "")

    current_user = await get_user_data(int(chat_id))

    if not current_user:
        await bot.send_message(msg.from_user.id, "User not found")
        return

    message = f"""
<b>Username:</b> {current_user.username}
<b>Name:</b> {current_user.full_name}
<b>Chat id:</b> {current_user.chat_id}
<b>Created at:</b> {current_user.created_at.strftime("%Y-%m-%d %H:%M:%S")}
<b>Last activity at:</b> {current_user.last_activity_at.strftime("%Y-%m-%d %H:%M:%S")}
    """

    await bot.send_message(msg.from_user.id, message)


@router.message(
    ChatTypeFilter(chat_type=["private"]), Command("announce"), IsAdmin(ADMINS_ID)
)
async def Announce(msg: types.Message, state: FSMContext):
    await bot.send_message(
        msg.from_user.id,
        "Send me any type of message that you want to send to all users",
        reply_markup=cancel_btn,
    )
    await state.set_state(Wait.waitAnnounce)


@router.message(
    ChatTypeFilter(chat_type=["private"]),
    IsAdmin(ADMINS_ID),
    StateFilter(Wait.waitAnnounce),
)
async def ConfirmAnnounce(msg: types.Message, state: FSMContext):
    all_users_id = await get_all_users_id()

    users_len = len(all_users_id)

    active_users = 0
    inactive_users = 0

    await msg.reply(
        f"🙊Starting announcement to {users_len} users", reply_markup=clear_btn
    )

    for chat_id in all_users_id:
        try:
            await bot.copy_message(chat_id, msg.from_user.id, msg.message_id)
            active_users += 1
        except Exception as e:
            inactive_users += 1
            remove_user(chat_id)

    await bot.send_message(
        msg.from_user.id,
        f"<b>Successfully!</b>\n💚Active users: {active_users}\n💔Blocked users: {inactive_users}",
    )
    await state.clear()
