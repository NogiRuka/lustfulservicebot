from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import (
    get_pending_movie_requests, get_pending_content_submissions,
    get_all_movie_requests, get_all_content_submissions,
    review_movie_request, review_content_submission
)
from app.buttons.users import admin_review_center_kb, back_to_main_kb
from app.utils.message_utils import safe_edit_message
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.time_utils import humanize_time, get_status_text

review_router = Router()


# ==================== 审核中心 ====================

@review_router.callback_query(F.data == "admin_review_center")
async def cb_admin_review_center(cb: types.CallbackQuery):
    """审核中心"""
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


# ==================== 求片审核 ====================

@review_router.callback_query(F.data == "admin_review_movie")
async def cb_admin_review_movie(cb: types.CallbackQuery):
    """求片审核"""
    await cb_admin_review_movie_page(cb, 1)


@review_router.callback_query(F.data.startswith("movie_review_page_"))
async def cb_admin_review_movie_page(cb: types.CallbackQuery, page: int = None):
    """求片审核分页"""
    # 提取页码
    if page is None:
        page = extract_page_from_callback(cb.data, "movie_review")
    
    requests = await get_pending_movie_requests()
    
    if not requests:
        await safe_edit_message(
            cb.message,
            caption="🎬 <b>求片审核</b>\n\n暂无待审核的求片请求。",
            reply_markup=admin_review_center_kb
        )
        await cb.answer()
        return
    
    paginator = Paginator(requests, page_size=3)
    page_info = paginator.get_page_info(page)
    page_items = paginator.get_page_items(page)
    
    # 构建页面内容
    text = format_page_header("🎬 <b>求片审核</b>", page_info)
    
    start_num = (page - 1) * paginator.page_size + 1
    for i, req in enumerate(page_items, start_num):
        # 获取类型信息
        category_name = "未知类型"
        if hasattr(req, 'category') and req.category:
            category_name = req.category.name
        
        # 状态显示
        status_text = get_status_text(req.status)
        
        # 美化的卡片式布局
        text += f"┌─ {i}. 🎬 <b>【{category_name}】{req.title}</b>\n"
        text += f"├ 🆔 ID：<code>{req.id}</code>\n"
        text += f"├ 👤 用户：{req.user_id}\n"
        text += f"├ ⏰ 时间：<i>{humanize_time(req.created_at)}</i>\n"
        text += f"├ 🏷️ 状态：<code>{status_text}</code>\n"
        
        if req.description:
            desc_preview = req.description[:60] + ('...' if len(req.description) > 60 else '')
            text += f"├ 📝 描述：{desc_preview}\n"
        
        # 媒体链接
        if hasattr(req, 'file_id') and req.file_id:
            # 美化的媒体消息发送
            media_caption = (
                f"🎬 <b>【{category_name}】{req.title}</b>\n\n"
                f"🆔 <b>求片ID</b>：<code>{req.id}</code>\n"
                f"👤 <b>用户</b>：{req.user_id}\n"
                f"⏰ <b>时间</b>：{humanize_time(req.created_at)}\n"
                f"🏷️ <b>状态</b>：<code>{status_text}</code>\n\n"
            )
            
            if req.description:
                media_caption += f"📝 <b>描述</b>：\n{req.description}\n\n"
            
            media_caption += "📎 <b>附件预览</b> ⬆️"
            
            # 创建媒体消息的审核按钮
            media_keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text=f"✅ 通过 #{req.id}", callback_data=f"approve_movie_media_{req.id}"),
                        types.InlineKeyboardButton(text=f"❌ 拒绝 #{req.id}", callback_data=f"reject_movie_media_{req.id}")
                    ],
                    [
                        types.InlineKeyboardButton(text=f"💬 留言通过 #{req.id}", callback_data=f"approve_movie_note_media_{req.id}"),
                        types.InlineKeyboardButton(text=f"💬 留言拒绝 #{req.id}", callback_data=f"reject_movie_note_media_{req.id}")
                    ],
                    [
                        types.InlineKeyboardButton(text="🗑️ 关闭消息", callback_data=f"delete_media_message_{req.id}")
                    ]
                ]
            )
            
            try:
                await cb.message.bot.send_photo(
                    chat_id=cb.from_user.id, 
                    photo=req.file_id, 
                    caption=media_caption,
                    parse_mode="HTML",
                    reply_markup=media_keyboard
                )
            except Exception as e:
                logger.warning(f"发送媒体消息失败: {e}")
            
            text += f"└ 📎 <b>附件已发送</b> ✅\n"
        else:
            text += f"└─────────────────\n"
        
    
    # 创建分页键盘
    extra_buttons = []
    
    # 为当前页面的每个求片添加快速操作按钮
    for req in page_items:
        extra_buttons.append([
            types.InlineKeyboardButton(text=f"✅ 通过 #{req.id}", callback_data=f"approve_movie_{req.id}"),
            types.InlineKeyboardButton(text=f"❌ 拒绝 #{req.id}", callback_data=f"reject_movie_{req.id}")
        ])
        extra_buttons.append([
            types.InlineKeyboardButton(text=f"💬 留言通过 #{req.id}", callback_data=f"approve_movie_note_{req.id}"),
            types.InlineKeyboardButton(text=f"💬 留言拒绝 #{req.id}", callback_data=f"reject_movie_note_{req.id}")
        ])
    
    # 添加其他功能按钮
    extra_buttons.extend([
        [
            types.InlineKeyboardButton(text="📋 查看详情", callback_data=f"review_movie_detail_{page_items[0].id}" if page_items else "admin_review_movie"),
            types.InlineKeyboardButton(text="🔄 刷新", callback_data="admin_review_movie")
        ],
        [
            types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="admin_review_center"),
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
        ]
    ])
    
    keyboard = paginator.create_pagination_keyboard(
        page, "movie_review", extra_buttons
    )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=keyboard
    )
    await cb.answer()


