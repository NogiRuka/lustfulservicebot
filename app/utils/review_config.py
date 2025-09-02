from typing import Optional, Dict, Any, Callable, List
from aiogram import types
from aiogram.fsm.context import FSMContext
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.pagination import Paginator, format_page_header
from app.utils.panel_utils import get_user_display_link, send_review_notification, cleanup_sent_media_messages
from loguru import logger


class ReviewConfig:
    """审核配置类"""
    
    def __init__(self,
                 item_type: str,
                 emoji: str,
                 name: str,
                 title_field: str,
                 content_field: str,
                 get_pending_items_function: Callable,
                 get_all_items_function: Callable,
                 get_item_by_id_function: Callable,
                 review_function: Callable,
                 list_callback: str,
                 page_callback_prefix: str,
                 detail_callback_prefix: str,
                 approve_callback_prefix: str,
                 reject_callback_prefix: str,
                 approve_media_callback_prefix: str,
                 reject_media_callback_prefix: str,
                 approve_note_media_callback_prefix: str,
                 reject_note_media_callback_prefix: str,
                 cleanup_callback: str,
                 back_to_main_cleanup_callback: str):
        self.item_type = item_type
        self.emoji = emoji
        self.name = name
        self.title_field = title_field
        self.content_field = content_field
        self.get_pending_items_function = get_pending_items_function
        self.get_all_items_function = get_all_items_function
        self.get_item_by_id_function = get_item_by_id_function
        self.review_function = review_function
        self.list_callback = list_callback
        self.page_callback_prefix = page_callback_prefix
        self.detail_callback_prefix = detail_callback_prefix
        self.approve_callback_prefix = approve_callback_prefix
        self.reject_callback_prefix = reject_callback_prefix
        self.approve_media_callback_prefix = approve_media_callback_prefix
        self.reject_media_callback_prefix = reject_media_callback_prefix
        self.approve_note_media_callback_prefix = approve_note_media_callback_prefix
        self.reject_note_media_callback_prefix = reject_note_media_callback_prefix
        self.cleanup_callback = cleanup_callback
        self.back_to_main_cleanup_callback = back_to_main_cleanup_callback


class ReviewUIBuilder:
    """审核界面构建器"""
    
    @staticmethod
    async def build_review_list_text(config: ReviewConfig, items: List, paginator: Paginator) -> str:
        """构建审核列表文本"""
        page_info = paginator.get_page_info(paginator.current_page)
        text = format_page_header(f"{config.emoji} {config.name}审核", page_info)
        text += "\n\n"
        
        if not items:
            text += f"{config.emoji} 暂无待审核的{config.name}请求"
        else:
            for item in items:
                user_display = await get_user_display_link(item.user_id)
                text += (
                    f"🆔 ID: {item.id}\n"
                    f"📝 {config.title_field}: {getattr(item, config.title_field)}\n"
                    f"👤 用户: {user_display}\n"
                    f"📅 时间: {humanize_time(item.created_at)}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                )
        
        return text
    
    @staticmethod
    def build_review_list_keyboard(config: ReviewConfig, items: List, paginator: Paginator) -> types.InlineKeyboardMarkup:
        """构建审核列表键盘"""
        keyboard = []
        
        # 项目按钮
        if items:
            for item in items:
                title = getattr(item, config.title_field)
                display_title = title[:20] + "..." if len(title) > 20 else title
                keyboard.append([
                    types.InlineKeyboardButton(
                        text=f"📝 {display_title}",
                        callback_data=f"{config.detail_callback_prefix}{item.id}"
                    )
                ])
        
        # 分页按钮
        if paginator.total_pages > 1:
            nav_buttons = []
            current_page = getattr(paginator, 'current_page', 1)
            if current_page > 1:
                nav_buttons.append(
                    types.InlineKeyboardButton(
                        text="⬅️ 上一页",
                        callback_data=f"{config.page_callback_prefix}{current_page - 1}"
                    )
                )
            if current_page < paginator.total_pages:
                nav_buttons.append(
                    types.InlineKeyboardButton(
                        text="➡️ 下一页",
                        callback_data=f"{config.page_callback_prefix}{current_page + 1}"
                    )
                )
            if nav_buttons:
                keyboard.append(nav_buttons)
        
        # 返回按钮
        keyboard.append([
            types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center")
        ])
        
        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    async def build_detail_text(config: ReviewConfig, item: Any) -> str:
        """构建详情文本"""
        user_display = await get_user_display_link(item.user_id)
        
        detail_text = (
            f"{config.emoji} <b>{config.name}详情</b>\n\n"
            f"🆔 ID：{item.id}\n"
            f"📝 {config.title_field}：{getattr(item, config.title_field)}\n"
            f"👤 用户：{user_display}\n"
            f"📅 提交时间：{humanize_time(item.created_at)}\n"
            f"📝 状态：{get_status_text(item.status)}\n\n"
        )
        
        # 内容字段
        content = getattr(item, config.content_field, None)
        if content:
            detail_text += f"📄 {config.content_field}：\n{content}\n\n"
        else:
            detail_text += f"📄 {config.content_field}：无\n\n"
        
        # 附件信息
        if hasattr(item, 'file_id') and item.file_id:
            detail_text += f"📎 附件：有（文件ID: {item.file_id[:20]}...）\n\n"
        else:
            detail_text += f"📎 附件：无\n\n"
        
        return detail_text
    
    @staticmethod
    def build_detail_keyboard(config: ReviewConfig, item_id: int) -> types.InlineKeyboardMarkup:
        """构建详情键盘"""
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ 通过", callback_data=f"{config.approve_callback_prefix}{item_id}"),
                    types.InlineKeyboardButton(text="❌ 拒绝", callback_data=f"{config.reject_callback_prefix}{item_id}")
                ],
                [
                    types.InlineKeyboardButton(text="📋 返回列表", callback_data=config.cleanup_callback),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data=config.back_to_main_cleanup_callback)
                ]
            ]
        )
    
    @staticmethod
    def build_media_keyboard(config: ReviewConfig, item_id: int) -> types.InlineKeyboardMarkup:
        """构建媒体消息键盘"""
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ 通过", callback_data=f"{config.approve_media_callback_prefix}{item_id}"),
                    types.InlineKeyboardButton(text="❌ 拒绝", callback_data=f"{config.reject_media_callback_prefix}{item_id}")
                ],
                [
                    types.InlineKeyboardButton(text="✅ 通过并留言", callback_data=f"{config.approve_note_media_callback_prefix}{item_id}"),
                    types.InlineKeyboardButton(text="❌ 拒绝并留言", callback_data=f"{config.reject_note_media_callback_prefix}{item_id}")
                ],
                [
                    types.InlineKeyboardButton(text="🗑️ 删除此消息", callback_data=f"delete_media_message_{item_id}")
                ]
            ]
        )


