from aiogram import types, F, Router
from aiogram.filters import Command
from loguru import logger
from datetime import datetime

from app.database.users import get_role
from app.utils.roles import ROLE_SUPERADMIN
from app.config.image_config import (
    image_manager, ImageType, ImageConfig,
    get_welcome_image, get_admin_image, get_error_image, get_success_image, get_loading_image
)
from app.buttons.users import back_to_main_kb

image_router = Router()


@image_router.message(Command("image_list", "il"))
async def image_list_command(msg: types.Message):
    """查看图片列表"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    text = "🖼️ <b>图片管理系统</b>\n\n"
    
    for image_type in ImageType:
        info = image_manager.get_image_info(image_type)
        status_emoji = "🟢" if info['active_count'] > 0 else "🔴"
        
        text += f"{status_emoji} <b>{image_type.value.upper()}</b>\n"
        text += f"├ 总数：{info['total_count']} 张\n"
        text += f"├ 激活：{info['active_count']} 张\n"
        text += f"└ 当前：{info['current_image'][:50]}...\n\n"
    
    text += "💡 <b>可用命令</b>：\n"
    text += "├ /image_add [类型] [URL] [描述] - 添加图片\n"
    text += "├ /image_toggle [类型] [URL] - 切换图片状态\n"
    text += "├ /image_remove [类型] [URL] - 删除图片\n"
    text += "├ /image_test [类型] - 测试图片显示\n"
    text += "└ /il - 查看图片列表"
    
    await msg.reply(text, parse_mode="HTML")


@image_router.message(Command("image_add", "ia"))
async def image_add_command(msg: types.Message):
    """添加图片"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=3)
    if len(parts) < 4:
        await msg.reply(
            "用法：/image_add [类型] [URL] [描述] 或 /ia [类型] [URL] [描述]\n"
            "类型：welcome, admin, error, success, loading\n"
            "示例：/ia welcome https://example.com/image.jpg 新的欢迎图片"
        )
        return
    
    type_str = parts[1].lower()
    image_url = parts[2]
    description = parts[3]
    
    # 验证图片类型
    try:
        image_type = ImageType(type_str)
    except ValueError:
        await msg.reply(
            f"❌ 无效的图片类型：{type_str}\n"
            "可用类型：welcome, admin, error, success, loading"
        )
        return
    
    # 创建图片配置
    config = ImageConfig(
        url=image_url,
        description=description,
        tags=["custom", "added_by_admin"],
        is_active=True,
        priority=50
    )
    
    try:
        # 添加图片
        image_manager.add_image(image_type, config)
        
        await msg.reply(
            f"✅ <b>图片添加成功</b>\n\n"
            f"📷 <b>类型</b>：{image_type.value}\n"
            f"🔗 <b>URL</b>：{image_url[:50]}...\n"
            f"📝 <b>描述</b>：{description}\n"
            f"✨ <b>状态</b>：已激活\n\n"
            f"⏰ <b>添加时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"添加图片失败: {e}")
        await msg.reply(f"❌ 添加图片失败：{str(e)}")


@image_router.message(Command("image_toggle", "it"))
async def image_toggle_command(msg: types.Message):
    """切换图片状态"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.reply(
            "用法：/image_toggle [类型] [URL] 或 /it [类型] [URL]\n"
            "示例：/it welcome https://example.com/image.jpg"
        )
        return
    
    type_str = parts[1].lower()
    image_url = parts[2]
    
    # 验证图片类型
    try:
        image_type = ImageType(type_str)
    except ValueError:
        await msg.reply(
            f"❌ 无效的图片类型：{type_str}\n"
            "可用类型：welcome, admin, error, success, loading"
        )
        return
    
    # 获取当前状态
    images = image_manager.get_all_images(image_type)[image_type]
    target_image = None
    for img in images:
        if img.url == image_url:
            target_image = img
            break
    
    if not target_image:
        await msg.reply("❌ 未找到指定的图片")
        return
    
    # 切换状态
    new_status = not target_image.is_active
    success = image_manager.set_image_active(image_type, image_url, new_status)
    
    if success:
        status_text = "激活" if new_status else "停用"
        status_emoji = "✅" if new_status else "❌"
        
        await msg.reply(
            f"{status_emoji} <b>图片状态已更新</b>\n\n"
            f"📷 <b>类型</b>：{image_type.value}\n"
            f"🔗 <b>URL</b>：{image_url[:50]}...\n"
            f"📝 <b>描述</b>：{target_image.description}\n"
            f"✨ <b>新状态</b>：{status_text}\n\n"
            f"⏰ <b>更新时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="HTML"
        )
    else:
        await msg.reply("❌ 更新图片状态失败")


@image_router.message(Command("image_remove", "ir"))
async def image_remove_command(msg: types.Message):
    """删除图片"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.reply(
            "用法：/image_remove [类型] [URL] 或 /ir [类型] [URL]\n"
            "示例：/ir welcome https://example.com/image.jpg"
        )
        return
    
    type_str = parts[1].lower()
    image_url = parts[2]
    
    # 验证图片类型
    try:
        image_type = ImageType(type_str)
    except ValueError:
        await msg.reply(
            f"❌ 无效的图片类型：{type_str}\n"
            "可用类型：welcome, admin, error, success, loading"
        )
        return
    
    # 删除图片
    success = image_manager.remove_image(image_type, image_url)
    
    if success:
        await msg.reply(
            f"🗑️ <b>图片删除成功</b>\n\n"
            f"📷 <b>类型</b>：{image_type.value}\n"
            f"🔗 <b>URL</b>：{image_url[:50]}...\n\n"
            f"⏰ <b>删除时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="HTML"
        )
    else:
        await msg.reply("❌ 删除图片失败，未找到指定的图片")


