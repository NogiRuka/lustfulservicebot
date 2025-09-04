from sqlalchemy import select, update, func
from datetime import datetime
from loguru import logger

from app.database.db import get_db
from app.database.schema import User
from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN
from app.config import SUPERADMIN_ID


async def add_user(
    chat_id: int, 
    full_name: str, 
    username: str | None,
    language_code: str = None,
    is_bot: bool = False,
    is_premium: bool = False,
    ip_address: str = None,
    user_agent: str = None,
    device_info: dict = None
) -> bool:
    """
    添加用户到数据库（若不存在则创建），包含详细信息。
    """
    async for session in get_db():
        try:
            # Check if the user already exists
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            is_exists = result.scalars().first()

            if not is_exists:
                safe_username = username if username else f"user_{chat_id}"
                new_user = User(
                    chat_id=chat_id,
                    full_name=full_name,
                    username=safe_username,
                    role=ROLE_USER,
                    language_code=language_code,
                    is_bot=is_bot,
                    is_premium=is_premium,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_type=device_info.get('device_type') if device_info else None,
                    platform=device_info.get('platform') if device_info else None,
                    app_version=device_info.get('app_version') if device_info else None,
                )
                session.add(new_user)
                await session.commit()  # Commit the transaction
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            await session.rollback()  # Rollback in case of error
            return False


async def get_user(chat_id: int) -> User | None:
    """根据 chat_id 获取用户。找不到返回 None。"""
    async for session in get_db():
        try:
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            await session.rollback()
            return None