# ==================== 投稿审核 ====================

@review_router.callback_query(F.data == "admin_review_content")
async def cb_admin_review_content(cb: types.CallbackQuery):
    """投稿审核"""
    await cb_admin_review_content_page(cb, 1)


@review_router.callback_query(F.data.startswith("content_review_page_"))
async def cb_admin_review_content_page(cb: types.CallbackQuery, page: int = None):
    """投稿审核分页"""
    # 提取页码
    if page is None:
        page = extract_page_from_callback(cb.data, "content_review")
    
    submissions = await get_pending_content_submissions()
    
    if not submissions:
        await safe_edit_message(
            cb.message,
            caption="📝 <b>投稿审核</b>\n\n暂无待审核的投稿。",
            reply_markup=admin_review_center_kb
        )
        await cb.answer()
        return
    
    paginator = Paginator(submissions, page_size=3)
    page_info = paginator.get_page_info(page)
    page_items = paginator.get_page_items(page)
    
    # 构建页面内容
    text = format_page_header("📝 <b>投稿审核</b>", page_info)
    
    start_num = (page - 1) * paginator.page_size + 1
    for i, sub in enumerate(page_items, start_num):
        # 获取类型信息
        category_name = "通用内容"
        if hasattr(sub, 'category') and sub.category:
            category_name = sub.category.name
        
        # 状态显示
        status_text = get_status_text(sub.status)
        
        # 美化的卡片式布局
        text += f"┌─ {i}. 📝 <b>【{category_name}】{sub.title}</b>\n"
        text += f"├ 🆔 ID：<code>{sub.id}</code>\n"
        text += f"├ 👤 用户：{sub.user_id}\n"
        text += f"├ ⏰ 时间：<i>{humanize_time(sub.created_at)}</i>\n"
        text += f"├ 🏷️ 状态：<code>{status_text}</code>\n"
        
        content_preview = sub.content[:60] + ('...' if len(sub.content) > 60 else '')
        text += f"├ 📄 内容：{content_preview}\n"
        
        # 媒体链接
        if sub.file_id:
            # 美化的媒体消息发送
            media_caption = (
                f"📝 <b>【{category_name}】{sub.title}</b>\n\n"
                f"🆔 <b>投稿ID</b>：<code>{sub.id}</code>\n"
                f"👤 <b>用户</b>：{sub.user_id}\n"
                f"⏰ <b>时间</b>：{humanize_time(sub.created_at)}\n"
                f"🏷️ <b>状态</b>：<code>{status_text}</code>\n\n"
            )
            
            content_preview = sub.content[:200] + ('...' if len(sub.content) > 200 else '')
            media_caption += f"📄 <b>内容</b>：\n{content_preview}\n\n"
            
            # 显示审核备注（如果有）
            if hasattr(sub, 'review_note') and sub.review_note:
                media_caption += f"💬 <b>审核备注</b>：\n{sub.review_note}\n\n"
            
            media_caption += "📎 <b>附件预览</b> ⬆️"
            
            try:
                 sent_message = await cb.message.bot.send_photo(
                     chat_id=cb.from_user.id, 
                     photo=sub.file_id, 
                     caption=media_caption,
                     parse_mode="HTML"
                 )
                 # 记录发送的媒体消息ID
                 if state:
                     data = await state.get_data()
                     sent_media_ids = data.get('sent_media_ids', [])
                     sent_media_ids.append(sent_message.message_id)
                     await state.update_data(sent_media_ids=sent_media_ids)
            except Exception as e:
                logger.warning(f"发送媒体消息失败: {e}")
            
            text += f"└ 📎 <b>附件已发送</b> ✅\n"
        else:
            text += f"└─────────────────\n"
        
    
    # 创建分页键盘
    extra_buttons = []
    
    # 为当前页面的每个投稿添加快速操作按钮
    for sub in page_items:
        extra_buttons.append([
            types.InlineKeyboardButton(text=f"✅ 通过 #{sub.id}", callback_data=f"approve_content_{sub.id}"),
            types.InlineKeyboardButton(text=f"❌ 拒绝 #{sub.id}", callback_data=f"reject_content_{sub.id}")
        ])
        extra_buttons.append([
            types.InlineKeyboardButton(text=f"💬 留言通过 #{sub.id}", callback_data=f"approve_content_note_{sub.id}"),
            types.InlineKeyboardButton(text=f"💬 留言拒绝 #{sub.id}", callback_data=f"reject_content_note_{sub.id}")
        ])
    
    # 添加其他功能按钮
    extra_buttons.extend([
        [
            types.InlineKeyboardButton(text="📋 查看详情", callback_data=f"review_content_detail_{page_items[0].id}" if page_items else "admin_review_content"),
            types.InlineKeyboardButton(text="🔄 刷新", callback_data="admin_review_content")
        ],
        [
            types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="admin_review_center"),
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
        ]
    ])
    
    keyboard = paginator.create_pagination_keyboard(
        page, "content_review", extra_buttons
    )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=keyboard
    )
    await cb.answer()


