import asyncio

from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command
from loguru import logger

from app.utils.filters import IsBusyFilter, IsCommand
from app.database.users import get_busy, set_busy, get_user
from app.database.users import get_role
from app.buttons.users import (
    get_main_menu_by_role, movie_center_kb, content_center_kb, 
    feedback_center_kb, other_functions_kb, back_to_main_kb,
    movie_input_kb, content_input_kb, feedback_input_kb,
    admin_review_detail_kb, superadmin_action_kb
)
from app.buttons.panels import get_panel_for_role
from app.database.business import get_server_stats
from app.utils.group_utils import get_group_member_count
from app.utils.commands_catalog import build_commands_help
from app.config.config import GROUP
from app.utils.group_utils import user_in_group_filter
from app.utils.states import Wait
from app.database.business import (
    create_movie_request, get_user_movie_requests, create_content_submission,
    get_user_content_submissions, create_user_feedback, get_user_feedback_list,
    promote_user_to_admin, demote_admin_to_user, get_admin_list
)
from app.buttons.users import superadmin_manage_center_kb
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter


users_router = Router()


# /start：欢迎与菜单
@users_router.message(CommandStart())
async def start(msg: types.Message):
    # 第一步：检查是否是私聊
    if msg.chat.type != 'private':
        # 在群组中给出更明确的提示
        bot_username = (await msg.bot.get_me()).username
        await msg.reply(
            f"👋 你好！请点击 @{bot_username} 或直接私聊我来使用完整功能。\n\n"
            "🔒 为了保护隐私，主要功能仅在私聊中提供。"
        )
        return
    
    # 第二步：检查是否在设置的群组里（如果设置了GROUP）
    if GROUP:
        is_in_group = await user_in_group_filter(msg.bot, msg.from_user.id)
        if not is_in_group:
            await msg.reply(f"❌ 请先加入群组 @{GROUP} 后再使用机器人功能。")
            return
    
    # 第三步：根据用户ID判断权限显示不同的面板
    role = await get_role(msg.from_user.id)
    title, kb = get_panel_for_role(role)
    
    # 发送带图片的欢迎面板
    welcome_photo = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"
    welcome_text = f"🎉 欢迎使用机器人！\n\n👤 用户角色：{role}\n\n{title}"
    
    await msg.bot.send_photo(
        chat_id=msg.from_user.id,
        photo=welcome_photo,
        caption=welcome_text,
        reply_markup=kb
    )


# /menu：按角色显示面板
@users_router.message(Command("menu"))
async def show_menu(msg: types.Message):
    role = await get_role(msg.from_user.id)
    title, kb = get_panel_for_role(role)
    await msg.bot.send_message(msg.from_user.id, title, reply_markup=kb)


# /commands：按角色显示命令目录
@users_router.message(Command("commands"))
async def show_commands(msg: types.Message):
    role = await get_role(msg.from_user.id)
    catalog = build_commands_help(role)
    await msg.bot.send_message(msg.from_user.id, catalog)


# /role：显示当前账号角色（调试用）
@users_router.message(Command("role"))
async def show_role(msg: types.Message):
    role = await get_role(msg.from_user.id)
    await msg.bot.send_message(msg.from_user.id, f"当前角色：{role}")


# /id：显示当前 Telegram 数字ID（调试用）
@users_router.message(Command("id"))
async def show_id(msg: types.Message):
    await msg.bot.send_message(msg.from_user.id, f"你的聊天ID：{msg.from_user.id}")


# 用户按钮回调处理
@users_router.callback_query(F.data == "user_help")
async def cb_user_help(cb: types.CallbackQuery):
    help_text = (
        "📖 <b>帮助信息</b>\n\n"
        "🤖 这是一个多功能机器人\n"
        "💬 发送任意文本，我会回显给你\n"
        "🔧 使用菜单按钮查看更多功能\n\n"
        "如需返回主菜单，请点击下方按钮。"
    )
    
    # 创建返回按钮
    back_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ]
    )
    
    await cb.message.edit_caption(
        caption=help_text,
        reply_markup=back_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "user_profile")
