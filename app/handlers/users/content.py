from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import create_content_submission, get_user_content_submissions
from app.buttons.users import content_center_kb, content_input_kb, back_to_main_kb

content_router = Router()


@content_router.callback_query(F.data == "content_center")
async def cb_content_center(cb: types.CallbackQuery):
    """内容投稿中心"""
    await cb.message.edit_caption(
        caption="📝 <b>内容投稿中心</b>\n\n请选择您需要的功能：",
        reply_markup=content_center_kb
    )
    await cb.answer()


@content_router.callback_query(F.data == "content_submit_new")
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


@content_router.message(StateFilter(Wait.waitContentTitle))
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
    confirm_text = (
        f"📋 <b>确认投稿信息</b>\n\n"
        f"📝 标题：{title}\n"
        f"📄 内容：{content_preview}{file_info}\n\n"
        f"请确认以上信息是否正确？"
    )
    
    confirm_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ 确认提交", callback_data="confirm_content_submit"),
                types.InlineKeyboardButton(text="✏️ 重新编辑", callback_data="content_submit_new")
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


@content_router.callback_query(F.data == "confirm_content_submit")
async def cb_confirm_content_submit(cb: types.CallbackQuery, state: FSMContext):
    """确认提交投稿"""
    data = await state.get_data()
    title = data.get('title', '')
    content = data.get('content', '')
    file_id = data.get('file_id')
    file_info = data.get('file_info', '')
    
    success = await create_content_submission(cb.from_user.id, title, content, file_id)
    
    # 显示最终结果
    if success:
        content_preview = content[:50] + ('...' if len(content) > 50 else '')
        result_text = f"✅ <b>投稿提交成功！</b>\n\n📝 标题：{title}\n📄 内容：{content_preview}{file_info}\n\n您的投稿已提交，等待管理员审核。"
    else:
        result_text = "❌ 提交失败，请稍后重试。"
    
    await cb.message.edit_caption(
        caption=result_text,
        reply_markup=back_to_main_kb
    )
    
    await state.clear()
    await cb.answer()


@content_router.callback_query(F.data == "content_submit_my")
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