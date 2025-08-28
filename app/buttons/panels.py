from aiogram.types import InlineKeyboardMarkup

from app.buttons.users import main_menu_kb
from app.buttons.admin import admin_panel_kb
from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN


def get_panel_for_role(role: str) -> tuple[str, InlineKeyboardMarkup]:
    """
    根据角色返回欢迎面板文案与键盘。
    - user: 用户主菜单
    - admin: 管理员面板
    - superadmin: 超管面板（复用管理员面板，文案不同）
    """
    if role == ROLE_SUPERADMIN:
        return ("超管面板：", admin_panel_kb)
    if role == ROLE_ADMIN:
        return ("管理员面板：", admin_panel_kb)
    # 默认用户
    return ("欢迎使用！请选择菜单或直接发送消息。", main_menu_kb)


