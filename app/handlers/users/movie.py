from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import create_movie_request, get_user_movie_requests
from app.buttons.users import movie_center_kb, movie_input_kb, back_to_main_kb

movie_router = Router()


@movie_router.callback_query(F.data == "movie_center")
async def cb_movie_center(cb: types.CallbackQuery):
    """求片中心"""
    await cb.message.edit_caption(
        caption="🎬 <b>求片中心</b>\n\n请选择您需要的功能：",
        reply_markup=movie_center_kb
    )
    await cb.answer()


@movie_router.callback_query(F.data == "movie_request_new")
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


@movie_router.message(StateFilter(Wait.waitMovieTitle))
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


@movie_router.callback_query(F.data == "skip_description")
async def cb_skip_description(cb: types.CallbackQuery, state: FSMContext):
    """跳过描述"""
    data = await state.get_data()
    title = data.get('title', '')
    
    # 保存跳过描述的状态
    await state.update_data(description=None, file_info="")
    
    # 显示确认页面
    confirm_text = (
        f"📋 <b>确认求片信息</b>\n\n"
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
    desc_text = f"📝 描述：{description}" if description else "📝 描述：无"
    confirm_text = (
        f"📋 <b>确认求片信息</b>\n\n"
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
    title = data.get('title', '')
    current_description = data.get('description')
    
    # 显示当前信息和编辑提示
    edit_text = (
        f"✏️ <b>重新编辑描述</b>\n\n"
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
                [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="movie_center")],
                [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ]
        )
    )
    await state.set_state(Wait.waitMovieDescription)
    await cb.answer()


@movie_router.callback_query(F.data == "confirm_movie_submit")
async def cb_confirm_movie_submit(cb: types.CallbackQuery, state: FSMContext):
    """确认提交求片"""
    data = await state.get_data()
    title = data.get('title', '')
    description = data.get('description')
    file_id = data.get('file_id')
    file_info = data.get('file_info', '')
    
    success = await create_movie_request(cb.from_user.id, title, description, file_id)
    
    # 显示最终结果
    if success:
        desc_text = f"\n📝 描述：{description}" if description else ""
        result_text = f"✅ <b>求片提交成功！</b>\n\n🎬 片名：{title}{desc_text}{file_info}\n\n您的求片请求已提交，等待管理员审核。"
    else:
        result_text = "❌ 提交失败，请稍后重试。"
    
    await cb.message.edit_caption(
        caption=result_text,
        reply_markup=back_to_main_kb
    )
    
    await state.clear()
    await cb.answer()


@movie_router.callback_query(F.data == "movie_request_my")
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