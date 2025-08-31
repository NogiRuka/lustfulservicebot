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
    
    welcome_text += (
        f"✨ **专属功能面板** ✨\n"
        f"{title}"
    )
    
    return welcome_text


def create_info_panel_text(user_info: dict) -> str:
    info_text = (
        f"🌟 **个人档案** 🌟\n\n"
        f"👤 **基本信息**\n"
        f"├ 用户名: `{user_info.get('username', '未设置')}`\n"
        f"├ 昵称: {user_info.get('full_name', '未知')}\n"
        f"├ 用户ID: `{user_info.get('user_id', '未知')}`\n"
        f"└ 身份角色: **{user_info.get('role', '未知')}**\n\n"
        f"⏰ **时间记录**\n"
        f"├ 开始时间: {user_info.get('created_at', '未知')}\n"
        f"└ 最后活跃: {user_info.get('last_activity_at', '未知')}"
    )
    
    return info_text


def create_movie_request_text(step: str, category_name: str = None, title: str = None) -> str:
    """
    创建求片流程的提示文本
    
    Args:
        step: 当前步骤 ('select_category', 'input_title', 'input_description')
        category_name: 类型名称（可选）
        title: 片名（可选）
    
    Returns:
        格式化的提示文本
    """
    if step == "select_category":
        return "🎬 **开始求片** 🎬\n\n📂 请选择您要求片的类型："
    
    elif step == "input_title":
        return f"🎬 **开始求片** 🎬\n\n📂 **类型**：{category_name or '未知类型'}\n\n📝 请输入您想要的片名："
    
    elif step == "input_description":
        return (
            f"🎬 **开始求片** 🎬\n\n"
            f"📂 **类型**：{category_name or '未知类型'}\n"
            f"✅ **片名**：{title or '未知'}\n\n"
            f"📝 **请输入详细描述**\n"
            f"├ 可以发送豆瓣链接或其他\n"
            f"├ 可以描述剧情、演员、年份等信息\n"
            f"├ 也可以发送相关图片\n"
            f"└ 仅限一条消息（文字或一张图片+说明文字）\n\n"
            f"💡 *详细信息有助于更快找到资源*"
        )
    
    else:
        return "🎬 **求片流程** 🎬\n\n请按照提示完成操作"


def create_content_submit_text(step: str, category_name: str = None, title: str = None) -> str:
    """
    创建内容投稿流程的提示文本
    
    Args:
        step: 当前步骤 ('select_category', 'input_title', 'input_content')
        category_name: 类型名称（可选）
        title: 标题（可选）
    
    Returns:
        格式化的提示文本
    """
    if step == "select_category":
        return "📝 **开始投稿** 📝\n\n📂 请选择内容类型："
    
    elif step == "input_title":
        return f"📝 **开始投稿** 📝\n\n📂 **类型**：【{category_name or '通用内容'}】\n\n📝 请输入投稿标题："
    
    elif step == "input_content":
        return (
            f"📝 **开始投稿** 📝\n\n"
            f"📂 **类型**：【{category_name or '通用内容'}】\n"
            f"✅ **标题**：{title or '未知'}\n\n"
            f"📄 **请输入投稿内容**\n"
            f"├ 可以发送磁力链接\n"
            f"├ 可以发送网盘链接\n"
            f"├ 可以发送资源描述\n"
            f"└ 仅限一条消息（文字或一张图片+说明文字）\n\n"
            f"💡 *丰富的内容更容易通过审核*"
        )
    
    else:
        return "📝 **投稿流程** 📝\n\n请按照提示完成操作"


# 默认的欢迎图片URL
DEFAULT_WELCOME_PHOTO = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"