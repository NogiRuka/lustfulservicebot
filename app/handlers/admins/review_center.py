from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger
from app.utils.debug_utils import (
    debug_log, debug_message_info, debug_state_info, debug_main_message_tracking,
    debug_review_flow, debug_media_message_tracking, debug_function
)
from aiogram.filters import Command
from app.utils.filters import HasRole
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN
from app.config import ADMINS_ID, SUPERADMIN_ID

from app.database.business import (
    get_pending_movie_requests, get_pending_content_submissions,
    get_all_movie_requests, get_all_content_submissions,
    get_movie_request_by_id, get_content_submission_by_id
)
from app.database.users import get_role
from app.buttons.panels import get_panel_for_role
from app.buttons.users import admin_review_center_kb, back_to_main_kb
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.panel_utils import get_user_display_link, cleanup_sent_media_messages, create_welcome_panel_text, DEFAULT_WELCOME_PHOTO
from app.utils.states import Wait
from app.utils.browse_config import (
    MOVIE_BROWSE_CONFIG, CONTENT_BROWSE_CONFIG, BrowseHandler
)

review_center_router = Router()

# 初始化配置
MOVIE_BROWSE_CONFIG.get_all_items_function = get_all_movie_requests
MOVIE_BROWSE_CONFIG.get_item_by_id_function = get_movie_request_by_id

CONTENT_BROWSE_CONFIG.get_all_items_function = get_all_content_submissions
CONTENT_BROWSE_CONFIG.get_item_by_id_function = get_content_submission_by_id

# 创建处理器实例
movie_browse_handler = BrowseHandler(MOVIE_BROWSE_CONFIG)
content_browse_handler = BrowseHandler(CONTENT_BROWSE_CONFIG)


# ==================== 审核中心 ====================

@review_center_router.callback_query(F.data == "admin_advanced_browse")
async def cb_admin_advanced_browse(cb: types.CallbackQuery, state: FSMContext):
    """高级浏览菜单"""
    # 检查管理员权限
    from app.utils.review_config import check_admin_permission
    
    if not await check_admin_permission(cb.from_user.id):
        await cb.answer("❌ 审核功能已关闭", show_alert=True)
        return
    
    from app.buttons.users import admin_advanced_browse_kb
    
    text = "🔍 <b>高级浏览</b>\n\n"
    text += "选择要浏览的数据类型：\n\n"
    text += "🎬 浏览求片 - 查看所有求片请求\n"
    text += "📝 浏览投稿 - 查看所有投稿内容\n"
    text += "💬 浏览反馈 - 查看用户反馈信息\n"
    text += "👥 浏览用户 - 查看用户信息\n\n"
    text += "💡 支持分页、排序、筛选等高级功能"
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=admin_advanced_browse_kb
    )
    await cb.answer()


# 高级浏览按钮处理器
@review_center_router.callback_query(F.data == "browse_requests_btn")
async def cb_browse_requests_btn(cb: types.CallbackQuery):
    """按钮触发浏览求片"""
    from app.handlers.admins.advanced_browse import request_browser
    
    user_id = str(cb.from_user.id)
    
    try:
        # 获取第一页数据
        data = await request_browser.get_page_data(user_id, 1)
        
        # 格式化显示
        text = request_browser.format_page_header(
            "求片请求浏览", 
            data['page_info'], 
            data['config']
        )
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = request_browser.format_item_display(
                item,
                data['config'].visible_fields,
                {
                    'status': lambda x: {'pending': '待审核', 'approved': '已通过', 'rejected': '已拒绝'}.get(x, x),
                    'category_id': lambda x: getattr(item.category, 'name', '未分类') if hasattr(item, 'category') and item.category else '未分类'
                }
            )
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        keyboard = request_browser.create_navigation_keyboard(
            user_id, 
            "browse_requests", 
            data['page_info']
        )
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"浏览求片请求失败: {e}")
        await cb.answer("❌ 浏览求片请求失败，请稍后重试", show_alert=True)
        return
    
    await cb.answer()


