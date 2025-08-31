from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN


# 用户主菜单（内联键盘）
def get_user_main_menu() -> InlineKeyboardMarkup:
    """获取用户主菜单"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🙋 我的信息", callback_data="common_my_info"),
                InlineKeyboardButton(text="🖥️ 服务信息", callback_data="common_server_info"),
            ],
            [
                InlineKeyboardButton(text="🎬 求片中心", callback_data="movie_center"),
                InlineKeyboardButton(text="📝 内容投稿", callback_data="content_center"),
            ],
            [
                InlineKeyboardButton(text="💬 用户反馈", callback_data="feedback_center"),
                InlineKeyboardButton(text="⚙️ 其他功能", callback_data="other_functions"),
            ],
        ]
    )


# 管理员主菜单
def get_admin_main_menu() -> InlineKeyboardMarkup:
    """获取管理员主菜单"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🙋 我的信息", callback_data="common_my_info"),
                InlineKeyboardButton(text="🖥️ 服务器信息", callback_data="common_server_info"),
            ],
            [
                InlineKeyboardButton(text="🎬 求片中心", callback_data="movie_center"),
                InlineKeyboardButton(text="📝 内容投稿", callback_data="content_center"),
            ],
            [
                InlineKeyboardButton(text="💬 用户反馈", callback_data="feedback_center"),
                InlineKeyboardButton(text="👀 反馈浏览", callback_data="admin_feedback_browse"),
            ],
            [
                InlineKeyboardButton(text="✅ 审核处理", callback_data="admin_review_center"),
                InlineKeyboardButton(text="⚙️ 其他功能", callback_data="other_functions"),
            ],
        ]
    )


# 超管主菜单
def get_superadmin_main_menu() -> InlineKeyboardMarkup:
    """获取超管主菜单"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🙋 我的信息", callback_data="common_my_info"),
                InlineKeyboardButton(text="🖥️ 服务器信息", callback_data="common_server_info"),
            ],
            [
                InlineKeyboardButton(text="🎬 求片中心", callback_data="movie_center"),
                InlineKeyboardButton(text="📝 内容投稿", callback_data="content_center"),
            ],
            [
                InlineKeyboardButton(text="💬 用户反馈", callback_data="feedback_center"),
                InlineKeyboardButton(text="👀 反馈浏览", callback_data="admin_feedback_browse"),
            ],
            [
                InlineKeyboardButton(text="✅ 审核处理", callback_data="admin_review_center"),
                InlineKeyboardButton(text="🛡️ 管理中心", callback_data="superadmin_manage_center"),
            ],
            [
                InlineKeyboardButton(text="🤖 人工回复", callback_data="superadmin_manual_reply"),
                InlineKeyboardButton(text="⚙️ 其他功能", callback_data="other_functions"),
            ],
        ]
    )


# 根据角色获取对应的主菜单
def get_main_menu_by_role(role: str) -> InlineKeyboardMarkup:
    """根据角色获取对应的主菜单"""
    if role == ROLE_SUPERADMIN:
        return get_superadmin_main_menu()
    elif role == ROLE_ADMIN:
        return get_admin_main_menu()
    else:
        return get_user_main_menu()


# 求片中心菜单
movie_center_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 开始求片", callback_data="movie_request_new"),
            InlineKeyboardButton(text="📋 我的求片", callback_data="movie_request_my"),
        ],
        [
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)

# 求片输入菜单（带返回上一级）
movie_input_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center"),
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)


# 内容投稿菜单
content_center_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 开始投稿", callback_data="content_submit_new"),
            InlineKeyboardButton(text="📋 我的投稿", callback_data="content_submit_my"),
        ],
        [
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)

# 内容投稿输入菜单（带返回上一级）
content_input_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center"),
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)


# 用户反馈菜单
feedback_center_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🐛 Bug反馈", callback_data="feedback_bug"),
            InlineKeyboardButton(text="💡 建议反馈", callback_data="feedback_suggestion"),
        ],
        [
            InlineKeyboardButton(text="😤 投诉反馈", callback_data="feedback_complaint"),
            InlineKeyboardButton(text="❓ 其他反馈", callback_data="feedback_other"),
        ],
        [
            InlineKeyboardButton(text="📋 我的反馈", callback_data="feedback_my"),
        ],
        [
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)

# 反馈输入菜单（带返回上一级）
feedback_input_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="feedback_center"),
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)


# 管理员审核中心菜单
admin_review_center_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 求片审核", callback_data="admin_review_movie"),
            InlineKeyboardButton(text="📝 投稿审核", callback_data="admin_review_content"),
        ],
        [
            InlineKeyboardButton(text="📋 所有求片", callback_data="admin_all_movies"),
            InlineKeyboardButton(text="📄 所有投稿", callback_data="admin_all_content"),
        ],
        [
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)

# 审核详情菜单（带返回上一级）
admin_review_detail_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="admin_review_center"),
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)


# 超管管理中心菜单
superadmin_manage_center_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ 添加管理", callback_data="superadmin_add_admin"),
            InlineKeyboardButton(text="👥 我的管理", callback_data="superadmin_my_admins"),
        ],
        [
            InlineKeyboardButton(text="📂 类型管理", callback_data="superadmin_category_manage"),
            InlineKeyboardButton(text="⚙️ 系统设置", callback_data="superadmin_system_settings"),
        ],
        [
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)

# 超管操作菜单（带返回上一级）
superadmin_action_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="superadmin_manage_center"),
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)


# 其他功能菜单
other_functions_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔁 切换忙碌状态", callback_data="user_toggle_busy"),
            InlineKeyboardButton(text="📖 帮助信息", callback_data="user_help"),
        ],
        [
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)


# 返回按钮
back_to_main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ]
)


# 兼容性：保留原有的main_menu_kb
main_menu_kb = get_user_main_menu()


