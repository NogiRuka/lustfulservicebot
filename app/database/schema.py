from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, func, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """用户数据表。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    is_busy = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, nullable=True)
    # 角色：user / admin / superadmin
    role = Column(String, nullable=False, server_default="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, name={self.full_name})>"


class MovieRequest(Base):
    """求片请求表。"""
    
    __tablename__ = "movie_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)
    title = Column(String, nullable=False)  # 片名
    description = Column(Text, nullable=True)  # 描述
    status = Column(String, nullable=False, server_default="pending")  # pending/approved/rejected
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(BigInteger, nullable=True)  # 审核人ID
    
    def __repr__(self):
        return f"<MovieRequest(id={self.id}, title={self.title}, status={self.status})>"


class ContentSubmission(Base):
    """内容投稿表。"""
    
    __tablename__ = "content_submissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)
    title = Column(String, nullable=False)  # 标题
    content = Column(Text, nullable=False)  # 内容
    file_id = Column(String, nullable=True)  # Telegram文件ID
    status = Column(String, nullable=False, server_default="pending")  # pending/approved/rejected
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(BigInteger, nullable=True)  # 审核人ID
    
    def __repr__(self):
        return f"<ContentSubmission(id={self.id}, title={self.title}, status={self.status})>"


class UserFeedback(Base):
    """用户反馈表。"""
    
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)
    feedback_type = Column(String, nullable=False)  # bug/suggestion/complaint/other
    content = Column(Text, nullable=False)
    status = Column(String, nullable=False, server_default="pending")  # pending/processing/resolved
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    replied_at = Column(DateTime, nullable=True)
    replied_by = Column(BigInteger, nullable=True)  # 回复人ID
    reply_content = Column(Text, nullable=True)  # 回复内容
    
    def __repr__(self):
        return f"<UserFeedback(id={self.id}, type={self.feedback_type}, status={self.status})>"


class AdminAction(Base):
    """管理员操作记录表。"""
    
    __tablename__ = "admin_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)
    action_type = Column(String, nullable=False)  # promote/demote/review/reply
    target_id = Column(BigInteger, nullable=True)  # 目标用户ID或内容ID
    description = Column(Text, nullable=False)  # 操作描述
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<AdminAction(id={self.id}, admin={self.admin_id}, action={self.action_type})>"
