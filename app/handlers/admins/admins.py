from aiogram import types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from app.database.admin import (
    get_count_of_users,
    get_user_data,
    get_all_users_id,
    remove_user,
)
from app.buttons.admin import admin_panel_kb
from app.utils.states import Wait
from app.database.users import set_role, get_role
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN, ROLE_USER
from app.utils.commands_catalog import build_commands_help
from app.database.business import (
    get_all_feedback_list, reply_user_feedback, get_pending_movie_requests,
    get_pending_content_submissions, review_movie_request, review_content_submission
)
from app.buttons.users import admin_review_center_kb, back_to_main_kb
from app.utils.message_utils import safe_edit_message
from app.database.business import is_feature_enabled
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.time_utils import humanize_time, get_status_text
import re

admins_router = Router()


@admins_router.message(Command("panel"))
async def ShowPanel(msg: types.Message):
    # 检查管理员面板开关
    if not await is_feature_enabled("system_enabled"):
        await msg.reply("❌ 系统维护中，暂时无法使用")
        return
    
    if not await is_feature_enabled("admin_panel_enabled"):
        await msg.reply("❌ 管理员面板已关闭")
        return
    
    role = await get_role(msg.from_user.id)
    admin_photo = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"
    admin_text = f"🛡️ 管理员面板\n\n👤 用户角色：{role}\n\n欢迎使用管理员功能，请选择下方按钮进行操作。"
    
    await msg.bot.send_photo(
        chat_id=msg.from_user.id,
        photo=admin_photo,
        caption=admin_text,
        reply_markup=admin_panel_kb
    )


# 面板回调：统计
@admins_router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(cb: types.CallbackQuery):
    users_len = await get_count_of_users()
    # 使用安全编辑函数
    await safe_edit_message(
        cb.message,
        caption=f"📊 <b>用户统计</b>\n\n当前用户总数：{users_len}\n\n点击下方按钮查看更多功能。",
        text=f"当前用户总数：{users_len}",
        reply_markup=admin_panel_kb
    )
    await cb.answer()


# 面板回调：查询提示
@admins_router.callback_query(F.data == "admin_query_user")
async def cb_admin_query_tip(cb: types.CallbackQuery):
    query_text = "🔎 <b>查询用户</b>\n\n请使用命令：/info [chat_id]\n\n示例：/info 123456789"
    try:
        if cb.message.photo:
            await cb.message.edit_caption(caption=query_text, reply_markup=admin_panel_kb)
        else:
            await cb.message.edit_text(query_text, reply_markup=admin_panel_kb)
    except Exception as e:
        # 忽略消息未修改的错误
        if "message is not modified" not in str(e):
            logger.error(f"编辑消息失败: {e}")
    await cb.answer()


# 面板回调：群发公告指引
@admins_router.callback_query(F.data == "admin_announce")
async def cb_admin_announce_tip(cb: types.CallbackQuery, state: FSMContext):
    announce_text = "📢 <b>群发公告</b>\n\n请发送要群发给所有用户的消息（任意类型）\n\n支持文本、图片、视频等各种消息类型。"
    await safe_edit_message(cb.message, caption=announce_text, text=announce_text, reply_markup=admin_panel_kb)
    await state.set_state(Wait.waitAnnounce)
    await cb.answer()


# 面板回调：清理封禁用户（懒方式：实际在群发时自动移除）
@admins_router.callback_query(F.data == "admin_cleanup")
async def cb_admin_cleanup(cb: types.CallbackQuery):
    cleanup_text = "🧹 <b>清理封禁用户</b>\n\n清理功能在群发时自动进行：无法接收的用户会被移除。\n\n这是一个自动化过程，无需手动操作。"
    await safe_edit_message(cb.message, caption=cleanup_text, text=cleanup_text, reply_markup=admin_panel_kb)
    await cb.answer()


# 显示管理员命令
@admins_router.message(Command("commands"))
async def ShowCommands(msg: types.Message):
    role = await get_role(msg.from_user.id)
    await msg.bot.send_message(msg.from_user.id, build_commands_help(role))


# 获取用户总数
@admins_router.message(Command("users"))
async def GetCountOfUsers(msg: types.Message):
    users_len = await get_count_of_users()
    await msg.bot.send_message(msg.from_user.id, "用户总数：" + str(users_len))