async def cb_user_profile(cb: types.CallbackQuery):
    user = await get_user(cb.from_user.id)
    role = await get_role(cb.from_user.id)
    
    profile_text = (
        f"🙋 <b>我的信息</b>\n\n"
        f"👤 用户名: {cb.from_user.username or '未设置'}\n"
        f"📝 昵称: {cb.from_user.full_name}\n"
        f"🆔 ID: {cb.from_user.id}\n"
        f"🎭 角色: {role}\n\n"
        "如需返回主菜单，请点击下方按钮。"
    )
    
    back_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ]
    )
    
    await cb.message.edit_caption(
        caption=profile_text,
        reply_markup=back_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "user_toggle_busy")
async def cb_user_toggle_busy(cb: types.CallbackQuery):
    current_busy = await get_busy(cb.from_user.id)
    new_busy = not current_busy
    await set_busy(cb.from_user.id, new_busy)
    
    status_text = "忙碌" if new_busy else "空闲"
    toggle_text = (
        f"🔁 <b>状态切换</b>\n\n"
        f"当前状态: {status_text}\n\n"
        "忙碌状态下，机器人将不会处理你的消息。\n\n"
        "如需返回主菜单，请点击下方按钮。"
    )
    
    back_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ]
    )
    
    await cb.message.edit_caption(
        caption=toggle_text,
        reply_markup=back_kb
    )
    await cb.answer(f"状态已切换为: {status_text}")


@users_router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(cb: types.CallbackQuery):
    role = await get_role(cb.from_user.id)
    title, kb = get_panel_for_role(role)
    
    welcome_text = f"🎉 欢迎使用机器人！\n\n👤 用户角色：{role}\n\n{title}"
    welcome_photo = "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true"
    
    # 检查当前消息是否有图片
    if cb.message.photo:
        # 如果有图片，编辑caption
        await cb.message.edit_caption(
            caption=welcome_text,
            reply_markup=kb
        )
    else:
        # 如果没有图片，删除当前消息并发送新的带图片消息
        try:
            await cb.message.delete()
        except:
            pass  # 忽略删除失败的错误
        
        await cb.bot.send_photo(
            chat_id=cb.from_user.id,
            photo=welcome_photo,
            caption=welcome_text,
            reply_markup=kb
        )
    
    await cb.answer()


# ==================== 公共功能模块 ====================

@users_router.callback_query(F.data == "common_my_info")
async def cb_common_my_info(cb: types.CallbackQuery):
    """我的信息"""
    user = await get_user(cb.from_user.id)
    role = await get_role(cb.from_user.id)
    
    info_text = (
        f"🙋 <b>我的信息</b>\n\n"
        f"👤 用户名: {cb.from_user.username or '未设置'}\n"
        f"📝 昵称: {cb.from_user.full_name}\n"
        f"🆔 用户ID: {cb.from_user.id}\n"
        f"🎭 角色: {role}\n"
        f"📅 注册时间: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user else '未知'}\n"
        f"⏰ 最后活跃: {user.last_activity_at.strftime('%Y-%m-%d %H:%M:%S') if user and user.last_activity_at else '未知'}\n\n"
        "如需返回主菜单，请点击下方按钮。"
    )
    
    await cb.message.edit_caption(
        caption=info_text,
        reply_markup=back_to_main_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "common_server_info")
