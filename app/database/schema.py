from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, func
from sqlalchemy.ext.declarative import declarative_base

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