async def set_role(chat_id: int, role: str) -> bool:
    """设置用户角色。"""
    async for session in get_db():
        try:
            await session.execute(
                update(User).filter_by(chat_id=chat_id).values(role=role)
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting role: {e}")
            await session.rollback()
            return False


async def get_role(chat_id: int) -> str:
    """获取用户角色，默认 user。"""
    async for session in get_db():
        try:
            # 环境层：超管唯一 ID 拥有最高权限
            if SUPERADMIN_ID is not None and chat_id == SUPERADMIN_ID:
                return ROLE_SUPERADMIN
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user.role if user and user.role else ROLE_USER
        except Exception as e:
            logger.error(f"Error getting role: {e}")
            await session.rollback()
            return ROLE_USER


async def set_busy(chat_id: int, is_busy: bool) -> None:
    """设置用户忙碌状态。"""
    async for session in get_db():
        try:
            await session.execute(
                update(User).filter_by(chat_id=chat_id).values(is_busy=is_busy)
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Error setting busy status: {e}")
            await session.rollback()


async def get_busy(chat_id: int) -> bool:
    """获取用户忙碌状态，默认 False。"""
    async for session in get_db():
        try:
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user.is_busy if user else False
        except Exception as e:
            logger.error(f"Error getting busy status: {e}")
            await session.rollback()
            return False


async def update_last_acitivity(chat_id: int) -> None:
    """更新用户最近活跃时间为当前本地时间。"""
    async for session in get_db():
        try:
            await session.execute(
                update(User)
                .filter_by(chat_id=chat_id)
                .values(last_activity_at=datetime.now())
            )
            await session.commit()
        except Exception as e:
            logger.error(f"更新用户最后活动时间失败: {e}")
            await session.rollback()


async def update_user_location(chat_id: int, location_data: dict) -> bool:
    """
    更新用户地理位置信息。
    """
    async for session in get_db():
        try:
            await session.execute(
                update(User)
                .filter_by(chat_id=chat_id)
                .values(
                    country=location_data.get('country'),
                    country_code=location_data.get('country_code'),
                    region=location_data.get('region'),
                    city=location_data.get('city'),
                    timezone=location_data.get('timezone'),
                    latitude=location_data.get('latitude'),
                    longitude=location_data.get('longitude')
                )
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"更新用户地理位置失败: {e}")
            await session.rollback()
            return False


async def update_user_stats(chat_id: int, stat_type: str, increment: int = 1) -> bool:
    """
    更新用户统计信息。
    stat_type: 'messages', 'commands', 'requests', 'submissions', 'feedback'
    """
    async for session in get_db():
        try:
            stat_mapping = {
                'messages': User.total_messages,
                'commands': User.total_commands,
                'requests': User.total_requests,
                'submissions': User.total_submissions,
                'feedback': User.total_feedback
            }
            
            if stat_type not in stat_mapping:
                return False
                
            await session.execute(
                update(User)
                .filter_by(chat_id=chat_id)
                .values({stat_mapping[stat_type]: stat_mapping[stat_type] + increment})
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"更新用户统计信息失败: {e}")
            await session.rollback()
            return False


async def update_user_behavior(chat_id: int, behavior_data: dict) -> bool:
    """
    更新用户行为分析数据。
    """
    async for session in get_db():
        try:
            update_values = {}
            if 'preferred_category' in behavior_data:
                update_values['preferred_category'] = behavior_data['preferred_category']
            if 'most_active_hour' in behavior_data:
                update_values['most_active_hour'] = behavior_data['most_active_hour']
            if 'avg_session_duration' in behavior_data:
                update_values['avg_session_duration'] = behavior_data['avg_session_duration']
            if 'last_command' in behavior_data:
                update_values['last_command'] = behavior_data['last_command']
                
            if update_values:
                await session.execute(
                    update(User)
                    .filter_by(chat_id=chat_id)
                    .values(**update_values)
                )
                await session.commit()
            return True
        except Exception as e:
            logger.error(f"更新用户行为数据失败: {e}")
            await session.rollback()
            return False


async def block_user(chat_id: int, reason: str, blocked_by: int) -> bool:
    """
    封禁用户。
    """
    async for session in get_db():
        try:
            await session.execute(
                update(User)
                .filter_by(chat_id=chat_id)
                .values(
                    is_blocked=True,
                    blocked_reason=reason,
                    blocked_at=datetime.now(),
                    blocked_by=blocked_by
                )
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"封禁用户失败: {e}")
            await session.rollback()
            return False


async def unblock_user(chat_id: int) -> bool:
    """
    解封用户。
    """
    async for session in get_db():
        try:
            await session.execute(
                update(User)
                .filter_by(chat_id=chat_id)
                .values(
                    is_blocked=False,
                    blocked_reason=None,
                    blocked_at=None,
                    blocked_by=None
                )
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"解封用户失败: {e}")
            await session.rollback()
            return False


async def get_user_detailed_info(chat_id: int) -> dict | None:
    """
    获取用户详细信息。
    """
    async for session in get_db():
        try:
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            
            if not user:
                return None
                
            return {
                'basic_info': {
                    'chat_id': user.chat_id,
                    'full_name': user.full_name,
                    'username': user.username,
                    'role': user.role,
                    'created_at': user.created_at,
                    'last_activity_at': user.last_activity_at
                },
                'network_info': {
                    'ip_address': user.ip_address,
                    'user_agent': user.user_agent
                },
                'location_info': {
                    'country': user.country,
                    'country_code': user.country_code,
                    'region': user.region,
                    'city': user.city,
                    'timezone': user.timezone,
                    'latitude': user.latitude,
                    'longitude': user.longitude
                },
                'telegram_info': {
                    'language_code': user.language_code,
                    'is_bot': user.is_bot,
                    'is_premium': user.is_premium,
                    'added_to_attachment_menu': user.added_to_attachment_menu,
                    'can_join_groups': user.can_join_groups,
                    'can_read_all_group_messages': user.can_read_all_group_messages,
                    'supports_inline_queries': user.supports_inline_queries
                },
                'device_info': {
                    'device_type': user.device_type,
                    'platform': user.platform,
                    'app_version': user.app_version
                },
                'statistics': {
                    'total_messages': user.total_messages,
                    'total_commands': user.total_commands,
                    'total_requests': user.total_requests,
                    'total_submissions': user.total_submissions,
                    'total_feedback': user.total_feedback
                },
                'behavior': {
                    'preferred_category': user.preferred_category,
                    'most_active_hour': user.most_active_hour,
                    'avg_session_duration': user.avg_session_duration,
                    'last_command': user.last_command
                },
                'security': {
                    'login_attempts': user.login_attempts,
                    'is_blocked': user.is_blocked,
                    'blocked_reason': user.blocked_reason,
                    'blocked_at': user.blocked_at,
                    'blocked_by': user.blocked_by
                },
                'privacy': {
                    'allow_location_tracking': user.allow_location_tracking,
                    'allow_analytics': user.allow_analytics
                }
            }
        except Exception as e:
            logger.error(f"获取用户详细信息失败: {e}")
            return None
