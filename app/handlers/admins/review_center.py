from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.database.business import (
    get_pending_movie_requests, get_pending_content_submissions,
    get_all_movie_requests, get_all_content_submissions,
    get_movie_request_by_id, get_content_submission_by_id
)
from app.database.users import get_role
from app.buttons.panels import get_panel_for_role
from app.buttons.users import admin_review_center_kb, back_to_main_kb
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.panel_utils import get_user_display_link, cleanup_sent_media_messages, create_welcome_panel_text, DEFAULT_WELCOME_PHOTO
from app.utils.states import Wait
from app.utils.browse_config import (
    MOVIE_BROWSE_CONFIG, CONTENT_BROWSE_CONFIG, BrowseHandler
)

review_center_router = Router()

# 初始化配置
MOVIE_BROWSE_CONFIG.get_all_items_function = get_all_movie_requests
MOVIE_BROWSE_CONFIG.get_item_by_id_function = get_movie_request_by_id

CONTENT_BROWSE_CONFIG.get_all_items_function = get_all_content_submissions
CONTENT_BROWSE_CONFIG.get_item_by_id_function = get_content_submission_by_id

# 创建处理器实例
movie_browse_handler = BrowseHandler(MOVIE_BROWSE_CONFIG)
content_browse_handler = BrowseHandler(CONTENT_BROWSE_CONFIG)


# ==================== 审核中心 ====================

@review_center_router.callback_query(F.data == "admin_review_center")
async def cb_admin_review_center(cb: types.CallbackQuery, state: FSMContext):
    """审核中心"""
    # 检查管理员权限和功能开关
    from app.utils.review_config import check_admin_permission
    
    if not await check_admin_permission(cb.from_user.id):
        await cb.answer("❌ 审核功能已关闭", show_alert=True)
        return
    
    # 删除之前发送的媒体消息
    try:
        data = await state.get_data()
        sent_media_ids = data.get('sent_media_ids', [])
        for message_id in sent_media_ids:
            try:
                await cb.message.bot.delete_message(chat_id=cb.from_user.id, message_id=message_id)
            except Exception as e:
                logger.warning(f"删除媒体消息失败: {e}")
        # 清空已发送的媒体消息ID列表
        await state.update_data(sent_media_ids=[])
    except Exception as e:
        logger.warning(f"状态处理失败: {e}")
        # 如果状态处理失败，初始化一个空的媒体消息列表
        try:
            await state.update_data(sent_media_ids=[])
        except Exception as e2:
            logger.error(f"状态初始化也失败: {e2}")
    
    movie_requests = await get_pending_movie_requests()
    content_submissions = await get_pending_content_submissions()
    
    text = "✅ <b>审核中心</b>\n\n"
    text += f"🎬 待审核求片：{len(movie_requests)} 条\n"
    text += f"📝 待审核投稿：{len(content_submissions)} 条\n\n"
    text += "请选择要审核的类型："
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=admin_review_center_kb
    )
    await cb.answer()


# ==================== 所有求片管理 ====================

@review_center_router.callback_query(F.data == "admin_all_movies")
async def cb_admin_all_movies(cb: types.CallbackQuery, state: FSMContext):
    """所有求片管理"""
    # 检查管理员权限和功能开关
    from app.utils.review_config import check_admin_permission
    
    if not await check_admin_permission(cb.from_user.id):
        await cb.answer("❌ 审核功能已关闭", show_alert=True)
        return
    
    await movie_browse_handler.handle_browse_list(cb, state, 1)


@review_center_router.callback_query(F.data.startswith("all_movie_page_"))
async def cb_admin_all_movies_page(cb: types.CallbackQuery, state: FSMContext):
    """所有求片分页"""
    page = extract_page_from_callback(cb.data, "all_movie")
    await movie_browse_handler.handle_browse_list(cb, state, page)


# 原有的_show_all_movies_page函数已被配置类统一处理，删除重复代码


# 原有的_send_media_messages_for_movies函数已被配置类统一处理，删除重复代码


# ==================== 预览详情功能 ====================