@image_router.message(Command("image_test", "itest"))
async def image_test_command(msg: types.Message):
    """测试图片显示"""
    role = await get_role(msg.from_user.id)
    if role != ROLE_SUPERADMIN:
        await msg.reply("❌ 仅超管可使用此命令")
        return
    
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply(
            "用法：/image_test [类型] 或 /itest [类型]\n"
            "类型：welcome, admin, error, success, loading\n"
            "示例：/itest welcome"
        )
        return
    
    type_str = parts[1].lower()
    
    # 验证图片类型
    try:
        image_type = ImageType(type_str)
    except ValueError:
        await msg.reply(
            f"❌ 无效的图片类型：{type_str}\n"
            "可用类型：welcome, admin, error, success, loading"
        )
        return
    
    # 获取图片URL
    if image_type == ImageType.WELCOME:
        image_url = get_welcome_image()
    elif image_type == ImageType.ADMIN:
        image_url = get_admin_image()
    elif image_type == ImageType.ERROR:
        image_url = get_error_image()
    elif image_type == ImageType.SUCCESS:
        image_url = get_success_image()
    elif image_type == ImageType.LOADING:
        image_url = get_loading_image()
    else:
        image_url = image_manager.get_image(image_type)
    
    # 获取图片信息
    info = image_manager.get_image_info(image_type)
    
    test_text = (
        f"🧪 <b>图片测试 - {image_type.value.upper()}</b>\n\n"
        f"📊 <b>统计信息</b>：\n"
        f"├ 总图片数：{info['total_count']}\n"
        f"├ 激活图片：{info['active_count']}\n"
        f"└ 当前显示：{image_url[:50]}...\n\n"
        f"🎯 <b>测试结果</b>：图片加载{('成功' if image_url else '失败')}\n\n"
        f"⏰ <b>测试时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    try:
        await msg.answer_photo(
            photo=image_url,
            caption=test_text,
            reply_markup=back_to_main_kb,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"图片测试失败: {e}")
        await msg.reply(
            f"❌ <b>图片测试失败</b>\n\n"
            f"📷 <b>类型</b>：{image_type.value}\n"
            f"🔗 <b>URL</b>：{image_url}\n"
            f"❌ <b>错误</b>：{str(e)}\n\n"
            f"💡 <b>可能原因</b>：\n"
            f"├ 图片URL无效\n"
            f"├ 图片文件损坏\n"
            f"├ 网络连接问题\n"
            f"└ 图片格式不支持",
            parse_mode="HTML"
        )