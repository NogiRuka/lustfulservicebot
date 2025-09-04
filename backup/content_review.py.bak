from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import (
    get_pending_content_submissions, get_all_content_submissions,
    review_content_submission, get_movie_category_by_id
)
from app.utils.message_utils import safe_edit_message
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.panel_utils import send_review_notification, cleanup_sent_media_messages, get_user_display_link
from app.utils.time_utils import humanize_time
from app.utils.review_utils import (
    ReviewUIBuilder, ReviewDataProcessor, ReviewMediaHandler, ReviewActionHandler
)
from app.buttons.users import back_to_main_kb

content_review_router = Router()


@content_review_router.callback_query(F.data == "admin_review_content")
async def cb_admin_review_content(cb: types.CallbackQuery, state: FSMContext):
    """管理员投稿审核"""
    # 清理之前发送的媒体消息
    await cleanup_sent_media_messages(cb.bot, state)
    
    # 获取待审核的投稿
    submissions = await get_pending_content_submissions()
    
    if not submissions:
        await cb.message.edit_caption(
            caption="📋 <b>投稿审核</b>\n\n📝 暂无待审核的投稿内容",
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
    page_data = paginator.get_page(1)
    
    # 构建投稿列表文本
    text = format_page_header("📝 投稿审核", paginator.current_page, paginator.total_pages)
    text += "\n\n"
    
    for submission in page_data:
        user_display = await get_user_display_link(submission.user_id)
        text += (
            f"🆔 ID: {submission.id}\n"
            f"📝 标题: {submission.title}\n"
            f"👤 用户: {user_display}\n"
            f"📅 时间: {humanize_time(submission.created_at)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    
    # 构建按钮
    keyboard = []
    
    # 详情按钮（每行2个）
    detail_buttons = []
    for i, submission in enumerate(page_data):
        detail_buttons.append(
            types.InlineKeyboardButton(
                text=f"📋 详情 {submission.id}",
                callback_data=f"review_content_detail_{submission.id}"
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
                types.InlineKeyboardButton(text="⬅️ 上一页", callback_data=f"content_review_page_{paginator.current_page - 1}")
            )
        if paginator.has_next():
            nav_buttons.append(
                types.InlineKeyboardButton(text="➡️ 下一页", callback_data=f"content_review_page_{paginator.current_page + 1}")
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


@content_review_router.callback_query(F.data.startswith("content_review_page_"))
async def cb_admin_review_content_page(cb: types.CallbackQuery, state: FSMContext, page: int = None):
    """投稿审核分页"""
    if page is None:
        page = extract_page_from_callback(cb.data, "content_review")
    
    # 删除之前发送的媒体消息
    await cleanup_sent_media_messages(cb.bot, state)
    
    # 重新调用主函数，但设置页码
    await cb_admin_review_content(cb, state)


@content_review_router.callback_query(F.data.startswith("review_content_detail_"))
async def cb_review_content_detail(cb: types.CallbackQuery, state: FSMContext):
    """查看投稿详情"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 获取投稿详情
    submissions = await get_pending_content_submissions()
    submission = next((s for s in submissions if s.id == submission_id), None)
    
    if not submission:
        await cb.answer("❌ 投稿不存在或已被处理")
        return
    
    # 准备数据
    item_data = await ReviewDataProcessor.prepare_item_data(submission, 'content')
    
    # 构建详情文本
    detail_text = ReviewUIBuilder.build_detail_text('content', item_data)
    
    # 构建键盘
    detail_kb = ReviewUIBuilder.build_detail_keyboard('content', submission.id, 'admin_review_content')
    
    # 如果有附件，发送媒体消息
    if submission.file_id:
        detail_text += f"📎 附件：有（文件ID: {submission.file_id[:20]}...）\n\n"
        detail_text += "请选择审核操作："
        
        await cb.message.edit_caption(
            caption=detail_text,
            reply_markup=detail_kb
        )
        
        # 发送媒体消息
        await ReviewMediaHandler.send_media_message(
            cb.bot, cb.from_user.id, submission.file_id, 'content', submission.title, submission.id, state
        )
    else:
        detail_text += f"📎 附件：无\n\n"
        detail_text += "请选择审核操作："
        
        await cb.message.edit_caption(
            caption=detail_text,
            reply_markup=detail_kb
        )
    
    await cb.answer()


@content_review_router.callback_query(F.data.regexp(r'^approve_content_\d+$'))
async def cb_approve_content(cb: types.CallbackQuery, state: FSMContext):
    """快速通过投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    success = await ReviewActionHandler.handle_quick_review('content', submission_id, cb.from_user.id, 'approved')
    
    if success:
        # 获取投稿信息发送通知
        submissions = await get_pending_content_submissions()
        submission = next((s for s in submissions if s.id == submission_id), None)
        
        if submission:
            # 通过category_id获取分类名称
            category = await get_movie_category_by_id(submission.category_id) if submission.category_id else None
            category_name = category.name if category else None
            
            await send_review_notification(
                cb.bot, submission.user_id, 'content', submission.title, 'approved',
                file_id=submission.file_id, item_content=submission.content, item_id=submission.id,
                category_name=category_name
            )
        
        await cb.answer("✅ 投稿已通过")
        # 刷新审核列表
        await cb_admin_review_content(cb, state)
    else:
        await cb.answer("❌ 操作失败，请检查投稿ID是否正确")


@content_review_router.callback_query(F.data.regexp(r'^reject_content_\d+$'))
async def cb_reject_content(cb: types.CallbackQuery, state: FSMContext):
    """快速拒绝投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    success = await ReviewActionHandler.handle_quick_review('content', submission_id, cb.from_user.id, 'rejected')
    
    if success:
        # 获取投稿信息发送通知
        submissions = await get_pending_content_submissions()
        submission = next((s for s in submissions if s.id == submission_id), None)
        
        if submission:
            # 通过category_id获取分类名称
            category = await get_movie_category_by_id(submission.category_id) if submission.category_id else None
            category_name = category.name if category else None
            
            await send_review_notification(
                cb.bot, submission.user_id, 'content', submission.title, 'rejected',
                file_id=submission.file_id, item_content=submission.content, item_id=submission.id,
                category_name=category_name
            )
        
        await cb.answer("❌ 投稿已拒绝")
        # 刷新审核列表
        await cb_admin_review_content(cb, state)
    else:
        await cb.answer("❌ 操作失败，请检查投稿ID是否正确")


@content_review_router.callback_query(F.data.startswith("approve_content_media_"))
async def cb_approve_content_media(cb: types.CallbackQuery):
    """媒体消息快速通过投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    success = await ReviewActionHandler.handle_quick_review('content', submission_id, cb.from_user.id, 'approved')
    
    if success:
        await cb.answer(f"✅ 已通过投稿 {submission_id}", show_alert=True)
        # 删除媒体消息
        try:
            await cb.message.delete()
        except Exception as e:
            logger.warning(f"删除媒体消息失败: {e}")
    else:
        await cb.answer("❌ 操作失败，请检查投稿ID是否正确", show_alert=True)


@content_review_router.callback_query(F.data.startswith("reject_content_media_"))
async def cb_reject_content_media(cb: types.CallbackQuery):
    """媒体消息快速拒绝投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    success = await ReviewActionHandler.handle_quick_review('content', submission_id, cb.from_user.id, 'rejected')
    
    if success:
        await cb.answer(f"❌ 已拒绝投稿 {submission_id}", show_alert=True)
        # 删除媒体消息
        try:
            await cb.message.delete()
        except Exception as e:
            logger.warning(f"删除媒体消息失败: {e}")
    else:
        await cb.answer("❌ 操作失败，请检查投稿ID是否正确", show_alert=True)


@content_review_router.callback_query(F.data.startswith("approve_content_note_media_"))
async def cb_approve_content_note_media(cb: types.CallbackQuery, state: FSMContext):
    """媒体消息通过投稿并留言"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 设置状态等待留言输入
    await state.set_state(Wait.review_note)
    await state.update_data(
        review_type="content",
        item_id=submission_id,
        review_action="approved",
        media_message_id=cb.message.message_id
    )
    
    await cb.answer("📝 请输入审核留言：", show_alert=True)
    await cb.bot.send_message(
        chat_id=cb.from_user.id,
        text="📝 <b>请输入审核留言</b>\n\n💡 留言将发送给用户，请输入您的审核意见：",
        parse_mode="HTML"
    )


@content_review_router.callback_query(F.data.startswith("reject_content_note_media_"))
async def cb_reject_content_note_media(cb: types.CallbackQuery, state: FSMContext):
    """媒体消息拒绝投稿并留言"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 设置状态等待留言输入
    await state.set_state(Wait.review_note)
    await state.update_data(
        review_type="content",
        item_id=submission_id,
        review_action="rejected",
        media_message_id=cb.message.message_id
    )
    
    await cb.answer("📝 请输入审核留言：", show_alert=True)
    await cb.bot.send_message(
        chat_id=cb.from_user.id,
        text="📝 <b>请输入审核留言</b>\n\n💡 留言将发送给用户，请输入您的拒绝理由：",
        parse_mode="HTML"
    )


@content_review_router.callback_query(F.data == "admin_review_content_cleanup")
async def cb_admin_review_content_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """返回投稿审核列表并清理媒体消息"""
    # 清理媒体消息
    await cleanup_sent_media_messages(cb.bot, state)
    # 返回投稿审核列表
    await cb_admin_review_content(cb, state)


@content_review_router.callback_query(F.data == "back_to_main_cleanup")
async def cb_back_to_main_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """返回主菜单并清理媒体消息"""
    # 清理媒体消息
    await cleanup_sent_media_messages(cb.bot, state)
    # 返回主菜单
    await cb.message.edit_caption(
        caption="🌸 欢迎回到主菜单 🌸",
        reply_markup=back_to_main_kb
    )
    await cb.answer()


@content_review_router.callback_query(F.data.startswith("delete_media_message_"))
async def cb_delete_media_message(cb: types.CallbackQuery, state: FSMContext):
    """删除媒体消息"""
    try:
        await cb.message.delete()
        await cb.answer("🗑️ 媒体消息已删除")
    except Exception as e:
        logger.warning(f"删除媒体消息失败: {e}")
        await cb.answer("❌ 删除失败")