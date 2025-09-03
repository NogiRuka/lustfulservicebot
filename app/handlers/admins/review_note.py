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
    
    # 兼容新旧数据格式
    action = data.get('action') or data.get('review_action')
    item_id = data.get('item_id') or data.get('review_id')
    item_type = data.get('item_type') or data.get('review_type')
    message_id = data.get('message_id')
    
    # 留言现在可以为空，不需要检查
    
    # 在面板回显管理员输入的内容
    action_text = "通过" if action == "approve" or action == "approved" else "拒绝"
    type_text = "求片" if item_type == "movie" else "投稿"
    
    if review_note.strip():
        echo_text = (
            f"💬 <b>审核留言</b>\n\n"
            f"🎯 操作：{action_text}{type_text} #{item_id}\n"
            f"📝 留言：{review_note}\n\n"
            f"请确认以上信息是否正确？"
        )
    else:
        echo_text = (
            f"💬 <b>审核留言</b>\n\n"
            f"🎯 操作：{action_text}{type_text} #{item_id}\n"
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
                types.InlineKeyboardButton(text="❌ 取消审核", callback_data=f"admin_review_{item_type}" if item_type == "movie" else "admin_review_content")
            ]
        ]
    )
    
    # 保存留言到状态
    await state.update_data(review_note=review_note)
    
    # 在面板回显
    try:
        # 如果没有message_id，尝试使用当前消息的reply_to_message
        if not message_id and msg.reply_to_message:
            message_id = msg.reply_to_message.message_id
        
        if message_id:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption=echo_text,
                reply_markup=confirm_kb
            )
        else:
            # 如果没有message_id，发送新消息
            await msg.answer_photo(
                photo=DEFAULT_WELCOME_PHOTO,
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
    
    # 兼容新旧数据格式
    action = data.get('action') or data.get('review_action')
    item_id = data.get('item_id') or data.get('review_id')
    item_type = data.get('item_type') or data.get('review_type')
    
    # 转换action格式
    if action == 'approve':
        review_action = 'approved'
    elif action == 'reject':
        review_action = 'rejected'
    else:
        review_action = action  # 兼容旧格式
    
    # 先获取项目信息用于通知
    item = None
    if item_type == 'movie':
        requests = await get_pending_movie_requests()
        item = next((r for r in requests if r.id == item_id), None)
        success = await review_movie_request(item_id, cb.from_user.id, review_action, None)
        type_text = "求片"
    elif item_type == 'content':
        submissions = await get_pending_content_submissions()
        item = next((s for s in submissions if s.id == item_id), None)
        success = await review_content_submission(item_id, cb.from_user.id, review_action, None)
        type_text = "投稿"
    else:
        await cb.answer("❌ 审核类型错误", show_alert=True)
        await state.clear()
        return
    
    if success:
        action_text = "通过" if review_action == "approved" else "拒绝"
        
        # 发送通知给用户
        if item:
            # 通过category_id获取分类名称
            from app.database.business import get_movie_category_by_id
            category = await get_movie_category_by_id(item.category_id) if item.category_id else None
            category_name = category.name if category else None
            
            if item_type == 'movie':
                await send_review_notification(
                    cb.bot, item.user_id, item_type, item.title, review_action,
                    file_id=item.file_id, item_content=item.description, item_id=item.id,
                    category_name=category_name
                )
            elif item_type == 'content':
                await send_review_notification(
                    cb.bot, item.user_id, item_type, item.title, review_action,
                    file_id=item.file_id, item_content=item.content, item_id=item.id,
                    category_name=category_name
                )
        
        # 检查是否为媒体消息
        is_media_message = data.get('is_media_message', False)
        
        if is_media_message:
            # 媒体消息审核完成：alert提示 + 删除媒体消息 + 刷新主面板
            await cb.answer(f"✅ 已{action_text}{type_text} {item_id}（无留言）", show_alert=True)
            
            # 删除所有已发送的媒体消息
            from app.utils.panel_utils import cleanup_sent_media_messages
            await cleanup_sent_media_messages(cb.bot, state)
            
            # 刷新原来的主面板并发送新的媒体消息
            # 检查是否来自数据浏览页面（review_center）
            from_review_center = data.get('from_review_center', False)
            
            if from_review_center:
                 # 如果来自数据浏览页面，编辑主消息返回审核中心
                 movie_requests = await get_pending_movie_requests()
                 content_submissions = await get_pending_content_submissions()
                 
                 text = "✅ <b>审核中心</b>\n\n"
                 text += f"🎬 待审核求片：{len(movie_requests)} 条\n"
                 text += f"📝 待审核投稿：{len(content_submissions)} 条\n\n"
                 text += "请选择要审核的类型："
                 
                 from app.buttons.users import admin_review_center_kb
                 await cb.message.edit_caption(
                     caption=text,
                     reply_markup=admin_review_center_kb
                 )
                 
                 # 重新发送当前页面的媒体消息
                 if item_type == 'movie':
                     from app.handlers.admins.review_center import _send_media_messages_for_movies
                     from app.database.business import get_all_movie_requests
                     all_requests = await get_all_movie_requests()
                     # 获取当前页面的数据（这里简化为前5条）
                     current_page_data = all_requests[:5] if all_requests else []
                     await _send_media_messages_for_movies(cb, state, current_page_data)
                 elif item_type == 'content':
                     from app.handlers.admins.review_center import _send_media_messages_for_content
                     from app.database.business import get_all_content_submissions
                     all_submissions = await get_all_content_submissions()
                     # 获取当前页面的数据（这里简化为前5条）
                     current_page_data = all_submissions[:5] if all_submissions else []
                     await _send_media_messages_for_content(cb, state, current_page_data)
            else:
                # 否则返回具体的审核列表
                if item_type == 'movie':
                    from app.handlers.admins.movie_review_new import movie_review_handler
                    await movie_review_handler.handle_review_list(cb, state)
                elif item_type == 'content':
                    from app.handlers.admins.content_review_new import content_review_handler
                    await content_review_handler.handle_review_list(cb, state)
        else:
            # 普通消息显示结果页面
            result_text = f"✅ <b>审核完成！</b>\n\n🎯 操作：{action_text}{type_text} #{item_id}\n💬 留言：无\n\n审核结果已保存。"
            
            result_kb = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="🔄 返回审核", callback_data=f"admin_review_{item_type}" if item_type == "movie" else "admin_review_content"),
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
    
    # 兼容新旧数据格式
    action = data.get('action') or data.get('review_action')
    item_id = data.get('item_id') or data.get('review_id')
    item_type = data.get('item_type') or data.get('review_type')
    review_note = data.get('review_note')
    
    # 转换action格式
    if action == 'approve':
        review_action = 'approved'
    elif action == 'reject':
        review_action = 'rejected'
    else:
        review_action = action  # 兼容旧格式
    
    # 先获取项目信息用于通知
    item = None
    if item_type == 'movie':
        requests = await get_pending_movie_requests()
        item = next((r for r in requests if r.id == item_id), None)
        success = await review_movie_request(item_id, cb.from_user.id, review_action, review_note)
        type_text = "求片"
    elif item_type == 'content':
        submissions = await get_pending_content_submissions()
        item = next((s for s in submissions if s.id == item_id), None)
        success = await review_content_submission(item_id, cb.from_user.id, review_action, review_note)
        type_text = "投稿"
    else:
        await cb.answer("❌ 审核类型错误", show_alert=True)
        await state.clear()
        return
    
    if success:
        action_text = "通过" if review_action == "approved" else "拒绝"
        
        # 发送通知给用户（包含留言）
        if item:
            # 通过category_id获取分类名称
            from app.database.business import get_movie_category_by_id
            category = await get_movie_category_by_id(item.category_id) if item.category_id else None
            category_name = category.name if category else None
            
            if item_type == 'movie':
                await send_review_notification(
                    cb.bot, item.user_id, item_type, item.title, review_action, review_note,
                    file_id=item.file_id, item_content=item.description, item_id=item.id,
                    category_name=category_name
                )
            elif item_type == 'content':
                await send_review_notification(
                    cb.bot, item.user_id, item_type, item.title, review_action, review_note,
                    file_id=item.file_id, item_content=item.content, item_id=item.id,
                    category_name=category_name
                )
        
        # 检查是否为媒体消息
        is_media_message = data.get('is_media_message', False)
        
        if is_media_message:
            # 媒体消息审核完成：alert提示 + 删除媒体消息 + 刷新主面板
            note_preview = review_note[:30] + ('...' if len(review_note) > 30 else '') if review_note else "无留言"
            await cb.answer(f"✅ 已{action_text}{type_text} {item_id}（{note_preview}）", show_alert=True)
            
            # 删除所有已发送的媒体消息
            from app.utils.panel_utils import cleanup_sent_media_messages
            await cleanup_sent_media_messages(cb.bot, state)
            
            # 刷新原来的主面板并发送新的媒体消息
            # 检查是否来自数据浏览页面（review_center）
            from_review_center = data.get('from_review_center', False)
            
            if from_review_center:
                # 如果来自数据浏览页面，编辑主消息返回审核中心
                movie_requests = await get_pending_movie_requests()
                content_submissions = await get_pending_content_submissions()
                
                text = "✅ <b>审核中心</b>\n\n"
                text += f"🎬 待审核求片：{len(movie_requests)} 条\n"
                text += f"📝 待审核投稿：{len(content_submissions)} 条\n\n"
                text += "请选择要审核的类型："
                
                from app.buttons.users import admin_review_center_kb
                await cb.message.edit_caption(
                    caption=text,
                    reply_markup=admin_review_center_kb
                )
                
                # 重新发送当前页面的媒体消息
                if item_type == 'movie':
                    from app.handlers.admins.review_center import _send_media_messages_for_movies
                    from app.database.business import get_all_movie_requests
                    all_requests = await get_all_movie_requests()
                    # 获取当前页面的数据（这里简化为前5条）
                    current_page_data = all_requests[:5] if all_requests else []
                    await _send_media_messages_for_movies(cb, state, current_page_data)
                elif item_type == 'content':
                    from app.handlers.admins.review_center import _send_media_messages_for_content
                    from app.database.business import get_all_content_submissions
                    all_submissions = await get_all_content_submissions()
                    # 获取当前页面的数据（这里简化为前5条）
                    current_page_data = all_submissions[:5] if all_submissions else []
                    await _send_media_messages_for_content(cb, state, current_page_data)
            else:
                # 否则返回具体的审核列表
                if item_type == 'movie':
                    from app.handlers.admins.movie_review_new import movie_review_handler
                    await movie_review_handler.handle_review_list(cb, state)
                elif item_type == 'content':
                    from app.handlers.admins.content_review_new import content_review_handler
                    await content_review_handler.handle_review_list(cb, state)
        else:
            # 检查是否为单独发送的媒体消息
            is_standalone_media = hasattr(cb.message, 'photo') or hasattr(cb.message, 'video') or hasattr(cb.message, 'document')
            
            if is_standalone_media:
                # 单独的媒体消息：alert提示 + 删除消息 + 刷新主消息
                note_preview = review_note[:30] + ('...' if len(review_note) > 30 else '') if review_note else "无留言"
                await cb.answer(f"✅ 已{action_text}{type_text} {item_id}（{note_preview}）", show_alert=True)
                
                # 删除当前媒体消息
                try:
                    await cb.message.delete()
                except Exception as e:
                    logger.warning(f"删除媒体消息失败: {e}")
                
                # 从状态中移除已删除的媒体消息ID
                data = await state.get_data()
                sent_media_ids = data.get('sent_media_ids', [])
                if cb.message.message_id in sent_media_ids:
                    sent_media_ids.remove(cb.message.message_id)
                    await state.update_data(sent_media_ids=sent_media_ids)
                
                # 检测并同步主消息的媒体消息状态
                from_review_center = data.get('from_review_center', False)
                if from_review_center:
                    # 重新发送当前页面的媒体消息（排除已审核的）
                    if item_type == 'movie':
                        from app.handlers.admins.review_center import _send_media_messages_for_movies
                        from app.database.business import get_all_movie_requests
                        all_requests = await get_all_movie_requests()
                        # 获取当前页面的数据，排除已审核的项目
                        current_page_data = [r for r in all_requests[:5] if r.id != item_id] if all_requests else []
                        await _send_media_messages_for_movies(cb, state, current_page_data)
                    elif item_type == 'content':
                        from app.handlers.admins.review_center import _send_media_messages_for_content
                        from app.database.business import get_all_content_submissions
                        all_submissions = await get_all_content_submissions()
                        # 获取当前页面的数据，排除已审核的项目
                        current_page_data = [s for s in all_submissions[:5] if s.id != item_id] if all_submissions else []
                        await _send_media_messages_for_content(cb, state, current_page_data)
            else:
                # 主消息显示结果页面
                result_text = f"✅ <b>审核完成！</b>\n\n🎯 操作：{action_text}{type_text} #{item_id}\n💬 留言：{review_note}\n\n审核结果已保存，用户将看到您的留言。"
                
                result_kb = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="🔄 返回审核", callback_data=f"admin_review_{item_type}" if item_type == "movie" else "admin_review_content"),
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
    
    # 兼容新旧数据格式
    action = data.get('action') or data.get('review_action')
    item_id = data.get('item_id') or data.get('review_id')
    item_type = data.get('item_type') or data.get('review_type')
    
    action_text = "通过" if action == "approve" or action == "approved" else "拒绝"
    type_text = "求片" if item_type == "movie" else "投稿"
    
    # 返回输入状态
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请重新输入{action_text}{type_text} #{item_id} 的留言（可选）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="⏭️ 跳过留言", callback_data="skip_review_note"),
                    types.InlineKeyboardButton(text="❌ 取消", callback_data=f"admin_review_{item_type}" if item_type == "movie" else "admin_review_content")
                ]
            ]
        )
    )
    await cb.answer()