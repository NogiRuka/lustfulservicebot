from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, and_
from datetime import datetime
from typing import List, Optional

from app.database.db import engine
from app.database.schema import SentMessage

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    session = SessionLocal()
    try:
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
        session.commit()
        session.refresh(sent_message)
        return sent_message.id
    finally:
        session.close()


async def update_message_reply(
    target_id: int,
    reply_content: str,
    admin_id: Optional[int] = None
) -> bool:
    """更新消息回复内容"""
    session = SessionLocal()
    try:
        # 查找最近发送给该用户的消息记录
        query = session.query(SentMessage).filter(
            and_(
                SentMessage.target_id == target_id,
                SentMessage.target_type == "user",
                SentMessage.status == "sent"
            )
        )
        
        if admin_id:
            query = query.filter(SentMessage.admin_id == admin_id)
            
        sent_message = query.order_by(desc(SentMessage.sent_at)).first()
        
        if sent_message:
            sent_message.reply_content = reply_content
            sent_message.replied_at = datetime.now()
            sent_message.status = "replied"
            sent_message.is_read = False
            session.commit()
            return True
        return False
    finally:
        session.close()


async def get_unread_replies(admin_id: int) -> List[SentMessage]:
    """获取管理员的未读回复"""
    session = SessionLocal()
    try:
        return session.query(SentMessage).filter(
            and_(
                SentMessage.admin_id == admin_id,
                SentMessage.status == "replied",
                SentMessage.is_read == False
            )
        ).order_by(desc(SentMessage.replied_at)).all()
    finally:
        session.close()


async def get_all_unread_replies() -> List[SentMessage]:
    """获取所有未读回复"""
    session = SessionLocal()
    try:
        return session.query(SentMessage).filter(
            and_(
                SentMessage.status == "replied",
                SentMessage.is_read == False
            )
        ).order_by(desc(SentMessage.replied_at)).all()
    finally:
        session.close()


async def mark_reply_as_read(message_id: int) -> bool:
    """标记回复为已读"""
    session = SessionLocal()
    try:
        sent_message = session.query(SentMessage).filter(
            SentMessage.id == message_id
        ).first()
        
        if sent_message:
            sent_message.is_read = True
            session.commit()
            return True
        return False
    finally:
        session.close()


async def get_sent_messages_by_admin(admin_id: int, limit: int = 20) -> List[SentMessage]:
    """获取管理员发送的消息记录"""
    session = SessionLocal()
    try:
        return session.query(SentMessage).filter(
            SentMessage.admin_id == admin_id
        ).order_by(desc(SentMessage.sent_at)).limit(limit).all()
    finally:
        session.close()


async def get_conversation_history(admin_id: int, target_id: int, limit: int = 10) -> List[SentMessage]:
    """获取与特定用户的对话历史"""
    session = SessionLocal()
    try:
        return session.query(SentMessage).filter(
            and_(
                SentMessage.admin_id == admin_id,
                SentMessage.target_id == target_id,
                SentMessage.target_type == "user"
            )
        ).order_by(desc(SentMessage.sent_at)).limit(limit).all()
    finally:
        session.close()


async def delete_old_messages(days: int = 30) -> int:
    """删除指定天数前的消息记录"""
    session = SessionLocal()
    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        deleted_count = session.query(SentMessage).filter(
            SentMessage.sent_at < cutoff_date
        ).delete()
        
        session.commit()
        return deleted_count
    finally:
        session.close()