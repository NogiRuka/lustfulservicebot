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
        f"🌸 <b>欢迎来到 {BOT_NICKNAME}</b> 🌸\n\n"
    )
    
    welcome_text += (
        f"✨ <b>专属功能面板</b> ✨\n"
        f"{title}"
    )
    
    return welcome_text


def create_info_panel_text(user_info: dict) -> str:
    info_text = (
        f"🌟 <b>个人档案</b> 🌟\n\n"
        f"👤 <b>基本信息</b>\n"
        f"├ 用户名: <a href='https://t.me/{user_info.get('username', '未设置')}'>@{user_info.get('username', '未设置')}</a>\n"
        f"├ 昵称: {user_info.get('full_name', '未知')}\n"
        f"├ 用户ID: <code>{user_info.get('user_id', '未知')}</code>\n"
        f"└ 身份角色: <b>{'用户' if user_info.get('role') == 'user' else '管理员' if user_info.get('role') == 'admin' else '超级管理员' if user_info.get('role') == 'superadmin' else '未知'}</b>\n\n"
        f"⏰ <b>时间记录</b>\n"
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
        return "🎬 <b>开始求片</b> 🎬\n\n📂 请选择您要求片的类型："
    
    elif step == "input_title":
        return f"🎬 <b>开始求片</b> 🎬\n\n📂 <b>类型</b>：{category_name or '未知类型'}\n\n📝 请输入您想要的片名："
    
    elif step == "input_description":
        return (
            f"🎬 <b>开始求片</b> 🎬\n\n"
            f"📂 <b>类型</b>：{category_name or '未知类型'}\n"
            f"✅ <b>片名</b>：{title or '未知'}\n\n"
            f"📝 <b>请输入详细描述</b>\n"
            f"├ 可以发送豆瓣链接或其他\n"
            f"├ 可以描述剧情、演员、年份等信息\n"
            f"├ 也可以发送相关图片\n"
            f"└ 仅限一条消息（文字或一张图片+说明文字）\n\n"
            f"💡 <i>详细信息有助于更快找到资源</i>"
        )
    
    else:
        return "🎬 <b>求片流程</b> 🎬\n\n请按照提示完成操作"


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
        return "📝 <b>开始投稿</b> 📝\n\n📂 请选择内容类型："
    
    elif step == "input_title":
        return f"📝 <b>开始投稿</b> 📝\n\n📂 <b>类型</b>：【{category_name or '通用内容'}】\n\n📝 请输入投稿标题："
    
    elif step == "input_content":
        return (
            f"📝 <b>开始投稿</b> 📝\n\n"
            f"📂 <b>类型</b>：【{category_name or '通用内容'}】\n"
            f"✅ <b>标题</b>：{title or '未知'}\n\n"
            f"📄 <b>请输入投稿内容</b>\n"
            f"├ 可以发送磁力链接\n"
            f"├ 可以发送网盘链接\n"
            f"├ 可以发送资源描述\n"
            f"└ 仅限一条消息（文字或一张图片+说明文字）\n\n"
            f"💡 <i>丰富的内容更容易通过审核</i>"
        )
    
    else:
        return "📝 <b>投稿流程</b> 📝\n\n请按照提示完成操作"


async def send_review_notification(bot, user_id: int, item_type: str, item_title: str, status: str, review_note: str = None):
    """
    发送审核结果通知给用户
    
    Args:
        bot: 机器人实例
        user_id: 用户ID
        item_type: 项目类型 ('movie', 'content', 'feedback')
        item_title: 项目标题
        status: 审核状态 ('approved', 'rejected')
        review_note: 审核备注（可选）
    """
    try:
        # 根据类型和状态生成通知文本
        type_emoji = {
            'movie': '🎬',
            'content': '📝',
            'feedback': '💬'
        }.get(item_type, '📋')
        
        type_name = {
            'movie': '求片',
            'content': '投稿',
            'feedback': '反馈'
        }.get(item_type, '项目')
        
        if status == 'approved':
            status_emoji = '✅'
            status_text = '已通过'
            title_text = f"🎉 <b>{type_name}审核通过</b> 🎉"
        else:
            status_emoji = '❌'
            status_text = '已拒绝'
            title_text = f"📋 <b>{type_name}审核结果</b> 📋"
        
        notification_text = (
            f"{title_text}\n\n"
            f"{type_emoji} <b>{type_name}标题</b>：{item_title}\n"
            f"{status_emoji} <b>审核结果</b>：{status_text}\n\n"
        )
        
        if review_note:
            notification_text += f"💬 <b>管理员留言</b>：\n{review_note}\n\n"
        
        if status == 'approved':
            notification_text += "💫 感谢您的{type_name}，已成功通过审核！".format(type_name=type_name)
        else:
            notification_text += "📝 如有疑问，请联系管理员了解详情。"
        
        await bot.send_message(
            chat_id=user_id,
            text=notification_text,
            parse_mode="HTML"
        )
        
    except Exception as e:
        from loguru import logger
        logger.error(f"发送审核通知失败: {e}")


# 默认的欢迎图片URL
DEFAULT_WELCOME_PHOTO = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"