async def cb_common_server_info(cb: types.CallbackQuery):
    """服务器信息"""
    stats = await get_server_stats()
    group_members = await get_group_member_count(cb.bot)
    
    server_text = (
        f"🖥️ <b>服务器信息</b>\n\n"
        f"👥 总用户数: {stats.get('total_users', 0)}\n"
        f"👮 管理员数: {stats.get('total_admins', 0)}\n"
        f"🎬 求片总数: {stats.get('total_requests', 0)}\n"
        f"⏳ 待审求片: {stats.get('pending_requests', 0)}\n"
        f"📝 投稿总数: {stats.get('total_submissions', 0)}\n"
        f"⏳ 待审投稿: {stats.get('pending_submissions', 0)}\n"
        f"💬 反馈总数: {stats.get('total_feedback', 0)}\n"
        f"⏳ 待处理反馈: {stats.get('pending_feedback', 0)}\n"
    )
    
    if group_members > 0:
        server_text += f"🏠 群组成员: {group_members}\n"
    
    server_text += "\n如需返回主菜单，请点击下方按钮。"
    
    await cb.message.edit_caption(
        caption=server_text,
        reply_markup=back_to_main_kb
    )
    await cb.answer()


# ==================== 功能中心导航 ====================

@users_router.callback_query(F.data == "movie_center")
async def cb_movie_center(cb: types.CallbackQuery):
    """求片中心"""
    center_text = (
        f"🎬 <b>求片中心</b>\n\n"
        "欢迎来到求片中心！\n\n"
        "🎬 开始求片 - 提交新的求片请求\n"
        "📋 我的求片 - 查看我的求片记录\n\n"
        "请选择您需要的功能："
    )
    
    await cb.message.edit_caption(
        caption=center_text,
        reply_markup=movie_center_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "content_center")
async def cb_content_center(cb: types.CallbackQuery):
    """内容投稿中心"""
    center_text = (
        f"📝 <b>内容投稿中心</b>\n\n"
        "欢迎来到内容投稿中心！\n\n"
        "📝 开始投稿 - 提交新的内容投稿\n"
        "📋 我的投稿 - 查看我的投稿记录\n\n"
        "请选择您需要的功能："
    )
    
    await cb.message.edit_caption(
        caption=center_text,
        reply_markup=content_center_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "feedback_center")
async def cb_feedback_center(cb: types.CallbackQuery):
    """用户反馈中心"""
    center_text = (
        f"💬 <b>用户反馈中心</b>\n\n"
        "欢迎来到用户反馈中心！\n\n"
        "🐛 Bug反馈 - 报告程序错误\n"
        "💡 建议反馈 - 提出改进建议\n"
        "😤 投诉反馈 - 投诉相关问题\n"
        "❓ 其他反馈 - 其他类型反馈\n"
        "📋 我的反馈 - 查看反馈记录\n\n"
        "请选择反馈类型："
    )
    
    await cb.message.edit_caption(
        caption=center_text,
        reply_markup=feedback_center_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "other_functions")
async def cb_other_functions(cb: types.CallbackQuery):
    """其他功能"""
    functions_text = (
        f"⚙️ <b>其他功能</b>\n\n"
        "这里是一些额外的实用功能：\n\n"
        "🔁 切换忙碌状态 - 控制消息处理\n"
        "📖 帮助信息 - 查看使用帮助\n\n"
        "请选择您需要的功能："
    )
    
    await cb.message.edit_caption(
        caption=functions_text,
        reply_markup=other_functions_kb
    )
    await cb.answer()


# ==================== 求片中心功能 ====================

@users_router.callback_query(F.data == "movie_request_new")
async def cb_movie_request_new(cb: types.CallbackQuery, state: FSMContext):
    """开始求片"""
    await cb.message.edit_caption(
        caption="🎬 <b>开始求片</b>\n\n请输入您想要的片名：",
        reply_markup=movie_input_kb
    )
    # 保存消息ID用于后续编辑
    await state.update_data(message_id=cb.message.message_id)
    await state.set_state(Wait.waitMovieTitle)
    await cb.answer()