# ==================== 快速审核操作 ====================

@review_router.callback_query(F.data.regexp(r'^approve_movie_\d+$'))
async def cb_approve_movie(cb: types.CallbackQuery):
    logger.info(f"cb_approve_movie求片review: {cb.data}")
    """快速通过求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await review_movie_request(request_id, cb.from_user.id, "approved")
    
    if success:
        await cb.answer(f"✅ 已通过求片 {request_id}")
        # 刷新审核列表
        await cb_admin_review_movie(cb)
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确")


@review_router.callback_query(F.data.regexp(r'^reject_movie_\d+$'))
async def cb_reject_movie(cb: types.CallbackQuery):
    """快速拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await review_movie_request(request_id, cb.from_user.id, "rejected")
    
    if success:
        await cb.answer(f"❌ 已拒绝求片 {request_id}")
        # 刷新审核列表
        await cb_admin_review_movie(cb)
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确")


@review_router.callback_query(F.data.regexp(r'^approve_content_\d+$'))
async def cb_approve_content(cb: types.CallbackQuery):
    """快速通过投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    success = await review_content_submission(submission_id, cb.from_user.id, "approved")
    
    if success:
        await cb.answer(f"✅ 已通过投稿 {submission_id}")
        # 刷新审核列表
        await cb_admin_review_content(cb)
    else:
        await cb.answer("❌ 操作失败，请检查投稿ID是否正确")


# ==================== 详情查看功能 ====================

@review_router.callback_query(F.data.startswith("review_movie_detail_"))
async def cb_review_movie_detail(cb: types.CallbackQuery):
    """查看求片详情"""
    request_id = int(cb.data.split("_")[-1])
    
    # 获取求片详情
    requests = await get_pending_movie_requests()
    request = next((r for r in requests if r.id == request_id), None)
    
    if not request:
        await cb.answer("❌ 求片请求不存在或已被处理")
        return
    
    # 构建详情文本
    detail_text = (
        f"🎬 <b>求片详情</b>\n\n"
        f"🆔 ID：{request.id}\n"
        f"🎭 片名：{request.title}\n"
        f"👤 用户ID：{request.user_id}\n"
        f"📅 提交时间：{humanize_time(request.created_at)}\n"
        f"📝 状态：{get_status_text(request.status)}\n\n"
    )
    
    if request.description:
        detail_text += f"📄 描述：\n{request.description}\n\n"
    else:
        detail_text += f"📄 描述：无\n\n"
    
    if hasattr(request, 'file_id') and request.file_id:
        detail_text += f"📎 附件：有（文件ID: {request.file_id[:20]}...）\n\n"
    else:
        detail_text += f"📎 附件：无\n\n"
    
    detail_text += "请选择审核操作："
    
    # 详情页面按钮
    detail_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ 通过", callback_data=f"approve_movie_{request.id}"),
                types.InlineKeyboardButton(text="❌ 拒绝", callback_data=f"reject_movie_{request.id}")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回列表", callback_data="admin_review_movie"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=detail_text,
        reply_markup=detail_kb
    )
    await cb.answer()


@review_router.callback_query(F.data.startswith("review_content_detail_"))
async def cb_review_content_detail(cb: types.CallbackQuery):
    """查看投稿详情"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 获取投稿详情
    submissions = await get_pending_content_submissions()
    submission = next((s for s in submissions if s.id == submission_id), None)
    
    if not submission:
        await cb.answer("❌ 投稿不存在或已被处理",)
        return
    
    # 构建详情文本
    detail_text = (
        f"📝 <b>投稿详情</b>\n\n"
        f"🆔 ID：{submission.id}\n"
        f"📝 标题：{submission.title}\n"
        f"👤 用户ID：{submission.user_id}\n"
        f"📅 提交时间：{humanize_time(submission.created_at)}\n"
        f"📊 状态：{get_status_text(submission.status)}\n\n"
    )
    
    # 显示内容（限制长度）
    if len(submission.content) > 500:
        content_display = submission.content[:500] + "\n\n... (内容过长，已截断)"
    else:
        content_display = submission.content
    
    detail_text += f"📄 内容：\n{content_display}\n\n"
    
    if submission.file_id:
        detail_text += f"📎 附件：有（文件ID: {submission.file_id[:20]}...）\n\n"
    else:
        detail_text += f"📎 附件：无\n\n"
    
    detail_text += "请选择审核操作："
    
    # 详情页面按钮
    detail_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ 通过", callback_data=f"approve_content_{submission.id}"),
                types.InlineKeyboardButton(text="❌ 拒绝", callback_data=f"reject_content_{submission.id}")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回列表", callback_data="admin_review_content"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=detail_text,
        reply_markup=detail_kb
    )
    await cb.answer()