# 查询指定用户
@admins_router.message(Command("info"))
async def GetUserData(msg: types.Message):
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.bot.send_message(msg.from_user.id, "用法：/info [chat_id]")
        return
    chat_id = parts[1]

    current_user = await get_user_data(int(chat_id))

    if not current_user:
        await msg.bot.send_message(msg.from_user.id, "未找到该用户")
        return

    message = f"""
<b>用户名：</b> {current_user.username}
<b>昵称：</b> {current_user.full_name}
<b>聊天ID：</b> {current_user.chat_id}
<b>创建时间：</b> {current_user.created_at.strftime("%Y-%m-%d %H:%M:%S")}
<b>最后活跃：</b> {current_user.last_activity_at.strftime("%Y-%m-%d %H:%M:%S")}
    """

    await msg.bot.send_message(msg.from_user.id, message)


# 群发公告
@admins_router.message(Command("announce"))
async def Announce(msg: types.Message, state: FSMContext):
    await msg.bot.send_message(msg.from_user.id, "请发送要群发给所有用户的消息（任意类型）")
    await state.set_state(Wait.waitAnnounce)


@admins_router.message(StateFilter(Wait.waitAnnounce))
async def ConfirmAnnounce(msg: types.Message, state: FSMContext):
    all_users_id = await get_all_users_id()

    users_len = len(all_users_id)

    active_users = 0
    inactive_users = 0

    await msg.reply(f"开始向 {users_len} 位用户群发…")

    for chat_id in all_users_id:
        try:
            await msg.bot.copy_message(chat_id, msg.from_user.id, msg.message_id)
            active_users += 1
        except Exception as e:
            inactive_users += 1
            remove_user(chat_id)

    await msg.bot.send_message(
        msg.from_user.id,
        f"<b>发送完成</b>\n💚成功：{active_users}\n💔已移除：{inactive_users}",
    )
    await state.clear()


@admins_router.message(StateFilter(Wait.waitReviewNote))
async def process_review_note(msg: types.Message, state: FSMContext):
    """处理审核留言"""
    review_note = msg.text
    data = await state.get_data()
    
    review_type = data.get('review_type')
    review_id = data.get('review_id')
    review_action = data.get('review_action')
    
    if review_type == 'movie':
        success = await review_movie_request(review_id, msg.from_user.id, review_action, review_note)
        item_type = "求片"
    elif review_type == 'content':
        success = await review_content_submission(review_id, msg.from_user.id, review_action, review_note)
        item_type = "投稿"
    else:
        await msg.reply("❌ 审核类型错误")
        await state.clear()
        return
    
    if success:
        action_text = "通过" if review_action == "approved" else "拒绝"
        await msg.reply(f"✅ 已{action_text}{item_type} #{review_id}\n💬 留言：{review_note}")
        
        # 返回审核页面
        if review_type == 'movie':
            # 创建一个临时的callback query对象来重用现有函数
            from types import SimpleNamespace
            fake_cb = SimpleNamespace()
            fake_cb.message = msg
            fake_cb.from_user = msg.from_user
            fake_cb.answer = lambda: None
            await cb_admin_review_movie(fake_cb)
        else:
            from types import SimpleNamespace
            fake_cb = SimpleNamespace()
            fake_cb.message = msg
            fake_cb.from_user = msg.from_user
            fake_cb.answer = lambda: None
            await cb_admin_review_content(fake_cb)
    else:
        await msg.reply("❌ 审核失败，请重试")
    
    await state.clear()


# 仅超管：升为管理员
@admins_router.message(Command("promote"))
async def PromoteToAdmin(msg: types.Message):
    caller_role = await get_role(msg.from_user.id)
    if caller_role != ROLE_SUPERADMIN:
        await msg.bot.send_message(msg.from_user.id, "仅超管可执行此操作。")
        return

    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.bot.send_message(msg.from_user.id, "用法：/promote [chat_id]")
        return
    target_id = int(parts[1])
    ok = await set_role(target_id, ROLE_ADMIN)
    if ok:
        await msg.bot.send_message(msg.from_user.id, f"已将 {target_id} 设为管理员。")
    else:
        await msg.bot.send_message(msg.from_user.id, "操作失败，请稍后重试。")


# ==================== 管理员专用功能 ====================