class ReviewHandler:
    """审核处理器"""
    
    def __init__(self, config: ReviewConfig):
        self.config = config
    
    async def handle_review_list(self, cb: types.CallbackQuery, state: FSMContext, page: int = 1):
        """处理审核列表"""
        # 清理之前发送的媒体消息
        await cleanup_sent_media_messages(cb.bot, state)
        
        # 获取待审核的项目
        items = await self.config.get_pending_items_function()
        
        if not items:
            await cb.message.edit_caption(
                caption=f"📋 <b>{self.config.name}审核</b>\n\n{self.config.emoji} 暂无待审核的{self.config.name}请求",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center")]
                    ]
                )
            )
            await cb.answer()
            return
        
        # 创建分页器
        paginator = Paginator(items, page_size=5)
        page_data = paginator.get_page_items(page)
        
        # 设置当前页码
        paginator.current_page = page
        
        # 构建界面
        text = await ReviewUIBuilder.build_review_list_text(self.config, page_data, paginator)
        keyboard = ReviewUIBuilder.build_review_list_keyboard(self.config, page_data, paginator)
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=keyboard
        )
        await cb.answer()
    
    async def handle_detail(self, cb: types.CallbackQuery, state: FSMContext, item_id: int):
        """处理详情查看"""
        # 获取项目详情
        item = await self.config.get_item_by_id_function(item_id)
        if not item:
            await cb.answer("❌ 项目不存在", show_alert=True)
            return
        
        # 构建详情文本
        detail_text = await ReviewUIBuilder.build_detail_text(self.config, item)
        
        # 如果有附件，发送媒体消息
        if hasattr(item, 'file_id') and item.file_id:
            try:
                media_msg = await cb.message.answer_photo(
                    photo=item.file_id,
                    caption=detail_text,
                    reply_markup=ReviewUIBuilder.build_media_keyboard(self.config, item_id),
                    parse_mode="HTML"
                )
                # 保存媒体消息ID
                await state.update_data(media_message_id=media_msg.message_id)
            except Exception as e:
                logger.error(f"发送媒体消息失败: {e}")
        
        # 编辑原消息
        await cb.message.edit_caption(
            caption=detail_text,
            reply_markup=ReviewUIBuilder.build_detail_keyboard(self.config, item_id),
            parse_mode="HTML"
        )
        await cb.answer()
    
    async def handle_approve(self, cb: types.CallbackQuery, state: FSMContext, item_id: int, note: str = None):
        """处理通过审核"""
        success = await self.config.review_function(item_id, "approved", note)
        
        if success:
            await cb.message.edit_caption(
                caption=f"✅ {self.config.name}审核通过！",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="📋 返回列表", callback_data=self.config.list_callback)]
                    ]
                )
            )
            # 清理媒体消息
            await cleanup_sent_media_messages(cb.bot, state)
        else:
            await cb.answer("❌ 操作失败", show_alert=True)
        
        await cb.answer()
    
    async def handle_reject(self, cb: types.CallbackQuery, state: FSMContext, item_id: int, note: str = None):
        """处理拒绝审核"""
        success = await self.config.review_function(item_id, "rejected", note)
        
        if success:
            await cb.message.edit_caption(
                caption=f"❌ {self.config.name}审核拒绝！",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="📋 返回列表", callback_data=self.config.list_callback)]
                    ]
                )
            )
            # 清理媒体消息
            await cleanup_sent_media_messages(cb.bot, state)
        else:
            await cb.answer("❌ 操作失败", show_alert=True)
        
        await cb.answer()
    
    async def handle_cleanup(self, cb: types.CallbackQuery, state: FSMContext):
        """处理清理并返回列表"""
        await cleanup_sent_media_messages(cb.bot, state)
        await self.handle_review_list(cb, state)
    
    async def handle_back_to_main_cleanup(self, cb: types.CallbackQuery, state: FSMContext):
        """处理清理并返回主菜单"""
        from app.buttons.users import back_to_main_kb
        
        await cleanup_sent_media_messages(cb.bot, state)
        await cb.message.edit_caption(
            caption="🌸 欢迎回到主菜单 🌸",
            reply_markup=back_to_main_kb
        )
        await cb.answer()
    
    async def handle_delete_media_message(self, cb: types.CallbackQuery, state: FSMContext, item_id: int):
        """处理删除媒体消息"""
        try:
            await cb.message.delete()
            await cb.answer("✅ 消息已删除")
        except Exception as e:
            logger.error(f"删除媒体消息失败: {e}")
            await cb.answer("❌ 删除失败")