@review_router.callback_query(F.data.regexp(r'^reject_content_\d+$'))
async def cb_reject_content(cb: types.CallbackQuery):
    """快速拒绝投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    success = await review_content_submission(submission_id, cb.from_user.id, "rejected")
    
    if success:
        await cb.answer(f"❌ 已拒绝投稿 {submission_id}", show_alert=True)
        # 刷新审核列表
        await cb_admin_review_content(cb)
    else:
        await cb.answer("❌ 操作失败，请检查投稿ID是否正确", show_alert=True)


# ==================== 媒体消息审核操作 ====================

@review_router.callback_query(F.data.startswith("approve_movie_media_"))
async def cb_approve_movie_media(cb: types.CallbackQuery):
    """媒体消息快速通过求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await review_movie_request(request_id, cb.from_user.id, "approved")
    
    if success:
        await cb.answer(f"✅ 已通过求片 {request_id}", show_alert=True)
        # 删除媒体消息
        try:
            await cb.message.delete()
        except Exception as e:
            logger.warning(f"删除媒体消息失败: {e}")
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确", show_alert=True)


@review_router.callback_query(F.data.startswith("reject_movie_media_"))
async def cb_reject_movie_media(cb: types.CallbackQuery):
    """媒体消息快速拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await review_movie_request(request_id, cb.from_user.id, "rejected")
    
    if success:
        await cb.answer(f"❌ 已拒绝求片 {request_id}", show_alert=True)
        # 删除媒体消息
        try:
            await cb.message.delete()
        except Exception as e:
            logger.warning(f"删除媒体消息失败: {e}")
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确", show_alert=True)


@review_router.callback_query(F.data.startswith("approve_movie_note_media_"))
async def cb_approve_movie_note_media(cb: types.CallbackQuery, state: FSMContext):
    """媒体消息留言通过求片"""
    request_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'movie',
        'review_id': request_id,
        'review_action': 'approved',
        'message_id': cb.message.message_id,
        'is_media_message': True
    })
    
    await state.set_state(Wait.waitReviewNote)
    
    # 更新媒体消息为留言输入状态
    note_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="⏭️ 跳过留言", callback_data="skip_review_note"),
                types.InlineKeyboardButton(text="🗑️ 关闭消息", callback_data=f"delete_media_message_{request_id}")
            ]
        ]
    )
    
    try:
        await cb.message.edit_caption(
            caption=f"💬 <b>审核留言</b>\n\n请输入通过求片 #{request_id} 的留言（可选）：",
            reply_markup=note_keyboard
        )
    except Exception as e:
        logger.warning(f"编辑媒体消息失败: {e}")
    
    await cb.answer()


@review_router.callback_query(F.data.startswith("reject_movie_note_media_"))
async def cb_reject_movie_note_media(cb: types.CallbackQuery, state: FSMContext):
    """媒体消息留言拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'movie',
        'review_id': request_id,
        'review_action': 'rejected',
        'message_id': cb.message.message_id,
        'is_media_message': True
    })
    
    await state.set_state(Wait.waitReviewNote)
    
    # 更新媒体消息为留言输入状态
    note_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="⏭️ 跳过留言", callback_data="skip_review_note"),
                types.InlineKeyboardButton(text="🗑️ 关闭消息", callback_data=f"delete_media_message_{request_id}")
            ]
        ]
    )
    
    try:
        await cb.message.edit_caption(
            caption=f"💬 <b>审核留言</b>\n\n请输入拒绝求片 #{request_id} 的留言（可选）：",
            reply_markup=note_keyboard
        )
    except Exception as e:
        logger.warning(f"编辑媒体消息失败: {e}")
    
    await cb.answer()


