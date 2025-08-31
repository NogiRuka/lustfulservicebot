from sqlalchemy import select, delete, func, update
from sqlalchemy.orm import selectinload
from app.database.schema import User, MovieRequest, ContentSubmission, UserFeedback, AdminAction, MovieCategory, SystemSettings
from app.database.db import get_db
from loguru import logger
from typing import List, Optional
from datetime import datetime


# ==================== 管理员管理 ====================

async def promote_user_to_admin(admin_id: int, target_id: int) -> bool:
    """提升用户为管理员"""
    async for session in get_db():
        try:
            # 更新用户角色
            result = await session.execute(
                update(User).where(User.chat_id == target_id).values(role="admin")
            )
            
            # 记录管理员操作
            action = AdminAction(
                admin_id=admin_id,
                action_type="promote",
                target_id=target_id,
                description=f"提升用户 {target_id} 为管理员"
            )
            session.add(action)
            
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"提升管理员失败: {e}")
            await session.rollback()
            return False


async def demote_admin_to_user(admin_id: int, target_id: int) -> bool:
    """降级管理员为普通用户"""
    async for session in get_db():
        try:
            # 更新用户角色
            result = await session.execute(
                update(User).where(User.chat_id == target_id).values(role="user")
            )
            
            # 记录管理员操作
            action = AdminAction(
                admin_id=admin_id,
                action_type="demote",
                target_id=target_id,
                description=f"降级管理员 {target_id} 为普通用户"
            )
            session.add(action)
            
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"降级管理员失败: {e}")
            await session.rollback()
            return False


