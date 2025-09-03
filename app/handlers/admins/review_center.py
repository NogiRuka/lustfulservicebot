from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.database.business import (
    get_pending_movie_requests, get_pending_content_submissions,
    get_all_movie_requests, get_all_content_submissions
)
from app.buttons.users import admin_review_center_kb, back_to_main_kb
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.panel_utils import get_user_display_link, cleanup_sent_media_messages

review_center_router = Router()


# ==================== 审核中心 ====================

@review_center_router.callback_query(F.data == "admin_review_center")
async def cb_admin_review_center(cb: types.CallbackQuery, state: FSMContext):
    """审核中心"""
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
    await cleanup_sent_media_messages(cb.bot, state)
    await _show_all_movies_page(cb, state, 1)


@review_center_router.callback_query(F.data.startswith("all_movie_page_"))
async def cb_admin_all_movies_page(cb: types.CallbackQuery, state: FSMContext):
    """所有求片分页"""
    page = extract_page_from_callback(cb.data, "all_movie")
    await _show_all_movies_page(cb, state, page)


async def _show_all_movies_page(cb: types.CallbackQuery, state: FSMContext, page: int):
    """显示所有求片页面"""
    requests = await get_all_movie_requests()
    
    if not requests:
        await cb.message.edit_caption(
            caption="📋 <b>所有求片</b>\n\n🎬 暂无求片记录",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center")]
                ]
            )
        )
        await cb.answer()
        return
    
    # 创建分页器
    paginator = Paginator(requests, page_size=5)
    page_data = paginator.get_page_items(page)
    page_info = paginator.get_page_info(page)
    
    # 构建求片列表文本
    text = format_page_header("📋 所有求片", page_info)
    text += "\n\n"
    
    start_num = (page - 1) * paginator.page_size + 1
    for i, request in enumerate(page_data, start_num):
        user_display = await get_user_display_link(request.user_id)
        status_text = get_status_text(request.status)
        text += (
            f"🆔 ID: {request.id}\n"
            f"🎭 片名: {request.title}\n"
            f"👤 用户: {user_display}\n"
            f"📅 时间: {humanize_time(request.created_at)}\n"
            f"📊 状态: {status_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    
    # 构建键盘
    keyboard = []
    
    # 项目按钮
    for i, request in enumerate(page_data, start_num):
        title = request.title[:20] + "..." if len(request.title) > 20 else request.title
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"{i}. {title}",
                callback_data=f"review_movie_detail_{request.id}"
            )
        ])
    
    # 分页按钮
    if paginator.total_pages > 1:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(
                types.InlineKeyboardButton(
                    text="⬅️ 上一页",
                    callback_data=f"all_movie_page_{page - 1}"
                )
            )
        if page < paginator.total_pages:
            nav_buttons.append(
                types.InlineKeyboardButton(
                    text="➡️ 下一页",
                    callback_data=f"all_movie_page_{page + 1}"
                )
            )
        if nav_buttons:
            keyboard.append(nav_buttons)
    
    # 返回按钮
    keyboard.append([
        types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center")
    ])
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    # 发送有媒体的项目
    await _send_media_messages_for_movies(cb, state, page_data)
    
    await cb.answer()


async def _send_media_messages_for_movies(cb: types.CallbackQuery, state: FSMContext, items: list):
    """为有媒体的求片项目发送媒体消息"""
    data = await state.get_data()
    sent_media_ids = data.get('sent_media_ids', [])
    
    for item in items:
        if hasattr(item, 'file_id') and item.file_id:
            try:
                # 构建媒体消息文本
                user_display = await get_user_display_link(item.user_id)
                status_text = get_status_text(item.status)
                
                media_text = (
                    f"🎬 <b>{item.title}</b>\n\n"
                    f"🆔 ID: {item.id}\n"
                    f"👤 用户: {user_display}\n"
                    f"📅 时间: {humanize_time(item.created_at)}\n"
                    f"📊 状态: {status_text}\n"
                    f"📝 描述: {item.description or '无'}\n\n"
                    f"💡 点击下方按钮进行操作"
                )
                
                # 构建媒体消息键盘
                media_keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="📋 详情", callback_data=f"review_movie_detail_{item.id}")
                        ]
                    ]
                )
                
                # 发送媒体消息
                media_msg = await cb.message.answer_photo(
                    photo=item.file_id,
                    caption=media_text,
                    reply_markup=media_keyboard,
                    parse_mode="HTML"
                )
                
                # 保存媒体消息ID
                sent_media_ids.append(media_msg.message_id)
                
            except Exception as e:
                logger.error(f"发送求片媒体消息失败: {e}")
    
    # 更新状态中的媒体消息ID列表
    await state.update_data(sent_media_ids=sent_media_ids, chat_id=cb.from_user.id)


