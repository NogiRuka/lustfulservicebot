from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import (
    get_pending_content_submissions, get_all_content_submissions,
    review_content_submission, get_content_submission_by_id
)
from app.utils.review_config import ReviewConfig, ReviewHandler
from app.utils.pagination import extract_page_from_callback
from app.utils.permission_utils import require_admin_permission

content_review_router = Router()

# 投稿审核配置
content_review_config = ReviewConfig(
    item_type='content',
    emoji='📝',
    name='投稿',
    title_field='title',
    content_field='content',
    get_pending_items_function=get_pending_content_submissions,
    get_all_items_function=get_all_content_submissions,
    get_item_by_id_function=get_content_submission_by_id,
    review_function=review_content_submission,
    list_callback='admin_review_content',
    page_callback_prefix='content_review_page_',
    detail_callback_prefix='review_content_detail_',
    approve_callback_prefix='approve_content_',
    reject_callback_prefix='reject_content_',
    approve_media_callback_prefix='approve_content_media_',
    reject_media_callback_prefix='reject_content_media_',
    approve_note_media_callback_prefix='approve_content_note_media_',
    reject_note_media_callback_prefix='reject_content_note_media_',
    cleanup_callback='admin_review_content_cleanup',
    back_to_main_cleanup_callback='back_to_main_cleanup'
)

# 投稿审核处理器
content_review_handler = ReviewHandler(content_review_config)


@content_review_router.callback_query(F.data == "admin_review_content")
@require_admin_permission("admin_panel_enabled")
async def cb_admin_review_content(cb: types.CallbackQuery, state: FSMContext):
    """管理员投稿审核"""
    await content_review_handler.handle_review_list(cb, state)


@content_review_router.callback_query(F.data.startswith("content_review_page_"))
async def cb_admin_review_content_page(cb: types.CallbackQuery, state: FSMContext):
    """投稿审核分页"""
    page = extract_page_from_callback(cb.data, "content_review")
    await content_review_handler.handle_review_list(cb, state, page)


@content_review_router.callback_query(F.data.startswith("review_content_detail_"))
async def cb_review_content_detail(cb: types.CallbackQuery, state: FSMContext):
    """查看投稿详情"""
    item_id = int(cb.data.split("_")[-1])
    await content_review_handler.handle_detail(cb, state, item_id)


@content_review_router.callback_query(F.data.regexp(r'^approve_content_\d+$'))
async def cb_approve_content(cb: types.CallbackQuery, state: FSMContext):
    """通过投稿"""
    item_id = int(cb.data.split("_")[-1])
    await content_review_handler.handle_approve(cb, state, item_id)


@content_review_router.callback_query(F.data.regexp(r'^reject_content_\d+$'))
async def cb_reject_content(cb: types.CallbackQuery, state: FSMContext):
    """拒绝投稿"""
    item_id = int(cb.data.split("_")[-1])
    await content_review_handler.handle_reject(cb, state, item_id)


@content_review_router.callback_query(F.data.startswith("approve_content_media_"))
async def cb_approve_content_media(cb: types.CallbackQuery, state: FSMContext):
    """从媒体消息通过投稿"""
    item_id = int(cb.data.split("_")[-1])
    await content_review_handler.handle_approve(cb, state, item_id)


@content_review_router.callback_query(F.data.startswith("reject_content_media_"))
async def cb_reject_content_media(cb: types.CallbackQuery, state: FSMContext):
    """从媒体消息拒绝投稿"""
    item_id = int(cb.data.split("_")[-1])
    await content_review_handler.handle_reject(cb, state, item_id)


@content_review_router.callback_query(F.data.startswith("approve_content_note_"))
async def cb_approve_content_note(cb: types.CallbackQuery, state: FSMContext):
    """通过投稿并留言"""
    item_id = int(cb.data.split("_")[-1])
    await state.set_state(Wait.waitReviewNote)
    await state.update_data(
        action="approve", 
        item_id=item_id, 
        item_type="content",
        message_id=cb.message.message_id
    )
    
    await cb.message.edit_caption(
        caption="✅ <b>通过投稿并留言</b>\n\n请输入留言内容：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 返回", callback_data=f"review_content_detail_{item_id}")]
            ]
        )
    )
    await cb.answer()


@content_review_router.callback_query(F.data.startswith("reject_content_note_"))
async def cb_reject_content_note(cb: types.CallbackQuery, state: FSMContext):
    """拒绝投稿并留言"""
    item_id = int(cb.data.split("_")[-1])
    await state.set_state(Wait.waitReviewNote)
    await state.update_data(
        action="reject", 
        item_id=item_id, 
        item_type="content",
        message_id=cb.message.message_id
    )
    
    await cb.message.edit_caption(
        caption="❌ <b>拒绝投稿并留言</b>\n\n请输入拒绝原因：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 返回", callback_data=f"review_content_detail_{item_id}")]
            ]
        )
    )
    await cb.answer()


@content_review_router.callback_query(F.data.startswith("approve_content_note_media_"))
async def cb_approve_content_note_media(cb: types.CallbackQuery, state: FSMContext):
    """从媒体消息通过投稿并留言"""
    item_id = int(cb.data.split("_")[-1])
    await state.set_state(Wait.waitReviewNote)
    await state.update_data(action="approve", item_id=item_id, item_type="content")
    
    await cb.message.edit_caption(
        caption="✅ <b>通过投稿并留言</b>\n\n请输入留言内容：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 返回", callback_data=f"review_content_detail_{item_id}")]
            ]
        )
    )
    await cb.answer()


@content_review_router.callback_query(F.data.startswith("reject_content_note_media_"))
async def cb_reject_content_note_media(cb: types.CallbackQuery, state: FSMContext):
    """从媒体消息拒绝投稿并留言"""
    item_id = int(cb.data.split("_")[-1])
    await state.set_state(Wait.waitReviewNote)
    await state.update_data(action="reject", item_id=item_id, item_type="content")
    
    await cb.message.edit_caption(
        caption="❌ <b>拒绝投稿并留言</b>\n\n请输入拒绝原因：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 返回", callback_data=f"review_content_detail_{item_id}")]
            ]
        )
    )
    await cb.answer()


@content_review_router.callback_query(F.data == "admin_review_content_cleanup")
async def cb_admin_review_content_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """清理并返回投稿审核列表"""
    await content_review_handler.handle_cleanup(cb, state)


@content_review_router.callback_query(F.data == "back_to_main_cleanup")
async def cb_back_to_main_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """清理并返回主菜单"""
    await content_review_handler.handle_back_to_main_cleanup(cb, state)


@content_review_router.callback_query(F.data.startswith("delete_media_message_"))
async def cb_delete_media_message(cb: types.CallbackQuery, state: FSMContext):
    """删除媒体消息"""
    item_id = int(cb.data.split("_")[-1])
    await content_review_handler.handle_delete_media_message(cb, state, item_id)