@review_center_router.callback_query(F.data == "browse_submissions_btn")
async def cb_browse_submissions_btn(cb: types.CallbackQuery):
    """按钮触发浏览投稿"""
    from app.handlers.admins.advanced_browse import submission_browser
    
    user_id = str(cb.from_user.id)
    
    try:
        # 获取第一页数据
        data = await submission_browser.get_page_data(user_id, 1)
        
        # 格式化显示
        text = submission_browser.format_page_header(
            "投稿内容浏览", 
            data['page_info'], 
            data['config']
        )
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = submission_browser.format_item_display(
                item,
                data['config'].visible_fields,
                {
                    'status': lambda x: {'pending': '待审核', 'approved': '已通过', 'rejected': '已拒绝'}.get(x, x),
                    'category_id': lambda x: getattr(item.category, 'name', '未分类') if hasattr(item, 'category') and item.category else '未分类'
                }
            )
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        keyboard = submission_browser.create_navigation_keyboard(
            user_id, 
            "browse_submissions", 
            data['page_info']
        )
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"浏览投稿失败: {e}")
        await cb.answer("❌ 浏览投稿失败，请稍后重试", show_alert=True)
        return
    
    await cb.answer()


@review_center_router.callback_query(F.data == "browse_feedback_btn")
async def cb_browse_feedback_btn(cb: types.CallbackQuery):
    """按钮触发浏览反馈"""
    from app.handlers.admins.advanced_browse import feedback_browser
    
    user_id = str(cb.from_user.id)
    
    try:
        # 获取第一页数据
        data = await feedback_browser.get_page_data(user_id, 1)
        
        # 格式化显示
        text = feedback_browser.format_page_header(
            "用户反馈浏览", 
            data['page_info'], 
            data['config']
        )
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = feedback_browser.format_item_display(
                item,
                data['config'].visible_fields,
                {
                    'status': lambda x: {'pending': '待处理', 'processing': '处理中', 'resolved': '已解决'}.get(x, x),
                    'feedback_type': lambda x: {'bug': '错误报告', 'suggestion': '建议', 'complaint': '投诉', 'other': '其他'}.get(x, x)
                }
            )
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        keyboard = feedback_browser.create_navigation_keyboard(
            user_id, 
            "browse_feedback", 
            data['page_info']
        )
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"浏览反馈失败: {e}")
        await cb.answer("❌ 浏览反馈失败，请稍后重试", show_alert=True)
        return
    
    await cb.answer()


@review_center_router.callback_query(F.data == "browse_users_btn")
async def cb_browse_users_btn(cb: types.CallbackQuery):
    """按钮触发浏览用户"""
    from app.handlers.admins.advanced_browse import user_browser
    
    user_id = str(cb.from_user.id)
    
    try:
        # 获取第一页数据
        data = await user_browser.get_page_data(user_id, 1)
        
        # 格式化显示
        text = user_browser.format_page_header(
            "用户信息浏览", 
            data['page_info'], 
            data['config']
        )
        
        # 显示数据项
        for i, item in enumerate(data['items'], 1):
            item_text = user_browser.format_item_display(
                item,
                data['config'].visible_fields,
                {
                    'role': lambda x: {'user': '普通用户', 'admin': '管理员', 'superadmin': '超级管理员'}.get(x, x)
                }
            )
            text += f"{i}. {item_text}\n\n"
        
        # 创建键盘
        keyboard = user_browser.create_navigation_keyboard(
            user_id, 
            "browse_users", 
            data['page_info']
        )
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"浏览用户失败: {e}")
        await cb.answer("❌ 浏览用户失败，请稍后重试", show_alert=True)
        return
    
    await cb.answer()


@review_center_router.callback_query(F.data == "admin_review_center")
@debug_function("审核中心入口")
async def cb_admin_review_center(cb: types.CallbackQuery, state: FSMContext):
    """审核中心"""
    debug_review_flow("进入审核中心")
    debug_message_info(cb, "审核中心回调")
    await debug_state_info(state, "进入前")
    
    # 检查管理员权限和功能开关
    from app.utils.review_config import check_admin_permission
    
    if not await check_admin_permission(cb.from_user.id):
        debug_log("权限检查失败", user_id=cb.from_user.id)
        await cb.answer("❌ 审核功能已关闭", show_alert=True)
        return
    
    debug_log("权限检查通过", user_id=cb.from_user.id)
    
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
    
    debug_review_flow(
        "准备编辑审核中心主消息",
        target_message_id=cb.message.message_id,
        movie_count=len(movie_requests),
        content_count=len(content_submissions)
    )
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=admin_review_center_kb
    )
    
    # 保存主消息ID，确保后续操作能正确编辑这个消息
    old_main_id = (await state.get_data()).get('main_message_id')
    new_main_id = cb.message.message_id
    
    debug_main_message_tracking(
        "审核中心设置主消息ID",
        old_id=old_main_id,
        new_id=new_main_id,
        source="审核中心主面板"
    )
    
    await state.update_data(main_message_id=new_main_id)
    await debug_state_info(state, "主消息ID设置后")
    
    debug_review_flow("审核中心初始化完成")
    await cb.answer()


