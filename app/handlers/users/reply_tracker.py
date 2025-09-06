from aiogram import types, Router
from aiogram.filters import Command
from loguru import logger

from app.database.sent_messages import update_message_reply
from app.database.users import get_role
from app.utils.roles import ROLE_SUPERADMIN, ROLE_ADMIN

reply_tracker_router = Router()


@reply_tracker_router.message()
async def track_user_replies(msg: types.Message):
    """监听用户回复并记录到代发消息系统"""
    logger.debug(f"回复追踪器收到消息，用户: {msg.from_user.id}, 聊天类型: {msg.chat.type}")
    
    # 只处理私聊消息
    if msg.chat.type != 'private':
        logger.debug(f"跳过非私聊消息，聊天类型: {msg.chat.type}")
        return
    
    # 跳过命令消息
    if msg.text and msg.text.startswith('/'):
        logger.debug(f"跳过命令消息: {msg.text[:20]}...")
        return
    
    # 跳过管理员消息
    user_role = await get_role(msg.from_user.id)
    logger.debug(f"用户 {msg.from_user.id} 角色: {user_role}")
    if user_role in [ROLE_ADMIN, ROLE_SUPERADMIN]:
        logger.debug(f"跳过管理员消息，用户角色: {user_role}")
        return
    
    # 跳过空消息
    if not msg.text and not msg.caption:
        logger.debug("跳过空消息")
        return
    
    # 检查是否是回复机器人的反馈回复通知
    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if "反馈回复通知" in msg.reply_to_message.text:
            logger.info(f"用户 {msg.from_user.id} 回复了反馈回复通知，转为反馈回复处理")
            await handle_feedback_reply(msg)
            return
    
    logger.info(f"开始处理用户 {msg.from_user.id} 的回复消息")
    
    try:
        # 获取消息内容
        reply_content = msg.text or msg.caption or "[非文本消息]"
        
        # 如果消息过长，截取前500字符
        if len(reply_content) > 500:
            reply_content = reply_content[:500] + "..."
        
        # 尝试更新消息回复记录
        logger.info(f"尝试记录用户 {msg.from_user.id} 的回复: {reply_content[:50]}...")
        success = await update_message_reply(
            target_id=msg.from_user.id,
            reply_content=reply_content
        )
        
        if success:
            logger.info(f"用户 {msg.from_user.id} 的回复已成功记录: {reply_content[:50]}...")
        else:
            logger.warning(f"用户 {msg.from_user.id} 的回复未找到对应的代发消息记录")
            
            # 通知所有超管有新回复
            from app.config.config import SUPERADMIN_ID
            from app.database.business import get_admin_list
            
            # 获取用户信息
            from app.database.users import get_user
            user_info = await get_user(msg.from_user.id)
            user_name = user_info.full_name if user_info else f"用户{msg.from_user.id}"
            
            notification_text = (
                f"📬 <b>收到新回复</b>\n\n"
                f"👤 <b>用户</b>：{user_name} ({msg.from_user.id})\n"
                f"💬 <b>回复内容</b>：{reply_content[:100]}{'...' if len(reply_content) > 100 else ''}\n\n"
                f"💡 使用 /replies 查看所有回复"
            )
            
            # 发送给超管
            try:
                await msg.bot.send_message(
                    chat_id=SUPERADMIN_ID,
                    text=notification_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"发送回复通知给超管失败: {e}")
            
            # 发送给其他管理员
            try:
                admins = await get_admin_list()
                for admin in admins:
                    if admin.chat_id != SUPERADMIN_ID:  # 避免重复发送给超管
                        try:
                            await msg.bot.send_message(
                                chat_id=admin.chat_id,
                                text=notification_text,
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logger.error(f"发送回复通知给管理员 {admin.chat_id} 失败: {e}")
            except Exception as e:
                logger.error(f"获取管理员列表失败: {e}")
        
    except Exception as e:
        logger.error(f"处理用户回复失败: {e}")


async def handle_feedback_reply(msg: types.Message):
    """处理用户回复反馈的消息"""
    try:
        # 从回复的消息中提取反馈ID
        reply_text = msg.reply_to_message.text
        feedback_id = None
        
        # 查找反馈ID（格式：反馈ID: 123）
        import re
        match = re.search(r'反馈ID[：:] ?(\d+)', reply_text)
        if match:
            feedback_id = int(match.group(1))
        
        if not feedback_id:
            logger.warning(f"无法从反馈回复通知中提取反馈ID: {reply_text}")
            return
        
        # 获取用户回复内容
        user_reply = msg.text or msg.caption or "[非文本消息]"
        
        # 获取用户信息
        from app.database.users import get_user
        user_info = await get_user(msg.from_user.id)
        user_name = user_info.full_name if user_info else f"用户{msg.from_user.id}"
        
        # 构建通知消息
        notification_text = (
            f"📬 <b>收到反馈回复</b>\n\n"
            f"👤 <b>用户</b>：{user_name} ({msg.from_user.id})\n"
            f"🆔 <b>反馈ID</b>：{feedback_id}\n"
            f"💬 <b>回复内容</b>：{user_reply}\n\n"
            f"⏰ <b>回复时间</b>：{msg.date.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # 发送给所有管理员
        from app.config.config import SUPERADMIN_ID
        from app.database.business import get_admin_list
        
        # 发送给超管
        try:
            await msg.bot.send_message(
                chat_id=SUPERADMIN_ID,
                text=notification_text,
                parse_mode="HTML"
            )
            logger.info(f"反馈回复通知已发送给超管: 反馈ID {feedback_id}")
        except Exception as e:
            logger.error(f"发送反馈回复通知给超管失败: {e}")
        
        # 发送给其他管理员
        try:
            admins = await get_admin_list()
            for admin in admins:
                if admin.chat_id != SUPERADMIN_ID:  # 避免重复发送给超管
                    try:
                        await msg.bot.send_message(
                            chat_id=admin.chat_id,
                            text=notification_text,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"发送反馈回复通知给管理员 {admin.chat_id} 失败: {e}")
        except Exception as e:
            logger.error(f"获取管理员列表失败: {e}")
        
        logger.info(f"用户 {msg.from_user.id} 的反馈回复已处理完成，反馈ID: {feedback_id}")
        
    except Exception as e:
        logger.error(f"处理反馈回复失败: {e}")