@review_router.callback_query(F.data.startswith("delete_media_message_"))
async def cb_delete_media_message(cb: types.CallbackQuery, state: FSMContext):
    """删除媒体消息"""
    try:
        await cb.message.delete()
        await state.clear()  # 清除状态
    except Exception as e:
        logger.warning(f"删除媒体消息失败: {e}")
        await cb.answer("❌ 删除消息失败", show_alert=True)


# ==================== 所有记录查看 ====================

@review_router.callback_query(F.data == "admin_all_movies")
async def cb_admin_all_movies(cb: types.CallbackQuery, state: FSMContext):
    """查看所有求片"""
    # 清空之前的媒体消息记录
    await state.update_data(sent_media_ids=[])
    await cb_admin_all_movies_page(cb, 1, state)


@review_router.callback_query(F.data.startswith("all_movie_page_"))
async def cb_admin_all_movies_page(cb: types.CallbackQuery, state: FSMContext, page: int = None):
    """所有求片分页"""
    # 提取页码
    if page is None:
        page = extract_page_from_callback(cb.data, "all_movie")
    
    # 删除之前发送的媒体消息
    if state:
        data = await state.get_data()
        sent_media_ids = data.get('sent_media_ids', [])
        for message_id in sent_media_ids:
            try:
                await cb.message.bot.delete_message(chat_id=cb.from_user.id, message_id=message_id)
            except Exception as e:
                logger.warning(f"删除媒体消息失败: {e}")
        # 清空已发送的媒体消息ID列表
        await state.update_data(sent_media_ids=[])
    
    requests = await get_all_movie_requests()
    
    if not requests:
        await safe_edit_message(
            cb.message,
            caption="📋 <b>所有求片</b>\n\n暂无求片记录。",
            reply_markup=admin_review_center_kb
        )
        await cb.answer()
        return
    
    paginator = Paginator(requests, page_size=3)
    page_info = paginator.get_page_info(page)
    page_items = paginator.get_page_items(page)
    
    # 构建页面内容
    text = format_page_header("📋 <b>所有求片</b>", page_info)
    
    start_num = (page - 1) * paginator.page_size + 1
    for i, req in enumerate(page_items, start_num):
        # 获取类型信息
        category_name = "未知类型"
        if hasattr(req, 'category') and req.category:
            category_name = req.category.name
        
        # 状态显示
        status_text = get_status_text(req.status)
        
        # 美化的卡片式布局
        text += f"┌─ {i}. 🎬 <b>【{category_name}】{req.title}</b>\n"
        text += f"├ 🆔 ID：<code>{req.id}</code>\n"
        text += f"├ 👤 用户：{req.user_id}\n"
        text += f"├ ⏰ 时间：<i>{humanize_time(req.created_at)}</i>\n"
        text += f"├ 🏷️ 状态：<code>{status_text}</code>\n"
        
        if req.description:
            desc_preview = req.description[:60] + ('...' if len(req.description) > 60 else '')
            text += f"├ 📝 描述：{desc_preview}\n"
        
        # 媒体链接
        if hasattr(req, 'file_id') and req.file_id:
            # 美化的媒体消息发送
            media_caption = (
                f"🎬 <b>【{category_name}】{req.title}</b>\n\n"
                f"🆔 <b>求片ID</b>：<code>{req.id}</code>\n"
                f"👤 <b>用户</b>：{req.user_id}\n"
                f"⏰ <b>时间</b>：{humanize_time(req.created_at)}\n"
                f"🏷️ <b>状态</b>：<code>{status_text}</code>\n\n"
            )
            
            if req.description:
                media_caption += f"📝 <b>描述</b>：\n{req.description}\n\n"
            
            # 显示审核备注（如果有）
            if hasattr(req, 'review_note') and req.review_note:
                media_caption += f"💬 <b>审核备注</b>：\n{req.review_note}\n\n"
            
            media_caption += "📎 <b>附件预览</b> ⬆️"
            
            try:
                sent_message = await cb.message.bot.send_photo(
                    chat_id=cb.from_user.id, 
                    photo=req.file_id, 
                    caption=media_caption,
                    parse_mode="HTML"
                )
                # 记录发送的媒体消息ID
                if state:
                    data = await state.get_data()
                    sent_media_ids = data.get('sent_media_ids', [])
                    sent_media_ids.append(sent_message.message_id)
                    await state.update_data(sent_media_ids=sent_media_ids)
            except Exception as e:
                logger.warning(f"发送媒体消息失败: {e}")
            
            text += f"└ 📎 <b>附件已发送</b> ✅\n"
        else:
            # 显示审核备注（如果有）
            if hasattr(req, 'review_note') and req.review_note:
                note_preview = req.review_note[:60] + ('...' if len(req.review_note) > 60 else '')
                text += f"└ 💬 <b>审核备注</b>：<blockquote>{note_preview}</blockquote>\n"
            else:
                text += f"└─────────────────\n"
        
        text += "\n"
    
    # 创建分页键盘
    keyboard = paginator.create_pagination_keyboard(
        page, 
        "all_movie_page",
        extra_buttons=[
            [
                types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center")
            ]
        ]
    )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=keyboard
    )
    await cb.answer()


