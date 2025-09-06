from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN


# ==================== 公共按钮常量 ====================

# 常用按钮
BTN_MY_INFO = InlineKeyboardButton(text="🙋 我的信息", callback_data="common_my_info")
BTN_SERVER_INFO = InlineKeyboardButton(text="🖥️ 服务信息", callback_data="common_server_info")
BTN_MOVIE_CENTER = InlineKeyboardButton(text="🎬 求片中心", callback_data="movie_center")
BTN_CONTENT_CENTER = InlineKeyboardButton(text="📝 内容投稿", callback_data="content_center")
BTN_FEEDBACK_CENTER = InlineKeyboardButton(text="💬 用户反馈", callback_data="feedback_center")
BTN_OTHER_FUNCTIONS = InlineKeyboardButton(text="⚙️ 其他功能", callback_data="other_functions")

# 导航按钮
BTN_BACK_TO_MAIN = InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
BTN_BACK_TO_MOVIE = InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center")
BTN_BACK_TO_CONTENT = InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center")
BTN_BACK_TO_FEEDBACK = InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="feedback_center")
BTN_BACK_TO_REVIEW = InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="admin_review_center")
BTN_BACK_TO_SUPERADMIN = InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="superadmin_manage_center")

# 管理员专用按钮
BTN_FEEDBACK_BROWSE = InlineKeyboardButton(text="👀 反馈浏览", callback_data="admin_feedback_browse")
BTN_REVIEW_CENTER = InlineKeyboardButton(text="✅ 审核处理", callback_data="admin_review_center")
BTN_SUPERADMIN_CENTER = InlineKeyboardButton(text="🛡️ 管理中心", callback_data="superadmin_manage_center")
BTN_MANUAL_REPLY = InlineKeyboardButton(text="🤖 代发消息", callback_data="superadmin_manual_reply")


# ==================== 菜单构建函数 ====================


# 用户主菜单（内联键盘）
def get_user_main_menu() -> InlineKeyboardMarkup:
    """获取用户主菜单"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [BTN_MY_INFO, BTN_SERVER_INFO],
            [BTN_MOVIE_CENTER, BTN_CONTENT_CENTER],
            [BTN_FEEDBACK_CENTER, BTN_OTHER_FUNCTIONS],
        ]
    )


# 管理员主菜单
def get_admin_main_menu() -> InlineKeyboardMarkup:
    """获取管理员主菜单"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [BTN_MY_INFO, BTN_SERVER_INFO],
            [BTN_MOVIE_CENTER, BTN_CONTENT_CENTER],
            [BTN_FEEDBACK_CENTER, BTN_FEEDBACK_BROWSE],
            [BTN_REVIEW_CENTER, BTN_OTHER_FUNCTIONS],
        ]
    )


# 超管主菜单
def get_superadmin_main_menu() -> InlineKeyboardMarkup:
    """获取超管主菜单"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [BTN_MY_INFO, BTN_SERVER_INFO],
            [BTN_MOVIE_CENTER, BTN_CONTENT_CENTER],
            [BTN_FEEDBACK_CENTER, BTN_FEEDBACK_BROWSE],
            [BTN_REVIEW_CENTER, BTN_SUPERADMIN_CENTER],
            [BTN_MANUAL_REPLY, BTN_OTHER_FUNCTIONS],
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
        [BTN_BACK_TO_MAIN],
    ]
)

# 求片输入菜单（带返回上一级）
movie_input_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [BTN_BACK_TO_MOVIE, BTN_BACK_TO_MAIN],
    ]
)


# 内容投稿菜单
content_center_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 开始投稿", callback_data="content_submit_new"),
            InlineKeyboardButton(text="📋 我的投稿", callback_data="content_submit_my"),
        ],
        [BTN_BACK_TO_MAIN],
    ]
)

# 内容投稿输入菜单（带返回上一级）
content_input_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [BTN_BACK_TO_CONTENT, BTN_BACK_TO_MAIN],
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
            BTN_BACK_TO_MAIN,
        ],
    ]
)

# 反馈输入菜单（带返回上一级）
feedback_input_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [BTN_BACK_TO_FEEDBACK, BTN_BACK_TO_MAIN],
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
            InlineKeyboardButton(text="🔍 高级浏览", callback_data="admin_advanced_browse"),
            InlineKeyboardButton(text="👀 反馈浏览", callback_data="admin_feedback_browse"),
        ],
        [BTN_BACK_TO_MAIN],
    ]
)

# 审核详情菜单（带返回上一级）
admin_review_detail_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [BTN_BACK_TO_REVIEW, BTN_BACK_TO_MAIN],
    ]
)

# 高级浏览菜单
admin_advanced_browse_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 浏览求片", callback_data="browse_requests_btn"),
            InlineKeyboardButton(text="📝 浏览投稿", callback_data="browse_submissions_btn"),
        ],
        [
            InlineKeyboardButton(text="💬 浏览反馈", callback_data="browse_feedback_btn"),
            InlineKeyboardButton(text="👥 浏览用户", callback_data="browse_users_btn"),
        ],
        [BTN_BACK_TO_REVIEW, BTN_BACK_TO_MAIN],
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
        [BTN_BACK_TO_MAIN],
    ]
)

# 超管操作菜单（带返回上一级）
superadmin_action_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [BTN_BACK_TO_SUPERADMIN, BTN_BACK_TO_MAIN],
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
            InlineKeyboardButton(text="🗑️ 清空记录", callback_data="clear_chat_history"),
            BTN_BACK_TO_MAIN,
        ],
    ]
)


# 返回主菜单键盘
back_to_main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [BTN_BACK_TO_MAIN],
    ]
)


# 兼容性：保留原有的main_menu_kb
main_menu_kb = get_user_main_menu()


