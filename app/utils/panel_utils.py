from app.config.config import BOT_NICKNAME
from app.database.users import get_user


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
        f"🌸 欢迎来到 <b>{BOT_NICKNAME}</b> 🌸\n\n"
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


async def send_review_notification(bot, user_id: int, item_type: str, item_title: str, status: str, review_note: str = None, file_id: str = None, item_content: str = None, item_id: int = None, category_name: str = None):
    """
    发送审核结果通知给用户
    
    Args:
        bot: 机器人实例
        user_id: 用户ID
        item_type: 项目类型 ('movie', 'content', 'feedback')
        item_title: 项目标题
        status: 审核状态 ('approved', 'rejected')
        review_note: 审核备注（可选）
        file_id: 图片文件ID（可选）
        item_content: 项目内容（可选，用于频道同步）
        item_id: 项目ID（可选，用于频道同步）
        category_name: 分类名称（可选，如电影、剧集、国产等）
    """
    from loguru import logger
    logger.info(f"开始发送审核通知: user_id={user_id}, item_type={item_type}, title={item_title}, status={status}")
    
    try:
        # 根据类型和状态生成美化的通知文本
        type_config = {
            'movie': {
                'emoji': '🎬',
                'name': '求片',
                'icon': '🎭',
                'category': '影视内容'
            },
            'content': {
                'emoji': '📝',
                'name': '投稿',
                'icon': '✍️',
                'category': '原创内容'
            },
            'feedback': {
                'emoji': '💬',
                'name': '反馈',
                'icon': '📢',
                'category': '用户反馈'
            }
        }
        
        config = type_config.get(item_type, {
            'emoji': '📋',
            'name': '项目',
            'icon': '📄',
            'category': '其他内容'
        })
        
        if status == 'approved':
            status_emoji = '✅'
            status_text = '审核通过'
            status_color = '🟢'
            title_decoration = '🎉✨🎉'
            title_text = f"{title_decoration} <b>{config['name']}审核通过</b> {title_decoration}"
            result_bg = '━━━━━━━━━━━━━━━━━━━━'
        else:
            status_emoji = '❌'
            status_text = '审核拒绝'
            status_color = '🔴'
            title_decoration = '📋⚠️📋'
            title_text = f"{title_decoration} <b>{config['name']}审核结果</b> {title_decoration}"
            result_bg = '━━━━━━━━━━━━━━━━━━━━'
        
        # 构建美化的通知消息
        # 如果有分类名称，显示具体分类；否则显示默认类别
        category_display = f"{category_name}"
        
        notification_text = (
            f"{title_text}\n"
            f"{result_bg}\n\n"
            f"{config['icon']} <b>内容类型</b>：{category_display}\n"
            f"{config['emoji']} <b>标题</b>：{item_title}\n"
            f"{status_color} <b>审核状态</b>：{status_emoji} {status_text}\n"
        )
        
        # 添加项目ID（如果有）
        if item_id:
            notification_text += f"🆔 <b>项目编号</b>：#{item_id}\n"
        
        notification_text += f"\n{result_bg}\n"
        
        # 添加管理员留言
        if review_note:
            notification_text += f"\n💬 <b>管理员留言</b>：\n📄 {review_note}\n\n{result_bg}\n"
        
        # 添加结尾消息
        if status == 'approved':
            notification_text += (
                f"\n🎊 <b>恭喜您！</b>\n"
                f"💫 您的{config['name']}已成功通过审核！\n"
                f"🚀 内容将会在相关频道展示\n"
                f"🙏 感谢您的优质贡献！"
            )
        else:
            notification_text += (
                f"\n📝 <b>温馨提示</b>：\n"
                f"🔍 如对审核结果有疑问，请联系管理员\n"
                f"💡 您可以根据建议修改后重新提交\n"
                f"🤝 感谢您的理解与配合！"
            )
        
        # 发送通知给用户（带图片或纯文本）
        logger.info(f"准备发送通知给用户 {user_id}, 是否有图片: {bool(file_id)}")
        
        if file_id:
            await bot.send_photo(
                chat_id=user_id,
                photo=file_id,
                caption=notification_text,
                parse_mode="HTML"
            )
            logger.info(f"已发送图片通知给用户 {user_id}")
        else:
            await bot.send_message(
                chat_id=user_id,
                text=notification_text,
                parse_mode="HTML"
            )
            logger.info(f"已发送文本通知给用户 {user_id}")
        
        # 如果审核通过，同步到频道
        if status == 'approved' and item_type in ['movie', 'content']:
            logger.info(f"准备同步到频道: {item_type} - {item_title}")
            await sync_to_channel(bot, item_type, item_title, item_content, file_id, user_id, item_id, category_name)
        else:
            logger.info(f"跳过频道同步: status={status}, item_type={item_type}")
        
    except Exception as e:
        from loguru import logger
        logger.error(f"发送审核通知失败: {e}")


