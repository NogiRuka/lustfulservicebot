from typing import Any, Callable, Dict, List
from aiogram import types
from aiogram.fsm.context import FSMContext
from dataclasses import dataclass

from app.utils.pagination import Paginator, format_page_header
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.panel_utils import get_user_display_link, cleanup_sent_media_messages
from loguru import logger


@dataclass
class BrowseConfig:
    """数据浏览配置类"""
    name: str  # 显示名称，如"求片"、"投稿"
    emoji: str  # 表情符号，如"🎬"、"📝"
    title_field: str  # 标题字段名
    content_field: str  # 内容字段名
    get_all_items_function: Callable  # 获取所有项目的函数
    get_item_by_id_function: Callable  # 根据ID获取项目的函数
    page_callback_prefix: str  # 分页回调前缀
    

class BrowseUIBuilder:
    """数据浏览UI构建器"""
    
    @staticmethod
    def build_item_display_text(config: BrowseConfig, items: List[Any], page_info: Dict) -> str:
        """构建项目显示文本"""
        text = format_page_header(f"{config.emoji} <b>所有{config.name}</b>", page_info)
        text += "\n\n"
        
        if not items:
            text += f"{config.emoji} 暂无{config.name}记录"
            return text
        
        start_num = (page_info['current_page'] - 1) * page_info['page_size'] + 1
        for i, item in enumerate(items, start_num):
            # 构建美化的卡片式显示
            text += f"┌{'─' * 38}┐\n"
            text += f"│ {config.emoji} <b>{getattr(item, config.title_field)}</b>\n"
            text += f"│\n"
            text += f"│ 🆔 ID: <code>{item.id}</code>\n"
            
            # 获取用户显示
            try:
                # 这里需要异步处理，在调用处处理
                text += f"│ 👤 用户: [用户{item.user_id}]\n"
            except:
                text += f"│ 👤 用户: 未知\n"
            
            text += f"│ 📅 时间: {humanize_time(item.created_at)}\n"
            text += f"│ 📊 状态: {get_status_text(item.status)}\n"
            
            # 显示内容预览
            content = getattr(item, config.content_field, None)
            if content:
                preview = content[:30] + "..." if len(content) > 30 else content
                text += f"│ 📄 内容: {preview}\n"
            else:
                text += f"│ 📄 内容: 无\n"
            
            # 附件信息
            if hasattr(item, 'file_id') and item.file_id:
                text += f"│ 📎 附件: ✅ 有\n"
            else:
                text += f"│ 📎 附件: ❌ 无\n"
            
            text += f"└{'─' * 38}┘\n\n"
        
        return text
    
    @staticmethod
    async def build_item_display_text_async(config: BrowseConfig, items: List[Any], page_info: Dict) -> str:
        """构建项目显示文本（异步版本，用于获取用户信息）"""
        text = format_page_header(f"{config.emoji} <b>所有{config.name}</b>", page_info)
        
        if not items:
            text += f"\n\n{config.emoji} 暂无{config.name}记录。"
            return text
        
        start_num = (page_info['current_page'] - 1) * page_info['page_size'] + 1
        for i, item in enumerate(items, start_num):
            # 获取类型信息
            category_name = "未知类型"
            if hasattr(item, 'category') and item.category:
                category_name = item.category.name
            
            # 状态显示
            status_text = get_status_text(item.status)
            
            # 获取用户显示链接
            try:
                user_display = await get_user_display_link(item.user_id)
            except Exception as e:
                user_display = f"[用户{item.user_id}]"
            
            # 美化的卡片式布局（与审核界面保持一致）
            title = getattr(item, config.title_field)
            text += f"\n┌─ {i}. {config.emoji} <b>【{category_name}】{title}</b>\n"
            text += f"├ 🆔 ID：<code>{item.id}</code>\n"
            text += f"├ 👤 用户：{user_display}\n"
            text += f"├ ⏰ 时间：<i>{humanize_time(item.created_at)}</i>\n"
            text += f"├ 🏷️ 状态：<code>{status_text}</code>\n"
            
            # 显示内容预览
            content = getattr(item, config.content_field, None)
            if content:
                preview = content[:60] + ('...' if len(content) > 60 else '')
                if config.name == "求片":
                    text += f"├ 📝 描述：{preview}\n"
                else:
                    text += f"├ 📄 内容：{preview}\n"
            
            # 附件信息
            if hasattr(item, 'file_id') and item.file_id:
                text += f"└ 📎 <b>附件已发送</b> ✅\n"
            else:
                # 显示审核备注（如果有）
                if hasattr(item, 'review_note') and item.review_note:
                    note_preview = item.review_note[:60] + ('...' if len(item.review_note) > 60 else '')
                    text += f"└ 💬 <b>审核备注</b>：<blockquote>{note_preview}</blockquote>\n"
                else:
                    text += f"└─────────────────\n"
            
            text += "\n"
        
        return text
    
    @staticmethod
    def build_navigation_keyboard(config: BrowseConfig, page_info: Dict) -> types.InlineKeyboardMarkup:
        """构建导航键盘"""
        keyboard = []
        
        # 分页按钮
        if page_info['total_pages'] > 1:
            nav_buttons = []
            if page_info['current_page'] > 1:
                nav_buttons.append(
                    types.InlineKeyboardButton(
                        text="⬅️ 上一页",
                        callback_data=f"{config.page_callback_prefix}_page_{page_info['current_page'] - 1}"
                    )
                )
            if page_info['current_page'] < page_info['total_pages']:
                nav_buttons.append(
                    types.InlineKeyboardButton(
                        text="➡️ 下一页",
                        callback_data=f"{config.page_callback_prefix}_page_{page_info['current_page'] + 1}"
                    )
                )
            if nav_buttons:
                keyboard.append(nav_buttons)
        
        # 返回按钮
        keyboard.append([
            types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="admin_review_center_cleanup"),
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main_cleanup")
        ])
        
        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)