# ==================== 所有投稿管理 ====================

@review_center_router.callback_query(F.data == "admin_all_content")
async def cb_admin_all_content(cb: types.CallbackQuery, state: FSMContext):
    """所有投稿管理"""
    await cleanup_sent_media_messages(cb.bot, state)
    await _show_all_content_page(cb, state, 1)


@review_center_router.callback_query(F.data.startswith("all_content_page_"))
async def cb_admin_all_content_page(cb: types.CallbackQuery, state: FSMContext):
    """所有投稿分页"""
    page = extract_page_from_callback(cb.data, "all_content")
    await _show_all_content_page(cb, state, page)


async def _show_all_content_page(cb: types.CallbackQuery, state: FSMContext, page: int):
    """显示所有投稿页面"""
    submissions = await get_all_content_submissions()
    
    if not submissions:
        await cb.message.edit_caption(
            caption="📋 <b>所有投稿</b>\n\n📝 暂无投稿记录",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center")]
                ]
            )
        )
        await cb.answer()
        return
    
    # 创建分页器
    paginator = Paginator(submissions, page_size=5)
    page_data = paginator.get_page_items(page)
    page_info = paginator.get_page_info(page)
    
    # 构建投稿列表文本
    text = format_page_header("📋 所有投稿", page_info)
    text += "\n\n"
    
    start_num = (page - 1) * paginator.page_size + 1
    for i, submission in enumerate(page_data, start_num):
        user_display = await get_user_display_link(submission.user_id)
        status_text = get_status_text(submission.status)
        text += (
            f"🆔 ID: {submission.id}\n"
            f"📝 标题: {submission.title}\n"
            f"👤 用户: {user_display}\n"
            f"📅 时间: {humanize_time(submission.created_at)}\n"
            f"📊 状态: {status_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    
    # 构建键盘
    keyboard = []
    
    # 项目按钮
    for i, submission in enumerate(page_data, start_num):
        title = submission.title[:20] + "..." if len(submission.title) > 20 else submission.title
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"{i}. {title}",
                callback_data=f"review_content_detail_{submission.id}"
            )
        ])
    
    # 分页按钮
    if paginator.total_pages > 1:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(
                types.InlineKeyboardButton(
                    text="⬅️ 上一页",
                    callback_data=f"all_content_page_{page - 1}"
                )
            )
        if page < paginator.total_pages:
            nav_buttons.append(
                types.InlineKeyboardButton(
                    text="➡️ 下一页",
                    callback_data=f"all_content_page_{page + 1}"
                )
            )
        if nav_buttons:
            keyboard.append(nav_buttons)
    
    # 返回按钮
    keyboard.append([
        types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center")
    ])
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    # 发送有媒体的项目
    await _send_media_messages_for_content(cb, state, page_data)
    
    await cb.answer()


async def _send_media_messages_for_content(cb: types.CallbackQuery, state: FSMContext, items: list):
    """为有媒体的投稿项目发送媒体消息"""
    data = await state.get_data()
    sent_media_ids = data.get('sent_media_ids', [])
    
    for item in items:
        if hasattr(item, 'file_id') and item.file_id:
            try:
                # 构建媒体消息文本
                user_display = await get_user_display_link(item.user_id)
                status_text = get_status_text(item.status)
                
                media_text = (
                    f"📝 <b>{item.title}</b>\n\n"
                    f"🆔 ID: {item.id}\n"
                    f"👤 用户: {user_display}\n"
                    f"📅 时间: {humanize_time(item.created_at)}\n"
                    f"📊 状态: {status_text}\n"
                    f"📄 内容: {item.content or '无'}\n\n"
                    f"💡 点击下方按钮进行操作"
                )
                
                # 构建媒体消息键盘
                media_keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="📋 详情", callback_data=f"review_content_detail_{item.id}")
                        ]
                    ]
                )
                
                # 发送媒体消息
                media_msg = await cb.message.answer_photo(
                    photo=item.file_id,
                    caption=media_text,
                    reply_markup=media_keyboard,
                    parse_mode="HTML"
                )
                
                # 保存媒体消息ID
                sent_media_ids.append(media_msg.message_id)
                
            except Exception as e:
                logger.error(f"发送投稿媒体消息失败: {e}")
    
    # 更新状态中的媒体消息ID列表
    await state.update_data(sent_media_ids=sent_media_ids, chat_id=cb.from_user.id)