async def sync_to_channel(bot, item_type: str, item_title: str, item_content: str = None, file_id: str = None, user_id: int = None, item_id: int = None, category_name: str = None):
    """
    同步审核通过的内容到频道
    
    Args:
        bot: 机器人实例
        item_type: 项目类型 ('movie', 'content')
        item_title: 项目标题
        item_content: 项目内容（可选）
        file_id: 图片文件ID（可选）
        user_id: 用户ID（可选）
        item_id: 项目ID（可选）
        category_name: 分类名称（可选，如电影、剧集、国产等）
    """
    try:
        from app.config.config import SYNC_CHANNELS
        
        if not SYNC_CHANNELS:
            return  # 如果没有配置频道，则不同步
        
        # 获取用户信息（不显示ID）
        user_display = "匿名用户"
        if user_id:
            try:
                user = await get_user(user_id)
                if user and user.username:
                    user_display = f"@{user.username}"
                elif user and user.full_name:
                    user_display = user.full_name
                else:
                    user_display = f"用户{user_id}"
            except Exception:
                user_display = f"用户{user_id}"
        
        # 根据类型生成美化的频道消息
        type_config = {
            'movie': {
                'emoji': '🎬',
                'name': '求片',
                'icon': '🎭',
                'category': '影视内容',
                'bg_emoji': '🎪',
                'title_decoration': '🌟🎬🌟'
            },
            'content': {
                'emoji': '📝',
                'name': '投稿',
                'icon': '✍️',
                'category': '原创内容',
                'bg_emoji': '📚',
                'title_decoration': '✨📝✨'
            }
        }
        
        config = type_config.get(item_type, {
            'emoji': '📋',
            'name': '内容',
            'icon': '📄',
            'category': '其他内容',
            'bg_emoji': '📋',
            'title_decoration': '⭐📋⭐'
        })
        
        # 构建美化的频道消息
        title_text = f"{config['title_decoration']} <b>{config['name']}上新</b> {config['title_decoration']}"
        
        # 如果有分类名称，显示具体分类；否则显示默认类别
        category_display = f"{config['category']} - {category_name}" if category_name else config['category']
        
        channel_text = (
            f"{title_text}\n\n"
            f"{config['bg_emoji']} <b>内容分类</b>：{category_display}\n"
            f"{config['emoji']} <b>标题</b>：{item_title}\n"
        )
        
        # 添加项目信息
        current_time = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')
        channel_text += (
            f"👤 <b>贡献者</b>：{user_display}\n"
            f"🎯 <b>审核状态</b>：✅ 已通过审核\n"
            f"📅 <b>发布时间</b>：{current_time}\n"
        )
        
        # 发送到所有配置的频道（带图片或纯文本）
        success_count = 0
        for channel in SYNC_CHANNELS:
            try:
                if file_id:
                    await bot.send_photo(
                        chat_id=channel,
                        photo=file_id,
                        caption=channel_text,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=channel,
                        text=channel_text,
                        parse_mode="HTML"
                    )
                success_count += 1
            except Exception as e:
                from loguru import logger
                logger.error(f"同步到频道 {channel} 失败: {e}")
        
        from loguru import logger
        if success_count > 0:
            logger.info(f"已同步{config['name']}到 {success_count}/{len(SYNC_CHANNELS)} 个频道: {item_title}")
        else:
            logger.warning(f"同步{config['name']}到所有频道都失败: {item_title}")
        
    except Exception as e:
        from loguru import logger
        logger.error(f"同步到频道失败: {e}")


