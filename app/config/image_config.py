import random

# 随机图片配置
# 主面板每次唤起时随机选择一张图片，编辑操作在同一张图片上进行

# 图片列表
IMAGE_LIST = [
    "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/JQVISION_ISSUE16_078.jpg?raw=true",
    "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true",
]

# 当前会话使用的图片URL（每次/start时随机选择）
CURRENT_WELCOME_IMAGE = None


# 用户会话图片缓存
user_session_images = {}

def get_random_image() -> str:
    """从图片列表中随机选择一张图片"""
    return random.choice(IMAGE_LIST)

def get_user_session_image(user_id: int) -> str:
    """获取用户会话的图片（如果没有则随机选择一张）"""
    if user_id not in user_session_images:
        user_session_images[user_id] = get_random_image()
    return user_session_images[user_id]

def refresh_user_session_image(user_id: int) -> str:
    """刷新用户会话图片（重新随机选择）"""
    user_session_images[user_id] = get_random_image()
    return user_session_images[user_id]

def get_welcome_image(user_id: int = None) -> str:
    """获取欢迎图片"""
    if user_id is None:
        return get_random_image()
    return get_user_session_image(user_id)

def get_admin_image(user_id: int = None) -> str:
    """获取管理员图片（与欢迎图片相同）"""
    return get_welcome_image(user_id)

def get_error_image(user_id: int = None) -> str:
    """获取错误图片（与欢迎图片相同）"""
    return get_welcome_image(user_id)

def get_success_image(user_id: int = None) -> str:
    """获取成功图片（与欢迎图片相同）"""
    return get_welcome_image(user_id)

def get_loading_image(user_id: int = None) -> str:
    """获取加载图片（与欢迎图片相同）"""
    return get_welcome_image(user_id)

# 向后兼容
DEFAULT_WELCOME_PHOTO = IMAGE_LIST[0]

# 图片信息显示函数
def get_image_info() -> dict:
    """获取图片配置信息"""
    return {
        'image_list': IMAGE_LIST,
        'total_images': len(IMAGE_LIST),
        'description': '主面板随机图片系统',
        'active_sessions': len(user_session_images)
    }

# 图片管理函数
def add_image(url: str) -> bool:
    """添加图片到列表"""
    if url not in IMAGE_LIST:
        IMAGE_LIST.append(url)
        return True
    return False

def remove_image(url: str) -> bool:
    """从列表中移除图片"""
    if url in IMAGE_LIST and len(IMAGE_LIST) > 1:  # 至少保留一张图片
        IMAGE_LIST.remove(url)
        # 清除使用了该图片的会话缓存
        for user_id in list(user_session_images.keys()):
            if user_session_images[user_id] == url:
                user_session_images[user_id] = get_random_image()
        return True
    return False

def clear_all_sessions():
    """清除所有用户会话图片缓存"""
    global user_session_images
    user_session_images = {}