from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import create_movie_request, get_user_movie_requests, get_all_movie_categories, is_feature_enabled
from app.buttons.users import movie_center_kb, movie_input_kb, back_to_main_kb
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.pagination import Paginator, format_page_header, extract_page_from_callback
from app.utils.panel_utils import create_movie_request_text

movie_router = Router()


@movie_router.callback_query(F.data == "movie_center")
async def cb_movie_center(cb: types.CallbackQuery):
    """求片中心"""
    # 系统总开关由BotStatusMiddleware统一处理
    
    if not await is_feature_enabled("movie_request_enabled"):
        await cb.answer("❌ 求片功能已关闭", show_alert=True)
        return
    
    await cb.message.edit_caption(
        caption="🎬 <b>求片中心</b>\n\n请选择您需要的功能：",
        reply_markup=movie_center_kb
    )
    await cb.answer()


@movie_router.callback_query(F.data == "movie_request_new")
async def cb_movie_request_new(cb: types.CallbackQuery, state: FSMContext):
    """开始求片 - 选择类型"""
    # 检查求片功能开关
    if not await is_feature_enabled("movie_request_enabled"):
        await cb.answer("❌ 求片功能已关闭", show_alert=True)
        return
    
    await state.clear()
    
    # 获取所有可用的求片类型
    categories = await get_all_movie_categories(active_only=True)
    
    if not categories:
        await cb.message.edit_caption(
            caption="❌ 暂无可用的求片类型，请联系管理员。",
            reply_markup=back_to_main_kb
        )
        await cb.answer()
        return
    
    # 创建类型选择按钮
    category_buttons = []
    for category in categories:
        category_buttons.append([
            types.InlineKeyboardButton(
                text=category.name,
                callback_data=f"select_category_{category.id}"
            )
        ])
    
    # 添加返回按钮
    category_buttons.append([
        types.InlineKeyboardButton(text="⬅️ 返回求片中心", callback_data="movie_center"),
        types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
    ])
    
    category_kb = types.InlineKeyboardMarkup(inline_keyboard=category_buttons)
    
    await cb.message.edit_caption(
        caption="🎬 <b>开始求片</b>\n\n请选择求片类型：",
        reply_markup=category_kb
    )
    
    await cb.answer()


@movie_router.callback_query(F.data.startswith("select_category_"))
async def cb_select_category(cb: types.CallbackQuery, state: FSMContext):
    """选择求片类型后输入片名"""
    category_id = int(cb.data.split("_")[-1])
    
    # 获取类型信息
    from app.database.business import get_movie_category_by_id
    category = await get_movie_category_by_id(category_id)
    
    if not category:
        await cb.answer("❌ 类型不存在", show_alert=True)
        return
    
    # 保存选择的类型
    await state.update_data(message_id=cb.message.message_id, category_id=category_id, category_name=category.name)
    
    await cb.message.edit_caption(
        caption=create_movie_request_text("input_title", category.name),
        reply_markup=back_to_main_kb,
        parse_mode="HTML"
    )
    
    await state.set_state(Wait.waitMovieTitle)
    logger.debug(f"用户 {cb.from_user.id} 选择类型 {category.name}，设置状态为 waitMovieTitle")
    await cb.answer()


@movie_router.message(StateFilter(Wait.waitMovieTitle))
async def process_movie_title(msg: types.Message, state: FSMContext):
    """处理片名输入"""
    logger.debug(f"收到片名输入: {msg.text}, 用户: {msg.from_user.id}, 当前状态: {await state.get_state()}")
    
    title = msg.text.strip()
    
    if not title:
        await msg.reply("片名不能为空，请重新输入：")
        return
    
    # 获取状态数据
    data = await state.get_data()
    category_name = data.get('category_name', '未知类型')
    
    # 保存片名
    await state.update_data(title=title)
    
    # 删除用户输入的消息
    try:
        await msg.delete()
    except:
        pass
    
    # 编辑原消息显示下一步
    data = await state.get_data()
    message_id = data.get('message_id')
    
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.from_user.id,
            message_id=message_id,
            caption=create_movie_request_text("input_description", category_name, title),
            reply_markup=movie_input_kb,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"编辑消息失败: {e}")
    
    await state.set_state(Wait.waitMovieDescription)