@review_router.callback_query(F.data == "admin_all_content")
async def cb_admin_all_content(cb: types.CallbackQuery, state: FSMContext):
    """查看所有投稿"""
    # 清空之前的媒体消息记录
    await state.update_data(sent_media_ids=[])
    await cb_admin_all_content_page(cb, 1, state)


@review_router.callback_query(F.data.startswith("all_content_page_"))
async def cb_admin_all_content_page(cb: types.CallbackQuery, state: FSMContext, page: int = None):
    """所有投稿分页"""
    # 提取页码
    if page is None:
        page = extract_page_from_callback(cb.data, "all_content")
    
    # 删除之前发送的媒体消息
    if state:
        data = await state.get_data()
        sent_media_ids = data.get('sent_media_ids', [])
        for message_id in sent_media_ids:
            try:
                await cb.message.bot.delete_message(chat_id=cb.from_user.id, message_id=message_id)
            except Exception as e:
                logger.warning(f"删除媒体消息失败: {e}")
        # 清空已发送的媒体消息ID列表
        await state.update_data(sent_media_ids=[])
    
    submissions = await get_all_content_submissions()
    
    if not submissions:
        await safe_edit_message(
            cb.message,
            caption="📄 <b>所有投稿</b>\n\n暂无投稿记录。",
            reply_markup=admin_review_center_kb
        )
        await cb.answer()
        return
    
    paginator = Paginator(submissions, page_size=3)
    page_info = paginator.get_page_info(page)
    page_items = paginator.get_page_items(page)
    
    # 构建页面内容
    text = format_page_header("📄 <b>所有投稿</b>", page_info)
    
    start_num = (page - 1) * paginator.page_size + 1
    for i, sub in enumerate(page_items, start_num):
        # 获取类型信息
        category_name = "未知类型"
        if hasattr(sub, 'category') and sub.category:
            category_name = sub.category.name
        
        # 状态显示
        status_text = get_status_text(sub.status)
        
        # 美化的卡片式布局
        text += f"┌─ {i}. 📝 <b>【{category_name}】{sub.title}</b>\n"
        text += f"├ 🆔 ID：<code>{sub.id}</code>\n"
        text += f"├ 👤 用户：{sub.user_id}\n"
        text += f"├ ⏰ 时间：<i>{humanize_time(sub.created_at)}</i>\n"
        text += f"├ 🏷️ 状态：<code>{status_text}</code>\n"
        
        content_preview = sub.content[:60] + ('...' if len(sub.content) > 60 else '')
        text += f"├ 📄 内容：{content_preview}\n"
        
        # 媒体链接
        if hasattr(sub, 'file_id') and sub.file_id:
            # 美化的媒体消息发送
            media_caption = (
                f"📝 <b>【{category_name}】{sub.title}</b>\n\n"
                f"🆔 <b>投稿ID</b>：<code>{sub.id}</code>\n"
                f"👤 <b>用户</b>：{sub.user_id}\n"
                f"⏰ <b>时间</b>：{humanize_time(sub.created_at)}\n"
                f"🏷️ <b>状态</b>：<code>{status_text}</code>\n\n"
            )
            
            content_full = sub.content[:200] + ('...' if len(sub.content) > 200 else '')
            media_caption += f"📄 <b>内容</b>：\n{content_full}\n\n"
            
            # 显示审核备注（如果有）
            if hasattr(sub, 'review_note') and sub.review_note:
                media_caption += f"💬 <b>审核备注</b>：\n{sub.review_note}\n\n"
            
            media_caption += "📎 <b>附件预览</b> ⬆️"
            
            try:
                sent_message = await cb.message.bot.send_photo(
                    chat_id=cb.from_user.id, 
                    photo=sub.file_id, 
                    caption=media_caption,
                    parse_mode="HTML"
                )
                # 记录发送的媒体消息ID
                if state:
                    data = await state.get_data()
                    sent_media_ids = data.get('sent_media_ids', [])
                    sent_media_ids.append(sent_message.message_id)
                    await state.update_data(sent_media_ids=sent_media_ids)
            except Exception as e:
                logger.warning(f"发送媒体消息失败: {e}")
            
            text += f"└ 📎 <b>附件已发送</b> ✅\n"
        else:
            # 显示审核备注（如果有）
            if hasattr(sub, 'review_note') and sub.review_note:
                note_preview = sub.review_note[:60] + ('...' if len(sub.review_note) > 60 else '')
                text += f"└ 💬 <b>审核备注</b>：<blockquote>{note_preview}</blockquote>\n"
            else:
                text += f"└─────────────────\n"
        
        text += "\n"
    
    # 创建分页键盘
    keyboard = paginator.create_pagination_keyboard(
        page, 
        "all_content_page",
        extra_buttons=[
            [
                types.InlineKeyboardButton(text="🔙 返回审核中心", callback_data="admin_review_center")
            ]
        ]
    )
    
    await safe_edit_message(
        cb.message,
        caption=text,
        reply_markup=keyboard
    )
    await cb.answer()