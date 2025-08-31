from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import create_user_feedback, get_user_feedback_list, is_feature_enabled
from app.buttons.users import feedback_center_kb, feedback_input_kb, back_to_main_kb

feedback_router = Router()


@feedback_router.callback_query(F.data == "feedback_center")
async def cb_feedback_center(cb: types.CallbackQuery):
    """用户反馈中心"""
    # 检查系统总开关和反馈功能开关
    if not await is_feature_enabled("system_enabled"):
        await cb.answer("❌ 系统维护中，暂时无法使用", show_alert=True)
        return
    
    if not await is_feature_enabled("feedback_enabled"):
        await cb.answer("❌ 用户反馈功能已关闭", show_alert=True)
        return
    
    await cb.message.edit_caption(
        caption="💬 <b>用户反馈中心</b>\n\n请选择您需要的功能：",
        reply_markup=feedback_center_kb
    )
    await cb.answer()


@feedback_router.callback_query(F.data.in_(["feedback_bug", "feedback_suggestion", "feedback_complaint", "feedback_other"]))
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


@feedback_router.message(StateFilter(Wait.waitFeedbackContent))
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
    
    # 保存反馈信息到状态
    await state.update_data(content=content, file_info=file_info)
    
    # 显示确认页面
    feedback_type_names = {
        "bug": "🐛 Bug反馈",
        "suggestion": "💡 建议反馈",
        "complaint": "😤 投诉反馈",
        "other": "❓ 其他反馈"
    }
    
    content_preview = content[:100] + ('...' if len(content) > 100 else '')
    confirm_text = (
        f"📋 <b>确认反馈信息</b>\n\n"
        f"📝 类型：{feedback_type_names.get(feedback_type, feedback_type)}\n"
        f"💬 内容：{content_preview}{file_info}\n\n"
        f"请确认以上信息是否正确？"
    )
    
    confirm_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                 types.InlineKeyboardButton(text="✅ 确认提交", callback_data="confirm_feedback_submit"),
                 types.InlineKeyboardButton(text="✏️ 重新编辑", callback_data="edit_feedback_content")
             ],
            [
                types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="feedback_center"),
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


@feedback_router.callback_query(F.data == "edit_feedback_content")
async def cb_edit_feedback_content(cb: types.CallbackQuery, state: FSMContext):
    """重新编辑反馈内容"""
    data = await state.get_data()
    feedback_type = data.get('feedback_type', 'other')
    current_content = data.get('content', '')
    current_file_info = data.get('file_info', '')
    
    feedback_type_names = {
        "bug": "🐛 Bug反馈",
        "suggestion": "💡 建议反馈",
        "complaint": "😤 投诉反馈",
        "other": "❓ 其他反馈"
    }
    
    # 显示当前信息和编辑提示
    edit_text = (
        f"✏️ <b>重新编辑反馈内容</b>\n\n"
        f"📝 类型：{feedback_type_names.get(feedback_type, feedback_type)}\n"
    )
    
    if current_content:
        content_preview = current_content[:100] + ('...' if len(current_content) > 100 else '')
        edit_text += f"💬 当前内容：{content_preview}{current_file_info}\n\n"
    else:
        edit_text += f"💬 当前内容：无\n\n"
    
    edit_text += "请输入新的反馈内容或发送相关图片："
    
    await cb.message.edit_caption(
        caption=edit_text,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ 返回上一级", callback_data="feedback_center")],
                [types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ]
        )
    )
    await state.set_state(Wait.waitFeedbackContent)
    await cb.answer()


@feedback_router.callback_query(F.data == "confirm_feedback_submit")
async def cb_confirm_feedback_submit(cb: types.CallbackQuery, state: FSMContext):
    """确认提交反馈"""
    data = await state.get_data()
    feedback_type = data.get('feedback_type', 'other')
    content = data.get('content', '')
    file_info = data.get('file_info', '')
    
    success = await create_user_feedback(cb.from_user.id, feedback_type, content)
    
    # 显示最终结果
    feedback_type_names = {
        "bug": "🐛 Bug反馈",
        "suggestion": "💡 建议反馈",
        "complaint": "😤 投诉反馈",
        "other": "❓ 其他反馈"
    }
    
    if success:
        content_preview = content[:100] + ('...' if len(content) > 100 else '')
        result_text = f"✅ <b>反馈提交成功！</b>\n\n📝 类型：{feedback_type_names.get(feedback_type, feedback_type)}\n💬 内容：{content_preview}{file_info}\n\n感谢您的反馈，我们会尽快处理。"
        
        # 成功页面按钮
        success_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="💬 继续反馈", callback_data="feedback_center"),
                    types.InlineKeyboardButton(text="📋 我的反馈", callback_data="feedback_my")
                ],
                [
                    types.InlineKeyboardButton(text="⬅️ 返回反馈中心", callback_data="feedback_center"),
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


@feedback_router.callback_query(F.data == "feedback_my")
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
            
            # 美化的卡片式布局
            content_preview = feedback.content[:30] + ('...' if len(feedback.content) > 30 else '')
            text += f"┌─ {i}. {type_emoji} {status_emoji} <b>{content_preview}</b>\n"
            text += f"├ 🏷️ 状态：<code>{feedback.status}</code>\n"
            text += f"├ ⏰ 时间：<i>{feedback.created_at.strftime('%m-%d %H:%M')}</i>\n"
            text += f"├ 📂 类型：{type_emoji} {feedback.feedback_type}\n"
            
            if feedback.reply_content:
                reply_preview = feedback.reply_content[:50] + ('...' if len(feedback.reply_content) > 50 else '')
                text += f"└ 💬 <b>管理员回复</b>：<blockquote>{reply_preview}</blockquote>\n"
            else:
                text += f"└─────────────────\n"
            
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