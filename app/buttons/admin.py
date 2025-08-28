from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# 管理员主面板（内联键盘）
admin_panel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 用户统计", callback_data="admin_stats"),
            InlineKeyboardButton(text="🔎 查询用户", callback_data="admin_query_user"),
        ],
        [
            InlineKeyboardButton(text="📢 群发公告", callback_data="admin_announce"),
            InlineKeyboardButton(text="🧹 清理封禁用户", callback_data="admin_cleanup"),
        ],
    ]
)

# 取消与清理（用于回复键盘移除的场景已不再需要，保留占位）
