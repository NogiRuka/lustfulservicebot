from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import create_content_submission, get_user_content_submissions, get_all_movie_categories, is_feature_enabled
from app.buttons.users import content_center_kb, content_input_kb, back_to_main_kb
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.panel_utils import create_content_submit_text

content_router = Router()


@content_router.callback_query(F.data == "content_center")
async def cb_content_center(cb: types.CallbackQuery):
    """内容投稿中心"""
    # 检查系统总开关和投稿功能开关
    if not await is_feature_enabled("system_enabled"):
        await cb.answer("❌ 系统维护中，暂时无法使用", show_alert=True)
        return
    
    if not await is_feature_enabled("content_submit_enabled"):
        await cb.answer("❌ 内容投稿功能已关闭", show_alert=True)
        return
    
    await cb.message.edit_caption(
        caption="📝 <b>内容投稿中心</b>\n\n请选择您需要的功能：",
        reply_markup=content_center_kb
    )
    await cb.answer()


@content_router.callback_query(F.data == "content_submit_new")
async def cb_content_submit_new(cb: types.CallbackQuery, state: FSMContext):
    """开始投稿 - 选择类型"""
    # 检查功能开关
    if not await is_feature_enabled("system_enabled") or not await is_feature_enabled("content_submit_enabled"):
        await cb.answer("❌ 投稿功能暂时不可用", show_alert=True)
        return
    
    await state.clear()
    
    # 获取可用的类型
    categories = await get_all_movie_categories(active_only=True)
    if not categories:
        await cb.message.edit_caption(
            caption="❌ 暂无可用的内容类型，请联系管理员。",
            reply_markup=back_to_main_kb
        )
        await cb.answer()
        return
    
    # 创建类型选择键盘
    keyboard = []
    for category in categories:
        keyboard.append([types.InlineKeyboardButton(
            text=f"📂 {category.name}",
            callback_data=f"select_content_category_{category.id}"
        )])
    
    # 添加通用内容选项
    keyboard.append([types.InlineKeyboardButton(
        text="📄 通用内容（无分类）",
        callback_data="select_content_category_0"
    )])
    
    keyboard.append([types.InlineKeyboardButton(
        text="🔙 返回",
        callback_data="content_center"
    )])
    
    category_kb = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await cb.message.edit_caption(
        caption="📝 <b>开始投稿</b>\n\n请选择内容类型：",
        reply_markup=category_kb
    )
    # 保存消息ID用于后续编辑
    await state.update_data(message_id=cb.message.message_id)
    await cb.answer()


@content_router.callback_query(F.data.startswith("select_content_category_"))
async def cb_select_content_category(cb: types.CallbackQuery, state: FSMContext):
    """选择投稿类型"""
    category_id = int(cb.data.split("_")[-1])
    
    # 获取类型信息
    category_name = "通用内容"
    if category_id > 0:
        categories = await get_all_movie_categories(active_only=True)
        category = next((c for c in categories if c.id == category_id), None)
        if category:
            category_name = category.name
        else:
            await cb.message.edit_caption(
                caption="❌ 类型不存在，请重新选择。",
                reply_markup=back_to_main_kb
            )
            await cb.answer()
            return
    
    # 保存选择的类型
    await state.update_data(
        category_id=category_id if category_id > 0 else None,
        category_name=category_name
    )
    
    await cb.message.edit_caption(
        caption=create_content_submit_text("input_title", category_name),
        reply_markup=content_input_kb,
        parse_mode="Markdown"
    )
    await state.set_state(Wait.waitContentTitle)
    await cb.answer()


@content_router.message(StateFilter(Wait.waitContentTitle))
async def process_content_title(msg: types.Message, state: FSMContext):
    """处理投稿标题"""
    logger.debug(f"收到投稿标题输入: {msg.text}, 用户: {msg.from_user.id}, 当前状态: {await state.get_state()}")
    
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
            caption=create_content_submit_text("input_content", data.get('category_name'), title),
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center")],
                    [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
    
    await state.set_state(Wait.waitContentBody)


@content_router.message(StateFilter(Wait.waitContentBody))
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
    
    # 保存内容信息到状态
    await state.update_data(content=content, file_id=file_id, file_info=file_info)
    
    # 显示确认页面
    content_preview = content[:100] + ('...' if len(content) > 100 else '')
    # 获取类型信息
    category_name = data.get('category_name', '通用内容')
    
    confirm_text = (
        f"📋 <b>确认投稿信息</b>\n\n"
        f"📂 类型：【{category_name}】\n"
        f"📝 标题：{title}\n"
        f"📄 内容：{content_preview}{file_info}\n\n"
        f"请确认以上信息是否正确？"
    )
    
    confirm_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ 确认提交", callback_data="confirm_content_submit"),
                types.InlineKeyboardButton(text="✏️ 重新编辑", callback_data="edit_content_body")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
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


@content_router.callback_query(F.data == "edit_content_body")
async def cb_edit_content_body(cb: types.CallbackQuery, state: FSMContext):
    """重新编辑投稿内容"""
    data = await state.get_data()
    title = data.get('title', '')
    category_name = data.get('category_name', '通用内容')
    current_content = data.get('content', '')
    current_file_info = data.get('file_info', '')
    
    # 显示当前信息和编辑提示
    edit_text = (
        f"✏️ <b>重新编辑投稿内容</b>\n\n"
        f"📂 类型：【{category_name}】\n"
        f"📝 标题：{title}\n"
    )
    
    if current_content:
        content_preview = current_content[:100] + ('...' if len(current_content) > 100 else '')
        edit_text += f"📄 当前内容：{content_preview}{current_file_info}\n\n"
    else:
        edit_text += f"📄 当前内容：无\n\n"
    
    edit_text += "请输入新的投稿内容或发送图片/文件："
    
    await cb.message.edit_caption(
        caption=edit_text,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center")],
                [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ]
        )
    )
    await state.set_state(Wait.waitContentBody)
    await cb.answer()