@review_center_router.callback_query(F.data.startswith("preview_movie_detail_"))
async def cb_preview_movie_detail(cb: types.CallbackQuery, state: FSMContext):
    """预览求片详情"""
    item_id = int(cb.data.split("_")[-1])
    
    # 获取求片详情
    from app.database.business import get_movie_request_by_id
    request = await get_movie_request_by_id(item_id)
    
    if not request:
        await cb.answer("❌ 求片请求不存在", show_alert=True)
        return
    
    # 构建预览文本
    user_display = await get_user_display_link(request.user_id)
    status_text = get_status_text(request.status)
    
    preview_text = (
        f"🎬 <b>求片预览</b>\n\n"
        f"🆔 ID：{request.id}\n"
        f"🎭 片名：{request.title}\n"
        f"👤 用户：{user_display}\n"
        f"📅 提交时间：{humanize_time(request.created_at)}\n"
        f"📊 状态：{status_text}\n\n"
    )
    
    if request.description:
        preview_text += f"📄 描述：\n{request.description}\n\n"
    else:
        preview_text += f"📄 描述：无\n\n"
    
    if hasattr(request, 'file_id') and request.file_id:
        preview_text += f"📎 附件：有\n\n"
    else:
        preview_text += f"📎 附件：无\n\n"
    
    # 构建预览键盘（简化版）
    preview_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="💬 回复用户", callback_data=f"reply_movie_{item_id}")
            ],
            [
                types.InlineKeyboardButton(text="🔙 返回列表", callback_data="admin_all_movies")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=preview_text,
        reply_markup=preview_kb
    )
    
    # 如果有媒体文件，发送媒体消息
    if hasattr(request, 'file_id') and request.file_id:
        try:
            media_text = (
                f"🎬 <b>{request.title}</b>\n\n"
                f"🆔 ID: {request.id}\n"
                f"👤 用户: {user_display}\n"
                f"📅 时间: {humanize_time(request.created_at)}\n"
                f"📊 状态: {status_text}\n"
                f"📝 描述: {request.description or '无'}\n\n"
                f"💡 这是用户提交的附件"
            )
            
            media_keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="💬 回复用户", callback_data=f"reply_movie_{item_id}")
                    ]
                ]
            )
            
            media_msg = await cb.message.answer_photo(
                photo=request.file_id,
                caption=media_text,
                reply_markup=media_keyboard,
                parse_mode="HTML"
            )
            
            # 保存媒体消息ID
            data = await state.get_data()
            sent_media_ids = data.get('sent_media_ids', [])
            sent_media_ids.append(media_msg.message_id)
            await state.update_data(sent_media_ids=sent_media_ids)
            
        except Exception as e:
            logger.error(f"发送求片媒体消息失败: {e}")
    
    await cb.answer()


@review_center_router.callback_query(F.data.startswith("preview_content_detail_"))
async def cb_preview_content_detail(cb: types.CallbackQuery, state: FSMContext):
    """预览投稿详情"""
    item_id = int(cb.data.split("_")[-1])
    
    # 获取投稿详情
    from app.database.business import get_content_submission_by_id
    submission = await get_content_submission_by_id(item_id)
    
    if not submission:
        await cb.answer("❌ 投稿不存在", show_alert=True)
        return
    
    # 构建预览文本
    user_display = await get_user_display_link(submission.user_id)
    status_text = get_status_text(submission.status)
    
    preview_text = (
        f"📝 <b>投稿预览</b>\n\n"
        f"🆔 ID：{submission.id}\n"
        f"📝 标题：{submission.title}\n"
        f"👤 用户：{user_display}\n"
        f"📅 提交时间：{humanize_time(submission.created_at)}\n"
        f"📊 状态：{status_text}\n\n"
    )
    
    # 显示内容（限制长度）
    if submission.content:
        if len(submission.content) > 500:
            content_display = submission.content[:500] + "\n\n... (内容过长，已截断)"
        else:
            content_display = submission.content
        preview_text += f"📄 内容：\n{content_display}\n\n"
    else:
        preview_text += f"📄 内容：无\n\n"
    
    if hasattr(submission, 'file_id') and submission.file_id:
        preview_text += f"📎 附件：有\n\n"
    else:
        preview_text += f"📎 附件：无\n\n"
    
    # 构建预览键盘（简化版）
    preview_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="💬 回复用户", callback_data=f"reply_content_{item_id}")
            ],
            [
                types.InlineKeyboardButton(text="🔙 返回列表", callback_data="admin_all_content")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=preview_text,
        reply_markup=preview_kb
    )
    
    # 如果有媒体文件，发送媒体消息
    if hasattr(submission, 'file_id') and submission.file_id:
        try:
            media_text = (
                f"📝 <b>{submission.title}</b>\n\n"
                f"🆔 ID: {submission.id}\n"
                f"👤 用户: {user_display}\n"
                f"📅 时间: {humanize_time(submission.created_at)}\n"
                f"📊 状态: {status_text}\n"
                f"📄 内容: {submission.content or '无'}\n\n"
                f"💡 这是用户提交的附件"
            )
            
            media_keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="💬 回复用户", callback_data=f"reply_content_{item_id}")
                    ]
                ]
            )
            
            media_msg = await cb.message.answer_photo(
                photo=submission.file_id,
                caption=media_text,
                reply_markup=media_keyboard,
                parse_mode="HTML"
            )
            
            # 保存媒体消息ID
            data = await state.get_data()
            sent_media_ids = data.get('sent_media_ids', [])
            sent_media_ids.append(media_msg.message_id)
            await state.update_data(sent_media_ids=sent_media_ids)
            
        except Exception as e:
            logger.error(f"发送投稿媒体消息失败: {e}")
    
    await cb.answer()