@movie_router.callback_query(F.data == "skip_description")
async def cb_skip_description(cb: types.CallbackQuery, state: FSMContext):
    """跳过描述"""
    data = await state.get_data()
    category_name = data.get('category_name', '未知类型')
    title = data.get('title', '')
    
    # 保存跳过描述的状态
    await state.update_data(description=None, file_info="")
    
    # 显示确认页面
    confirm_text = (
        f"📋 <b>确认求片信息</b>\n\n"
        f"📂 类型：{category_name}\n"
        f"🎬 片名：{title}\n"
        f"📝 描述：无\n\n"
        f"请确认以上信息是否正确？"
    )
    
    confirm_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ 确认提交", callback_data="confirm_movie_submit"),
                types.InlineKeyboardButton(text="✏️ 重新编辑", callback_data="edit_movie_description")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
            ]
        ]
    )
    
    await cb.message.edit_caption(
        caption=confirm_text,
        reply_markup=confirm_kb
    )
    await cb.answer()


@movie_router.message(StateFilter(Wait.waitMovieDescription))
async def process_movie_description(msg: types.Message, state: FSMContext):
    """处理描述输入（支持文本和图片）"""
    data = await state.get_data()
    title = data.get('title', '')
    message_id = data.get('message_id')
    
    # 处理不同类型的输入
    description = None
    file_id = None
    file_info = ""
    
    if msg.text:
        description = msg.text if msg.text.lower() != '跳过' else None
    elif msg.photo:
        description = msg.caption or "[图片描述]"
        file_id = msg.photo[-1].file_id
        file_info = "\n📷 包含图片"
        # await msg.bot.send_photo(chat_id=msg.chat.id, photo=file_id, caption="就是这张😏")
    elif msg.document:
        description = msg.caption or "[文件描述]"
        file_id = msg.document.file_id
        file_info = "\n📎 包含文件"
    elif msg.video:
        description = msg.caption or "[视频描述]"
        file_id = msg.video.file_id
        file_info = "\n🎥 包含视频"
    
    # 删除用户消息
    try:
        await msg.delete()
    except:
        pass
    
    # 保存描述信息到状态
    await state.update_data(description=description, file_id=file_id, file_info=file_info)
    
    # 显示确认页面
    category_name = data.get('category_name', '未知类型')
    desc_text = f"📝 描述：{description}" if description else "📝 描述：无"
    confirm_text = (
        f"📋 <b>确认求片信息</b>\n\n"
        f"📂 类型：{category_name}\n"
        f"🎬 片名：{title}\n"
        f"{desc_text}{file_info}\n\n"
        f"请确认以上信息是否正确？"
    )
    
    confirm_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ 确认提交", callback_data="confirm_movie_submit"),
                types.InlineKeyboardButton(text="✏️ 重新编辑", callback_data="edit_movie_description")
            ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center"),
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


@movie_router.callback_query(F.data == "edit_movie_description")
async def cb_edit_movie_description(cb: types.CallbackQuery, state: FSMContext):
    """重新编辑描述"""
    data = await state.get_data()
    category_name = data.get('category_name', '未知类型')
    title = data.get('title', '')
    current_description = data.get('description')
    
    # 显示当前信息和编辑提示
    edit_text = (
        f"✏️ <b>重新编辑描述</b>\n\n"
        f"📂 类型：{category_name}\n"
        f"🎬 片名：{title}\n"
    )
    
    if current_description:
        edit_text += f"📝 当前描述：{current_description}\n\n"
    else:
        edit_text += f"📝 当前描述：无\n\n"
    
    edit_text += "请输入新的描述（可选）或发送图片："
    
    await cb.message.edit_caption(
        caption=edit_text,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="跳过描述", callback_data="skip_description")],
                [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center"),
                types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ]
        )
    )
    await state.set_state(Wait.waitMovieDescription)
    await cb.answer()


