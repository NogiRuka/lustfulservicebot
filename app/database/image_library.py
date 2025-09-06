#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片库数据库操作模块
处理管理员添加的图片链接信息的存储和管理
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.db import AsyncSessionLocal
from app.database.schema import ImageLibrary


async def save_image_url(image_url: str, added_by: int, description: str = None) -> Optional[ImageLibrary]:
    """保存图片URL到数据库
    
    Args:
        image_url: 图片URL
        added_by: 添加者ID（管理员）
        description: 图片描述
        
    Returns:
        保存的图片记录，失败返回None
    """
    try:
        async with AsyncSessionLocal() as session:
            # 检查URL是否已存在
            existing = await session.execute(
                select(ImageLibrary).where(ImageLibrary.image_url == image_url)
            )
            if existing.scalar_one_or_none():
                logger.warning(f"图片URL已存在: {image_url}")
                return None
            
            # 创建新记录
            image_record = ImageLibrary(
                image_url=image_url,
                description=description,
                added_by=added_by,
                added_at=datetime.now(),
                is_active=True,
                usage_count=0
            )
            
            session.add(image_record)
            await session.commit()
            await session.refresh(image_record)
            
            logger.info(f"图片URL保存成功: {image_url} (ID: {image_record.id})")
            return image_record
            
    except Exception as e:
        logger.error(f"保存图片URL失败: {e}")
        return None


async def get_all_images(limit: int = 50, offset: int = 0, active_only: bool = True) -> List[ImageLibrary]:
    """获取所有图片记录
    
    Args:
        limit: 限制数量
        offset: 偏移量
        active_only: 是否只获取活跃的图片
        
    Returns:
        图片记录列表
    """
    try:
        async with AsyncSessionLocal() as session:
            query = select(ImageLibrary)
            
            if active_only:
                query = query.where(ImageLibrary.is_active == True)
            
            query = query.order_by(ImageLibrary.added_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(query)
            images = result.scalars().all()
            
            return list(images)
            
    except Exception as e:
        logger.error(f"获取图片列表失败: {e}")
        return []


async def get_image_by_id(image_id: int) -> Optional[ImageLibrary]:
    """根据ID获取图片记录
    
    Args:
        image_id: 图片ID
        
    Returns:
        图片记录，不存在返回None
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ImageLibrary).where(ImageLibrary.id == image_id)
            )
            return result.scalar_one_or_none()
            
    except Exception as e:
        logger.error(f"获取图片记录失败: {e}")
        return None


async def get_image_by_url(image_url: str) -> Optional[ImageLibrary]:
    """根据URL获取图片记录
    
    Args:
        image_url: 图片URL
        
    Returns:
        图片记录，不存在返回None
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ImageLibrary).where(ImageLibrary.image_url == image_url)
            )
            return result.scalar_one_or_none()
            
    except Exception as e:
        logger.error(f"获取图片记录失败: {e}")
        return None


async def delete_image_by_url(image_url: str) -> bool:
    """根据URL删除图片记录
    
    Args:
        image_url: 图片URL
        
    Returns:
        删除成功返回True，失败返回False
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                delete(ImageLibrary).where(ImageLibrary.image_url == image_url)
            )
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"图片记录删除成功: {image_url}")
                return True
            else:
                logger.warning(f"图片记录不存在: {image_url}")
                return False
                
    except Exception as e:
        logger.error(f"删除图片记录失败: {e}")
        return False


async def update_image_usage(image_url: str) -> bool:
    """更新图片使用次数
    
    Args:
        image_url: 图片URL
        
    Returns:
        更新成功返回True，失败返回False
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update(ImageLibrary)
                .where(ImageLibrary.image_url == image_url)
                .values(
                    usage_count=ImageLibrary.usage_count + 1,
                    last_used_at=datetime.now()
                )
            )
            await session.commit()
            
            if result.rowcount > 0:
                logger.debug(f"图片使用次数更新成功: {image_url}")
                return True
            else:
                logger.warning(f"图片记录不存在，无法更新使用次数: {image_url}")
                return False
                
    except Exception as e:
        logger.error(f"更新图片使用次数失败: {e}")
        return False


async def get_image_stats() -> Dict[str, Any]:
    """获取图片库统计信息
    
    Returns:
        统计信息字典
    """
    try:
        async with AsyncSessionLocal() as session:
            # 总图片数
            total_result = await session.execute(
                select(func.count(ImageLibrary.id))
            )
            total_images = total_result.scalar()
            
            # 活跃图片数
            active_result = await session.execute(
                select(func.count(ImageLibrary.id)).where(ImageLibrary.is_active == True)
            )
            active_images = active_result.scalar()
            
            # 总使用次数
            usage_result = await session.execute(
                select(func.sum(ImageLibrary.usage_count))
            )
            total_usage = usage_result.scalar() or 0
            
            # 最近添加的图片
            recent_result = await session.execute(
                select(ImageLibrary)
                .order_by(ImageLibrary.added_at.desc())
                .limit(5)
            )
            recent_images = recent_result.scalars().all()
            
            return {
                'total_images': total_images,
                'active_images': active_images,
                'inactive_images': total_images - active_images,
                'total_usage': total_usage,
                'recent_images': [
                    {
                        'id': img.id,
                        'image_url': img.image_url,
                        'description': img.description,
                        'usage_count': img.usage_count,
                        'added_at': img.added_at.strftime('%Y-%m-%d %H:%M:%S')
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


async def get_active_image_urls() -> List[str]:
    """获取所有活跃图片的URL列表
    
    Returns:
        图片URL列表
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ImageLibrary.image_url)
                .where(ImageLibrary.is_active == True)
                .order_by(ImageLibrary.added_at.desc())
            )
            urls = result.scalars().all()
            return list(urls)
            
    except Exception as e:
        logger.error(f"获取活跃图片URL列表失败: {e}")
        return []


async def toggle_image_status(image_url: str, is_active: bool) -> bool:
    """切换图片状态
    
    Args:
        image_url: 图片URL
        is_active: 是否活跃
        
    Returns:
        更新成功返回True，失败返回False
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update(ImageLibrary)
                .where(ImageLibrary.image_url == image_url)
                .values(is_active=is_active)
            )
            await session.commit()
            
            if result.rowcount > 0:
                status_text = "启用" if is_active else "禁用"
                logger.info(f"图片状态更新成功: {image_url} -> {status_text}")
                return True
            else:
                logger.warning(f"图片记录不存在: {image_url}")
                return False
                
    except Exception as e:
        logger.error(f"切换图片状态失败: {e}")
        return False