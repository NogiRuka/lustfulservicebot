from .basic import basic_router
from .movie import movie_router
from .content import content_router
from .feedback import feedback_router
from .reply_tracker import reply_tracker_router

# 导出所有用户路由器
# 注意：状态相关的路由应该优先于通用路由
# 回复追踪器需要在basic_router之前，以确保能接收到所有消息
users_routers = [
    movie_router,      # 状态相关路由优先
    content_router,    # 状态相关路由优先
    feedback_router,   # 状态相关路由优先
    reply_tracker_router,  # 回复追踪路由（在basic_router之前）
    basic_router,      # 通用路由最后
]

__all__ = [
    'users_routers',
    'basic_router',
    'movie_router', 
    'content_router',
    'feedback_router',
    'reply_tracker_router'
]