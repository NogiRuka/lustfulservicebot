from aiogram.types import InlineKeyboardMarkup

from app.buttons.users import get_main_menu_by_role
from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN


def get_panel_for_role(role: str) -> tuple[str, InlineKeyboardMarkup]:
    """
    根据角色返回欢迎面板文案与键盘。
    - user: 用户主菜单
    - admin: 管理员主菜单
    - superadmin: 超管主菜单
    """
    kb = get_main_menu_by_role(role)
    
    if role == ROLE_SUPERADMIN:
        return ("🛡️ 超级管理员面板\n\n欢迎使用超管功能，您拥有最高权限。", kb)
    elif role == ROLE_ADMIN:
        return ("👮 管理员面板\n\n欢迎使用管理员功能，请选择下方操作。", kb)
    else:
        return ("👋 用户面板\n\n欢迎使用机器人，请选择下方功能。", kb)