# ==================== 所有求片管理 ====================

@review_center_router.callback_query(F.data == "admin_all_movies")
async def cb_admin_all_movies(cb: types.CallbackQuery, state: FSMContext):
    """所有求片管理"""
    # 检查管理员权限和功能开关
    from app.utils.review_config import check_admin_permission
    
    if not await check_admin_permission(cb.from_user.id):
        await cb.answer("❌ 审核功能已关闭", show_alert=True)
        return
    
    await movie_browse_handler.handle_browse_list(cb, state, 1)


@review_center_router.callback_query(F.data.startswith("all_movie_page_"))
async def cb_admin_all_movies_page(cb: types.CallbackQuery, state: FSMContext):
    """所有求片分页"""
    page = extract_page_from_callback(cb.data, "all_movie")
    await movie_browse_handler.handle_browse_list(cb, state, page)


# 原有的_show_all_movies_page函数已被配置类统一处理，删除重复代码


# 原有的_send_media_messages_for_movies函数已被配置类统一处理，删除重复代码


# ==================== 预览详情功能 ====================

@review_center_router.callback_query(F.data.startswith("preview_movie_detail_"))
async def cb_preview_movie_detail(cb: types.CallbackQuery, state: FSMContext):
    """预览求片详情"""
    item_id = int(cb.data.split("_")[-1])
    
    # 获取求片详情
    from app.database.business import get_movie_request_by_id
    request = await get_movie_request_by_id(item_id)
    
    if not request:
        await cb.answer("❌ 求片请求不存在", show_alert=True)
        return
    
    # 构建预览文本
    user_display = await get_user_display_link(request.user_id)
    status_text = get_status_text(request.status)
    
    preview_text = (
        f"🎬 <b>求片预览</b>\n\n"
        f"🆔 ID：{request.id}\n"
        f"🎭 片名：{request.title}\n"
        f"👤 用户：{user_display}\n"
        f"📅 提交时间：{humanize_time(request.created_at)}\n"
        f"📊 状态：{status_text}\n\n"
    )
    
    if request.description:
        preview_text += f"📄 描述：\n{request.description}\n\n"
    else:
        preview_text += f"📄 描述：无\n\n"
    
    if hasattr(request, 'file_id') and request.file_id:
        preview_text += f"📎 附件：有\n\n"
    else:
        preview_text += f"📎 附件：无\n\n"
    
    # 构建预览键盘（简化版）
    preview_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="💬 回复用户", callback_data=f"reply_movie_{item_id}")
            ],
            [
                types.InlineKeyboardButton(text="🔙 返回列表", callback_data="admin_all_movies")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=preview_text,
        reply_markup=preview_kb
    )
    
    # 如果有媒体文件，发送媒体消息
    if hasattr(request, 'file_id') and request.file_id:
        try:
            media_text = (
                f"🎬 <b>{request.title}</b>\n\n"
                f"🆔 ID: {request.id}\n"
                f"👤 用户: {user_display}\n"
                f"📅 时间: {humanize_time(request.created_at)}\n"
                f"📊 状态: {status_text}\n"
                f"📝 描述: {request.description or '无'}\n\n"
                f"💡 这是用户提交的附件"
            )
            
            media_keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="💬 回复用户", callback_data=f"reply_movie_{item_id}")
                    ]
                ]
            )
            
            media_msg = await cb.message.answer_photo(
                photo=request.file_id,
                caption=media_text,
                reply_markup=media_keyboard,
                parse_mode="HTML"
            )
            
            # 保存媒体消息ID
            data = await state.get_data()
            sent_media_ids = data.get('sent_media_ids', [])
            sent_media_ids.append(media_msg.message_id)
            await state.update_data(sent_media_ids=sent_media_ids)
            
        except Exception as e:
            logger.error(f"发送求片媒体消息失败: {e}")
    
    await cb.answer()