async def get_admin_list() -> List[User]:
    """获取所有管理员列表"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(User).where(User.role.in_(["admin", "superadmin"]))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取管理员列表失败: {e}")
            return []


# ==================== 求片中心 ====================

async def create_movie_request(user_id: int, category_id: int, title: str, description: str = None, file_id: str = None) -> bool:
    """创建求片请求"""
    async for session in get_db():
        try:
            request = MovieRequest(
                user_id=user_id,
                category_id=category_id,
                title=title,
                description=description,
                file_id=file_id,
                created_at=datetime.now()  # 使用本地时间而不是数据库服务器时间
            )
            session.add(request)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"创建求片请求失败: {e}")
            await session.rollback()
            return False


async def get_user_movie_requests(user_id: int) -> List[MovieRequest]:
    """获取用户的求片请求"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(MovieRequest)
                .options(selectinload(MovieRequest.category))
                .where(MovieRequest.user_id == user_id)
                .order_by(MovieRequest.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取用户求片请求失败: {e}")
            return []


async def get_pending_movie_requests() -> List[MovieRequest]:
    """获取待审核的求片请求"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(MovieRequest)
                .options(selectinload(MovieRequest.category))
                .where(MovieRequest.status == "pending")
                .order_by(MovieRequest.created_at.asc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取待审核求片请求失败: {e}")
            return []


async def review_movie_request(request_id: int, reviewer_id: int, status: str, review_note: str = None) -> bool:
    """审核求片请求"""
    async for session in get_db():
        try:
            result = await session.execute(
                update(MovieRequest)
                .where(MovieRequest.id == request_id)
                .values(
                    status=status,
                    reviewed_at=datetime.now(),
                    reviewed_by=reviewer_id,
                    review_note=review_note
                )
            )
            
            # 记录管理员操作
            note_text = f"，备注：{review_note}" if review_note else ""
            action = AdminAction(
                admin_id=reviewer_id,
                action_type="review",
                target_id=request_id,
                description=f"审核求片请求 {request_id}，结果：{status}{note_text}"
            )
            session.add(action)
            
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"审核求片请求失败: {e}")
            await session.rollback()
            return False


# ==================== 内容投稿 ====================

async def create_content_submission(user_id: int, title: str, content: str, file_id: str = None, category_id: int = None) -> bool:
    """创建内容投稿"""
    async for session in get_db():
        try:
            submission = ContentSubmission(
                user_id=user_id,
                category_id=category_id,
                title=title,
                content=content,
                file_id=file_id,
                created_at=datetime.now()  # 使用本地时间而不是数据库服务器时间
            )
            session.add(submission)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"创建内容投稿失败: {e}")
            await session.rollback()
            return False


async def get_user_content_submissions(user_id: int) -> List[ContentSubmission]:
    """获取用户的内容投稿"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(ContentSubmission)
                .options(selectinload(ContentSubmission.category))
                .where(ContentSubmission.user_id == user_id)
                .order_by(ContentSubmission.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取用户内容投稿失败: {e}")
            return []


async def get_pending_content_submissions() -> List[ContentSubmission]:
    """获取待审核的内容投稿"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(ContentSubmission)
                .options(selectinload(ContentSubmission.category))
                .where(ContentSubmission.status == "pending")
                .order_by(ContentSubmission.created_at.asc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取待审核内容投稿失败: {e}")
            return []


async def review_content_submission(submission_id: int, reviewer_id: int, status: str, review_note: str = None) -> bool:
    """审核内容投稿"""
    async for session in get_db():
        try:
            result = await session.execute(
                update(ContentSubmission)
                .where(ContentSubmission.id == submission_id)
                .values(
                    status=status,
                    reviewed_at=datetime.now(),
                    reviewed_by=reviewer_id,
                    review_note=review_note
                )
            )
            
            # 记录管理员操作
            note_text = f"，备注：{review_note}" if review_note else ""
            action = AdminAction(
                admin_id=reviewer_id,
                action_type="review",
                target_id=submission_id,
                description=f"审核内容投稿 {submission_id}，结果：{status}{note_text}"
            )
            session.add(action)
            
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"审核内容投稿失败: {e}")
            await session.rollback()
            return False


# ==================== 用户反馈 ====================

async def create_user_feedback(user_id: int, feedback_type: str, content: str) -> bool:
    """创建用户反馈"""
    async for session in get_db():
        try:
            feedback = UserFeedback(
                user_id=user_id,
                feedback_type=feedback_type,
                content=content,
                created_at=datetime.now()  # 使用本地时间而不是数据库服务器时间
            )
            session.add(feedback)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"创建用户反馈失败: {e}")
            await session.rollback()
            return False


async def get_user_feedback_list(user_id: int) -> List[UserFeedback]:
    """获取用户的反馈列表"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(UserFeedback).where(UserFeedback.user_id == user_id)
                .order_by(UserFeedback.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取用户反馈列表失败: {e}")
            return []


async def get_all_feedback_list() -> List[UserFeedback]:
    """获取所有反馈列表（管理员用）"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(UserFeedback).order_by(UserFeedback.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取所有反馈列表失败: {e}")
            return []


async def reply_user_feedback(feedback_id: int, admin_id: int, reply_content: str) -> bool:
    """回复用户反馈"""
    async for session in get_db():
        try:
            result = await session.execute(
                update(UserFeedback)
                .where(UserFeedback.id == feedback_id)
                .values(
                    status="resolved",
                    replied_at=datetime.now(),
                    replied_by=admin_id,
                    reply_content=reply_content
                )
            )
            
            # 记录管理员操作
            action = AdminAction(
                admin_id=admin_id,
                action_type="reply",
                target_id=feedback_id,
                description=f"回复用户反馈 {feedback_id}"
            )
            session.add(action)
            
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"回复用户反馈失败: {e}")
            await session.rollback()
            return False


# ==================== 统计信息 ====================

async def get_server_stats() -> dict:
    """获取服务器统计信息"""
    async for session in get_db():
        try:
            # 用户统计
            user_count = await session.execute(select(func.count()).select_from(User))
            total_users = user_count.scalar()
            
            admin_count = await session.execute(
                select(func.count()).select_from(User).where(User.role == "admin")
            )
            total_admins = admin_count.scalar()
            
            # 求片统计
            movie_count = await session.execute(select(func.count()).select_from(MovieRequest))
            total_requests = movie_count.scalar()
            
            pending_movie_count = await session.execute(
                select(func.count()).select_from(MovieRequest).where(MovieRequest.status == "pending")
            )
            pending_requests = pending_movie_count.scalar()
            
            # 投稿统计
            submission_count = await session.execute(select(func.count()).select_from(ContentSubmission))
            total_submissions = submission_count.scalar()
            
            pending_submission_count = await session.execute(
                select(func.count()).select_from(ContentSubmission).where(ContentSubmission.status == "pending")
            )
            pending_submissions = pending_submission_count.scalar()
            
            # 反馈统计
            feedback_count = await session.execute(select(func.count()).select_from(UserFeedback))
            total_feedback = feedback_count.scalar()
            
            pending_feedback_count = await session.execute(
                select(func.count()).select_from(UserFeedback).where(UserFeedback.status == "pending")
            )
            pending_feedback = pending_feedback_count.scalar()
            
            return {
                "total_users": total_users,
                "total_admins": total_admins,
                "total_requests": total_requests,
                "pending_requests": pending_requests,
                "total_submissions": total_submissions,
                "pending_submissions": pending_submissions,
                "total_feedback": total_feedback,
                "pending_feedback": pending_feedback
            }
        except Exception as e:
            logger.error(f"获取服务器统计信息失败: {e}")
            return {}


# ==================== 求片类型管理 ====================

async def create_movie_category(name: str, description: str = None, creator_id: int = None) -> bool:
    """创建求片类型"""
    async for session in get_db():
        try:
            category = MovieCategory(
                name=name,
                description=description,
                created_by=creator_id
            )
            session.add(category)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"创建求片类型失败: {e}")
            await session.rollback()
            return False


async def get_all_movie_categories(active_only: bool = True) -> List[MovieCategory]:
    """获取所有求片类型"""
    async for session in get_db():
        try:
            query = select(MovieCategory).order_by(MovieCategory.sort_order, MovieCategory.created_at)
            if active_only:
                query = query.where(MovieCategory.is_active == True)
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取求片类型失败: {e}")
            return []


async def get_movie_category_by_id(category_id: int) -> Optional[MovieCategory]:
    """根据ID获取求片类型"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(MovieCategory).where(MovieCategory.id == category_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取求片类型失败: {e}")
            return None


async def update_movie_category(category_id: int, name: str = None, description: str = None, is_active: bool = None) -> bool:
    """更新求片类型"""
    async for session in get_db():
        try:
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if description is not None:
                update_data['description'] = description
            if is_active is not None:
                update_data['is_active'] = is_active
            
            if update_data:
                await session.execute(
                    update(MovieCategory).where(MovieCategory.id == category_id).values(**update_data)
                )
                await session.commit()
            return True
        except Exception as e:
            logger.error(f"更新求片类型失败: {e}")
            await session.rollback()
            return False


async def delete_movie_category(category_id: int) -> bool:
    """删除求片类型"""
    async for session in get_db():
        try:
            await session.execute(
                delete(MovieCategory).where(MovieCategory.id == category_id)
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"删除求片类型失败: {e}")
            await session.rollback()
            return False


# ==================== 系统设置管理 ====================

async def get_system_setting(setting_key: str, default_value: str = None) -> str:
    """获取系统设置值"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(SystemSettings).where(
                    SystemSettings.setting_key == setting_key,
                    SystemSettings.is_active == True
                )
            )
            setting = result.scalar_one_or_none()
            return setting.setting_value if setting else default_value
        except Exception as e:
            logger.error(f"获取系统设置失败: {e}")
            return default_value


async def set_system_setting(setting_key: str, setting_value: str, setting_type: str = "boolean", description: str = None, updater_id: int = None) -> bool:
    """设置系统设置值"""
    async for session in get_db():
        try:
            # 检查设置是否已存在
            result = await session.execute(
                select(SystemSettings).where(SystemSettings.setting_key == setting_key)
            )
            existing_setting = result.scalar_one_or_none()
            
            if existing_setting:
                # 更新现有设置
                await session.execute(
                    update(SystemSettings).where(SystemSettings.setting_key == setting_key).values(
                        setting_value=setting_value,
                        updated_at=datetime.now(),
                        updated_by=updater_id
                    )
                )
            else:
                # 创建新设置
                setting = SystemSettings(
                    setting_key=setting_key,
                    setting_value=setting_value,
                    setting_type=setting_type,
                    description=description,
                    updated_by=updater_id
                )
                session.add(setting)
            
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"设置系统设置失败: {e}")
            await session.rollback()
            return False


async def get_all_system_settings() -> List[SystemSettings]:
    """获取所有系统设置"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(SystemSettings).order_by(SystemSettings.setting_key)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取系统设置失败: {e}")
            return []


async def is_feature_enabled(feature_key: str) -> bool:
    """检查功能是否启用"""
    setting_value = await get_system_setting(feature_key, "true")
    return setting_value.lower() in ["true", "1", "yes", "on"]