from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, and_, select
from datetime import datetime
from typing import List, Optional

from app.database.db import AsyncSessionLocal
from app.database.schema import SentMessage


async def create_sent_message_record(
    admin_id: int,
    target_type: str,
    target_id: int,
    target_name: str,
    message_content: str,
    sent_message_id: Optional[int] = None,
    status: str = "sent"
) -> int:
    """创建代发消息记录"""
    async with AsyncSessionLocal() as session:
        sent_message = SentMessage(
            admin_id=admin_id,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            message_content=message_content,
            sent_message_id=sent_message_id,
            status=status
        )
        session.add(sent_message)
        await session.commit()
        await session.refresh(sent_message)
        return sent_message.id


async def update_message_reply(
    target_id: int,
    reply_content: str,
    admin_id: Optional[int] = None
) -> bool:
    """更新消息回复内容"""
    async with AsyncSessionLocal() as session:
        # 查找最近发送给该用户的消息记录
        query = select(SentMessage).filter(
            and_(
                SentMessage.target_id == target_id,
                SentMessage.target_type == "user",
                SentMessage.status == "sent"
            )
        )
        
        if admin_id:
            query = query.filter(SentMessage.admin_id == admin_id)
            
        query = query.order_by(desc(SentMessage.sent_at))
        result = await session.execute(query)
        sent_message = result.scalars().first()
        
        if sent_message:
            sent_message.reply_content = reply_content
            sent_message.replied_at = datetime.now()
            sent_message.status = "replied"
            sent_message.is_read = False
            await session.commit()
            return True
        return False


async def get_unread_replies(admin_id: int) -> List[SentMessage]:
    """获取管理员的未读回复"""
    async with AsyncSessionLocal() as session:
        query = select(SentMessage).filter(
            and_(
                SentMessage.admin_id == admin_id,
                SentMessage.status == "replied",
                SentMessage.is_read == False
            )
        ).order_by(desc(SentMessage.replied_at))
        result = await session.execute(query)
        return result.scalars().all()


async def get_all_unread_replies() -> List[SentMessage]:
    """获取所有未读回复"""
    async with AsyncSessionLocal() as session:
        query = select(SentMessage).filter(
            and_(
                SentMessage.status == "replied",
                SentMessage.is_read == False
            )
        ).order_by(desc(SentMessage.replied_at))
        result = await session.execute(query)
        return result.scalars().all()


async def mark_reply_as_read(message_id: int) -> bool:
    """标记回复为已读"""
    async with AsyncSessionLocal() as session:
        query = select(SentMessage).filter(SentMessage.id == message_id)
        result = await session.execute(query)
        sent_message = result.scalars().first()
        
        if sent_message:
            sent_message.is_read = True
            await session.commit()
            return True
        return False


async def get_sent_messages_by_admin(admin_id: int, limit: int = 20) -> List[SentMessage]:
    """获取管理员发送的消息记录"""
    async with AsyncSessionLocal() as session:
        query = select(SentMessage).filter(
            SentMessage.admin_id == admin_id
        ).order_by(desc(SentMessage.sent_at)).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()


async def get_conversation_history(admin_id: int, target_id: int, limit: int = 10) -> List[SentMessage]:
    """获取与特定用户的对话历史"""
    async with AsyncSessionLocal() as session:
        query = select(SentMessage).filter(
            and_(
                SentMessage.admin_id == admin_id,
                SentMessage.target_id == target_id,
                SentMessage.target_type == "user"
            )
        ).order_by(desc(SentMessage.sent_at)).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()


async def delete_old_messages(days: int = 30) -> int:
    """删除指定天数前的消息记录"""
    async with AsyncSessionLocal() as session:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = select(SentMessage).filter(SentMessage.sent_at < cutoff_date)
        result = await session.execute(query)
        messages_to_delete = result.scalars().all()
        
        for message in messages_to_delete:
            await session.delete(message)
        
        await session.commit()
        return len(messages_to_delete)