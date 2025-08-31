from app.config.config import BOT_NICKNAME


def create_welcome_panel_text(title: str, role: str = None) -> str:
    """
    创建欢迎面板文本
    
    Args:
        title: 面板标题内容
        role: 用户角色（可选）
    
    Returns:
        格式化的欢迎文本
    """
    welcome_text = (
        f"🌸 **欢迎来到 {BOT_NICKNAME}** 🌸\n\n"
    )
    
    if role:
        welcome_text += f"🎭 **您的身份**：{role}\n\n"
    
    welcome_text += (
        f"✨ **专属功能面板** ✨\n"
        f"{title}\n\n"
        f"💫 **开始您的精彩体验吧！** 💫"
    )
    
    return welcome_text


def create_info_panel_text(user_info: dict) -> str:
    """
    创建信息面板文本
    
    Args:
        user_info: 包含用户信息的字典
            - username: 用户名
            - full_name: 昵称
            - user_id: 用户ID
            - role: 角色
            - created_at: 注册时间
            - last_activity_at: 最后活跃时间
    
    Returns:
        格式化的信息文本
    """
    info_text = (
        f"🌟 **个人档案** 🌟\n\n"
        f"┌─────────────────────┐\n"
        f"│ 👤 **基本信息**\n"
        f"├─────────────────────┤\n"
        f"│ 🏷️ **用户名**: `{user_info.get('username', '未设置')}`\n"
        f"│ 📝 **昵称**: {user_info.get('full_name', '未知')}\n"
        f"│ 🆔 **用户ID**: `{user_info.get('user_id', '未知')}`\n"
        f"│ 🎭 **身份角色**: **{user_info.get('role', '未知')}**\n"
        f"├─────────────────────┤\n"
        f"│ ⏰ **时间记录**\n"
        f"├─────────────────────┤\n"
        f"│ 📅 **注册时间**: {user_info.get('created_at', '未知')}\n"
        f"│ 🕐 **最后活跃**: {user_info.get('last_activity_at', '未知')}\n"
        f"└─────────────────────┘\n\n"
        f"💫 **感谢您使用我们的服务！** 💫"
    )
    
    return info_text


# 默认的欢迎图片URL
DEFAULT_WELCOME_PHOTO = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"