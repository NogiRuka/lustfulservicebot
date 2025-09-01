from typing import Optional, Dict, Any
from aiogram import types
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.panel_utils import get_user_display_link
from loguru import logger


class ReviewUIBuilder:
    """审核界面构建器"""
    
    @staticmethod
    def build_detail_text(item_type: str, item_data: Dict[str, Any]) -> str:
        """构建详情文本
        
        Args:
            item_type: 项目类型 ('movie', 'content')
            item_data: 项目数据字典
            
        Returns:
            格式化的详情文本
        """
        if item_type == 'movie':
            return ReviewUIBuilder._build_movie_detail_text(item_data)
        elif item_type == 'content':
            return ReviewUIBuilder._build_content_detail_text(item_data)
        else:
            raise ValueError(f"不支持的项目类型: {item_type}")
    
    @staticmethod
    def _build_movie_detail_text(data: Dict[str, Any]) -> str:
        """构建求片详情文本"""
        detail_text = (
            f"🎬 <b>求片详情</b>\n\n"
            f"🆔 ID：{data['id']}\n"
            f"🎭 片名：{data['title']}\n"
            f"👤 用户：{data['user_display']}\n"
            f"📅 提交时间：{data['created_at']}\n"
            f"📝 状态：{data['status']}\n\n"
        )
        
        if data.get('description'):
            detail_text += f"📄 描述：\n{data['description']}\n\n"
        else:
            detail_text += f"📄 描述：无\n\n"
        
        if data.get('file_id'):
            detail_text += f"📎 附件：有（文件ID: {data['file_id'][:20]}...）\n\n"
        else:
            detail_text += f"📎 附件：无\n\n"
        
        detail_text += "请选择审核操作："
        return detail_text
    
    @staticmethod
    def _build_content_detail_text(data: Dict[str, Any]) -> str:
        """构建投稿详情文本"""
        detail_text = (
            f"📝 <b>投稿详情</b>\n\n"
            f"🆔 ID：{data['id']}\n"
            f"📝 标题：{data['title']}\n"
            f"👤 用户：{data['user_display']}\n"
            f"📅 提交时间：{data['created_at']}\n"
            f"📊 状态：{data['status']}\n\n"
        )
        
        # 显示内容（限制长度）
        if data.get('content'):
            content = data['content']
            if len(content) > 500:
                content_display = content[:500] + "\n\n... (内容过长，已截断)"
            else:
                content_display = content
            detail_text += f"📄 内容：\n{content_display}\n\n"
        else:
            detail_text += f"📄 内容：无\n\n"
        
        return detail_text
    
    @staticmethod
    def build_detail_keyboard(item_type: str, item_id: int, return_callback: str) -> types.InlineKeyboardMarkup:
        """构建详情页面键盘
        
        Args:
            item_type: 项目类型 ('movie', 'content')
            item_id: 项目ID
            return_callback: 返回按钮的回调数据
            
        Returns:
            内联键盘
        """
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ 通过", callback_data=f"approve_{item_type}_{item_id}"),
                    types.InlineKeyboardButton(text="❌ 拒绝", callback_data=f"reject_{item_type}_{item_id}")
                ],
                [
                    types.InlineKeyboardButton(text="⬅️ 返回列表", callback_data=f"{return_callback}_cleanup"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main_cleanup")
                ]
            ]
        )
    
    @staticmethod
    def build_media_keyboard(item_type: str, item_id: int) -> types.InlineKeyboardMarkup:
        """构建媒体消息键盘
        
        Args:
            item_type: 项目类型 ('movie', 'content')
            item_id: 项目ID
            
        Returns:
            内联键盘
        """
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ 通过", callback_data=f"approve_{item_type}_media_{item_id}"),
                    types.InlineKeyboardButton(text="❌ 拒绝", callback_data=f"reject_{item_type}_media_{item_id}")
                ],
                [
                    types.InlineKeyboardButton(text="📝 通过并留言", callback_data=f"approve_{item_type}_note_media_{item_id}"),
                    types.InlineKeyboardButton(text="📝 拒绝并留言", callback_data=f"reject_{item_type}_note_media_{item_id}")
                ],
                [
                    types.InlineKeyboardButton(text="🗑️ 删除此消息", callback_data=f"delete_media_message_{item_id}")
                ]
            ]
        )


