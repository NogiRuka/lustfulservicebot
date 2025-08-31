from .basic import basic_router
from .movie import movie_router
from .content import content_router
from .feedback import feedback_router
from .superadmin import superadmin_router

# 导出所有用户路由器
# 注意：状态相关的路由应该优先于通用路由
users_routers = [
    movie_router,      # 状态相关路由优先
    content_router,    # 状态相关路由优先
    feedback_router,   # 状态相关路由优先
    superadmin_router, # 特殊权限路由
    basic_router,      # 通用路由最后
]

__all__ = [
    'users_routers',
    'basic_router',
    'movie_router', 
    'content_router',
    'feedback_router',
    'superadmin_router'
]