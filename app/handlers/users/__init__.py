from .basic import basic_router
from .movie import movie_router
from .content import content_router
from .feedback import feedback_router
from .superadmin import superadmin_router

# 导出所有用户路由器
users_routers = [
    basic_router,
    movie_router,
    content_router,
    feedback_router,
    superadmin_router
]

__all__ = [
    'users_routers',
    'basic_router',
    'movie_router', 
    'content_router',
    'feedback_router',
    'superadmin_router'
]