@users_router.message(StateFilter(Wait.waitMovieTitle))
async def process_movie_title(msg: types.Message, state: FSMContext):
    """处理片名输入"""
    title = msg.text
    await state.update_data(title=title)
    
    # 删除用户消息
    try:
        await msg.delete()
    except:
        pass
    
    # 获取保存的消息ID并编辑原消息
    data = await state.get_data()
    message_id = data.get('message_id')
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=f"🎬 <b>开始求片</b>\n\n✅ 片名：{title}\n\n📝 请输入详细描述（可选）或发送图片：",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="跳过描述", callback_data="skip_description")],
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
    
    await state.set_state(Wait.waitMovieDescription)


@users_router.callback_query(F.data == "skip_description")
async def cb_skip_description(cb: types.CallbackQuery, state: FSMContext):
    """跳过描述"""
    data = await state.get_data()
    title = data.get('title', '')
    
    success = await create_movie_request(cb.from_user.id, title)
    
    if success:
        await cb.message.edit_caption(
            caption=f"✅ <b>求片提交成功！</b>\n\n片名：{title}\n\n您的求片请求已提交，等待管理员审核。",
            reply_markup=back_to_main_kb
        )
    else:
        await cb.message.edit_caption(
            caption="❌ 提交失败，请稍后重试。",
            reply_markup=back_to_main_kb
        )
    
    await state.clear()
    await cb.answer()


@users_router.message(StateFilter(Wait.waitMovieDescription))
async def process_movie_description(msg: types.Message, state: FSMContext):
    """处理描述输入（支持文本和图片）"""
    data = await state.get_data()
    title = data.get('title', '')
    message_id = data.get('message_id')
    
    # 处理不同类型的输入
    description = None
    file_info = ""
    
    if msg.text:
        description = msg.text if msg.text.lower() != '跳过' else None
    elif msg.photo:
        description = msg.caption or "[图片描述]"
        file_info = "\n📷 包含图片"
    elif msg.document:
        description = msg.caption or "[文件描述]"
        file_info = "\n📎 包含文件"
    
    # 删除用户消息
    try:
        await msg.delete()
    except:
        pass
    
    success = await create_movie_request(msg.from_user.id, title, description)
    
    # 编辑原消息显示结果
    if success:
        desc_text = f"\n📝 描述：{description}" if description else ""
        result_text = f"✅ <b>求片提交成功！</b>\n\n🎬 片名：{title}{desc_text}{file_info}\n\n您的求片请求已提交，等待管理员审核。"
    else:
        result_text = "❌ 提交失败，请稍后重试。"
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=result_text,
            reply_markup=back_to_main_kb
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
    
    await state.clear()


