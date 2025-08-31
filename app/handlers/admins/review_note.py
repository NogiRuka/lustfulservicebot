from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import review_movie_request, review_content_submission

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
        caption=f"💬 <b>审核留言</b>\n\n请输入通过求片 #{request_id} 的留言：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_movie")]
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
        caption=f"💬 <b>审核留言</b>\n\n请输入拒绝求片 #{request_id} 的留言：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_movie")]
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
        caption=f"💬 <b>审核留言</b>\n\n请输入通过投稿 #{submission_id} 的留言：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_content")]
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
        caption=f"💬 <b>审核留言</b>\n\n请输入拒绝投稿 #{submission_id} 的留言：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_content")]
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
    
    if not review_note:
        await msg.reply("留言内容不能为空，请重新输入：")
        return
    
    # 删除用户输入的消息
    try:
        await msg.delete()
    except:
        pass
    
    # 保存留言到状态
    await state.update_data(review_note=review_note)
    
    # 显示确认页面
    action_text = "通过" if review_action == "approved" else "拒绝"
    item_type = "求片" if review_type == "movie" else "投稿"
    
    note_preview = review_note[:100] + ('...' if len(review_note) > 100 else '')
    confirm_text = (
        f"📋 <b>确认审核留言</b>\n\n"
        f"🎯 操作：{action_text}{item_type} #{review_id}\n"
        f"💬 留言：{note_preview}\n\n"
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
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=confirm_text,
            reply_markup=confirm_kb
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
        # 如果编辑失败，发送新消息
        await msg.answer_photo(
            photo="https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true",
            caption=confirm_text,
            reply_markup=confirm_kb
        )


@review_note_router.callback_query(F.data == "confirm_review_note")
async def cb_confirm_review_note(cb: types.CallbackQuery, state: FSMContext):
    """确认提交审核留言"""
    data = await state.get_data()
    
    review_type = data.get('review_type')
    review_id = data.get('review_id')
    review_action = data.get('review_action')
    review_note = data.get('review_note')
    
    if review_type == 'movie':
        success = await review_movie_request(review_id, cb.from_user.id, review_action, review_note)
        item_type = "求片"
    elif review_type == 'content':
        success = await review_content_submission(review_id, cb.from_user.id, review_action, review_note)
        item_type = "投稿"
    else:
        await cb.answer("❌ 审核类型错误", show_alert=True)
        await state.clear()
        return
    
    if success:
        action_text = "通过" if review_action == "approved" else "拒绝"
        result_text = f"✅ <b>审核完成！</b>\n\n🎯 操作：{action_text}{item_type} #{review_id}\n💬 留言：{review_note}\n\n审核结果已保存，用户将看到您的留言。"
        
        # 显示结果页面
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
        caption=f"💬 <b>审核留言</b>\n\n请重新输入{action_text}{item_type} #{review_id} 的留言：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ 取消", callback_data=f"admin_review_{review_type}" if review_type == "movie" else "admin_review_content")]
            ]
        )
    )
    await cb.answer()