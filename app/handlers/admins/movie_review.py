from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import (
    get_pending_movie_requests, get_all_movie_requests,
    review_movie_request, get_movie_request_by_id
)
from app.utils.review_config import ReviewConfig, ReviewHandler
from app.utils.pagination import extract_page_from_callback
from app.utils.permission_utils import require_admin_permission

movie_review_router = Router()

# 求片审核配置
movie_review_config = ReviewConfig(
    item_type='movie',
    emoji='🎬',
    name='求片',
    title_field='title',
    content_field='description',
    get_pending_items_function=get_pending_movie_requests,
    get_all_items_function=get_all_movie_requests,
    get_item_by_id_function=get_movie_request_by_id,
    review_function=review_movie_request,
    list_callback='admin_review_movie',
    page_callback_prefix='movie_review_page_',
    detail_callback_prefix='review_movie_detail_',
    approve_callback_prefix='approve_movie_',
    reject_callback_prefix='reject_movie_',
    approve_media_callback_prefix='approve_movie_media_',
    reject_media_callback_prefix='reject_movie_media_',
    approve_note_media_callback_prefix='approve_movie_note_media_',
    reject_note_media_callback_prefix='reject_movie_note_media_',
    cleanup_callback='admin_review_movie_cleanup',
    back_to_main_cleanup_callback='back_to_main_cleanup'
)

# 求片审核处理器
movie_review_handler = ReviewHandler(movie_review_config)


@movie_review_router.callback_query(F.data == "admin_review_movie")
@require_admin_permission("admin_panel_enabled")
async def cb_admin_review_movie(cb: types.CallbackQuery, state: FSMContext):
    """管理员求片审核"""
    await movie_review_handler.handle_review_list(cb, state)


@movie_review_router.callback_query(F.data.startswith("movie_review_page_"))
async def cb_admin_review_movie_page(cb: types.CallbackQuery, state: FSMContext):
    """求片审核分页"""
    page = extract_page_from_callback(cb.data, "movie_review")
    await movie_review_handler.handle_review_list(cb, state, page)


@movie_review_router.callback_query(F.data.startswith("review_movie_detail_"))
async def cb_review_movie_detail(cb: types.CallbackQuery, state: FSMContext):
    """查看求片详情"""
    item_id = int(cb.data.split("_")[-1])
    await movie_review_handler.handle_detail(cb, state, item_id)


@movie_review_router.callback_query(F.data.regexp(r'^approve_movie_\d+$'))
async def cb_approve_movie(cb: types.CallbackQuery, state: FSMContext):
    """通过求片"""
    item_id = int(cb.data.split("_")[-1])
    await movie_review_handler.handle_approve(cb, state, item_id)


@movie_review_router.callback_query(F.data.regexp(r'^reject_movie_\d+$'))
async def cb_reject_movie(cb: types.CallbackQuery, state: FSMContext):
    """拒绝求片"""
    item_id = int(cb.data.split("_")[-1])
    await movie_review_handler.handle_reject(cb, state, item_id)


@movie_review_router.callback_query(F.data.startswith("approve_movie_media_"))
async def cb_approve_movie_media(cb: types.CallbackQuery, state: FSMContext):
    """从媒体消息通过求片"""
    item_id = int(cb.data.split("_")[-1])
    await movie_review_handler.handle_approve(cb, state, item_id)


@movie_review_router.callback_query(F.data.startswith("reject_movie_media_"))
async def cb_reject_movie_media(cb: types.CallbackQuery, state: FSMContext):
    """从媒体消息拒绝求片"""
    item_id = int(cb.data.split("_")[-1])
    await movie_review_handler.handle_reject(cb, state, item_id)


@movie_review_router.callback_query(F.data.startswith("approve_movie_note_"))
async def cb_approve_movie_note(cb: types.CallbackQuery, state: FSMContext):
    """通过求片并留言"""
    item_id = int(cb.data.split("_")[-1])
    await state.set_state(Wait.waitReviewNote)
    await state.update_data(
        action="approve", 
        item_id=item_id, 
        item_type="movie",
        message_id=cb.message.message_id
    )
    
    await cb.message.edit_caption(
        caption="✅ <b>通过求片并留言</b>\n\n请输入留言内容：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 返回", callback_data=f"review_movie_detail_{item_id}")]
            ]
        )
    )
    await cb.answer()


@movie_review_router.callback_query(F.data.startswith("reject_movie_note_"))
async def cb_reject_movie_note(cb: types.CallbackQuery, state: FSMContext):
    """拒绝求片并留言"""
    item_id = int(cb.data.split("_")[-1])
    await state.set_state(Wait.waitReviewNote)
    await state.update_data(
        action="reject", 
        item_id=item_id, 
        item_type="movie",
        message_id=cb.message.message_id
    )
    
    await cb.message.edit_caption(
        caption="❌ <b>拒绝求片并留言</b>\n\n请输入拒绝原因：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 返回", callback_data=f"review_movie_detail_{item_id}")]
            ]
        )
    )
    await cb.answer()


@movie_review_router.callback_query(F.data.startswith("approve_movie_note_media_"))
async def cb_approve_movie_note_media(cb: types.CallbackQuery, state: FSMContext):
    """从媒体消息通过求片并留言"""
    item_id = int(cb.data.split("_")[-1])
    await state.set_state(Wait.waitReviewNote)
    await state.update_data(action="approve", item_id=item_id, item_type="movie")
    
    await cb.message.edit_caption(
        caption="✅ <b>通过求片并留言</b>\n\n请输入留言内容：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 返回", callback_data=f"review_movie_detail_{item_id}")]
            ]
        )
    )
    await cb.answer()


@movie_review_router.callback_query(F.data.startswith("reject_movie_note_media_"))
async def cb_reject_movie_note_media(cb: types.CallbackQuery, state: FSMContext):
    """从媒体消息拒绝求片并留言"""
    item_id = int(cb.data.split("_")[-1])
    await state.set_state(Wait.waitReviewNote)
    await state.update_data(action="reject", item_id=item_id, item_type="movie")
    
    await cb.message.edit_caption(
        caption="❌ <b>拒绝求片并留言</b>\n\n请输入拒绝原因：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 返回", callback_data=f"review_movie_detail_{item_id}")]
            ]
        )
    )
    await cb.answer()


@movie_review_router.callback_query(F.data == "admin_review_movie_cleanup")
async def cb_admin_review_movie_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """清理并返回求片审核列表"""
    await movie_review_handler.handle_cleanup(cb, state)


@movie_review_router.callback_query(F.data == "back_to_main_cleanup")
async def cb_back_to_main_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """清理并返回主菜单"""
    await movie_review_handler.handle_back_to_main_cleanup(cb, state)


@movie_review_router.callback_query(F.data.startswith("delete_media_message_"))
async def cb_delete_media_message(cb: types.CallbackQuery, state: FSMContext):
    """删除媒体消息"""
    item_id = int(cb.data.split("_")[-1])
    await movie_review_handler.handle_delete_media_message(cb, state, item_id)