@review_center_router.callback_query(F.data.startswith("preview_content_detail_"))
async def cb_preview_content_detail(cb: types.CallbackQuery, state: FSMContext):
    """预览投稿详情"""
    item_id = int(cb.data.split("_")[-1])
    
    # 获取投稿详情
    from app.database.business import get_content_submission_by_id
    submission = await get_content_submission_by_id(item_id)
    
    if not submission:
        await cb.answer("❌ 投稿不存在", show_alert=True)
        return
    
    # 构建预览文本
    user_display = await get_user_display_link(submission.user_id)
    status_text = get_status_text(submission.status)
    
    preview_text = (
        f"📝 <b>投稿预览</b>\n\n"
        f"🆔 ID：{submission.id}\n"
        f"📝 标题：{submission.title}\n"
        f"👤 用户：{user_display}\n"
        f"📅 提交时间：{humanize_time(submission.created_at)}\n"
        f"📊 状态：{status_text}\n\n"
    )
    
    # 显示内容（限制长度）
    if submission.content:
        if len(submission.content) > 500:
            content_display = submission.content[:500] + "\n\n... (内容过长，已截断)"
        else:
            content_display = submission.content
        preview_text += f"📄 内容：\n{content_display}\n\n"
    else:
        preview_text += f"📄 内容：无\n\n"
    
    if hasattr(submission, 'file_id') and submission.file_id:
        preview_text += f"📎 附件：有\n\n"
    else:
        preview_text += f"📎 附件：无\n\n"
    
    # 构建预览键盘（简化版）
    preview_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="💬 回复用户", callback_data=f"reply_content_{item_id}")
            ],
            [
                types.InlineKeyboardButton(text="🔙 返回列表", callback_data="admin_all_content")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=preview_text,
        reply_markup=preview_kb
    )
    
    # 如果有媒体文件，发送媒体消息
    if hasattr(submission, 'file_id') and submission.file_id:
        try:
            media_text = (
                f"📝 <b>{submission.title}</b>\n\n"
                f"🆔 ID: {submission.id}\n"
                f"👤 用户: {user_display}\n"
                f"📅 时间: {humanize_time(submission.created_at)}\n"
                f"📊 状态: {status_text}\n"
                f"📄 内容: {submission.content or '无'}\n\n"
                f"💡 这是用户提交的附件"
            )
            
            media_keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="💬 回复用户", callback_data=f"reply_content_{item_id}")
                    ]
                ]
            )
            
            media_msg = await cb.message.answer_photo(
                photo=submission.file_id,
                caption=media_text,
                reply_markup=media_keyboard,
                parse_mode="HTML"
            )
            
            # 保存媒体消息ID
            data = await state.get_data()
            sent_media_ids = data.get('sent_media_ids', [])
            sent_media_ids.append(media_msg.message_id)
            await state.update_data(sent_media_ids=sent_media_ids)
            
        except Exception as e:
            logger.error(f"发送投稿媒体消息失败: {e}")
    
    await cb.answer()


# ==================== 回复用户功能 ====================

@review_center_router.callback_query(F.data.startswith("reply_movie_"))
async def cb_reply_movie(cb: types.CallbackQuery, state: FSMContext):
    """回复求片用户"""
    item_id = int(cb.data.split("_")[-1])
    
    # 获取求片详情
    from app.database.business import get_movie_request_by_id
    request = await get_movie_request_by_id(item_id)
    
    if not request:
        await cb.answer("❌ 求片请求不存在", show_alert=True)
        return
    
    # 设置状态
    from app.utils.states import Wait
    await state.set_state(Wait.waitReplyMessage)
    await state.update_data(
        reply_type="movie",
        reply_item_id=item_id,
        reply_user_id=request.user_id,
        reply_title=request.title
    )
    
    # 显示回复输入页面
    user_display = await get_user_display_link(request.user_id)
    reply_text = (
        f"💬 <b>回复用户</b>\n\n"
        f"🎬 求片：{request.title}\n"
        f"👤 用户：{user_display}\n\n"
        f"请输入您要发送给用户的回复消息："
    )
    
    reply_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="❌ 取消回复", callback_data=f"cancel_reply_movie_{item_id}")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=reply_text,
        reply_markup=reply_kb
    )
    await cb.answer()


