from sqlalchemy import select, delete, func, update, desc, asc
from sqlalchemy.orm import selectinload
from app.database.schema import User, MovieRequest, ContentSubmission, UserFeedback, AdminAction, MovieCategory, SystemSettings, DevChangelog
from app.database.db import get_db
from loguru import logger
from typing import List, Optional, Dict, Any
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


# ==================== 高级浏览功能 ====================

async def get_movie_requests_advanced(
    offset: int = 0,
    limit: int = 10,
    sort_field: str = "created_at",
    sort_order: str = "asc",
    status_filter: str = None
) -> Dict[str, Any]:
    """高级求片请求查询"""
    async for session in get_db():
        try:
            # 构建基础查询
            query = select(MovieRequest).options(selectinload(MovieRequest.category))
            
            # 状态过滤
            if status_filter:
                query = query.where(MovieRequest.status == status_filter)
            
            # 排序
            sort_column = getattr(MovieRequest, sort_field, MovieRequest.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # 获取总数
            count_query = select(func.count(MovieRequest.id))
            if status_filter:
                count_query = count_query.where(MovieRequest.status == status_filter)
            
            total_result = await session.execute(count_query)
            total_count = total_result.scalar()
            
            # 分页查询
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            items = result.scalars().all()
            
            return {
                'items': items,
                'total': total_count
            }
            
        except Exception as e:
            logger.error(f"高级求片请求查询失败: {e}")
            return {'items': [], 'total': 0}


async def get_content_submissions_advanced(
    offset: int = 0,
    limit: int = 10,
    sort_field: str = "created_at",
    sort_order: str = "asc",
    status_filter: str = None
) -> Dict[str, Any]:
    """高级投稿查询"""
    async for session in get_db():
        try:
            # 构建基础查询
            query = select(ContentSubmission).options(selectinload(ContentSubmission.category))
            
            # 状态过滤
            if status_filter:
                query = query.where(ContentSubmission.status == status_filter)
            
            # 排序
            sort_column = getattr(ContentSubmission, sort_field, ContentSubmission.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # 获取总数
            count_query = select(func.count(ContentSubmission.id))
            if status_filter:
                count_query = count_query.where(ContentSubmission.status == status_filter)
            
            total_result = await session.execute(count_query)
            total_count = total_result.scalar()
            
            # 分页查询
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            items = result.scalars().all()
            
            return {
                'items': items,
                'total': total_count
            }
            
        except Exception as e:
            logger.error(f"高级投稿查询失败: {e}")
            return {'items': [], 'total': 0}


async def get_user_feedback_advanced(
    offset: int = 0,
    limit: int = 10,
    sort_field: str = "created_at",
    sort_order: str = "asc",
    status_filter: str = None,
    type_filter: str = None
) -> Dict[str, Any]:
    """高级反馈查询"""
    async for session in get_db():
        try:
            # 构建基础查询
            query = select(UserFeedback)
            
            # 状态过滤
            if status_filter:
                query = query.where(UserFeedback.status == status_filter)
            
            # 类型过滤
            if type_filter:
                query = query.where(UserFeedback.feedback_type == type_filter)
            
            # 排序
            sort_column = getattr(UserFeedback, sort_field, UserFeedback.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # 获取总数
            count_query = select(func.count(UserFeedback.id))
            if status_filter:
                count_query = count_query.where(UserFeedback.status == status_filter)
            if type_filter:
                count_query = count_query.where(UserFeedback.feedback_type == type_filter)
            
            total_result = await session.execute(count_query)
            total_count = total_result.scalar()
            
            # 分页查询
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            items = result.scalars().all()
            
            return {
                'items': items,
                'total': total_count
            }
            
        except Exception as e:
            logger.error(f"高级反馈查询失败: {e}")
            return {'items': [], 'total': 0}


async def get_users_advanced(
    offset: int = 0,
    limit: int = 10,
    sort_field: str = "created_at",
    sort_order: str = "asc",
    role_filter: str = None
) -> Dict[str, Any]:
    """高级用户查询"""
    async for session in get_db():
        try:
            # 构建基础查询
            query = select(User)
            
            # 角色过滤
            if role_filter:
                query = query.where(User.role == role_filter)
            
            # 排序
            sort_column = getattr(User, sort_field, User.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # 获取总数
            count_query = select(func.count(User.id))
            if role_filter:
                count_query = count_query.where(User.role == role_filter)
            
            total_result = await session.execute(count_query)
            total_count = total_result.scalar()
            
            # 分页查询
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            items = result.scalars().all()
            
            return {
                'items': items,
                'total': total_count
            }
            
        except Exception as e:
            logger.error(f"高级用户查询失败: {e}")
            return {'items': [], 'total': 0}


async def get_admin_actions_advanced(
    offset: int = 0,
    limit: int = 10,
    sort_field: str = "created_at",
    sort_order: str = "asc",
    action_type_filter: str = None,
    admin_id_filter: int = None
) -> Dict[str, Any]:
    """高级管理员操作记录查询"""
    async for session in get_db():
        try:
            # 构建基础查询
            query = select(AdminAction)
            
            # 操作类型过滤
            if action_type_filter:
                query = query.where(AdminAction.action_type == action_type_filter)
            
            # 管理员过滤
            if admin_id_filter:
                query = query.where(AdminAction.admin_id == admin_id_filter)
            
            # 排序
            sort_column = getattr(AdminAction, sort_field, AdminAction.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # 获取总数
            count_query = select(func.count(AdminAction.id))
            if action_type_filter:
                count_query = count_query.where(AdminAction.action_type == action_type_filter)
            if admin_id_filter:
                count_query = count_query.where(AdminAction.admin_id == admin_id_filter)
            
            total_result = await session.execute(count_query)
            total_count = total_result.scalar()
            
            # 分页查询
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            items = result.scalars().all()
            
            return {
                'items': items,
                'total': total_count
            }
            
        except Exception as e:
            logger.error(f"高级管理员操作记录查询失败: {e}")
            return {'items': [], 'total': 0}


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
    from app.database.users import update_user_stats
    
    async for session in get_db():
        try:
            request = MovieRequest(
                user_id=user_id,
                category_id=category_id,
                title=title,
                description=description,
                file_id=file_id
            )
            session.add(request)
            await session.commit()
            
            # 更新用户求片统计
            await update_user_stats(user_id, 'requests')
            
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


async def get_all_movie_requests() -> List[MovieRequest]:
    """获取所有求片请求"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(MovieRequest)
                .options(selectinload(MovieRequest.category))
                .order_by(MovieRequest.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取所有求片请求失败: {e}")
            return []


async def get_movie_request_by_id(request_id: int) -> Optional[MovieRequest]:
    """根据ID获取求片请求"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(MovieRequest)
                .options(selectinload(MovieRequest.category))
                .where(MovieRequest.id == request_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取求片请求失败: {e}")
            return None


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
    from app.database.users import update_user_stats
    
    async for session in get_db():
        try:
            submission = ContentSubmission(
                user_id=user_id,
                category_id=category_id,
                title=title,
                content=content,
                file_id=file_id
            )
            session.add(submission)
            await session.commit()
            
            # 更新用户投稿统计
            await update_user_stats(user_id, 'submissions')
            
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


async def get_all_content_submissions() -> List[ContentSubmission]:
    """获取所有内容投稿"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(ContentSubmission)
                .options(selectinload(ContentSubmission.category))
                .order_by(ContentSubmission.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取所有内容投稿失败: {e}")
            return []


async def get_content_submission_by_id(submission_id: int) -> Optional[ContentSubmission]:
    """根据ID获取内容投稿"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(ContentSubmission)
                .where(ContentSubmission.id == submission_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取内容投稿失败: {e}")
            return None


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
    from app.database.users import update_user_stats
    
    async for session in get_db():
        try:
            feedback = UserFeedback(
                user_id=user_id,
                feedback_type=feedback_type,
                content=content
            )
            session.add(feedback)
            await session.commit()
            
            # 更新用户反馈统计
            await update_user_stats(user_id, 'feedback')
            
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


# ==================== 内容分类管理（求片和投稿共用） ====================

async def create_movie_category(name: str, description: str = None, creator_id: int = None, sort_order: int = 0) -> bool:
    """创建内容分类（求片和投稿共用）"""
    async for session in get_db():
        try:
            category = MovieCategory(
                name=name,
                description=description,
                created_by=creator_id or 0,  # 如果creator_id为None，使用0作为系统创建
                sort_order=sort_order,
                is_active=True  # 显式设置为启用状态
            )
            session.add(category)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"创建内容分类失败: {e}")
            await session.rollback()
            return False


async def get_all_movie_categories(active_only: bool = True) -> List[MovieCategory]:
    """获取所有内容分类（求片和投稿共用）"""
    async for session in get_db():
        try:
            query = select(MovieCategory).order_by(MovieCategory.sort_order, MovieCategory.created_at)
            if active_only:
                # SQLite兼容查询：虽然使用了布尔字段，但SQLite中仍需整数比较
                query = query.where(MovieCategory.is_active != 0)
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取内容分类失败: {e}")
            return []


async def get_movie_category_by_id(category_id: int) -> Optional[MovieCategory]:
    """根据ID获取内容分类"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(MovieCategory).where(MovieCategory.id == category_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取内容分类失败: {e}")
            return None


async def update_movie_category(category_id: int, name: str = None, description: str = None, is_active: bool = None) -> bool:
    """更新内容分类"""
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
            logger.error(f"更新内容分类失败: {e}")
            await session.rollback()
            return False


async def delete_movie_category(category_id: int) -> bool:
    """删除内容分类"""
    async for session in get_db():
        try:
            await session.execute(
                delete(MovieCategory).where(MovieCategory.id == category_id)
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"删除内容分类失败: {e}")
            await session.rollback()
            return False


# ==================== 系统设置管理 ====================

async def get_system_setting(setting_key: str, default_value: str = None) -> str:
    """获取系统设置值"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(SystemSettings).where(
                    SystemSettings.setting_key == setting_key
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
    setting_value = await get_system_setting(feature_key, "false")
    return setting_value.lower() in ["true", "1", "yes", "on"]


# ==================== 开发日志 ====================

async def create_dev_changelog(version: str, title: str, content: str, changelog_type: str, creator_id: int) -> bool:
    """创建开发日志"""
    async for session in get_db():
        try:
            changelog = DevChangelog(
                version=version,
                title=title,
                content=content,
                changelog_type=changelog_type,
                created_by=creator_id
            )
            session.add(changelog)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"创建开发日志失败: {e}")
            await session.rollback()
            return False


async def get_all_dev_changelogs() -> List[DevChangelog]:
    """获取所有开发日志"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(DevChangelog).order_by(DevChangelog.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取开发日志失败: {e}")
            return []


async def get_dev_changelog_by_id(changelog_id: int) -> DevChangelog:
    """根据ID获取开发日志"""
    async for session in get_db():
        try:
            result = await session.execute(
                select(DevChangelog).where(DevChangelog.id == changelog_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取开发日志失败: {e}")
            return None


async def update_dev_changelog(changelog_id: int, version: str = None, title: str = None, content: str = None, changelog_type: str = None) -> bool:
    """更新开发日志"""
    async for session in get_db():
        try:
            update_data = {}
            if version is not None:
                update_data[DevChangelog.version] = version
            if title is not None:
                update_data[DevChangelog.title] = title
            if content is not None:
                update_data[DevChangelog.content] = content
            if changelog_type is not None:
                update_data[DevChangelog.changelog_type] = changelog_type
            
            if update_data:
                result = await session.execute(
                    update(DevChangelog)
                    .where(DevChangelog.id == changelog_id)
                    .values(**update_data)
                )
                await session.commit()
                return result.rowcount > 0
            return False
        except Exception as e:
            logger.error(f"更新开发日志失败: {e}")
            await session.rollback()
            return False


async def delete_dev_changelog(changelog_id: int) -> bool:
    """删除开发日志"""
    async for session in get_db():
        try:
            result = await session.execute(
                delete(DevChangelog).where(DevChangelog.id == changelog_id)
            )
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"删除开发日志失败: {e}")
            await session.rollback()
            return False