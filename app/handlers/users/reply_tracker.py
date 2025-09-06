from aiogram import types, Router
from aiogram.filters import Command
from loguru import logger

from app.database.sent_messages import update_message_reply
from app.database.users import get_role
from app.utils.roles import ROLE_SUPERADMIN

reply_tracker_router = Router()


@reply_tracker_router.message()
async def track_user_replies(msg: types.Message):
    """监听用户回复并记录到代发消息系统"""
    # 只处理私聊消息
    if msg.chat.type != 'private':
        return
    
    # 跳过命令消息
    if msg.text and msg.text.startswith('/'):
        return
    
    # 跳过管理员消息
    user_role = await get_role(msg.from_user.id)
    if user_role in ['admin', 'superadmin']:
        return
    
    # 跳过空消息
    if not msg.text and not msg.caption:
        return
    
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