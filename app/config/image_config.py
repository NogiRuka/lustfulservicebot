from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class ImageType(Enum):
    """图片类型枚举"""
    WELCOME = "welcome"  # 欢迎图片
    ADMIN = "admin"      # 管理员面板图片
    ERROR = "error"      # 错误页面图片
    SUCCESS = "success"  # 成功页面图片
    LOADING = "loading"  # 加载页面图片


@dataclass
class ImageConfig:
    """图片配置类"""
    url: str
    description: str
    tags: List[str]
    is_active: bool = True
    priority: int = 0  # 优先级，数字越大优先级越高


class ImageManager:
    """图片管理器"""
    
    def __init__(self):
        self._images: Dict[ImageType, List[ImageConfig]] = {
            ImageType.WELCOME: [
                ImageConfig(
                    url="https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/JQVISION_ISSUE16_078.jpg?raw=true",
                    description="默认欢迎图片 - JQVISION ISSUE16",
                    tags=["default", "welcome", "main"],
                    is_active=True,
                    priority=100
                ),
                ImageConfig(
                    url="https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/in356days_Pok_Napapon_069.jpg?raw=true",
                    description="备用欢迎图片 - in356days Pok Napapon",
                    tags=["backup", "welcome", "alternative"],
                    is_active=False,
                    priority=50
                ),
            ],
            ImageType.ADMIN: [
                ImageConfig(
                    url="https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/JQVISION_ISSUE16_078.jpg?raw=true",
                    description="管理员面板图片",
                    tags=["admin", "panel", "management"],
                    is_active=True,
                    priority=100
                ),
            ],
            ImageType.ERROR: [
                ImageConfig(
                    url="https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/JQVISION_ISSUE16_078.jpg?raw=true",
                    description="错误页面图片",
                    tags=["error", "failure", "problem"],
                    is_active=True,
                    priority=100
                ),
            ],
            ImageType.SUCCESS: [
                ImageConfig(
                    url="https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/JQVISION_ISSUE16_078.jpg?raw=true",
                    description="成功页面图片",
                    tags=["success", "complete", "done"],
                    is_active=True,
                    priority=100
                ),
            ],
            ImageType.LOADING: [
                ImageConfig(
                    url="https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/JQVISION_ISSUE16_078.jpg?raw=true",
                    description="加载页面图片",
                    tags=["loading", "processing", "wait"],
                    is_active=True,
                    priority=100
                ),
            ],
        }
    
    def get_image(self, image_type: ImageType, tag: str = None) -> str:
        """获取指定类型的图片URL"""
        images = self._images.get(image_type, [])
        
        # 过滤激活的图片
        active_images = [img for img in images if img.is_active]
        
        if not active_images:
            # 如果没有激活的图片，返回默认图片
            return self.get_default_image()
        
        # 如果指定了标签，优先返回匹配标签的图片
        if tag:
            tagged_images = [img for img in active_images if tag in img.tags]
            if tagged_images:
                # 按优先级排序，返回最高优先级的图片
                return sorted(tagged_images, key=lambda x: x.priority, reverse=True)[0].url
        
        # 按优先级排序，返回最高优先级的图片
        return sorted(active_images, key=lambda x: x.priority, reverse=True)[0].url
    
    def get_default_image(self) -> str:
        """获取默认图片"""
        return "https://github.com/NogiRuka/images/blob/main/bot/lustfulboy/JQVISION_ISSUE16_078.jpg?raw=true"
    
    def add_image(self, image_type: ImageType, config: ImageConfig):
        """添加图片配置"""
        if image_type not in self._images:
            self._images[image_type] = []
        self._images[image_type].append(config)
    
    def remove_image(self, image_type: ImageType, url: str) -> bool:
        """移除图片配置"""
        if image_type not in self._images:
            return False
        
        original_count = len(self._images[image_type])
        self._images[image_type] = [img for img in self._images[image_type] if img.url != url]
        return len(self._images[image_type]) < original_count
    
    def set_image_active(self, image_type: ImageType, url: str, active: bool) -> bool:
        """设置图片激活状态"""
        if image_type not in self._images:
            return False
        
        for img in self._images[image_type]:
            if img.url == url:
                img.is_active = active
                return True
        return False
    
    def get_all_images(self, image_type: ImageType = None) -> Dict[ImageType, List[ImageConfig]]:
        """获取所有图片配置"""
        if image_type:
            return {image_type: self._images.get(image_type, [])}
        return self._images.copy()
    
    def get_image_info(self, image_type: ImageType) -> Dict:
        """获取图片类型的详细信息"""
        images = self._images.get(image_type, [])
        active_count = len([img for img in images if img.is_active])
        
        return {
            'type': image_type.value,
            'total_count': len(images),
            'active_count': active_count,
            'current_image': self.get_image(image_type),
            'images': images
        }


# 全局图片管理器实例
image_manager = ImageManager()


# 便捷函数
def get_welcome_image(tag: str = None) -> str:
    """获取欢迎图片"""
    return image_manager.get_image(ImageType.WELCOME, tag)


def get_admin_image(tag: str = None) -> str:
    """获取管理员图片"""
    return image_manager.get_image(ImageType.ADMIN, tag)


def get_error_image(tag: str = None) -> str:
    """获取错误图片"""
    return image_manager.get_image(ImageType.ERROR, tag)


def get_success_image(tag: str = None) -> str:
    """获取成功图片"""
    return image_manager.get_image(ImageType.SUCCESS, tag)


def get_loading_image(tag: str = None) -> str:
    """获取加载图片"""
    return image_manager.get_image(ImageType.LOADING, tag)


# 向后兼容
DEFAULT_WELCOME_PHOTO = get_welcome_image()