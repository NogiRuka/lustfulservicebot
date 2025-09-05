from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import review_movie_request, review_content_submission, get_pending_movie_requests, get_pending_content_submissions
from app.utils.panel_utils import send_review_notification, DEFAULT_WELCOME_PHOTO
from app.utils.debug_utils import (
    debug_log, debug_message_info, debug_state_info, debug_main_message_tracking,
    debug_review_flow, debug_error, debug_function
)

review_note_router = Router()


# ==================== 审核留言功能 ====================

@review_note_router.callback_query(F.data.startswith("approve_movie_note_"))
@debug_function("审核留言-通过求片")
async def cb_approve_movie_note(cb: types.CallbackQuery, state: FSMContext):
    """留言通过求片"""
    request_id = int(cb.data.split("_")[-1])
    
    debug_review_flow("开始处理求片通过留言", request_id=request_id)
    debug_message_info(cb, "当前回调消息")
    await debug_state_info(state, "进入前")

    # 保存审核信息到状态，保持原有的主消息ID
    data = await state.get_data()
    old_main_id = data.get('main_message_id')
    current_message_id = cb.message.message_id
    main_message_id = old_main_id or current_message_id
    
    debug_main_message_tracking(
        "设置主消息ID",
        old_id=old_main_id,
        new_id=main_message_id,
        current_msg_id=current_message_id,
        source="保存的ID" if old_main_id else "当前消息ID"
    )
    
    await state.update_data({
        'review_type': 'movie',
        'review_id': request_id,
        'review_action': 'approved',
        'message_id': main_message_id,  # 使用主消息ID而不是当前消息ID
        'main_message_id': main_message_id  # 确保主消息ID被保存
    })
    
    await debug_state_info(state, "状态更新后")
    debug_review_flow("准备编辑消息显示留言输入界面", target_message_id=main_message_id)
    
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请输入通过求片 #{request_id} 的留言（必填）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_movie")
                ]
            ]
        )
    )
    await cb.answer()


@review_note_router.callback_query(F.data.startswith("reject_movie_note_"))
@debug_function("审核留言-拒绝求片")
async def cb_reject_movie_note(cb: types.CallbackQuery, state: FSMContext):
    """留言拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    debug_review_flow("开始处理求片拒绝留言", request_id=request_id)
    debug_message_info(cb, "当前回调消息")
    await debug_state_info(state, "进入前")
    
    # 保存审核信息到状态，保持原有的主消息ID
    data = await state.get_data()
    old_main_id = data.get('main_message_id')
    current_message_id = cb.message.message_id
    main_message_id = old_main_id or current_message_id
    
    debug_main_message_tracking(
        "设置主消息ID",
        old_id=old_main_id,
        new_id=main_message_id,
        current_msg_id=current_message_id,
        source="保存的ID" if old_main_id else "当前消息ID"
    )
    
    await state.update_data({
        'review_type': 'movie',
        'review_id': request_id,
        'review_action': 'rejected',
        'message_id': main_message_id,  # 使用主消息ID而不是当前消息ID
        'main_message_id': main_message_id  # 确保主消息ID被保存
    })
    
    await debug_state_info(state, "状态更新后")
    debug_review_flow("准备编辑消息显示留言输入界面", target_message_id=main_message_id)
    
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请输入拒绝求片 #{request_id} 的留言（必填）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_movie")
                ]
            ]
        )
    )
    await cb.answer()


@review_note_router.callback_query(F.data.startswith("approve_content_note_"))
@debug_function("审核留言-通过投稿")
async def cb_approve_content_note(cb: types.CallbackQuery, state: FSMContext):
    """留言通过投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    debug_review_flow("开始处理投稿通过留言", submission_id=submission_id)
    debug_message_info(cb, "当前回调消息")
    await debug_state_info(state, "进入前")
    
    # 保存审核信息到状态，保持原有的主消息ID
    data = await state.get_data()
    old_main_id = data.get('main_message_id')
    current_message_id = cb.message.message_id
    main_message_id = old_main_id or current_message_id
    
    debug_main_message_tracking(
        "设置主消息ID",
        old_id=old_main_id,
        new_id=main_message_id,
        current_msg_id=current_message_id,
        source="保存的ID" if old_main_id else "当前消息ID"
    )
    
    await state.update_data({
        'review_type': 'content',
        'review_id': submission_id,
        'review_action': 'approved',
        'message_id': main_message_id,  # 使用主消息ID而不是当前消息ID
        'main_message_id': main_message_id  # 确保主消息ID被保存
    })
    
    await debug_state_info(state, "状态更新后")
    debug_review_flow("准备编辑消息显示留言输入界面", target_message_id=main_message_id)
    
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请输入通过投稿 #{submission_id} 的留言（必填）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_content")
                ]
            ]
        )
    )
    await cb.answer()


