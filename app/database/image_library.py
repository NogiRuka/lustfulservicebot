#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片库数据库操作模块
处理超管发送的图片信息的存储和管理
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.db import AsyncSessionLocal
from app.database.schema import ImageLibrary


async def save_image_info(
    file_id: str,
    uploaded_by: int,
    file_unique_id: str = None,
    file_url: str = None,
    file_size: int = None,
    width: int = None,
    height: int = None,
    caption: str = None,
    tags: str = None
) -> Optional[ImageLibrary]:
    """保存图片信息到数据库"""
    try:
        async with AsyncSessionLocal() as session:
            # 检查是否已存在相同的file_id
            stmt = select(ImageLibrary).where(ImageLibrary.file_id == file_id)
            result = await session.execute(stmt)
            existing_image = result.scalar_one_or_none()
            
            if existing_image:
                logger.info(f"图片已存在: {file_id}")
                return existing_image
            
            # 创建新的图片记录
            new_image = ImageLibrary(
                file_id=file_id,
                file_unique_id=file_unique_id,
                file_url=file_url,
                file_size=file_size,
                width=width,
                height=height,
                caption=caption,
                uploaded_by=uploaded_by,
                tags=tags
            )
            
            session.add(new_image)
            await session.commit()
            await session.refresh(new_image)
            
            logger.success(f"图片信息保存成功: {file_id}")
            return new_image
            
    except Exception as e:
        logger.error(f"保存图片信息失败: {e}")
        return None


async def get_image_by_id(image_id: int) -> Optional[ImageLibrary]:
    """根据ID获取图片信息"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(ImageLibrary).where(ImageLibrary.id == image_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        return None


async def get_image_by_file_id(file_id: str) -> Optional[ImageLibrary]:
    """根据file_id获取图片信息"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(ImageLibrary).where(ImageLibrary.file_id == file_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        return None


async def get_all_images(
    uploaded_by: int = None,
    is_active: bool = True,
    limit: int = 50,
    offset: int = 0
) -> List[ImageLibrary]:
    """获取图片列表"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(ImageLibrary)
            
            if uploaded_by is not None:
                stmt = stmt.where(ImageLibrary.uploaded_by == uploaded_by)
            
            if is_active is not None:
                stmt = stmt.where(ImageLibrary.is_active == is_active)
            
            stmt = stmt.order_by(ImageLibrary.uploaded_at.desc())
            stmt = stmt.limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"获取图片列表失败: {e}")
        return []


async def update_image_usage(file_id: str) -> bool:
    """更新图片使用次数和最后使用时间"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(ImageLibrary)
                .where(ImageLibrary.file_id == file_id)
                .values(
                    usage_count=ImageLibrary.usage_count + 1,
                    last_used_at=datetime.now()
                )
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新图片使用信息失败: {e}")
        return False


async def delete_image(image_id: int) -> bool:
    """删除图片记录"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = delete(ImageLibrary).where(ImageLibrary.id == image_id)
            result = await session.execute(stmt)
            await session.commit()
            
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"删除图片记录失败: {e}")
        return False


async def deactivate_image(image_id: int) -> bool:
    """停用图片（软删除）"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(ImageLibrary)
                .where(ImageLibrary.id == image_id)
                .values(is_active=False)
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"停用图片失败: {e}")
        return False


async def get_image_stats() -> Dict[str, Any]:
    """获取图片库统计信息"""
    try:
        async with AsyncSessionLocal() as session:
            # 总图片数
            total_stmt = select(func.count(ImageLibrary.id))
            total_result = await session.execute(total_stmt)
            total_images = total_result.scalar()
            
            # 活跃图片数
            active_stmt = select(func.count(ImageLibrary.id)).where(ImageLibrary.is_active == True)
            active_result = await session.execute(active_stmt)
            active_images = active_result.scalar()
            
            # 总使用次数
            usage_stmt = select(func.sum(ImageLibrary.usage_count))
            usage_result = await session.execute(usage_stmt)
            total_usage = usage_result.scalar() or 0
            
            # 最近上传的图片
            recent_stmt = (
                select(ImageLibrary)
                .order_by(ImageLibrary.uploaded_at.desc())
                .limit(5)
            )
            recent_result = await session.execute(recent_stmt)
            recent_images = recent_result.scalars().all()
            
            return {
                'total_images': total_images,
                'active_images': active_images,
                'inactive_images': total_images - active_images,
                'total_usage': total_usage,
                'recent_images': [
                    {
                        'id': img.id,
                        'file_id': img.file_id,
                        'caption': img.caption,
                        'uploaded_at': img.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'usage_count': img.usage_count
                    }
                    for img in recent_images
                ]
            }
    except Exception as e:
        logger.error(f"获取图片统计信息失败: {e}")
        return {
            'total_images': 0,
            'active_images': 0,
            'inactive_images': 0,
            'total_usage': 0,
            'recent_images': []
        }


async def search_images_by_tags(tags: str, limit: int = 20) -> List[ImageLibrary]:
    """根据标签搜索图片"""
    try:
        async with AsyncSessionLocal() as session:
            # 简单的标签搜索（包含指定标签）
            stmt = (
                select(ImageLibrary)
                .where(
                    ImageLibrary.is_active == True,
                    ImageLibrary.tags.contains(tags)
                )
                .order_by(ImageLibrary.uploaded_at.desc())
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"搜索图片失败: {e}")
        return []


async def get_popular_images(limit: int = 10) -> List[ImageLibrary]:
    """获取最受欢迎的图片（按使用次数排序）"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(ImageLibrary)
                .where(ImageLibrary.is_active == True)
                .order_by(ImageLibrary.usage_count.desc())
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"获取热门图片失败: {e}")
        return []