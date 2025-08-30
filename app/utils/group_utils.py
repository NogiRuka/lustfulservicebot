from aiogram import Bot
from loguru import logger
from app.config.config import GROUP


async def user_in_group_filter(bot: Bot, user_id: int) -> bool:
    """
    检查用户是否在指定群组中
    :param bot: aiogram 的 Bot 实例
    :param user_id: 用户 ID
    :return: bool
    """
    if not GROUP:
        # 如果没有设置群组，则默认通过验证
        return True
        
    try:
        # 支持群组用户名（@开头）和群组ID（数字）
        chat_id = GROUP if GROUP.startswith('@') else f'@{GROUP}'
        member = await bot.get_chat_member(chat_id, user_id)
        # 如果能拿到状态就说明在群里
        return member.status in {"member", "administrator", "creator"}
    except Exception as e:
        # 如果报错，大多数情况是用户不在群里或者群不存在
        logger.warning(f"⚠️ 检查群组成员失败: {e}")
        return False


async def get_group_member_count(bot: Bot) -> int:
    """
    获取群组成员数量
    :param bot: aiogram 的 Bot 实例
    :return: 成员数量，失败返回0
    """
    if not GROUP:
        return 0
        
    try:
        chat_id = GROUP if GROUP.startswith('@') else f'@{GROUP}'
        # 使用get_chat_member_count方法获取成员数量
        member_count = await bot.get_chat_member_count(chat_id)
        return member_count or 0
    except Exception as e:
        logger.warning(f"⚠️ 获取群组成员数量失败: {e}")
        return 0