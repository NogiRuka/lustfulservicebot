"""
角色常量与工具函数。

角色分级（从低到高）：
- user：普通用户
- admin：管理员
- superadmin：超管（创始人，唯一且权限最高）
"""

# 角色常量
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_SUPERADMIN = "superadmin"


def is_valid_role(role: str) -> bool:
    """校验是否为受支持的角色。"""
    return role in {ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN}


def is_elevated(role: str) -> bool:
    """是否为高权限（管理员及以上）。"""
    return role in {ROLE_ADMIN, ROLE_SUPERADMIN}


