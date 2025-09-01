from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import review_movie_request, review_content_submission, get_pending_movie_requests, get_pending_content_submissions
from app.utils.panel_utils import send_review_notification, DEFAULT_WELCOME_PHOTO

review_note_router = Router()


# ==================== 审核留言功能 ====================

@review_note_router.callback_query(F.data.startswith("approve_movie_note_"))
async def cb_approve_movie_note(cb: types.CallbackQuery, state: FSMContext):
    """留言通过求片"""
    request_id = int(cb.data.split("_")[-1])

    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'movie',
        'review_id': request_id,
        'review_action': 'approved',
        'message_id': cb.message.message_id
    })
    
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请输入通过求片 #{request_id} 的留言（可选）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⏭️ 跳过留言", callback_data="skip_review_note"),
                    types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_movie")
                ]
            ]
        )
    )
    await cb.answer()


@review_note_router.callback_query(F.data.startswith("reject_movie_note_"))
async def cb_reject_movie_note(cb: types.CallbackQuery, state: FSMContext):
    """留言拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'movie',
        'review_id': request_id,
        'review_action': 'rejected',
        'message_id': cb.message.message_id
    })
    
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请输入拒绝求片 #{request_id} 的留言（可选）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⏭️ 跳过留言", callback_data="skip_review_note"),
                    types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_movie")
                ]
            ]
        )
    )
    await cb.answer()


@review_note_router.callback_query(F.data.startswith("approve_content_note_"))
async def cb_approve_content_note(cb: types.CallbackQuery, state: FSMContext):
    """留言通过投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'content',
        'review_id': submission_id,
        'review_action': 'approved',
        'message_id': cb.message.message_id
    })
    
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请输入通过投稿 #{submission_id} 的留言（可选）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⏭️ 跳过留言", callback_data="skip_review_note"),
                    types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_content")
                ]
            ]
        )
    )
    await cb.answer()