@review_center_router.callback_query(F.data.startswith("reply_content_"))
async def cb_reply_content(cb: types.CallbackQuery, state: FSMContext):
    """回复投稿用户"""
    item_id = int(cb.data.split("_")[-1])
    
    # 获取投稿详情
    from app.database.business import get_content_submission_by_id
    submission = await get_content_submission_by_id(item_id)
    
    if not submission:
        await cb.answer("❌ 投稿不存在", show_alert=True)
        return
    
    # 设置状态
    from app.utils.states import Wait
    await state.set_state(Wait.waitReplyMessage)
    await state.update_data(
        reply_type="content",
        reply_item_id=item_id,
        reply_user_id=submission.user_id,
        reply_title=submission.title
    )
    
    # 显示回复输入页面
    user_display = await get_user_display_link(submission.user_id)
    reply_text = (
        f"💬 <b>回复用户</b>\n\n"
        f"📝 投稿：{submission.title}\n"
        f"👤 用户：{user_display}\n\n"
        f"请输入您要发送给用户的回复消息："
    )
    
    reply_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="❌ 取消回复", callback_data=f"cancel_reply_content_{item_id}")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=reply_text,
        reply_markup=reply_kb
    )
    await cb.answer()


@review_center_router.callback_query(F.data.startswith("cancel_reply_movie_"))
async def cb_cancel_reply_movie(cb: types.CallbackQuery, state: FSMContext):
    """取消回复求片用户"""
    item_id = int(cb.data.split("_")[-1])
    await state.clear()
    # 返回预览页面
    await cb_preview_movie_detail(cb, state)


@review_center_router.callback_query(F.data.startswith("cancel_reply_content_"))
async def cb_cancel_reply_content(cb: types.CallbackQuery, state: FSMContext):
    """取消回复投稿用户"""
    item_id = int(cb.data.split("_")[-1])
    await state.clear()
    # 返回预览页面
    await cb_preview_content_detail(cb, state)


@review_center_router.message(StateFilter(Wait.waitReplyMessage))
async def process_reply_message(msg: types.Message, state: FSMContext):
    """处理回复消息"""
    data = await state.get_data()
    reply_type = data.get('reply_type')
    reply_item_id = data.get('reply_item_id')
    reply_user_id = data.get('reply_user_id')
    reply_title = data.get('reply_title')
    
    if not all([reply_type, reply_item_id, reply_user_id, reply_title]):
        await msg.reply("❌ 回复信息不完整，请重新操作")
        await state.clear()
        return
    
    # 发送回复给用户
    try:
        reply_text = (
            f"📨 <b>管理员回复</b>\n\n"
            f"{'🎬' if reply_type == 'movie' else '📝'} 关于：{reply_title}\n\n"
            f"💬 回复内容：\n{msg.text}\n\n"
            f"如有疑问，请随时联系我们。"
        )
        
        await msg.bot.send_message(
            chat_id=reply_user_id,
            text=reply_text,
            parse_mode="HTML"
        )
        
        # 显示发送成功页面
        user_display = await get_user_display_link(reply_user_id)
        success_text = (
            f"✅ <b>回复发送成功！</b>\n\n"
            f"{'🎬' if reply_type == 'movie' else '📝'} 项目：{reply_title}\n"
            f"👤 用户：{user_display}\n"
            f"💬 回复内容：{msg.text}\n\n"
            f"用户已收到您的回复消息。"
        )
        
        success_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="🔙 返回列表", 
                        callback_data=f"admin_all_{'movies' if reply_type == 'movie' else 'content'}"
                    )
                ]
            ]
        )
        
        # 删除用户的回复消息
        try:
            await msg.delete()
        except:
            pass
        
        # 编辑主消息显示成功信息
        # 这里需要获取主消息，通过状态或其他方式
        # 暂时使用发送新消息的方式
        await msg.answer(
            text=success_text,
            reply_markup=success_kb,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"发送回复消息失败: {e}")
        await msg.reply(f"❌ 发送回复失败：{str(e)}")
    
    await state.clear()


