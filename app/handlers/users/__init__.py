from .basic import basic_router
from .movie import movie_router
from .content import content_router
from .feedback import feedback_router
from .reply_tracker import reply_tracker_router

# 导出所有用户路由器
# 注意：命令消息优先度最高，然后是状态相关路由
# 回复追踪器放在最后，确保能接收到所有未处理的消息
users_routers = [
    basic_router,      # 命令处理优先度最高（包含/start等命令）
    movie_router,      # 状态相关路由
    content_router,    # 状态相关路由
    feedback_router,   # 状态相关路由
    reply_tracker_router,  # 回复追踪路由最后（捕获剩余消息）
]

__all__ = [
    'users_routers',
    'basic_router',
    'movie_router', 
    'content_router',
    'feedback_router',
    'reply_tracker_router'
]