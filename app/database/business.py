from sqlalchemy import select, delete, func, update
from sqlalchemy.orm import selectinload
from app.database.schema import User, MovieRequest, ContentSubmission, UserFeedback, AdminAction
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

async def create_movie_request(user_id: int, title: str, description: str = None) -> bool:
    """创建求片请求"""
    async for session in get_db():
        try:
            request = MovieRequest(
                user_id=user_id,
                title=title,
                description=description
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
                select(MovieRequest).where(MovieRequest.user_id == user_id)
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
                select(MovieRequest).where(MovieRequest.status == "pending")
                .order_by(MovieRequest.created_at.asc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取待审核求片请求失败: {e}")
            return []


async def review_movie_request(request_id: int, reviewer_id: int, status: str) -> bool:
    """审核求片请求"""
    async for session in get_db():
        try:
            result = await session.execute(
                update(MovieRequest)
                .where(MovieRequest.id == request_id)
                .values(
                    status=status,
                    reviewed_at=datetime.now(),
                    reviewed_by=reviewer_id
                )
            )
            
            # 记录管理员操作
            action = AdminAction(
                admin_id=reviewer_id,
                action_type="review",
                target_id=request_id,
                description=f"审核求片请求 {request_id}，结果：{status}"
            )
            session.add(action)
            
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"审核求片请求失败: {e}")
            await session.rollback()
            return False


# ==================== 内容投稿 ====================

async def create_content_submission(user_id: int, title: str, content: str, file_id: str = None) -> bool:
    """创建内容投稿"""
    async for session in get_db():
        try:
            submission = ContentSubmission(
                user_id=user_id,
                title=title,
                content=content,
                file_id=file_id
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
                select(ContentSubmission).where(ContentSubmission.user_id == user_id)
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
                select(ContentSubmission).where(ContentSubmission.status == "pending")
                .order_by(ContentSubmission.created_at.asc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取待审核内容投稿失败: {e}")
            return []


async def review_content_submission(submission_id: int, reviewer_id: int, status: str) -> bool:
    """审核内容投稿"""
    async for session in get_db():
        try:
            result = await session.execute(
                update(ContentSubmission)
                .where(ContentSubmission.id == submission_id)
                .values(
                    status=status,
                    reviewed_at=datetime.now(),
                    reviewed_by=reviewer_id
                )
            )
            
            # 记录管理员操作
            action = AdminAction(
                admin_id=reviewer_id,
                action_type="review",
                target_id=submission_id,
                description=f"审核内容投稿 {submission_id}，结果：{status}"
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
                content=content
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