@admins_router.callback_query(F.data == "admin_feedback_browse")
async def cb_admin_feedback_browse(cb: types.CallbackQuery):
    """反馈浏览"""
    feedbacks = await get_all_feedback_list()
    
    if not feedbacks:
        await cb.message.edit_caption(
            caption="👀 <b>反馈浏览</b>\n\n暂无用户反馈。",
            reply_markup=back_to_main_kb
        )
    else:
        text = "👀 <b>反馈浏览</b>\n\n"
        pending_count = sum(1 for f in feedbacks if f.status == "pending")
        text += f"📊 总计 {len(feedbacks)} 条反馈，{pending_count} 条待处理\n\n"
        
        for i, feedback in enumerate(feedbacks[:15], 1):  # 最多显示15条
            status_emoji = {
                "pending": "⏳",
                "processing": "🔄", 
                "resolved": "✅"
            }.get(feedback.status, "❓")
            
            type_emoji = {
                "bug": "🐛",
                "suggestion": "💡",
                "complaint": "😤",
                "other": "❓"
            }.get(feedback.feedback_type, "❓")
            
            text += f"{i}. {type_emoji} {status_emoji} ID:{feedback.id}\n"
            text += f"   用户:{feedback.user_id} | {feedback.created_at.strftime('%m-%d %H:%M')}\n"
            text += f"   内容:{feedback.content[:40]}{'...' if len(feedback.content) > 40 else ''}\n\n"
        
        if len(feedbacks) > 15:
            text += f"... 还有 {len(feedbacks) - 15} 条记录\n\n"
        
        text += "💡 使用 /reply [反馈ID] [回复内容] 来回复反馈"
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=back_to_main_kb
        )
    
    await cb.answer()


@admins_router.callback_query(F.data == "admin_review_center")
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


@admins_router.callback_query(F.data == "admin_review_movie")
async def cb_admin_review_movie(cb: types.CallbackQuery):
    """求片审核"""
    await cb_admin_review_movie_page(cb, 1)


@admins_router.callback_query(F.data.startswith("movie_review_page_"))
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
            reply_markup=admin_review_detail_kb
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
        
        text += f"{i}. 【{category_name}】{req.title}\n"
        text += f"   🆔 ID:{req.id} | 👤 用户:{req.user_id} | 📅 {humanize_time(req.created_at)} | 🏷️ {status_text}\n"
        
        if req.description:
            desc_preview = req.description[:60] + ('...' if len(req.description) > 60 else '')
            text += f"   📝 {desc_preview}\n"
        
        # 媒体链接
        if hasattr(req, 'file_id') and req.file_id:
            text += f"   📎 [查看附件](https://t.me/c/{req.file_id})\n"
        
        text += "\n"
    
    text += "💡 使用下方按钮快速审核，或输入命令：\n"
    text += "/approve_movie [ID] - 通过 | /reject_movie [ID] - 拒绝"
    
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


@admins_router.callback_query(F.data.startswith("review_movie_detail_"))
async def cb_review_movie_detail(cb: types.CallbackQuery):
    """查看求片详情"""
    request_id = int(cb.data.split("_")[-1])
    
    # 获取求片详情
    requests = await get_pending_movie_requests()
    request = next((r for r in requests if r.id == request_id), None)
    
    if not request:
        await cb.answer("❌ 求片请求不存在或已被处理", show_alert=True)
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


@admins_router.callback_query(F.data.startswith("approve_movie_"))
async def cb_approve_movie(cb: types.CallbackQuery):
    """快速通过求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await review_movie_request(request_id, cb.from_user.id, "approved")
    
    if success:
        await cb.answer(f"✅ 已通过求片 {request_id}", show_alert=True)
        # 刷新审核列表
        await cb_admin_review_movie(cb)
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确", show_alert=True)


@admins_router.callback_query(F.data.startswith("reject_movie_"))
async def cb_reject_movie(cb: types.CallbackQuery):
    """快速拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    success = await review_movie_request(request_id, cb.from_user.id, "rejected")
    
    if success:
        await cb.answer(f"❌ 已拒绝求片 {request_id}", show_alert=True)
        # 刷新审核列表
        await cb_admin_review_movie(cb)
    else:
        await cb.answer("❌ 操作失败，请检查求片ID是否正确", show_alert=True)


@admins_router.callback_query(F.data.startswith("approve_movie_note_"))
async def cb_approve_movie_note(cb: types.CallbackQuery, state: FSMContext):
    """留言通过求片"""
    request_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'movie',
        'review_id': request_id,
        'review_action': 'approved'
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