@review_note_router.callback_query(F.data.startswith("reject_content_note_"))
@debug_function("审核留言-拒绝投稿")
async def cb_reject_content_note(cb: types.CallbackQuery, state: FSMContext):
    """留言拒绝投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    debug_review_flow("开始处理投稿拒绝留言", submission_id=submission_id)
    debug_message_info(cb, "当前回调消息")
    await debug_state_info(state, "进入前")
    
    # 保存审核信息到状态，保持原有的主消息ID
    data = await state.get_data()
    old_main_id = data.get('main_message_id')
    current_message_id = cb.message.message_id
    main_message_id = old_main_id or current_message_id
    
    debug_main_message_tracking(
        "设置主消息ID",
        old_id=old_main_id,
        new_id=main_message_id,
        current_msg_id=current_message_id,
        source="保存的ID" if old_main_id else "当前消息ID"
    )
    
    await state.update_data({
        'review_type': 'content',
        'review_id': submission_id,
        'review_action': 'rejected',
        'message_id': main_message_id,  # 使用主消息ID而不是当前消息ID
        'main_message_id': main_message_id  # 确保主消息ID被保存
    })
    
    await debug_state_info(state, "状态更新后")
    debug_review_flow("准备编辑消息显示留言输入界面", target_message_id=main_message_id)
    
    await state.set_state(Wait.waitReviewNote)
    await cb.message.edit_caption(
        caption=f"💬 <b>审核留言</b>\n\n请输入拒绝投稿 #{submission_id} 的留言（必填）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="❌ 取消", callback_data="admin_review_content")
                ]
            ]
        )
    )
    await cb.answer()


@review_note_router.message(StateFilter(Wait.waitReviewNote))
@debug_function("处理审核留言输入")
async def process_review_note(msg: types.Message, state: FSMContext):
    """处理审核留言"""
    review_note = msg.text.strip()
    
    debug_review_flow("开始处理用户输入的审核留言", note_length=len(review_note))
    debug_log("用户输入消息信息", user_id=msg.from_user.id, message_id=msg.message_id)
    await debug_state_info(state, "获取状态数据")
    
    data = await state.get_data()
    
    # 兼容新旧数据格式
    action = data.get('action') or data.get('review_action')
    item_id = data.get('item_id') or data.get('review_id')
    item_type = data.get('item_type') or data.get('review_type')
    message_id = data.get('message_id')
    main_message_id = data.get('main_message_id')
    
    debug_review_flow(
        "解析状态数据",
        action=action,
        item_id=item_id,
        item_type=item_type,
        message_id=message_id,
        main_message_id=main_message_id
    )
    
    # 检查留言是否为空（现在留言是必填的）
    if not review_note.strip():
        # 留言为空，提示用户重新输入
        action_text = "通过" if action == "approve" or action == "approved" else "拒绝"
        type_text = "求片" if item_type == "movie" else "投稿"
        
        error_text = (
            f"💬 <b>审核留言</b>\n\n"
            f"❌ 留言不能为空！\n\n"
            f"请重新输入{action_text}{type_text} #{item_id} 的留言："
        )
        
        cancel_callback = "admin_review_movie" if item_type == "movie" else "admin_review_content"
        error_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="❌ 取消", callback_data=cancel_callback)
                ]
            ]
        )
        
        # 编辑原消息显示错误提示
        try:
            if message_id:
                await msg.bot.edit_message_caption(
                    chat_id=msg.from_user.id,
                    message_id=message_id,
                    caption=error_text,
                    reply_markup=error_kb
                )
            else:
                await msg.answer_photo(
                    photo=DEFAULT_WELCOME_PHOTO,
                    caption=error_text,
                    reply_markup=error_kb
                )
        except Exception as e:
            logger.error(f"编辑错误消息失败: {e}")
            await msg.answer_photo(
                photo=DEFAULT_WELCOME_PHOTO,
                caption=error_text,
                reply_markup=error_kb
            )
        
        # 删除用户输入的空消息
        try:
            await msg.delete()
        except:
            pass
        return
    
    # 在面板回显管理员输入的内容
    action_text = "通过" if action == "approve" or action == "approved" else "拒绝"
    type_text = "求片" if item_type == "movie" else "投稿"
    
    echo_text = (
        f"💬 <b>审核留言</b>\n\n"
        f"🎯 操作：{action_text}{type_text} #{item_id}\n"
        f"📝 留言：{review_note}\n\n"
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


# skip_review_note 函数已删除，因为留言审核现在是必填的


async def _update_review_center_panel(cb: types.CallbackQuery, movie_requests, content_submissions):
    """更新审核中心主面板数据"""
    text = "✅ <b>审核中心</b>\n\n"
    text += f"🎬 待审核求片：{len(movie_requests)} 条\n"
    text += f"📝 待审核投稿：{len(content_submissions)} 条\n\n"
    text += "请选择要审核的类型："
    
    from app.buttons.users import admin_review_center_kb
    
    # 智能查找并更新主面板消息
    current_message_id = cb.message.message_id
    for offset in range(1, 10):
        try:
            potential_main_id = current_message_id - offset
            await cb.bot.edit_message_caption(
                chat_id=cb.message.chat.id,
                message_id=potential_main_id,
                caption=text,
                reply_markup=admin_review_center_kb
            )
            logger.info(f"成功更新审核中心主面板消息 ID: {potential_main_id}")
            return True
        except Exception as e:
            continue
    
    logger.warning("无法找到审核中心主面板消息进行更新")
    return False


async def _send_current_page_media(cb: types.CallbackQuery, state: FSMContext, item_type: str, movie_requests, content_submissions):
    """发送当前页的媒体消息"""
    if item_type == 'movie':
        from app.handlers.admins.review_center import _send_media_messages_for_movies
        current_page_data = movie_requests[:5] if movie_requests else []
        await _send_media_messages_for_movies(cb, state, current_page_data)
    elif item_type == 'content':
        from app.handlers.admins.review_center import _send_media_messages_for_content
        current_page_data = content_submissions[:5] if content_submissions else []
        await _send_media_messages_for_content(cb, state, current_page_data)


async def _return_to_review_list(cb: types.CallbackQuery, state: FSMContext, item_type: str):
    """返回具体的审核列表"""
    if item_type == 'movie':
        from app.handlers.admins.movie_review import movie_review_handler
        await movie_review_handler.handle_review_list(cb, state)
    elif item_type == 'content':
        from app.handlers.admins.content_review import content_review_handler
        await content_review_handler.handle_review_list(cb, state)


@review_note_router.callback_query(F.data == "confirm_review_note")
@debug_function("确认提交审核留言")
async def cb_confirm_review_note(cb: types.CallbackQuery, state: FSMContext):
    """确认提交审核留言"""
    debug_review_flow("开始确认提交审核留言")
    debug_message_info(cb, "确认按钮回调")
    await debug_state_info(state, "获取确认前状态")
    
    data = await state.get_data()
    
    # 兼容新旧数据格式
    action = data.get('action') or data.get('review_action')
    item_id = data.get('item_id') or data.get('review_id')
    item_type = data.get('item_type') or data.get('review_type')
    review_note = data.get('review_note')
    main_message_id = data.get('main_message_id')
    
    debug_review_flow(
        "解析确认数据",
        action=action,
        item_id=item_id,
        item_type=item_type,
        note_length=len(review_note) if review_note else 0,
        main_message_id=main_message_id
    )
    
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
        await cb.answer("❌ 审核类型错误")
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
        
        # 区分媒体消息审核和主面板审核的处理逻辑
        note_preview = review_note[:30] + ('...' if len(review_note) > 30 else '') if review_note else "无留言"
        
        # 检查是否为媒体消息（单独发送的媒体消息）
        is_media_message = hasattr(cb.message, 'photo') or hasattr(cb.message, 'video') or hasattr(cb.message, 'document')
        
        # 显示提示消息（不需要用户确认）
        await cb.answer(f"✅ 已{action_text}{type_text} {item_id}")
        
        if is_media_message:
            # 媒体消息审核：删除当前媒体消息，然后刷新主面板数据
            try:
                await cb.message.delete()
            except Exception as e:
                logger.warning(f"删除媒体消息失败: {e}")
            
            # 删除其他已发送的媒体消息
            from app.utils.panel_utils import cleanup_sent_media_messages
            await cleanup_sent_media_messages(cb.bot, state)
            
            # 媒体消息审核完成后，刷新主面板数据
            # 获取状态中保存的主消息ID
            data = await state.get_data()
            main_message_id = data.get('main_message_id')
            
            if main_message_id:
                # 直接编辑主面板消息来刷新数据
                try:
                    # 初始化变量
                    items = []
                    page_data = []
                    text = ""
                    keyboard = None
                    
                    # 导入必要的模块
                    from app.utils.review_config import ReviewUIBuilder
                    from app.utils.pagination import Paginator
                    from app.config.config import REVIEW_PAGE_SIZE
                    from app.buttons.users import admin_review_center_kb
                    
                    # 获取最新的待审核数据
                    if item_type == 'movie':
                        from app.handlers.admins.movie_review import movie_review_handler
                        items = await get_pending_movie_requests()
                        
                        if items:
                            paginator = Paginator(items, page_size=REVIEW_PAGE_SIZE)
                            page_data = paginator.get_page_items(1)
                            text = await ReviewUIBuilder.build_review_list_text(movie_review_handler.config, page_data, paginator, 1)
                            keyboard = ReviewUIBuilder.build_review_list_keyboard(movie_review_handler.config, page_data, paginator, 1)
                        else:
                            text = f"🎬 <b>求片审核</b>\n\n暂无待审核的求片请求。"
                            keyboard = admin_review_center_kb
                            
                    elif item_type == 'content':
                        from app.handlers.admins.content_review import content_review_handler
                        items = await get_pending_content_submissions()
                        
                        if items:
                            paginator = Paginator(items, page_size=REVIEW_PAGE_SIZE)
                            page_data = paginator.get_page_items(1)
                            text = await ReviewUIBuilder.build_review_list_text(content_review_handler.config, page_data, paginator, 1)
                            keyboard = ReviewUIBuilder.build_review_list_keyboard(content_review_handler.config, page_data, paginator, 1)
                        else:
                            text = f"📝 <b>投稿审核</b>\n\n暂无待审核的投稿请求。"
                            keyboard = admin_review_center_kb
                    
                    # 尝试编辑主面板消息，如果失败则发送新消息
                    try:
                        await cb.bot.edit_message_caption(
                            chat_id=cb.message.chat.id,
                            message_id=main_message_id,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                        debug_review_flow("主面板消息编辑成功", message_id=main_message_id)
                    except Exception as edit_error:
                        debug_error("主面板消息编辑失败", str(edit_error), message_id=main_message_id)
                        logger.warning(f"编辑主面板消息失败，发送新消息: {edit_error}")
                        
                        # 发送新的主面板消息
                        new_main_message = await cb.bot.send_photo(
                            chat_id=cb.message.chat.id,
                            photo=DEFAULT_WELCOME_PHOTO,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                        
                        # 更新主消息ID
                        new_main_id = new_main_message.message_id
                        await state.update_data(main_message_id=new_main_id)
                        
                        debug_main_message_tracking(
                            "创建新主消息",
                            old_id=main_message_id,
                            new_id=new_main_id,
                            reason="原主消息不存在"
                        )
                        debug_review_flow("新主面板消息创建成功", message_id=new_main_id)
                    
                    # 发送新的媒体消息（如果有待审核项目）
                    if items and page_data:
                        # 确保sent_media_ids列表是干净的，不包含主消息ID
                        await state.update_data(sent_media_ids=[])
                        
                        if item_type == 'movie':
                            await movie_review_handler._send_media_messages(cb, state, page_data)
                        elif item_type == 'content':
                            await content_review_handler._send_media_messages(cb, state, page_data)
                        
                except Exception as e:
                    logger.error(f"刷新主面板失败: {e}")
                    # 如果编辑失败，回退到原有逻辑
                    await _return_to_review_list(cb, state, item_type)
            else:
                # 如果没有主消息ID，回退到原有逻辑
                await _return_to_review_list(cb, state, item_type)
        else:
            # 主面板审核：删除媒体消息，然后返回审核列表
            from app.utils.panel_utils import cleanup_sent_media_messages
            await cleanup_sent_media_messages(cb.bot, state)
            
            # 返回审核列表（可以直接编辑主面板消息）
            await _return_to_review_list(cb, state, item_type)
    else:
        await cb.answer("❌ 审核失败，请重试")
    
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
        caption=f"💬 <b>审核留言</b>\n\n请重新输入{action_text}{type_text} #{item_id} 的留言（必填）：",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="❌ 取消", callback_data=f"admin_review_{item_type}" if item_type == "movie" else "admin_review_content")
                ]
            ]
        )
    )
    await cb.answer()