@users_router.callback_query(F.data == "movie_request_my")
async def cb_movie_request_my(cb: types.CallbackQuery):
    """我的求片"""
    requests = await get_user_movie_requests(cb.from_user.id)
    
    if not requests:
        await cb.message.edit_caption(
            caption="📋 <b>我的求片</b>\n\n您还没有提交过求片请求。",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
    else:
        text = "📋 <b>我的求片</b>\n\n"
        for i, req in enumerate(requests[:10], 1):  # 最多显示10条
            status_emoji = {
                "pending": "⏳",
                "approved": "✅", 
                "rejected": "❌"
            }.get(req.status, "❓")
            
            text += f"{i}. {status_emoji} {req.title}\n"
            text += f"   状态：{req.status} | {req.created_at.strftime('%m-%d %H:%M')}\n\n"
        
        if len(requests) > 10:
            text += f"... 还有 {len(requests) - 10} 条记录\n\n"
        
        text += "如需返回上一级或主菜单，请点击下方按钮。"
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
    
    await cb.answer()


# ==================== 内容投稿功能 ====================

@users_router.callback_query(F.data == "content_submit_new")
async def cb_content_submit_new(cb: types.CallbackQuery, state: FSMContext):
    """开始投稿"""
    await cb.message.edit_caption(
        caption="📝 <b>开始投稿</b>\n\n请输入投稿标题：",
        reply_markup=content_input_kb
    )
    # 保存消息ID用于后续编辑
    await state.update_data(message_id=cb.message.message_id)
    await state.set_state(Wait.waitContentTitle)
    await cb.answer()


@users_router.message(StateFilter(Wait.waitContentTitle))
async def process_content_title(msg: types.Message, state: FSMContext):
    """处理投稿标题"""
    title = msg.text
    await state.update_data(title=title)
    
    # 删除用户消息
    try:
        await msg.delete()
    except:
        pass
    
    # 获取保存的消息ID并编辑原消息
    data = await state.get_data()
    message_id = data.get('message_id')
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=f"📝 <b>开始投稿</b>\n\n✅ 标题：{title}\n\n📄 请输入投稿内容或发送图片/文件：",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
    
    await state.set_state(Wait.waitContentBody)


@users_router.message(StateFilter(Wait.waitContentBody))
async def process_content_body(msg: types.Message, state: FSMContext):
    """处理投稿内容（支持文本、图片、文件）"""
    data = await state.get_data()
    title = data.get('title', '')
    message_id = data.get('message_id')
    content = ""
    file_id = None
    file_info = ""
    
    # 处理不同类型的输入
    if msg.text:
        content = msg.text
    elif msg.photo:
        content = msg.caption or "[图片内容]"
        file_id = msg.photo[-1].file_id
        file_info = "\n📷 包含图片"
    elif msg.document:
        content = msg.caption or "[文件内容]"
        file_id = msg.document.file_id
        file_info = "\n📎 包含文件"
    elif msg.video:
        content = msg.caption or "[视频内容]"
        file_id = msg.video.file_id
        file_info = "\n🎥 包含视频"
    
    # 删除用户消息
    try:
        await msg.delete()
    except:
        pass
    
    success = await create_content_submission(msg.from_user.id, title, content, file_id)
    
    # 编辑原消息显示结果
    if success:
        content_preview = content[:50] + ('...' if len(content) > 50 else '')
        result_text = f"✅ <b>投稿提交成功！</b>\n\n📝 标题：{title}\n📄 内容：{content_preview}{file_info}\n\n您的投稿已提交，等待管理员审核。"
    else:
        result_text = "❌ 提交失败，请稍后重试。"
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=result_text,
            reply_markup=back_to_main_kb
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
    
    await state.clear()


@users_router.callback_query(F.data == "content_submit_my")
async def cb_content_submit_my(cb: types.CallbackQuery):
    """我的投稿"""
    submissions = await get_user_content_submissions(cb.from_user.id)
    
    if not submissions:
        await cb.message.edit_caption(
            caption="📋 <b>我的投稿</b>\n\n您还没有提交过投稿。",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
    else:
        text = "📋 <b>我的投稿</b>\n\n"
        for i, sub in enumerate(submissions[:10], 1):  # 最多显示10条
            status_emoji = {
                "pending": "⏳",
                "approved": "✅", 
                "rejected": "❌"
            }.get(sub.status, "❓")
            
            text += f"{i}. {status_emoji} {sub.title}\n"
            text += f"   状态：{sub.status} | {sub.created_at.strftime('%m-%d %H:%M')}\n\n"
        
        if len(submissions) > 10:
            text += f"... 还有 {len(submissions) - 10} 条记录\n\n"
        
        text += "如需返回上一级或主菜单，请点击下方按钮。"
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
    
    await cb.answer()


# ==================== 用户反馈功能 ====================

@users_router.callback_query(F.data.in_(["feedback_bug", "feedback_suggestion", "feedback_complaint", "feedback_other"]))
async def cb_feedback_start(cb: types.CallbackQuery, state: FSMContext):
    """开始反馈"""
    feedback_types = {
        "feedback_bug": "🐛 Bug反馈",
        "feedback_suggestion": "💡 建议反馈", 
        "feedback_complaint": "😤 投诉反馈",
        "feedback_other": "❓ 其他反馈"
    }
    
    feedback_type = cb.data.replace("feedback_", "")
    feedback_name = feedback_types.get(cb.data, "其他反馈")
    
    await state.update_data(feedback_type=feedback_type, message_id=cb.message.message_id)
    
    await cb.message.edit_caption(
        caption=f"{feedback_name}\n\n请详细描述您的反馈内容或发送相关图片：",
        reply_markup=feedback_input_kb
    )
    await state.set_state(Wait.waitFeedbackContent)
    await cb.answer()


@users_router.message(StateFilter(Wait.waitFeedbackContent))
async def process_feedback_content(msg: types.Message, state: FSMContext):
    """处理反馈内容（支持文本和图片）"""
    data = await state.get_data()
    feedback_type = data.get('feedback_type', 'other')
    message_id = data.get('message_id')
    
    # 处理不同类型的输入
    content = ""
    file_info = ""
    
    if msg.text:
        content = msg.text
    elif msg.photo:
        content = msg.caption or "[图片反馈]"
        file_info = "\n📷 包含图片"
    elif msg.document:
        content = msg.caption or "[文件反馈]"
        file_info = "\n📎 包含文件"
    
    # 删除用户消息
    try:
        await msg.delete()
    except:
        pass
    
    success = await create_user_feedback(msg.from_user.id, feedback_type, content)
    
    # 编辑原消息显示结果
    feedback_type_names = {
        "bug": "🐛 Bug反馈",
        "suggestion": "💡 建议反馈",
        "complaint": "😤 投诉反馈",
        "other": "❓ 其他反馈"
    }
    
    if success:
        content_preview = content[:100] + ('...' if len(content) > 100 else '')
        result_text = f"✅ <b>反馈提交成功！</b>\n\n📝 类型：{feedback_type_names.get(feedback_type, feedback_type)}\n💬 内容：{content_preview}{file_info}\n\n感谢您的反馈，我们会尽快处理。"
    else:
        result_text = "❌ 提交失败，请稍后重试。"
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=result_text,
            reply_markup=back_to_main_kb
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
    
    await state.clear()


@users_router.callback_query(F.data == "feedback_my")
async def cb_feedback_my(cb: types.CallbackQuery):
    """我的反馈"""
    feedbacks = await get_user_feedback_list(cb.from_user.id)
    
    if not feedbacks:
        await cb.message.edit_caption(
            caption="📋 <b>我的反馈</b>\n\n您还没有提交过反馈。",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="feedback_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
    else:
        text = "📋 <b>我的反馈</b>\n\n"
        for i, feedback in enumerate(feedbacks[:10], 1):  # 最多显示10条
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
            
            text += f"{i}. {type_emoji} {status_emoji} {feedback.content[:30]}{'...' if len(feedback.content) > 30 else ''}\n"
            text += f"   状态：{feedback.status} | {feedback.created_at.strftime('%m-%d %H:%M')}\n"
            
            if feedback.reply_content:
                text += f"   💬 回复：{feedback.reply_content[:50]}{'...' if len(feedback.reply_content) > 50 else ''}\n"
            
            text += "\n"
        
        if len(feedbacks) > 10:
            text += f"... 还有 {len(feedbacks) - 10} 条记录\n\n"
        
        text += "如需返回上一级或主菜单，请点击下方按钮。"
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="feedback_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
    
    await cb.answer()


# ==================== 超管专用功能 ====================

@users_router.callback_query(F.data == "superadmin_manage_center")
async def cb_superadmin_manage_center(cb: types.CallbackQuery):
    """管理中心"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    admins = await get_admin_list()
    admin_count = len([a for a in admins if a.role == ROLE_ADMIN])
    
    text = "🛡️ <b>管理中心</b>\n\n"
    text += f"👮 当前管理员数量：{admin_count}\n\n"
    text += "请选择管理操作："
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=superadmin_manage_center_kb
    )
    await cb.answer()


@users_router.callback_query(F.data == "superadmin_add_admin")
async def cb_superadmin_add_admin(cb: types.CallbackQuery, state: FSMContext):
    """添加管理员"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    await cb.message.edit_caption(
        caption="➕ <b>添加管理员</b>\n\n请输入要提升为管理员的用户ID：",
        reply_markup=superadmin_action_kb
    )
    # 保存消息ID用于后续编辑
    await state.update_data(message_id=cb.message.message_id)
    await state.set_state(Wait.waitAdminUserId)
    await cb.answer()


@users_router.message(StateFilter(Wait.waitAdminUserId))
async def process_admin_user_id(msg: types.Message, state: FSMContext):
    """处理管理员用户ID输入"""
    data = await state.get_data()
    message_id = data.get('message_id')
    
    try:
        user_id = int(msg.text.strip())
    except ValueError:
        # 删除用户消息
        try:
            await msg.delete()
        except:
            pass
        
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption="❌ 用户ID必须是数字，请重新输入：",
                reply_markup=superadmin_action_kb
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
        return
    
    # 删除用户消息
    try:
        await msg.delete()
    except:
        pass
    
    # 检查用户是否存在
    user = await get_user(user_id)
    if not user:
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption="❌ 用户不存在，请检查用户ID是否正确：",
                reply_markup=superadmin_action_kb
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
        return
    
    # 检查用户当前角色
    current_role = await get_role(user_id)
    
    if current_role == ROLE_ADMIN:
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption="❌ 该用户已经是管理员了。",
                reply_markup=back_to_main_kb
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
        await state.clear()
        return
    elif current_role == ROLE_SUPERADMIN:
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption="❌ 该用户是超管，无需提升。",
                reply_markup=back_to_main_kb
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
        await state.clear()
        return
    
    # 提升为管理员
    success = await promote_user_to_admin(msg.from_user.id, user_id)
    
    if success:
        result_text = f"✅ <b>提升成功！</b>\n\n用户 {user_id} 已被提升为管理员。"
    else:
        result_text = "❌ 提升失败，请稍后重试。"
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=result_text,
            reply_markup=back_to_main_kb
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
    
    await state.clear()


@users_router.callback_query(F.data == "superadmin_my_admins")
async def cb_superadmin_my_admins(cb: types.CallbackQuery):
    """我的管理员"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    admins = await get_admin_list()
    admin_users = [a for a in admins if a.role == ROLE_ADMIN]
    
    if not admin_users:
        await cb.message.edit_caption(
            caption="👥 <b>我的管理员</b>\n\n暂无管理员。",
            reply_markup=superadmin_action_kb
        )
    else:
        text = "👥 <b>我的管理员</b>\n\n"
        for i, admin in enumerate(admin_users, 1):
            text += f"{i}. {admin.full_name} (ID: {admin.chat_id})\n"
            text += f"   用户名: @{admin.username or '未设置'}\n"
            text += f"   注册时间: {admin.created_at.strftime('%Y-%m-%d')}\n\n"
        
        text += "💡 使用 /demote <用户ID> 来取消管理员权限"
        
        await cb.message.edit_caption(
            caption=text,
            reply_markup=superadmin_action_kb
        )
    
    await cb.answer()


@users_router.callback_query(F.data == "superadmin_manual_reply")
async def cb_superadmin_manual_reply(cb: types.CallbackQuery):
    """人工回复"""
    role = await get_role(cb.from_user.id)
    if role != ROLE_SUPERADMIN:
        await cb.answer("❌ 仅超管可访问此功能", show_alert=True)
        return
    
    # 获取待处理的反馈
    feedbacks = await get_all_feedback_list()
    pending_feedbacks = [f for f in feedbacks if f.status == "pending"]
    
    text = "🤖 <b>人工回复</b>\n\n"
    
    if not pending_feedbacks:
        text += "暂无待处理的反馈。"
    else:
        text += f"📊 共有 {len(pending_feedbacks)} 条待处理反馈\n\n"
        
        for i, feedback in enumerate(pending_feedbacks[:5], 1):  # 显示前5条
            type_emoji = {
                "bug": "🐛",
                "suggestion": "💡",
                "complaint": "😤",
                "other": "❓"
            }.get(feedback.feedback_type, "❓")
            
            text += f"{i}. {type_emoji} ID:{feedback.id}\n"
            text += f"   用户:{feedback.user_id}\n"
            text += f"   内容:{feedback.content[:60]}{'...' if len(feedback.content) > 60 else ''}\n\n"
        
        if len(pending_feedbacks) > 5:
            text += f"... 还有 {len(pending_feedbacks) - 5} 条待处理\n\n"
        
        text += "💡 使用 /reply <反馈ID> <回复内容> 进行回复"
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=superadmin_action_kb
    )
    await cb.answer()


# 超管命令：取消管理员
@users_router.message(Command("demote"))
async def superadmin_demote_admin(msg: types.Message):
    """取消管理员权限"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可执行此操作")
        return
    
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("用法：/demote <用户ID>")
        return
    
    user_id = int(parts[1])
    
    # 检查目标用户角色
    target_role = await get_role(user_id)
    if target_role != ROLE_ADMIN:
        await msg.reply("❌ 该用户不是管理员")
        return
    
    success = await demote_admin_to_user(msg.from_user.id, user_id)
    
    if success:
        await msg.reply(f"✅ 已取消用户 {user_id} 的管理员权限")
    else:
        await msg.reply("❌ 操作失败，请稍后重试")


# 普通文本消息：防并发回显
@users_router.message(F.text, IsCommand(), IsBusyFilter())
async def message(msg: types.Message):
    if await get_busy(msg.from_user.id):
        await msg.bot.send_message(msg.from_user.id, "请稍候，我正在处理你的上一个请求…")
        await asyncio.sleep(5)
        return

    try:
        await set_busy(msg.from_user.id, True)
        await msg.bot.send_message(msg.from_user.id, f"你发送了：{msg.text}")
    except Exception as e:
        logger.error(e)
    finally:
        await set_busy(msg.from_user.id, False)


# 处理内联菜单：帮助
@users_router.callback_query(F.data == "user_help")
async def cb_user_help(cb: types.CallbackQuery):
    await cb.message.edit_text(
        "<b>🤖 机器人帮助</b>\n- 发送任意文本，我会回显给你\n- 使用内联菜单查看更多功能",
        reply_markup=main_menu_kb,
    )
    await cb.answer()


# 处理内联菜单：我的信息
@users_router.callback_query(F.data == "user_profile")
async def cb_user_profile(cb: types.CallbackQuery):
    user = await get_user(cb.from_user.id)
    if not user:
        await cb.message.edit_text("未找到你的信息，稍后再试。", reply_markup=main_menu_kb)
    else:
        msg = (
            f"<b>用户名：</b> {user.username}\n"
            f"<b>昵称：</b> {user.full_name}\n"
            f"<b>聊天ID：</b> {user.chat_id}\n"
            f"<b>忙碌状态：</b> {'是' if user.is_busy else '否'}\n"
        )
        await cb.message.edit_text(msg, reply_markup=main_menu_kb)
    await cb.answer()


# 处理内联菜单：切换忙碌
@users_router.callback_query(F.data == "user_toggle_busy")
async def cb_toggle_busy(cb: types.CallbackQuery):
    current = await get_busy(cb.from_user.id)
    await set_busy(cb.from_user.id, not current)
    await cb.message.edit_text(
        f"忙碌状态已设置为：{'是' if not current else '否'}",
        reply_markup=main_menu_kb,
    )
    await cb.answer()
