#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理器 - 处理超管发送的图片
自动保存超管发送的图片信息到数据库
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from loguru import logger
from datetime import datetime

from app.utils.roles import ROLE_SUPERADMIN
from app.database.users import get_role
from app.database.image_library import (
    save_image_info,
    get_all_images,
    get_image_stats,
    delete_image,
    deactivate_image,
    get_image_by_id,
    search_images_by_tags,
    get_popular_images
)

image_handler_router = Router()


@image_handler_router.message(F.photo)
async def handle_superadmin_photo(msg: types.Message):
    """处理超管发送的图片"""
    # 检查是否为超管
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        return  # 非超管发送的图片不处理
    
    try:
        # 获取最大尺寸的图片
        photo = msg.photo[-1]
        
        # 提取图片信息
        file_id = photo.file_id
        file_unique_id = photo.file_unique_id
        file_size = photo.file_size
        width = photo.width
        height = photo.height
        caption = msg.caption or None
        
        # 保存图片信息到数据库
        saved_image = await save_image_info(
            file_id=file_id,
            uploaded_by=msg.from_user.id,
            file_unique_id=file_unique_id,
            file_size=file_size,
            width=width,
            height=height,
            caption=caption
        )
        
        if saved_image:
            # 发送确认消息
            confirm_text = (
                f"📸 <b>图片已保存到图片库</b>\n\n"
                f"🆔 <b>图片ID</b>：{saved_image.id}\n"
                f"📏 <b>尺寸</b>：{width} × {height}\n"
                f"📦 <b>大小</b>：{file_size / 1024:.1f} KB\n"
                f"⏰ <b>保存时间</b>：{saved_image.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            
            if caption:
                confirm_text += f"📝 <b>说明</b>：{caption}\n\n"
            
            confirm_text += (
                f"💡 <b>提示</b>：\n"
                f"├ 图片已自动保存到图片库\n"
                f"├ 可使用 /img_lib 查看图片库\n"
                f"├ 可使用 /img_stats 查看统计信息\n"
                f"└ 可使用 /img_search [标签] 搜索图片"
            )
            
            await msg.reply(confirm_text, parse_mode="HTML")
            
        else:
            await msg.reply("⚠️ 图片保存失败，请稍后重试")
            
    except Exception as e:
        logger.error(f"处理超管图片失败: {e}")
        await msg.reply(f"❌ 处理图片时发生错误：{str(e)}")


@image_handler_router.message(Command("img_lib", "il"))
async def img_library_command(msg: types.Message):
    """查看图片库"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    try:
        # 获取图片列表
        images = await get_all_images(limit=10)
        
        if not images:
            await msg.reply("📸 图片库为空，发送图片给我即可自动保存")
            return
        
        text = "📸 <b>图片库</b>\n\n"
        
        for i, img in enumerate(images, 1):
            text += f"<b>{i}. 图片 #{img.id}</b>\n"
            text += f"📏 尺寸：{img.width} × {img.height}\n"
            text += f"📦 大小：{img.file_size / 1024:.1f} KB\n" if img.file_size else ""
            text += f"📝 说明：{img.caption}\n" if img.caption else ""
            text += f"🔢 使用次数：{img.usage_count}\n"
            text += f"⏰ 上传时间：{img.uploaded_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        text += "💡 <b>更多命令</b>：\n"
        text += "├ /img_stats - 查看统计信息\n"
        text += "├ /img_search [标签] - 搜索图片\n"
        text += "├ /img_popular - 查看热门图片\n"
        text += "└ /img_delete [ID] - 删除图片"
        
        await msg.reply(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"查看图片库失败: {e}")
        await msg.reply(f"❌ 查看图片库失败：{str(e)}")


@image_handler_router.message(Command("img_stats", "is"))
async def img_stats_command(msg: types.Message):
    """查看图片库统计信息"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    try:
        stats = await get_image_stats()
        
        text = "📊 <b>图片库统计</b>\n\n"
        text += f"📸 <b>总图片数</b>：{stats['total_images']} 张\n"
        text += f"✅ <b>活跃图片</b>：{stats['active_images']} 张\n"
        text += f"❌ <b>已停用</b>：{stats['inactive_images']} 张\n"
        text += f"🔢 <b>总使用次数</b>：{stats['total_usage']} 次\n\n"
        
        if stats['recent_images']:
            text += "🕐 <b>最近上传</b>：\n"
            for img in stats['recent_images'][:3]:
                text += f"├ #{img['id']} - {img['uploaded_at']} (使用{img['usage_count']}次)\n"
                if img['caption']:
                    text += f"│   📝 {img['caption'][:30]}...\n" if len(img['caption']) > 30 else f"│   📝 {img['caption']}\n"
        
        await msg.reply(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"查看图片统计失败: {e}")
        await msg.reply(f"❌ 查看统计信息失败：{str(e)}")


@image_handler_router.message(Command("img_search", "ise"))
async def img_search_command(msg: types.Message):
    """搜索图片"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply(
            "用法：/img_search [标签] 或 /ise [标签]\n"
            "示例：/ise 风景"
        )
        return
    
    search_tags = parts[1]
    
    try:
        images = await search_images_by_tags(search_tags)
        
        if not images:
            await msg.reply(f"🔍 未找到包含标签 '{search_tags}' 的图片")
            return
        
        text = f"🔍 <b>搜索结果</b> (标签: {search_tags})\n\n"
        
        for i, img in enumerate(images[:5], 1):
            text += f"<b>{i}. 图片 #{img.id}</b>\n"
            text += f"📝 说明：{img.caption}\n" if img.caption else ""
            text += f"🏷️ 标签：{img.tags}\n" if img.tags else ""
            text += f"🔢 使用次数：{img.usage_count}\n"
            text += f"⏰ 上传时间：{img.uploaded_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        if len(images) > 5:
            text += f"... 还有 {len(images) - 5} 张图片\n\n"
        
        text += "💡 使用 /img_show [ID] 查看具体图片"
        
        await msg.reply(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"搜索图片失败: {e}")
        await msg.reply(f"❌ 搜索失败：{str(e)}")


@image_handler_router.message(Command("img_popular", "ip"))
async def img_popular_command(msg: types.Message):
    """查看热门图片"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    try:
        images = await get_popular_images(limit=5)
        
        if not images:
            await msg.reply("📸 暂无热门图片")
            return
        
        text = "🔥 <b>热门图片</b> (按使用次数排序)\n\n"
        
        for i, img in enumerate(images, 1):
            text += f"<b>{i}. 图片 #{img.id}</b> 🔥{img.usage_count}\n"
            text += f"📝 说明：{img.caption}\n" if img.caption else ""
            text += f"📏 尺寸：{img.width} × {img.height}\n"
            text += f"⏰ 上传时间：{img.uploaded_at.strftime('%Y-%m-%d %H:%M')}\n"
            if img.last_used_at:
                text += f"🕐 最后使用：{img.last_used_at.strftime('%Y-%m-%d %H:%M')}\n"
            text += "\n"
        
        await msg.reply(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"查看热门图片失败: {e}")
        await msg.reply(f"❌ 查看热门图片失败：{str(e)}")


@image_handler_router.message(Command("img_show", "ish"))
async def img_show_command(msg: types.Message):
    """显示指定ID的图片"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply(
            "用法：/img_show [图片ID] 或 /ish [图片ID]\n"
            "示例：/ish 123"
        )
        return
    
    try:
        image_id = int(parts[1])
    except ValueError:
        await msg.reply("❌ 图片ID必须是数字")
        return
    
    try:
        image = await get_image_by_id(image_id)
        
        if not image:
            await msg.reply(f"❌ 未找到ID为 {image_id} 的图片")
            return
        
        # 发送图片
        caption = (
            f"📸 <b>图片 #{image.id}</b>\n\n"
            f"📏 <b>尺寸</b>：{image.width} × {image.height}\n"
            f"📦 <b>大小</b>：{image.file_size / 1024:.1f} KB\n" if image.file_size else ""
            f"🔢 <b>使用次数</b>：{image.usage_count}\n"
            f"⏰ <b>上传时间</b>：{image.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        
        if image.caption:
            caption += f"📝 <b>说明</b>：{image.caption}\n"
        
        if image.tags:
            caption += f"🏷️ <b>标签</b>：{image.tags}\n"
        
        if image.last_used_at:
            caption += f"🕐 <b>最后使用</b>：{image.last_used_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        await msg.bot.send_photo(
            chat_id=msg.chat.id,
            photo=image.file_id,
            caption=caption,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"显示图片失败: {e}")
        await msg.reply(f"❌ 显示图片失败：{str(e)}")


@image_handler_router.message(Command("img_delete", "id"))
async def img_delete_command(msg: types.Message):
    """删除图片"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply(
            "用法：/img_delete [图片ID] 或 /id [图片ID]\n"
            "示例：/id 123"
        )
        return
    
    try:
        image_id = int(parts[1])
    except ValueError:
        await msg.reply("❌ 图片ID必须是数字")
        return
    
    try:
        # 先获取图片信息
        image = await get_image_by_id(image_id)
        if not image:
            await msg.reply(f"❌ 未找到ID为 {image_id} 的图片")
            return
        
        # 删除图片
        success = await delete_image(image_id)
        
        if success:
            await msg.reply(
                f"🗑️ <b>图片删除成功</b>\n\n"
                f"🆔 <b>图片ID</b>：{image_id}\n"
                f"📝 <b>说明</b>：{image.caption or '无'}\n"
                f"⏰ <b>删除时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode="HTML"
            )
        else:
            await msg.reply("❌ 删除图片失败")
        
    except Exception as e:
        logger.error(f"删除图片失败: {e}")
        await msg.reply(f"❌ 删除图片失败：{str(e)}")