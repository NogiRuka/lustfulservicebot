import random

# 随机图片配置
# 主面板每次唤起时随机选择一张图片，编辑操作在同一张图片上进行

# 图片列表
IMAGE_LIST = [
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2Fc1835465-3873-4e79-95c9-e2029fc67f06%2F24.jpg/size/w=1420?exp=1757176136&sig=i8CQfgOQ7lrsLa4cIfgroFBxohabcMkdHfG_rrxo8yQ&id=2666ee0b-e695-8023-a309-e9afebe5edf9&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2F2df003bf-e174-43ec-8c26-1f7a1f242bee%2FADONISJING_DESIRE_TO_ANGEL_058.jpg/size/w=1420?exp=1757176136&sig=KyOpj5TtRwQduXHPWeTXMjPWmAfwseZPViZZmcJaptI&id=2666ee0b-e695-80de-a072-d4db3aa5afb0&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2F778c0ad5-e167-4db4-ab08-5efe9bfa146f%2FBlossom_%E4%BB%B2%E5%A4%8F-PzAzjucqd-3.jpg/size/w=1420?exp=1757176136&sig=BsLsHcE_IQwKkZ2OjJD62fa4t7ZZ_qCcRkg5o7UiQkw&id=2666ee0b-e695-808f-b615-dfd75ef86df0&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2Fea8436cc-bc36-420b-9842-7152bd5e2f1c%2FJQVISION_ISSUE16_055.jpg/size/w=1420?exp=1757176136&sig=XJxgsAl5b2r_gqxJ3hoP2ugfbV7Z2bTEj6DGzvZRRfk&id=2666ee0b-e695-80f4-9d42-d363a34ac950&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2F1818038e-2f7d-49f2-b709-4246744bb0b5%2FJQVISION_ISSUE16_066.jpg/size/w=1420?exp=1757176136&sig=0ON-PPxFRKFP1QuJoTZ5TsTGoN26AROpY18qRo5N5HQ&id=2666ee0b-e695-8034-b2db-ffde76b868bb&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2F94176b70-e7ce-4a86-b7fa-81783519e519%2FJQVISION_VISIONseries_NO.09_012.jpg/size/w=1420?exp=1757176136&sig=NuMyUhcyqwRbftg37G1tuQo0FoSIXz-pCKqzbDslsPo&id=2666ee0b-e695-80ec-8060-d3f25b8b2c04&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2F3e7bb7e4-1c8f-4308-9850-86f9f99d84dc%2FJQVISION_VISIONseries_NO.13_054.jpg/size/w=1420?exp=1757176137&sig=C1OFb-1fnbWzhXwXoOD1UDBld7N5gUmCjZN7rmjiOa4&id=2666ee0b-e695-803b-b31b-f1e58a293da7&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2F10c5a31b-67b6-4116-91d4-0d448b94c170%2Fwallhaven-w8mm2r.jpg/size/w=1420?exp=1757176137&sig=avDhIfos2dRv6EFfMKgsGO1jn_2t_1zE-8Da2sb1CLk&id=2666ee0b-e695-80e1-8f7b-f85f83618eca&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2F68906fae-2204-4a67-b986-f1f7d111aa1c%2Fin356days_Pok_Napapon_069.jpg/size/w=1420?exp=1757176137&sig=ocHcULJ3LDmlSoD_ANR4E125O5JTvXEbn7WbCTwg9o4&id=2666ee0b-e695-80ac-b2be-fe377cfc0ecd&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2Fc47606cb-3abc-4e15-96a0-5660dcd45ee5%2FJQVISION_VISIONseries_NO.10_055.jpg/size/w=1420?exp=1757176137&sig=3BXWJHldGSFTsTPY6mEiwIVaP-Zz2F0G4W-7iEtlYaQ&id=2666ee0b-e695-8051-a2be-faff723c723f&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    "https://img.notionusercontent.com/s3/prod-files-secure%2F3d8ec1c3-18fb-4f55-b64d-e6d56db2bf1b%2F23bdf281-3f00-487d-9f8f-66b18c1dd4b7%2FJQVISION_VISIONseries_NO.15_135.jpg/size/w=1420?exp=1757176137&sig=ySEdviwIqKl0JAq5CiAAgrMIDiqdGSWo1XengULnvys&id=2666ee0b-e695-806c-b820-fede5e2ff617&table=block&userId=8fd1f12d-c366-41c6-a9de-3b5121011a15",
    # "",

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