# ==================== 回复用户功能 ====================

@review_center_router.callback_query(F.data.startswith("reply_movie_"))
async def cb_reply_movie(cb: types.CallbackQuery, state: FSMContext):
    """回复求片用户"""
    item_id = int(cb.data.split("_")[-1])
    
    # 获取求片详情
    from app.database.business import get_movie_request_by_id
    request = await get_movie_request_by_id(item_id)
    
    if not request:
        await cb.answer("❌ 求片请求不存在", show_alert=True)
        return
    
    # 设置状态
    from app.utils.states import Wait
    await state.set_state(Wait.waitReplyMessage)
    await state.update_data(
        reply_type="movie",
        reply_item_id=item_id,
        reply_user_id=request.user_id,
        reply_title=request.title
    )
    
    # 显示回复输入页面
    user_display = await get_user_display_link(request.user_id)
    reply_text = (
        f"💬 <b>回复用户</b>\n\n"
        f"🎬 求片：{request.title}\n"
        f"👤 用户：{user_display}\n\n"
        f"请输入您要发送给用户的回复消息："
    )
    
    reply_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="❌ 取消回复", callback_data=f"cancel_reply_movie_{item_id}")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=reply_text,
        reply_markup=reply_kb
    )
    await cb.answer()


@review_center_router.callback_query(F.data.startswith("reply_content_"))
async def cb_reply_content(cb: types.CallbackQuery, state: FSMContext):
    """回复投稿用户"""
    item_id = int(cb.data.split("_")[-1])
    
    # 获取投稿详情
    from app.database.business import get_content_submission_by_id
    submission = await get_content_submission_by_id(item_id)
    
    if not submission:
        await cb.answer("❌ 投稿不存在", show_alert=True)
        return
    
    # 设置状态
    from app.utils.states import Wait
    await state.set_state(Wait.waitReplyMessage)
    await state.update_data(
        reply_type="content",
        reply_item_id=item_id,
        reply_user_id=submission.user_id,
        reply_title=submission.title
    )
    
    # 显示回复输入页面
    user_display = await get_user_display_link(submission.user_id)
    reply_text = (
        f"💬 <b>回复用户</b>\n\n"
        f"📝 投稿：{submission.title}\n"
        f"👤 用户：{user_display}\n\n"
        f"请输入您要发送给用户的回复消息："
    )
    
    reply_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="❌ 取消回复", callback_data=f"cancel_reply_content_{item_id}")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=reply_text,
        reply_markup=reply_kb
    )
    await cb.answer()


@review_center_router.callback_query(F.data.startswith("cancel_reply_movie_"))
async def cb_cancel_reply_movie(cb: types.CallbackQuery, state: FSMContext):
    """取消回复求片用户"""
    item_id = int(cb.data.split("_")[-1])
    await state.clear()
    # 返回预览页面
    await cb_preview_movie_detail(cb, state)


