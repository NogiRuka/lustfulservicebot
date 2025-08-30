from loguru import logger
from aiogram import types


async def safe_edit_message_caption(message: types.Message, caption: str, reply_markup=None):
    """安全地编辑消息标题，避免重复编辑错误"""
    try:
        await message.edit_caption(caption=caption, reply_markup=reply_markup)
    except Exception as e:
        # 忽略消息未修改的错误
        if "message is not modified" not in str(e):
            logger.error(f"编辑消息标题失败: {e}")


async def safe_edit_message_text(message: types.Message, text: str, reply_markup=None):
    """安全地编辑消息文本，避免重复编辑错误"""
    try:
        await message.edit_text(text=text, reply_markup=reply_markup)
    except Exception as e:
        # 忽略消息未修改的错误
        if "message is not modified" not in str(e):
            logger.error(f"编辑消息文本失败: {e}")


async def safe_edit_message(message: types.Message, caption: str = None, text: str = None, reply_markup=None):
    """智能地编辑消息，根据消息类型选择合适的编辑方法"""
    try:
        if message.photo and caption is not None:
            await message.edit_caption(caption=caption, reply_markup=reply_markup)
        elif text is not None:
            await message.edit_text(text=text, reply_markup=reply_markup)
        else:
            logger.warning("无法确定消息编辑类型")
    except Exception as e:
        # 忽略消息未修改的错误
        if "message is not modified" not in str(e):
            logger.error(f"编辑消息失败: {e}")