class BrowseHandler:
    """数据浏览处理器"""
    
    def __init__(self, config: BrowseConfig):
        self.config = config
    
    async def handle_browse_list(self, cb: types.CallbackQuery, state: FSMContext, page: int = 1):
        """处理浏览列表"""
        # 清理媒体消息
        await cleanup_sent_media_messages(cb.bot, state)
        
        # 获取所有项目
        items = await self.config.get_all_items_function()
        
        if not items:
            await cb.message.edit_caption(
                caption=f"{self.config.emoji} <b>所有{self.config.name}</b>\n\n{self.config.emoji} 暂无{self.config.name}记录",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center_cleanup")]
                    ]
                )
            )
            await cb.answer()
            return
        
        # 创建分页器
        paginator = Paginator(items, page_size=5)
        page_data = paginator.get_page_items(page)
        page_info = paginator.get_page_info(page)
        
        # 构建显示文本
        text = await BrowseUIBuilder.build_item_display_text_async(self.config, page_data, page_info)
        
        # 构建键盘
        keyboard = BrowseUIBuilder.build_navigation_keyboard(self.config, page_info)
        
        # 更新消息
        await cb.message.edit_caption(
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # 发送有媒体的项目
        await self._send_media_messages(cb, state, page_data)
        
        await cb.answer()
    
    async def _send_media_messages(self, cb: types.CallbackQuery, state: FSMContext, items: List[Any]):
        """发送有媒体的项目消息"""
        data = await state.get_data()
        sent_media_ids = data.get('sent_media_ids', [])
        
        for item in items:
            if hasattr(item, 'file_id') and item.file_id:
                try:
                    # 构建媒体消息文本（与审核界面保持一致）
                    user_display = await get_user_display_link(item.user_id)
                    status_text = get_status_text(item.status)
                    
                    # 获取类型信息
                    category_name = "未知类型"
                    if hasattr(item, 'category') and item.category:
                        category_name = item.category.name
                    
                    title = getattr(item, self.config.title_field)
                    media_text = (
                        f"{self.config.emoji} <b>【{category_name}】{title}</b>\n\n"
                        f"🆔 <b>{self.config.name}ID</b>：<code>{item.id}</code>\n"
                        f"👤 <b>用户</b>：{user_display}\n"
                        f"⏰ <b>时间</b>：<i>{humanize_time(item.created_at)}</i>\n"
                        f"🏷️ <b>状态</b>：<code>{status_text}</code>\n"
                    )
                    
                    # 添加内容信息
                    content = getattr(item, self.config.content_field, None)
                    if content:
                        preview = content[:100] + "..." if len(content) > 100 else content
                        if self.config.name == "求片":
                            media_text += f"📝 <b>描述</b>：{preview}\n\n"
                        else:
                            media_text += f"📄 <b>内容</b>：{preview}\n\n"
                    else:
                        if self.config.name == "求片":
                            media_text += f"📝 <b>描述</b>：无\n\n"
                        else:
                            media_text += f"📄 <b>内容</b>：无\n\n"
                    
                    media_text += f"📎 <b>附件内容</b> ⬇️"
                    
                    # 发送媒体消息
                    media_msg = await cb.message.answer_photo(
                        photo=item.file_id,
                        caption=media_text,
                        parse_mode="HTML"
                    )
                    
                    # 保存媒体消息ID
                    sent_media_ids.append(media_msg.message_id)
                    
                except Exception as e:
                    logger.error(f"发送{self.config.name}媒体消息失败: {e}")
        
        # 更新状态中的媒体消息ID列表
        await state.update_data(sent_media_ids=sent_media_ids, chat_id=cb.from_user.id)


# 配置实例
MOVIE_BROWSE_CONFIG = BrowseConfig(
    name="求片",
    emoji="🎬",
    title_field="title",
    content_field="description",
    get_all_items_function=None,  # 将在使用时设置
    get_item_by_id_function=None,  # 将在使用时设置
    page_callback_prefix="all_movie"
)

CONTENT_BROWSE_CONFIG = BrowseConfig(
    name="投稿",
    emoji="📝",
    title_field="title",
    content_field="content",
    get_all_items_function=None,  # 将在使用时设置
    get_item_by_id_function=None,  # 将在使用时设置
    page_callback_prefix="all_content"
)