@review_note_router.callback_query(F.data.startswith("reject_content_note_"))
async def cb_reject_content_note(cb: types.CallbackQuery, state: FSMContext):
    """留言拒绝投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'content',
        'review_id': submission_id,
        'review_action': 'rejected',
        'message_id': cb.message.message_id
    })
    
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请输入拒绝投稿 #{submission_id} 的留言（可选）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⏭️ 跳过留言", callback_data="skip_review_note"),
                    types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_content")
                ]
            ]
        )
    )
    await cb.answer()


@review_note_router.message(StateFilter(Wait.waitReviewNote))
async def process_review_note(msg: types.Message, state: FSMContext):
    """处理审核留言"""
    review_note = msg.text.strip()
    data = await state.get_data()
    
    review_type = data.get('review_type')
    review_id = data.get('review_id')
    review_action = data.get('review_action')
    message_id = data.get('message_id')
    
    # 留言现在可以为空，不需要检查
    
    # 在面板回显管理员输入的内容
    action_text = "通过" if review_action == "approved" else "拒绝"
    item_type = "求片" if review_type == "movie" else "投稿"
    
    if review_note.strip():
        echo_text = (
            f"💬 <b>审核留言</b>\n\n"
            f"🎯 操作：{action_text}{item_type} #{review_id}\n"
            f"📝 留言：{review_note}\n\n"
            f"请确认以上信息是否正确？"
        )
    else:
        echo_text = (
            f"💬 <b>审核留言</b>\n\n"
            f"🎯 操作：{action_text}{item_type} #{review_id}\n"
            f"📝 留言：（空留言）\n\n"
            f"请确认以上信息是否正确？"
        )
    
    confirm_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ 确认提交", callback_data="confirm_review_note"),
                types.InlineKeyboardButton(text="✏️ 重新编辑", callback_data="edit_review_note")
            ],
            [
                types.InlineKeyboardButton(text="❌ 取消审核", callback_data=f"admin_review_{review_type}" if review_type == "movie" else "admin_review_content")
            ]
        ]
    )
    
    # 保存留言到状态
    await state.update_data(review_note=review_note)
    
    # 在面板回显
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=echo_text,
            reply_markup=confirm_kb
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
        # 如果编辑失败，发送新消息
        await msg.answer_photo(
            photo=DEFAULT_WELCOME_PHOTO,
            caption=echo_text,
            reply_markup=confirm_kb
        )
    
    # 删除管理员输入的消息
    try:
        await msg.delete()
    except:
        pass


@review_note_router.callback_query(F.data == "skip_review_note")
async def cb_skip_review_note(cb: types.CallbackQuery, state: FSMContext):
    """跳过留言直接审核"""
    data = await state.get_data()
    
    review_type = data.get('review_type')
    review_id = data.get('review_id')
    review_action = data.get('review_action')
    
    # 先获取项目信息用于通知
    item = None
    if review_type == 'movie':
        requests = await get_pending_movie_requests()
        item = next((r for r in requests if r.id == review_id), None)
        success = await review_movie_request(review_id, cb.from_user.id, review_action, None)
        item_type = "求片"
    elif review_type == 'content':
        submissions = await get_pending_content_submissions()
        item = next((s for s in submissions if s.id == review_id), None)
        success = await review_content_submission(review_id, cb.from_user.id, review_action, None)
        item_type = "投稿"
    else:
        await cb.answer("❌ 审核类型错误", show_alert=True)
        await state.clear()
        return
    
    if success:
        action_text = "通过" if review_action == "approved" else "拒绝"
        
        # 发送通知给用户
        if item:
            category_name = item.category.name if item.category else None
            if review_type == 'movie':
                await send_review_notification(
                    cb.bot, item.user_id, review_type, item.title, review_action,
                    file_id=item.file_id, item_content=item.description, item_id=item.id,
                    category_name=category_name
                )
            elif review_type == 'content':
                await send_review_notification(
                    cb.bot, item.user_id, review_type, item.title, review_action,
                    file_id=item.file_id, item_content=item.content, item_id=item.id,
                    category_name=category_name
                )
        
        # 检查是否为媒体消息
        is_media_message = data.get('is_media_message', False)
        
        if is_media_message:
            # 媒体消息直接删除
            await cb.answer(f"✅ 已{action_text}{item_type} {review_id}（无留言）", show_alert=True)
            try:
                await cb.message.delete()
            except Exception as e:
                logger.warning(f"删除媒体消息失败: {e}")
        else:
            # 普通消息显示结果页面
            result_text = f"✅ <b>审核完成！</b>\n\n🎯 操作：{action_text}{item_type} #{review_id}\n💬 留言：无\n\n审核结果已保存。"
            
            result_kb = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="🔄 返回审核", callback_data=f"admin_review_{review_type}" if review_type == "movie" else "admin_review_content"),
                        types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                    ]
                ]
            )
            
            await cb.message.edit_caption(
                caption=result_text,
                reply_markup=result_kb
            )
    else:
        await cb.answer("❌ 审核失败，请重试", show_alert=True)
    
    await state.clear()
    await cb.answer()


@review_note_router.callback_query(F.data == "confirm_review_note")
async def cb_confirm_review_note(cb: types.CallbackQuery, state: FSMContext):
    """确认提交审核留言"""
    data = await state.get_data()
    
    review_type = data.get('review_type')
    review_id = data.get('review_id')
    review_action = data.get('review_action')
    review_note = data.get('review_note')
    
    # 先获取项目信息用于通知
    item = None
    if review_type == 'movie':
        requests = await get_pending_movie_requests()
        item = next((r for r in requests if r.id == review_id), None)
        success = await review_movie_request(review_id, cb.from_user.id, review_action, review_note)
        item_type = "求片"
    elif review_type == 'content':
        submissions = await get_pending_content_submissions()
        item = next((s for s in submissions if s.id == review_id), None)
        success = await review_content_submission(review_id, cb.from_user.id, review_action, review_note)
        item_type = "投稿"
    else:
        await cb.answer("❌ 审核类型错误", show_alert=True)
        await state.clear()
        return
    
    if success:
        action_text = "通过" if review_action == "approved" else "拒绝"
        
        # 发送通知给用户（包含留言）
        if item:
            category_name = item.category.name if item.category else None
            if review_type == 'movie':
                await send_review_notification(
                    cb.bot, item.user_id, review_type, item.title, review_action, review_note,
                    file_id=item.file_id, item_content=item.description, item_id=item.id,
                    category_name=category_name
                )
            elif review_type == 'content':
                await send_review_notification(
                    cb.bot, item.user_id, review_type, item.title, review_action, review_note,
                    file_id=item.file_id, item_content=item.content, item_id=item.id,
                    category_name=category_name
                )
        
        # 检查是否为媒体消息
        is_media_message = data.get('is_media_message', False)
        
        if is_media_message:
            # 媒体消息直接删除
            note_preview = review_note[:30] + ('...' if len(review_note) > 30 else '') if review_note else "无留言"
            await cb.answer(f"✅ 已{action_text}{item_type} {review_id}（{note_preview}）", show_alert=True)
            try:
                await cb.message.delete()
            except Exception as e:
                logger.warning(f"删除媒体消息失败: {e}")
        else:
            # 普通消息显示结果页面
            result_text = f"✅ <b>审核完成！</b>\n\n🎯 操作：{action_text}{item_type} #{review_id}\n💬 留言：{review_note}\n\n审核结果已保存，用户将看到您的留言。"
            
            result_kb = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="🔄 返回审核", callback_data=f"admin_review_{review_type}" if review_type == "movie" else "admin_review_content"),
                        types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                    ]
                ]
            )
            
            await cb.message.edit_caption(
                caption=result_text,
                reply_markup=result_kb
            )
    else:
        await cb.answer("❌ 审核失败，请重试", show_alert=True)
    
    await state.clear()
    await cb.answer()


@review_note_router.callback_query(F.data == "edit_review_note")
async def cb_edit_review_note(cb: types.CallbackQuery, state: FSMContext):
    """重新编辑审核留言"""
    data = await state.get_data()
    
    review_type = data.get('review_type')
    review_id = data.get('review_id')
    review_action = data.get('review_action')
    
    action_text = "通过" if review_action == "approved" else "拒绝"
    item_type = "求片" if review_type == "movie" else "投稿"
    
    # 返回输入状态
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请重新输入{action_text}{item_type} #{review_id} 的留言（可选）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⏭️ 跳过留言", callback_data="skip_review_note"),
                    types.InlineKeyboardButton(text="❌ 取消", callback_data=f"admin_review_{review_type}" if review_type == "movie" else "admin_review_content")
                ]
            ]
        )
    )
    await cb.answer()