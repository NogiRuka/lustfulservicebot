from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import (
    get_pending_movie_requests, get_all_movie_requests,
    review_movie_request, get_movie_category_by_id
)
from app.utils.message_utils import safe_edit_message
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.panel_utils import send_review_notification, cleanup_sent_media_messages
from app.utils.review_utils import (
    ReviewUIBuilder, ReviewDataProcessor, ReviewMediaHandler, ReviewActionHandler
)

movie_review_router = Router()


@movie_review_router.callback_query(F.data == "admin_review_movie")
async def cb_admin_review_movie(cb: types.CallbackQuery, state: FSMContext):
    """管理员求片审核"""
    # 清理之前发送的媒体消息
    await cleanup_sent_media_messages(cb.bot, state)
    
    # 获取待审核的求片
    requests = await get_pending_movie_requests()
    
    if not requests:
        await cb.message.edit_caption(
            caption="📋 <b>求片审核</b>\n\n🎬 暂无待审核的求片请求",
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
    page_data = paginator.get_page(1)
    
    # 构建求片列表文本
    text = format_page_header("🎬 求片审核", paginator.current_page, paginator.total_pages)
    text += "\n\n"
    
    for request in page_data:
        user_display = await get_user_display_link(request.user_id)
        text += (
            f"🆔 ID: {request.id}\n"
            f"🎭 片名: {request.title}\n"
            f"👤 用户: {user_display}\n"
            f"📅 时间: {humanize_time(request.created_at)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    
    # 构建按钮
    keyboard = []
    
    # 详情按钮（每行2个）
    detail_buttons = []
    for i, request in enumerate(page_data):
        detail_buttons.append(
            types.InlineKeyboardButton(
                text=f"📋 详情 {request.id}",
                callback_data=f"review_movie_detail_{request.id}"
            )
        )
        if (i + 1) % 2 == 0 or i == len(page_data) - 1:
            keyboard.append(detail_buttons)
            detail_buttons = []
    
    # 分页按钮
    if paginator.total_pages > 1:
        nav_buttons = []
        if paginator.has_prev():
            nav_buttons.append(
                types.InlineKeyboardButton(text="⬅️ 上一页", callback_data=f"movie_review_page_{paginator.current_page - 1}")
            )
        if paginator.has_next():
            nav_buttons.append(
                types.InlineKeyboardButton(text="➡️ 下一页", callback_data=f"movie_review_page_{paginator.current_page + 1}")
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
    await cb.answer()


@movie_review_router.callback_query(F.data.startswith("movie_review_page_"))
async def cb_admin_review_movie_page(cb: types.CallbackQuery, state: FSMContext, page: int = None):
    """求片审核分页"""
    if page is None:
        page = extract_page_from_callback(cb.data, "movie_review")
    
    # 删除之前发送的媒体消息
    await cleanup_sent_media_messages(cb.bot, state)
    
    # 重新调用主函数，但设置页码
    await cb_admin_review_movie(cb, state)


@movie_review_router.callback_query(F.data.startswith("review_movie_detail_"))
async def cb_review_movie_detail(cb: types.CallbackQuery, state: FSMContext):
    """查看求片详情"""
    request_id = int(cb.data.split("_")[-1])
    
    # 获取求片详情
    requests = await get_pending_movie_requests()
    request = next((r for r in requests if r.id == request_id), None)
    
    if not request:
        await cb.answer("❌ 求片请求不存在或已被处理")
        return
    
    # 准备数据
    item_data = await ReviewDataProcessor.prepare_item_data(request, 'movie')
    
    # 构建详情文本
    detail_text = ReviewUIBuilder.build_detail_text('movie', item_data)
    
    # 构建键盘
    detail_kb = ReviewUIBuilder.build_detail_keyboard('movie', request.id, 'admin_review_movie')
    
    # 如果有附件，发送媒体消息
    if request.file_id:
        detail_text += f"📎 附件：有（文件ID: {request.file_id[:20]}...）\n\n"
        detail_text += "请选择审核操作："
        
        await cb.message.edit_caption(
            caption=detail_text,
            reply_markup=detail_kb
        )
        
        # 发送媒体消息
        await ReviewMediaHandler.send_media_message(
            cb.bot, cb.from_user.id, request.file_id, 'movie', request.title, request.id, state
        )
    else:
        detail_text += f"📎 附件：无\n\n"
        detail_text += "请选择审核操作："
        
        await cb.message.edit_caption(
            caption=detail_text,
            reply_markup=detail_kb
        )
    
    await cb.answer()


@movie_review_router.callback_query(F.data.regexp(r'^approve_movie_\d+$'))
async def cb_approve_movie(cb: types.CallbackQuery, state: FSMContext):
    """快速通过求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await ReviewActionHandler.handle_quick_review('movie', request_id, cb.from_user.id, 'approved')
    
    if success:
        # 获取求片信息发送通知
        requests = await get_pending_movie_requests()
        request = next((r for r in requests if r.id == request_id), None)
        
        if request:
            # 通过category_id获取分类名称
            category = await get_movie_category_by_id(request.category_id) if request.category_id else None
            category_name = category.name if category else None
            
            await send_review_notification(
                cb.bot, request.user_id, 'movie', request.title, 'approved',
                file_id=request.file_id, item_content=request.description, item_id=request.id,
                category_name=category_name
            )
        
        await cb.answer("✅ 求片已通过")
        # 刷新审核列表
        await cb_admin_review_movie(cb, state)
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确")


@movie_review_router.callback_query(F.data.regexp(r'^reject_movie_\d+$'))
async def cb_reject_movie(cb: types.CallbackQuery, state: FSMContext):
    """快速拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await ReviewActionHandler.handle_quick_review('movie', request_id, cb.from_user.id, 'rejected')
    
    if success:
        # 获取求片信息发送通知
        requests = await get_pending_movie_requests()
        request = next((r for r in requests if r.id == request_id), None)
        
        if request:
            # 通过category_id获取分类名称
            category = await get_movie_category_by_id(request.category_id) if request.category_id else None
            category_name = category.name if category else None
            
            await send_review_notification(
                cb.bot, request.user_id, 'movie', request.title, 'rejected',
                file_id=request.file_id, item_content=request.description, item_id=request.id,
                category_name=category_name
            )
        
        await cb.answer("❌ 求片已拒绝")
        # 刷新审核列表
        await cb_admin_review_movie(cb, state)
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确")


@movie_review_router.callback_query(F.data.startswith("approve_movie_media_"))
async def cb_approve_movie_media(cb: types.CallbackQuery):
    """媒体消息快速通过求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await ReviewActionHandler.handle_quick_review('movie', request_id, cb.from_user.id, 'approved')
    
    if success:
        await cb.answer(f"✅ 已通过求片 {request_id}", show_alert=True)
        # 删除媒体消息
        try:
            await cb.message.delete()
        except Exception as e:
            logger.warning(f"删除媒体消息失败: {e}")
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确", show_alert=True)


@movie_review_router.callback_query(F.data.startswith("reject_movie_media_"))
async def cb_reject_movie_media(cb: types.CallbackQuery):
    """媒体消息快速拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await ReviewActionHandler.handle_quick_review('movie', request_id, cb.from_user.id, 'rejected')
    
    if success:
        await cb.answer(f"❌ 已拒绝求片 {request_id}", show_alert=True)
        # 删除媒体消息
        try:
            await cb.message.delete()
        except Exception as e:
            logger.warning(f"删除媒体消息失败: {e}")
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确", show_alert=True)


@movie_review_router.callback_query(F.data.startswith("approve_movie_note_media_"))
async def cb_approve_movie_note_media(cb: types.CallbackQuery, state: FSMContext):
    """媒体消息通过求片并留言"""
    request_id = int(cb.data.split("_")[-1])
    
    # 设置状态等待留言输入
    await state.set_state(Wait.review_note)
    await state.update_data(
        review_type="movie",
        item_id=request_id,
        review_action="approved",
        media_message_id=cb.message.message_id
    )
    
    await cb.answer("📝 请输入审核留言：", show_alert=True)
    await cb.bot.send_message(
        chat_id=cb.from_user.id,
        text="📝 <b>请输入审核留言</b>\n\n💡 留言将发送给用户，请输入您的审核意见：",
        parse_mode="HTML"
    )


@movie_review_router.callback_query(F.data.startswith("reject_movie_note_media_"))
async def cb_reject_movie_note_media(cb: types.CallbackQuery, state: FSMContext):
    """媒体消息拒绝求片并留言"""
    request_id = int(cb.data.split("_")[-1])
    
    # 设置状态等待留言输入
    await state.set_state(Wait.review_note)
    await state.update_data(
        review_type="movie",
        item_id=request_id,
        review_action="rejected",
        media_message_id=cb.message.message_id
    )
    
    await cb.answer("📝 请输入审核留言：", show_alert=True)
    await cb.bot.send_message(
        chat_id=cb.from_user.id,
        text="📝 <b>请输入审核留言</b>\n\n💡 留言将发送给用户，请输入您的拒绝理由：",
        parse_mode="HTML"
    )