@admins_router.callback_query(F.data.startswith("reject_movie_note_"))
async def cb_reject_movie_note(cb: types.CallbackQuery, state: FSMContext):
    """留言拒绝求片"""
    request_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'movie',
        'review_id': request_id,
        'review_action': 'rejected'
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


@admins_router.callback_query(F.data == "admin_review_content")
async def cb_admin_review_content(cb: types.CallbackQuery):
    """投稿审核"""
    await cb_admin_review_content_page(cb, 1)


@admins_router.callback_query(F.data.startswith("content_review_page_"))
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
            reply_markup=admin_review_detail_kb
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
        
        text += f"{i}. 【{category_name}】{sub.title}\n"
        text += f"   🆔 ID:{sub.id} | 👤 用户:{sub.user_id} | 📅 {humanize_time(sub.created_at)} | 🏷️ {status_text}\n"
        
        content_preview = sub.content[:60] + ('...' if len(sub.content) > 60 else '')
        text += f"   📄 {content_preview}\n"
        
        # 媒体链接
        if sub.file_id:
            text += f"   📎 [查看附件](https://t.me/c/{sub.file_id})\n"
        
        text += "\n"
    
    text += "💡 使用下方按钮快速审核，或输入命令：\n"
    text += "/approve_content [ID] - 通过 | /reject_content [ID] - 拒绝"
    
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





@admins_router.callback_query(F.data.startswith("review_content_detail_"))
async def cb_review_content_detail(cb: types.CallbackQuery):
    """查看投稿详情"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 获取投稿详情
    submissions = await get_pending_content_submissions()
    submission = next((s for s in submissions if s.id == submission_id), None)
    
    if not submission:
        await cb.answer("❌ 投稿不存在或已被处理", show_alert=True)
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


@admins_router.callback_query(F.data.startswith("approve_content_"))
async def cb_approve_content(cb: types.CallbackQuery):
    """快速通过投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    success = await review_content_submission(submission_id, cb.from_user.id, "approved")
    
    if success:
        await cb.answer(f"✅ 已通过投稿 {submission_id}", show_alert=True)
        # 刷新审核列表
        await cb_admin_review_content(cb)
    else:
        await cb.answer("❌ 操作失败，请检查投稿ID是否正确", show_alert=True)


@admins_router.callback_query(F.data.startswith("reject_content_"))
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


