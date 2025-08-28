from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# 用户主菜单（内联键盘）
main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📖 帮助", callback_data="user_help"),
            InlineKeyboardButton(text="🙋 我的信息", callback_data="user_profile"),
        ],
        [
            InlineKeyboardButton(text="🔁 切换忙碌状态", callback_data="user_toggle_busy"),
        ],
    ]
)