class ReviewDataProcessor:
    """审核数据处理器"""
    
    @staticmethod
    async def prepare_item_data(item, item_type: str) -> Dict[str, Any]:
        """准备项目数据
        
        Args:
            item: 项目对象 (MovieRequest 或 ContentSubmission)
            item_type: 项目类型 ('movie', 'content')
            
        Returns:
            处理后的数据字典
        """
        user_display = await get_user_display_link(item.user_id)
        
        data = {
            'id': item.id,
            'title': item.title,
            'user_display': user_display,
            'created_at': humanize_time(item.created_at),
            'status': get_status_text(item.status),
            'file_id': getattr(item, 'file_id', None)
        }
        
        if item_type == 'movie':
            data['description'] = getattr(item, 'description', None)
        elif item_type == 'content':
            data['content'] = getattr(item, 'content', None)
        
        return data


class ReviewMediaHandler:
    """审核媒体处理器"""
    
    @staticmethod
    async def send_media_message(bot, chat_id: int, file_id: str, item_type: str, item_title: str, item_id: int, state) -> Optional[types.Message]:
        """发送媒体消息
        
        Args:
            bot: 机器人实例
            chat_id: 聊天ID
            file_id: 文件ID
            item_type: 项目类型
            item_title: 项目标题
            item_id: 项目ID
            state: FSM状态
            
        Returns:
            发送的消息对象，失败时返回None
        """
        try:
            type_emoji = {'movie': '🎬', 'content': '📝'}.get(item_type, '📋')
            type_name = {'movie': '求片', 'content': '投稿'}.get(item_type, '项目')
            
            media_kb = ReviewUIBuilder.build_media_keyboard(item_type, item_id)
            
            media_message = await bot.send_photo(
                chat_id=chat_id,
                photo=file_id,
                caption=f"{type_emoji} {type_name}附件 - {item_title}",
                reply_markup=media_kb
            )
            
            # 保存媒体消息ID
            data = await state.get_data()
            sent_media_ids = data.get('sent_media_ids', [])
            sent_media_ids.append(media_message.message_id)
            await state.update_data(sent_media_ids=sent_media_ids)
            
            return media_message
            
        except Exception as e:
            logger.error(f"发送{type_name}媒体消息失败: {e}")
            return None


class ReviewActionHandler:
    """审核操作处理器"""
    
    @staticmethod
    async def handle_quick_review(item_type: str, item_id: int, reviewer_id: int, action: str) -> bool:
        """处理快速审核
        
        Args:
            item_type: 项目类型 ('movie', 'content')
            item_id: 项目ID
            reviewer_id: 审核人ID
            action: 审核动作 ('approved', 'rejected')
            
        Returns:
            操作是否成功
        """
        try:
            if item_type == 'movie':
                from app.database.business import review_movie_request
                return await review_movie_request(item_id, reviewer_id, action)
            elif item_type == 'content':
                from app.database.business import review_content_submission
                return await review_content_submission(item_id, reviewer_id, action)
            else:
                logger.error(f"不支持的项目类型: {item_type}")
                return False
        except Exception as e:
            logger.error(f"审核操作失败: {e}")
            return False
    
    @staticmethod
    async def handle_review_with_note(item_type: str, item_id: int, reviewer_id: int, action: str, note: str) -> bool:
        """处理带留言的审核
        
        Args:
            item_type: 项目类型 ('movie', 'content')
            item_id: 项目ID
            reviewer_id: 审核人ID
            action: 审核动作 ('approved', 'rejected')
            note: 审核留言
            
        Returns:
            操作是否成功
        """
        try:
            if item_type == 'movie':
                from app.database.business import review_movie_request
                return await review_movie_request(item_id, reviewer_id, action, note)
            elif item_type == 'content':
                from app.database.business import review_content_submission
                return await review_content_submission(item_id, reviewer_id, action, note)
            else:
                logger.error(f"不支持的项目类型: {item_type}")
                return False
        except Exception as e:
            logger.error(f"带留言审核操作失败: {e}")
            return False