@admins_router.callback_query(F.data.startswith("approve_content_note_"))
async def cb_approve_content_note(cb: types.CallbackQuery, state: FSMContext):
    """留言通过投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'content',
        'review_id': submission_id,
        'review_action': 'approved'
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


@admins_router.callback_query(F.data.startswith("reject_content_note_"))
async def cb_reject_content_note(cb: types.CallbackQuery, state: FSMContext):
    """留言拒绝投稿"""
    submission_id = int(cb.data.split("_")[-1])
    
    # 保存审核信息到状态
    await state.update_data({
        'review_type': 'content',
        'review_id': submission_id,
        'review_action': 'rejected'
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


# 管理员命令：回复反馈
@admins_router.message(Command("reply"))
async def admin_reply_feedback(msg: types.Message):
    """回复用户反馈"""
    parts = msg.text.strip().split(maxsplit=2)
    if len(parts) < 3:
        await msg.reply("用法：/reply [反馈ID] [回复内容]")
        return
    
    try:
        feedback_id = int(parts[1])
        reply_content = parts[2]
    except ValueError:
        await msg.reply("反馈ID必须是数字")
        return
    
    success = await reply_user_feedback(feedback_id, msg.from_user.id, reply_content)
    
    if success:
        await msg.reply(f"✅ 已回复反馈 {feedback_id}")
    else:
        await msg.reply("❌ 回复失败，请检查反馈ID是否正确")


# 管理员命令：审核求片
@admins_router.message(Command("approve_movie"))
async def admin_approve_movie(msg: types.Message):
    """通过求片命令"""
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("用法：/approve_movie [ID]\n示例：/approve_movie 1")
        return
    
    request_id = int(parts[1])
    success = await review_movie_request(request_id, msg.from_user.id, "approved")
    
    if success:
        await msg.reply(f"✅ 已通过求片 {request_id}")
    else:
        await msg.reply("❌ 操作失败，请检查求片ID是否正确")


@admins_router.message(F.text.regexp(r'^/approve_movie_\d+$'))
async def admin_approve_movie_dynamic(msg: types.Message):
    """动态通过求片命令"""
    match = re.search(r'/approve_movie_(\d+)', msg.text)
    if not match:
        return
    
    request_id = int(match.group(1))
    success = await review_movie_request(request_id, msg.from_user.id, "approved")
    
    if success:
        await msg.reply(f"✅ 已通过求片 {request_id}")
    else:
        await msg.reply("❌ 操作失败，请检查求片ID是否正确")


@admins_router.message(Command("reject_movie"))
async def admin_reject_movie(msg: types.Message):
    """拒绝求片命令"""
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("用法：/reject_movie [ID]\n示例：/reject_movie 1")
        return
    
    request_id = int(parts[1])
    success = await review_movie_request(request_id, msg.from_user.id, "rejected")
    
    if success:
        await msg.reply(f"❌ 已拒绝求片 {request_id}")
    else:
        await msg.reply("❌ 操作失败，请检查求片ID是否正确")


@admins_router.message(F.text.regexp(r'^/reject_movie_\d+$'))
async def admin_reject_movie_dynamic(msg: types.Message):
    """动态拒绝求片命令"""
    match = re.search(r'/reject_movie_(\d+)', msg.text)
    if not match:
        return
    
    request_id = int(match.group(1))
    success = await review_movie_request(request_id, msg.from_user.id, "rejected")
    
    if success:
        await msg.reply(f"❌ 已拒绝求片 {request_id}")
    else:
        await msg.reply("❌ 操作失败，请检查求片ID是否正确")


# 管理员命令：审核投稿
@admins_router.message(Command("approve_content"))
async def admin_approve_content(msg: types.Message):
    """通过投稿命令"""
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("用法：/approve_content [ID]\n示例：/approve_content 1")
        return
    
    submission_id = int(parts[1])
    success = await review_content_submission(submission_id, msg.from_user.id, "approved")
    
    if success:
        await msg.reply(f"✅ 已通过投稿 {submission_id}")
    else:
        await msg.reply("❌ 操作失败，请检查投稿ID是否正确")


@admins_router.message(F.text.regexp(r'^/approve_content_\d+$'))
async def admin_approve_content_dynamic(msg: types.Message):
    """动态通过投稿命令"""
    match = re.search(r'/approve_content_(\d+)', msg.text)
    if not match:
        return
    
    submission_id = int(match.group(1))
    success = await review_content_submission(submission_id, msg.from_user.id, "approved")
    
    if success:
        await msg.reply(f"✅ 已通过投稿 {submission_id}")
    else:
        await msg.reply("❌ 操作失败，请检查投稿ID是否正确")


@admins_router.message(Command("reject_content"))
async def admin_reject_content(msg: types.Message):
    """拒绝投稿命令"""
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("用法：/reject_content [ID]\n示例：/reject_content 1")
        return
    
    submission_id = int(parts[1])
    success = await review_content_submission(submission_id, msg.from_user.id, "rejected")
    
    if success:
        await msg.reply(f"❌ 已拒绝投稿 {submission_id}")
    else:
        await msg.reply("❌ 操作失败，请检查投稿ID是否正确")


@admins_router.message(F.text.regexp(r'^/reject_content_\d+$'))
async def admin_reject_content_dynamic(msg: types.Message):
    """动态拒绝投稿命令"""
    match = re.search(r'/reject_content_(\d+)', msg.text)
    if not match:
        return
    
    submission_id = int(match.group(1))
    success = await review_content_submission(submission_id, msg.from_user.id, "rejected")
    
    if success:
        await msg.reply(f"❌ 已拒绝投稿 {submission_id}")
    else:
        await msg.reply("❌ 操作失败，请检查投稿ID是否正确")


# 仅超管：取消管理员
@admins_router.message(Command("demote"))
async def DemoteFromAdmin(msg: types.Message):
    caller_role = await get_role(msg.from_user.id)
    if caller_role != ROLE_SUPERADMIN:
        await msg.bot.send_message(msg.from_user.id, "仅超管可执行此操作。")
        return

    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.bot.send_message(msg.from_user.id, "用法：/demote [chat_id]")
        return
    target_id = int(parts[1])
    ok = await set_role(target_id, ROLE_USER)
    if ok:
        await msg.bot.send_message(msg.from_user.id, f"已将 {target_id} 设为普通用户。")
    else:
        await msg.bot.send_message(msg.from_user.id, "操作失败，请稍后重试。")