@movie_router.callback_query(F.data == "confirm_movie_submit")
async def cb_confirm_movie_submit(cb: types.CallbackQuery, state: FSMContext):
    """确认提交求片"""
    data = await state.get_data()
    category_id = data.get('category_id')
    category_name = data.get('category_name', '未知类型')
    title = data.get('title', '')
    description = data.get('description')
    file_id = data.get('file_id')
    file_info = data.get('file_info', '')
    
    success = await create_movie_request(cb.from_user.id, category_id, title, description, file_id)
    
    # 显示最终结果
    if success:
        desc_text = f"\n📝 描述：{description}" if description else ""
        result_text = f"✅ <b>求片提交成功！</b>\n\n📂 类型：{category_name}\n🎬 片名：{title}{desc_text}{file_info}\n\n您的求片请求已提交，等待管理员审核。"
        
        # 成功页面按钮
        success_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="🎬 继续求片", callback_data="movie_request_new"),
                    types.InlineKeyboardButton(text="📋 我的求片", callback_data="movie_request_my")
                ],
                [
                    types.InlineKeyboardButton(text="⬅️ 返回求片中心", callback_data="movie_center"),
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


@movie_router.callback_query(F.data == "movie_request_my")
async def cb_movie_request_my(cb: types.CallbackQuery):
    """我的求片"""
    await cb_movie_request_my_page(cb, 1)


@movie_router.callback_query(F.data.startswith("my_movie_page_"))
async def cb_movie_request_my_page(cb: types.CallbackQuery, page: int = None):
    """我的求片分页"""
    # 提取页码
    if page is None:
        page = extract_page_from_callback(cb.data, "my_movie")
    
    requests = await get_user_movie_requests(cb.from_user.id)
    
    if not requests:
        await cb.message.edit_caption(
            caption="📋 <b>我的求片</b>\n\n您还没有提交过求片请求。",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center"),
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ]
            )
        )
        await cb.answer()
        return
    
    paginator = Paginator(requests, page_size=5)
    page_info = paginator.get_page_info(page)
    page_items = paginator.get_page_items(page)
    
    # 构建页面内容
    text = format_page_header("📋 <b>我的求片</b>", page_info)
    
    start_num = (page - 1) * paginator.page_size + 1
    for i, req in enumerate(page_items, start_num):
        status_emoji = {
            "pending": "⏳",
            "approved": "✅", 
            "rejected": "❌"
        }.get(req.status, "❓")
        
        # 使用中文状态和人性化时间
        status_text = get_status_text(req.status)
        time_text = humanize_time(req.created_at)
        
        # 美化的卡片式布局
        text += f"┌─ {i}. {status_emoji} <b>{req.title}</b>\n"
        text += f"├ 🏷️ 状态：<code>{status_text}</code>\n"
        text += f"├ ⏰ 时间：<i>{time_text}</i>\n"
        
        # 显示类型信息（如果有）
        if hasattr(req, 'category') and req.category:
            text += f"├ 📂 类型：{req.category.name}\n"
        
        # 显示描述（如果有，限制长度）
        if hasattr(req, 'description') and req.description:
            desc_preview = req.description[:50] + ('...' if len(req.description) > 50 else '')
            text += f"├ 📝 描述：{desc_preview}\n"
        
        # 显示审核备注（如果有）
        if hasattr(req, 'review_note') and req.review_note:
            note_preview = req.review_note[:60] + ('...' if len(req.review_note) > 60 else '')
            text += f"└ 💬 <b>管理员备注</b>：<blockquote>{note_preview}</blockquote>\n"
        else:
            text += f"└─────────────────\n"
        
        text += "\n"
    
    # 创建分页键盘
    extra_buttons = [
        [
            types.InlineKeyboardButton(text="🎬 继续求片", callback_data="movie_request_new"),
            types.InlineKeyboardButton(text="🔄 刷新", callback_data="movie_request_my")
        ],
        [
            types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center"),
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
        ]
    ]
    
    keyboard = paginator.create_pagination_keyboard(
        page, "my_movie", extra_buttons
    )
    
    await cb.message.edit_caption(
        caption=text,
        reply_markup=keyboard
    )
    await cb.answer()