async def get_user_display_link(user_id: int) -> str:
    """
    根据用户ID生成用户显示链接
    
    Args:
        user_id: 用户ID
    
    Returns:
        格式化的用户链接或用户ID（包含用户ID）
    """
    try:
        user = await get_user(user_id)
        if user and user.username:
            # 显示用户名和用户ID，使用 | 分隔
            return f"<a href='https://t.me/{user.username}'>@{user.username}</a> | ID:{user_id}"
        elif user and user.full_name:
            # 如果没有用户名但有全名，显示全名和用户ID
            return f"{user.full_name} | ID:{user_id}"
        else:
            return f"用户{user_id}"
    except Exception:
        return f"用户{user_id}"


async def cleanup_sent_media_messages(bot, state):
    """
    清理已发送的媒体消息
    
    Args:
        bot: 机器人实例
        state: FSM状态
    """
    try:
        data = await state.get_data()
        sent_media_ids = data.get('sent_media_ids', [])
        
        for message_id in sent_media_ids:
            try:
                await bot.delete_message(chat_id=data.get('chat_id'), message_id=message_id)
            except Exception as e:
                from loguru import logger
                logger.warning(f"删除媒体消息失败 {message_id}: {e}")
        
        # 清空已发送的媒体消息记录
        await state.update_data(sent_media_ids=[])
        
    except Exception as e:
        from loguru import logger
        logger.error(f"清理媒体消息失败: {e}")


async def send_feedback_reply_notification(bot, user_id: int, feedback_id: int, reply_content: str, original_feedback: str = None):
    """
    发送反馈回复通知给用户
    
    Args:
        bot: 机器人实例
        user_id: 用户ID
        feedback_id: 反馈ID
        reply_content: 回复内容
        original_feedback: 原始反馈内容
    """
    try:
        notification_text = (
            f"💬 <b>反馈回复通知</b> 💬\n\n"
            f"🆔 <b>反馈ID</b>：{feedback_id}\n"
        )
        
        # 如果有原始反馈内容，则显示
        if original_feedback:
            notification_text += f"📝 <b>您的反馈</b>：\n{original_feedback}\n\n"
        
        notification_text += (
            f"👨‍💼 <b>管理员回复</b>：\n{reply_content}\n\n"
            f"💡 <b>如需回复</b>：请直接回复此消息，您的回复将转达给管理员\n"
            f"📝 感谢您的反馈，如有其他问题请继续联系我们。"
        )
        
        await bot.send_message(
            chat_id=user_id,
            text=notification_text,
            parse_mode="HTML"
        )
        
    except Exception as e:
        from loguru import logger
        logger.error(f"发送反馈回复通知失败: {e}")


async def send_admin_message_notification(bot, user_id: int, item_type: str, item_title: str, item_id: int, message_content: str):
    """
    发送管理员消息通知给用户
    
    Args:
        bot: 机器人实例
        user_id: 用户ID
        item_type: 项目类型 ('movie', 'content', 'feedback')
        item_title: 项目标题
        item_id: 项目ID
        message_content: 消息内容
    """
    try:
        type_name = {
            'movie': '求片',
            'content': '投稿',
            'feedback': '反馈'
        }.get(item_type, '项目')
        
        notification_text = (
            f"📨 <b>管理员消息</b> 📨\n\n"
            f"📋 <b>关于</b>：{type_name} - {item_title}\n"
            f"🆔 <b>ID</b>：{item_id}\n\n"
            f"💬 <b>消息内容</b>：\n{message_content}\n\n"
            f"💡 <b>如需回复</b>：请直接回复此消息，您的回复将转达给管理员\n"
            f"📝 如有其他疑问，请联系管理员。"
        )
        
        await bot.send_message(
            chat_id=user_id,
            text=notification_text,
            parse_mode="HTML"
        )
        
    except Exception as e:
        from loguru import logger
        logger.error(f"发送管理员消息通知失败: {e}")


# 默认的欢迎图片URL
# DEFAULT_WELCOME_PHOTO = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"

DEFAULT_WELCOME_PHOTO = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/JQVISION_ISSUE16_078.jpg?raw=true"