@content_router.callback_query(F.data == "confirm_content_submit")
async def cb_confirm_content_submit(cb: types.CallbackQuery, state: FSMContext):
    """确认提交投稿"""
    data = await state.get_data()
    title = data.get('title', '')
    content = data.get('content', '')
    file_id = data.get('file_id')
    file_info = data.get('file_info', '')
    category_id = data.get('category_id')
    category_name = data.get('category_name', '通用内容')
    
    success = await create_content_submission(cb.from_user.id, title, content, file_id, category_id)
    
    # 显示最终结果
    if success:
        content_preview = content[:50] + ('...' if len(content) > 50 else '')
        result_text = f"✅ <b>投稿提交成功！</b>\n\n📂 类型：【{category_name}】\n📝 标题：{title}\n📄 内容：{content_preview}{file_info}\n\n您的投稿已提交，等待管理员审核。"
        
        # 成功页面按钮
        success_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="📝 继续投稿", callback_data="content_submit_new"),
                    types.InlineKeyboardButton(text="📋 我的投稿", callback_data="content_submit_my")
                ],
                [
                    types.InlineKeyboardButton(text="⬅️ 返回投稿中心", callback_data="content_center"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                ]
            ]
        )
        reply_markup = success_kb
    else:
        result_text = "❌ 提交失败，请稍后重试。"
        reply_markup = back_to_main_kb
    
    await cb.message.edit_caption(
        caption=result_text,
        reply_markup=reply_markup
    )
    
    await state.clear()
    await cb.answer()


@content_router.callback_query(F.data == "content_submit_my")
async def cb_content_submit_my(cb: types.CallbackQuery):
    """我的投稿"""
    await cb_content_submit_my_page(cb, 1)


@content_router.callback_query(F.data.startswith("my_content_page_"))
async def cb_content_submit_my_page(cb: types.CallbackQuery, page: int = None):
    """我的投稿分页"""
    # 提取页码
    if page is None:
        page = extract_page_from_callback(cb.data, "my_content")
    
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
        await cb.answer()
        return
    
    paginator = Paginator(submissions, page_size=5)
    page_info = paginator.get_page_info(page)
    page_items = paginator.get_page_items(page)
    
    # 构建页面内容
    text = format_page_header("📋 <b>我的投稿</b>", page_info)
    
    start_num = (page - 1) * paginator.page_size + 1
    for i, sub in enumerate(page_items, start_num):
        status_emoji = {
            "pending": "⏳",
            "approved": "✅", 
            "rejected": "❌"
        }.get(sub.status, "❓")
        
        # 使用中文状态和人性化时间
        status_text = get_status_text(sub.status)
        time_text = humanize_time(sub.created_at)
        
        # 美化的卡片式布局
        text += f"┌─ {i}. {status_emoji} <b>{sub.title}</b>\n"
        text += f"├ 🏷️ 状态：<code>{status_text}</code>\n"
        text += f"├ ⏰ 时间：<i>{time_text}</i>\n"
        
        # 显示类型信息（如果有）
        if hasattr(sub, 'category') and sub.category:
            text += f"├ 📂 类型：{sub.category.name}\n"
        
        # 显示内容预览（限制长度）
        if hasattr(sub, 'content') and sub.content:
            content_preview = sub.content[:50] + ('...' if len(sub.content) > 50 else '')
            text += f"├ 📄 内容：{content_preview}\n"
        
        # 显示审核备注（如果有）
        if hasattr(sub, 'review_note') and sub.review_note:
            note_preview = sub.review_note[:60] + ('...' if len(sub.review_note) > 60 else '')
            text += f"└ 💬 <b>管理员备注</b>：<blockquote>{note_preview}</blockquote>\n"
        else:
            text += f"└─────────────────\n"
        
        text += "\n"
    
    # 创建分页键盘
    extra_buttons = [
        [
            types.InlineKeyboardButton(text="📝 继续投稿", callback_data="content_submit_new"),
            types.InlineKeyboardButton(text="🔄 刷新", callback_data="content_submit_my")
        ],
        [
            types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="content_center"),
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
        ]
    ]
    
    keyboard = paginator.create_pagination_keyboard(
        page, "my_content", extra_buttons
    )
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=keyboard
    )
    await cb.answer()