@review_center_router.callback_query(F.data.startswith("cancel_reply_content_"))
async def cb_cancel_reply_content(cb: types.CallbackQuery, state: FSMContext):
    """取消回复投稿用户"""
    item_id = int(cb.data.split("_")[-1])
    await state.clear()
    # 返回预览页面
    await cb_preview_content_detail(cb, state)


@review_center_router.message(StateFilter(Wait.waitReplyMessage))
async def process_reply_message(msg: types.Message, state: FSMContext):
    """处理回复消息"""
    data = await state.get_data()
    reply_type = data.get('reply_type')
    reply_item_id = data.get('reply_item_id')
    reply_user_id = data.get('reply_user_id')
    reply_title = data.get('reply_title')
    
    if not all([reply_type, reply_item_id, reply_user_id, reply_title]):
        await msg.reply("❌ 回复信息不完整，请重新操作")
        await state.clear()
        return
    
    # 发送回复给用户
    try:
        reply_text = (
            f"📨 <b>管理员回复</b>\n\n"
            f"{'🎬' if reply_type == 'movie' else '📝'} 关于：{reply_title}\n\n"
            f"💬 回复内容：\n{msg.text}\n\n"
            f"如有疑问，请随时联系我们。"
        )
        
        await msg.bot.send_message(
            chat_id=reply_user_id,
            text=reply_text,
            parse_mode="HTML"
        )
        
        # 显示发送成功页面
        user_display = await get_user_display_link(reply_user_id)
        success_text = (
            f"✅ <b>回复发送成功！</b>\n\n"
            f"{'🎬' if reply_type == 'movie' else '📝'} 项目：{reply_title}\n"
            f"👤 用户：{user_display}\n"
            f"💬 回复内容：{msg.text}\n\n"
            f"用户已收到您的回复消息。"
        )
        
        success_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="🔙 返回列表", 
                        callback_data=f"admin_all_{'movies' if reply_type == 'movie' else 'content'}"
                    )
                ]
            ]
        )
        
        # 删除用户的回复消息
        try:
            await msg.delete()
        except:
            pass
        
        # 编辑主消息显示成功信息
        # 这里需要获取主消息，通过状态或其他方式
        # 暂时使用发送新消息的方式
        await msg.answer(
            text=success_text,
            reply_markup=success_kb,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"发送回复消息失败: {e}")
        await msg.reply(f"❌ 发送回复失败：{str(e)}")
    
    await state.clear()


# ==================== 清理功能 ====================

@review_center_router.callback_query(F.data == "admin_review_center_cleanup")
async def cb_admin_review_center_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """清理媒体消息并返回审核中心"""
    await cleanup_sent_media_messages(cb.bot, state)
    await cb_admin_review_center(cb, state)


@review_center_router.callback_query(F.data == "back_to_main_cleanup")
async def cb_back_to_main_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """清理媒体消息并返回主菜单"""
    from app.utils.panel_utils import return_to_main_menu
    
    # 定义清理逻辑函数
    async def cleanup_logic(cb):
        await cleanup_sent_media_messages(cb.bot, state)
    
    # 使用通用函数，传入清理逻辑
    await return_to_main_menu(cb, cleanup_logic)


# ==================== 所有投稿管理 ====================

@review_center_router.callback_query(F.data == "admin_all_content")
async def cb_admin_all_content(cb: types.CallbackQuery, state: FSMContext):
    """所有投稿管理"""
    # 检查管理员权限和功能开关
    from app.utils.review_config import check_admin_permission
    
    if not await check_admin_permission(cb.from_user.id):
        await cb.answer("❌ 审核功能已关闭", show_alert=True)
        return
    
    await content_browse_handler.handle_browse_list(cb, state, 1)


@review_center_router.callback_query(F.data.startswith("all_content_page_"))
async def cb_admin_all_content_page(cb: types.CallbackQuery, state: FSMContext):
    """所有投稿分页"""
    page = extract_page_from_callback(cb.data, "all_content")
    await content_browse_handler.handle_browse_list(cb, state, page)


# 原有的投稿相关函数已被配置类统一处理，删除重复代码