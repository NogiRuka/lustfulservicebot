from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, func, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户数据表（详细信息）。"""

    __tablename__ = "users"

    # 基础信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    is_busy = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_activity_at = Column(DateTime, nullable=True)
    # 角色：user / admin / superadmin
    role = Column(String, nullable=False, server_default="user")
    
    # 网络信息
    ip_address = Column(String, nullable=True)  # IP地址
    user_agent = Column(Text, nullable=True)  # 用户代理字符串
    
    # 地理位置信息
    country = Column(String, nullable=True)  # 国家
    country_code = Column(String, nullable=True)  # 国家代码
    region = Column(String, nullable=True)  # 地区/省份
    city = Column(String, nullable=True)  # 城市
    timezone = Column(String, nullable=True)  # 时区
    latitude = Column(String, nullable=True)  # 纬度
    longitude = Column(String, nullable=True)  # 经度
    
    # Telegram详细信息
    language_code = Column(String, nullable=True)  # 语言代码
    is_bot = Column(Boolean, default=False, nullable=False)  # 是否为机器人
    is_premium = Column(Boolean, default=False, nullable=False)  # 是否为Premium用户
    added_to_attachment_menu = Column(Boolean, default=False, nullable=False)  # 是否添加到附件菜单
    can_join_groups = Column(Boolean, default=True, nullable=False)  # 是否可以加入群组
    can_read_all_group_messages = Column(Boolean, default=False, nullable=False)  # 是否可以读取所有群组消息
    supports_inline_queries = Column(Boolean, default=False, nullable=False)  # 是否支持内联查询
    
    # 设备信息
    device_type = Column(String, nullable=True)  # 设备类型（mobile/desktop/tablet）
    platform = Column(String, nullable=True)  # 平台（iOS/Android/Windows/macOS/Linux）
    app_version = Column(String, nullable=True)  # 应用版本
    
    # 统计信息
    total_messages = Column(Integer, default=0, nullable=False)  # 总消息数
    total_commands = Column(Integer, default=0, nullable=False)  # 总命令数
    total_requests = Column(Integer, default=0, nullable=False)  # 总求片数
    total_submissions = Column(Integer, default=0, nullable=False)  # 总投稿数
    total_feedback = Column(Integer, default=0, nullable=False)  # 总反馈数
    
    # 行为分析
    preferred_category = Column(String, nullable=True)  # 偏好分类
    most_active_hour = Column(Integer, nullable=True)  # 最活跃时间（小时）
    avg_session_duration = Column(Integer, nullable=True)  # 平均会话时长（秒）
    last_command = Column(String, nullable=True)  # 最后使用的命令
    
    # 安全信息
    login_attempts = Column(Integer, default=0, nullable=False)  # 登录尝试次数
    is_blocked = Column(Boolean, default=False, nullable=False)  # 是否被封禁
    blocked_reason = Column(Text, nullable=True)  # 封禁原因
    blocked_at = Column(DateTime, nullable=True)  # 封禁时间
    blocked_by = Column(BigInteger, nullable=True)  # 封禁操作者
    
    # 隐私设置
    allow_location_tracking = Column(Boolean, default=True, nullable=False)  # 是否允许位置跟踪
    allow_analytics = Column(Boolean, default=True, nullable=False)  # 是否允许数据分析
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, name={self.full_name}, country={self.country})>"


class MovieCategory(Base):
    """内容分类表（求片和投稿共用）。"""
    
    __tablename__ = "movie_categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)  # 类型名称
    description = Column(Text, nullable=True)  # 类型描述
    is_active = Column(Boolean, nullable=False, default=True)  # 是否启用
    sort_order = Column(Integer, nullable=False, server_default="0")  # 排序
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    created_by = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)  # 创建人
    
    def __repr__(self):
        return f"<MovieCategory(id={self.id}, name={self.name}, is_active={self.is_active})>"


class MovieRequest(Base):
    """求片请求表。"""
    
    __tablename__ = "movie_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)
    category_id = Column(Integer, ForeignKey('movie_categories.id'), nullable=False)  # 类型ID
    title = Column(String, nullable=False)  # 片名
    description = Column(Text, nullable=True)  # 描述
    file_id = Column(String, nullable=True)  # Telegram文件ID
    status = Column(String, nullable=False, server_default="pending")  # pending/approved/rejected
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(BigInteger, nullable=True)  # 审核人ID
    review_note = Column(Text, nullable=True)  # 审核备注
    
    # 关系
    category = relationship("MovieCategory")
    
    def __repr__(self):
        return f"<MovieRequest(id={self.id}, title={self.title}, status={self.status})>"


class ContentSubmission(Base):
    """内容投稿表。"""
    
    __tablename__ = "content_submissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)
    category_id = Column(Integer, ForeignKey('movie_categories.id'), nullable=True)  # 类型ID（可选）
    title = Column(String, nullable=False)  # 标题
    content = Column(Text, nullable=False)  # 内容
    file_id = Column(String, nullable=True)  # Telegram文件ID
    status = Column(String, nullable=False, server_default="pending")  # pending/approved/rejected
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(BigInteger, nullable=True)  # 审核人ID
    review_note = Column(Text, nullable=True)  # 审核备注
    
    # 关系
    category = relationship("MovieCategory")
    
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
    created_at = Column(DateTime, default=datetime.now, nullable=False)
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
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    def __repr__(self):
        return f"<AdminAction(id={self.id}, admin={self.admin_id}, action={self.action_type})>"


class SystemSettings(Base):
    """系统功能开关表。"""
    
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String, nullable=False, unique=True)  # 设置键名
    setting_value = Column(String, nullable=False)  # 设置值
    setting_type = Column(String, nullable=False, server_default="boolean")  # 设置类型：boolean/string/integer
    description = Column(Text, nullable=True)  # 设置描述
    is_active = Column(Boolean, nullable=False, default=True)  # 是否启用
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    updated_by = Column(BigInteger, ForeignKey('users.chat_id'), nullable=True)  # 最后修改人
    
    def __repr__(self):
        return f"<SystemSettings(id={self.id}, key={self.setting_key}, value={self.setting_value})>"


class DevChangelog(Base):
    """开发日志表。"""
    
    __tablename__ = "dev_changelog"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String, nullable=False)  # 版本号
    title = Column(String, nullable=False)  # 更新标题
    content = Column(Text, nullable=False)  # 更新内容
    changelog_type = Column(String, nullable=False, server_default="update")  # update/bugfix/feature/hotfix
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    created_by = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)  # 创建者ID（超管）
    
    def __repr__(self):
        return f"<DevChangelog(id={self.id}, version={self.version}, title={self.title})>"


class ImageLibrary(Base):
    """图片库表 - 存储超管发送的图片信息"""

    __tablename__ = "image_library"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, nullable=False, unique=True)  # Telegram文件ID
    file_unique_id = Column(String, nullable=True)  # Telegram唯一文件ID
    file_url = Column(String, nullable=True)  # 图片URL（如果有）
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    width = Column(Integer, nullable=True)  # 图片宽度
    height = Column(Integer, nullable=True)  # 图片高度
    caption = Column(Text, nullable=True)  # 图片说明
    uploaded_by = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)  # 上传者ID（超管）
    uploaded_at = Column(DateTime, default=datetime.now, nullable=False)  # 上传时间
    is_active = Column(Boolean, default=True, nullable=False)  # 是否启用
    usage_count = Column(Integer, default=0, nullable=False)  # 使用次数
    last_used_at = Column(DateTime, nullable=True)  # 最后使用时间
    tags = Column(String, nullable=True)  # 标签（用逗号分隔）
    
    def __repr__(self):
        return f"<ImageLibrary(id={self.id}, file_id='{self.file_id}', uploaded_by={self.uploaded_by})>"


class SentMessage(Base):
    """代发消息追踪表"""

    __tablename__ = "sent_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)  # 发送消息的管理员ID
    target_type = Column(String, nullable=False)  # 目标类型：user/channel/group
    target_id = Column(BigInteger, nullable=False)  # 目标ID（用户ID、频道ID、群组ID）
    target_name = Column(String, nullable=True)  # 目标名称（用于显示）
    message_content = Column(Text, nullable=False)  # 发送的消息内容
    sent_message_id = Column(BigInteger, nullable=True)  # 发送成功后的消息ID
    status = Column(String, nullable=False, server_default="sent")  # sent/failed/replied
    sent_at = Column(DateTime, default=datetime.now, nullable=False)  # 发送时间
    reply_content = Column(Text, nullable=True)  # 用户回复内容
    replied_at = Column(DateTime, nullable=True)  # 回复时间
    is_read = Column(Boolean, default=False, nullable=False)  # 管理员是否已读回复
    
    def __repr__(self):
        return f"<SentMessage(id={self.id}, admin_id={self.admin_id}, target_type='{self.target_type}', target_id={self.target_id})>"