# ==================== 清理功能 ====================

@review_center_router.callback_query(F.data == "admin_review_center_cleanup")
async def cb_admin_review_center_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """清理媒体消息并返回审核中心"""
    await cleanup_sent_media_messages(cb.bot, state)
    await cb_admin_review_center(cb, state)


@review_center_router.callback_query(F.data == "back_to_main_cleanup")
async def cb_back_to_main_cleanup(cb: types.CallbackQuery, state: FSMContext):
    """清理媒体消息并返回主菜单"""
    from app.utils.panel_utils import return_to_main_menu
    
    # 定义清理逻辑函数
    async def cleanup_logic(cb):
        await cleanup_sent_media_messages(cb.bot, state)
    
    # 使用通用函数，传入清理逻辑
    await return_to_main_menu(cb, cleanup_logic)


# ==================== 所有投稿管理 ====================

@review_center_router.callback_query(F.data == "admin_all_content")
async def cb_admin_all_content(cb: types.CallbackQuery, state: FSMContext):
    """所有投稿管理"""
    # 检查管理员权限和功能开关
    from app.utils.review_config import check_admin_permission
    
    if not await check_admin_permission(cb.from_user.id):
        await cb.answer("❌ 审核功能已关闭", show_alert=True)
        return
    
    await content_browse_handler.handle_browse_list(cb, state, 1)


@review_center_router.callback_query(F.data.startswith("all_content_page_"))
async def cb_admin_all_content_page(cb: types.CallbackQuery, state: FSMContext):
    """所有投稿分页"""
    page = extract_page_from_callback(cb.data, "all_content")
    await content_browse_handler.handle_browse_list(cb, state, page)


# ==================== 命令行审核功能 ====================

@review_center_router.message(Command("approve", "ap"), HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_ADMIN, ROLE_SUPERADMIN]))
async def approve_command(message: types.Message):
    """命令行通过审核"""
    # 检查管理员权限
    from app.utils.review_config import check_admin_permission
    from app.database.users import get_role
    from app.utils.roles import ROLE_SUPERADMIN
    from app.database.business import is_feature_enabled
    
    try:
        role = await get_role(message.from_user.id)
        # 超管不受功能开关限制，普通管理员需要检查开关
        if role != ROLE_SUPERADMIN and not await is_feature_enabled("admin_panel_enabled"):
            await message.reply("❌ 审核功能已关闭")
            return
        
        parts = message.text.strip().split()
        if len(parts) < 3:
            await message.reply(
                "用法：/approve [类型] [ID] [留言] 或 /ap [类型] [ID] [留言]\n"
                "示例：/ap movie 123 内容很好\n"
                "类型：movie(求片) 或 content(投稿)"
            )
            return
        
        item_type = parts[1].lower()
        try:
            item_id = int(parts[2])
        except ValueError:
            await message.reply("❌ ID必须是数字")
            return
        
        review_note = " ".join(parts[3:]) if len(parts) > 3 else "通过审核"
        
        if item_type not in ['movie', 'content']:
            await message.reply("❌ 类型必须是 movie 或 content")
            return
        
        # 执行审核
        if item_type == 'movie':
            from app.database.business import review_movie_request, get_pending_movie_requests
            success = await review_movie_request(item_id, message.from_user.id, "approved", review_note)
            type_text = "求片"
        else:
            from app.database.business import review_content_submission, get_pending_content_submissions
            success = await review_content_submission(item_id, message.from_user.id, "approved", review_note)
            type_text = "投稿"
        
        if success:
            # 发送通知
            from app.utils.panel_utils import send_review_notification
            from app.database.business import get_movie_requests_advanced, get_content_submissions_advanced
            
            # 获取项目信息用于通知
            if item_type == 'movie':
                data = await get_movie_requests_advanced(offset=0, limit=1000)
                item = next((r for r in data['items'] if r.id == item_id), None)
            else:
                data = await get_content_submissions_advanced(offset=0, limit=1000)
                item = next((s for s in data['items'] if s.id == item_id), None)
            
            if item:
                # 通过category_id获取分类名称
                from app.database.business import get_movie_category_by_id
                category = await get_movie_category_by_id(item.category_id) if item.category_id else None
                category_name = category.name if category else None
                
                if item_type == 'movie':
                    await send_review_notification(
                        message.bot, item.user_id, item_type, item.title, "approved", review_note,
                        file_id=item.file_id, item_content=item.description, item_id=item.id,
                        category_name=category_name
                    )
                else:
                    await send_review_notification(
                        message.bot, item.user_id, item_type, item.title, "approved", review_note,
                        file_id=item.file_id, item_content=item.content, item_id=item.id,
                        category_name=category_name
                    )
            
            await message.reply(f"✅ 已通过{type_text} #{item_id}\n💬 留言：{review_note}")
        else:
            await message.reply(f"❌ 操作失败，请检查{type_text}ID是否正确")
            
    except Exception as e:
        logger.error(f"命令行审核失败: {e}")
        await message.reply("❌ 审核失败，请稍后重试")


