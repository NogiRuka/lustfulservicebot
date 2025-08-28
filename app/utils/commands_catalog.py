"""
按角色构建命令目录的工具。
"""

from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN


def build_commands_help(role: str) -> str:
    sections: list[str] = []

    # 通用（用户）
    user_block = (
        "<b>通用命令</b>\n"
        "/start — 显示面板\n"
        "/menu — 显示面板\n"
        "/help — 帮助\n"
        "/commands — 命令目录\n"
    )
    sections.append(user_block)

    if role in {ROLE_ADMIN, ROLE_SUPERADMIN}:
        admin_block = (
            "➖➖➖➖➖\n"
            "<b>管理员命令</b>\n"
            "/panel — 管理员面板\n"
            "/users — 用户总数\n"
            "/info <chat_id> — 查询用户\n"
            "/announce — 群发公告\n"
        )
        sections.append(admin_block)

    if role == ROLE_SUPERADMIN:
        su_block = (
            "➖➖➖➖➖\n"
            "<b>超管命令</b>\n"
            "/promote <chat_id> — 设为管理员\n"
            "/demote <chat_id> — 取消管理员\n"
        )
        sections.append(su_block)

    return "".join(sections)