@review_center_router.message(Command("reject", "rj"), HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_ADMIN, ROLE_SUPERADMIN]))
async def reject_command(message: types.Message):
    """命令行拒绝审核"""
    # 检查管理员权限
    from app.utils.review_config import check_admin_permission
    from app.database.users import get_role
    from app.utils.roles import ROLE_SUPERADMIN
    from app.database.business import is_feature_enabled
    
    try:
        role = await get_role(message.from_user.id)
        # 超管不受功能开关限制，普通管理员需要检查开关
        if role != ROLE_SUPERADMIN and not await is_feature_enabled("admin_panel_enabled"):
            await message.reply("❌ 审核功能已关闭")
            return
        
        parts = message.text.strip().split()
        if len(parts) < 4:
            await message.reply(
                "用法：/reject [类型] [ID] [拒绝原因] 或 /rj [类型] [ID] [拒绝原因]\n"
                "示例：/rj movie 123 内容不符合要求\n"
                "类型：movie(求片) 或 content(投稿)"
            )
            return
        
        item_type = parts[1].lower()
        try:
            item_id = int(parts[2])
        except ValueError:
            await message.reply("❌ ID必须是数字")
            return
        
        review_note = " ".join(parts[3:])
        
        if item_type not in ['movie', 'content']:
            await message.reply("❌ 类型必须是 movie 或 content")
            return
        
        # 执行审核
        if item_type == 'movie':
            from app.database.business import review_movie_request
            success = await review_movie_request(item_id, message.from_user.id, "rejected", review_note)
            type_text = "求片"
        else:
            from app.database.business import review_content_submission
            success = await review_content_submission(item_id, message.from_user.id, "rejected", review_note)
            type_text = "投稿"
        
        if success:
            # 发送通知
            from app.utils.panel_utils import send_review_notification
            from app.database.business import get_movie_requests_advanced, get_content_submissions_advanced
            
            # 获取项目信息用于通知
            if item_type == 'movie':
                data = await get_movie_requests_advanced(offset=0, limit=1000)
                item = next((r for r in data['items'] if r.id == item_id), None)
            else:
                data = await get_content_submissions_advanced(offset=0, limit=1000)
                item = next((s for s in data['items'] if s.id == item_id), None)
            
            if item:
                # 通过category_id获取分类名称
                from app.database.business import get_movie_category_by_id
                category = await get_movie_category_by_id(item.category_id) if item.category_id else None
                category_name = category.name if category else None
                
                if item_type == 'movie':
                    await send_review_notification(
                        message.bot, item.user_id, item_type, item.title, "rejected", review_note,
                        file_id=item.file_id, item_content=item.description, item_id=item.id,
                        category_name=category_name
                    )
                else:
                    await send_review_notification(
                        message.bot, item.user_id, item_type, item.title, "rejected", review_note,
                        file_id=item.file_id, item_content=item.content, item_id=item.id,
                        category_name=category_name
                    )
            
            await message.reply(f"❌ 已拒绝{type_text} #{item_id}\n💬 原因：{review_note}")
        else:
            await message.reply(f"❌ 操作失败，请检查{type_text}ID是否正确")
            
    except Exception as e:
        logger.error(f"命令行审核失败: {e}")
        await message.reply("❌ 审核失败，请稍后重试")


# 原有的投稿相关函数已被配置类统一处理，删除重复代码