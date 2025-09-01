from typing import Optional, Dict, Any, List
from aiogram import types
from aiogram.fsm.context import FSMContext
from app.utils.time_utils import humanize_time, get_status_text
from app.utils.pagination import Paginator, format_page_header
from app.database.business import get_all_movie_categories
from loguru import logger


class SubmissionConfig:
    """提交配置类"""
    
    def __init__(self, 
                 item_type: str,
                 emoji: str,
                 name: str,
                 center_title: str,
                 feature_key: str,
                 create_function,
                 get_user_items_function,
                 title_state,
                 content_state,
                 title_field: str,
                 content_field: str,
                 content_label: str = "内容"):
        self.item_type = item_type
        self.emoji = emoji
        self.name = name
        self.center_title = center_title
        self.feature_key = feature_key
        self.create_function = create_function
        self.get_user_items_function = get_user_items_function
        self.title_state = title_state
        self.content_state = content_state
        self.title_field = title_field
        self.content_field = content_field
        self.content_label = content_label


class SubmissionUIBuilder:
    """提交界面构建器"""
    
    @staticmethod
    def build_center_text(config: SubmissionConfig) -> str:
        """构建中心页面文本"""
        return f"{config.emoji} <b>{config.center_title}</b>\n\n请选择您需要的功能："
    
    @staticmethod
    def build_category_selection_text(config: SubmissionConfig) -> str:
        """构建分类选择文本"""
        return f"{config.emoji} <b>开始{config.name}</b> {config.emoji}\n\n📂 请选择您要{config.name}的类型："
    
    @staticmethod
    def build_category_keyboard(categories: List, callback_prefix: str) -> types.InlineKeyboardMarkup:
        """构建分类选择键盘"""
        keyboard = []
        
        # 分类按钮（每行2个）
        category_buttons = []
        for i, category in enumerate(categories):
            category_buttons.append(
                types.InlineKeyboardButton(
                    text=f"📂 {category.name}",
                    callback_data=f"{callback_prefix}{category.id}"
                )
            )
            if (i + 1) % 2 == 0 or i == len(categories) - 1:
                keyboard.append(category_buttons)
                category_buttons = []
        
        # 返回按钮
        keyboard.append([
            types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
        ])
        
        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def build_title_input_text(config: SubmissionConfig, category_name: str) -> str:
        """构建标题输入文本"""
        return (
            f"{config.emoji} <b>开始{config.name}</b> {config.emoji}\n\n"
            f"📂 <b>类型</b>：{category_name}\n\n"
            f"📝 请输入您想要的{config.title_field}："
        )
    
    @staticmethod
    def build_content_input_text(config: SubmissionConfig, category_name: str, title: str) -> str:
        """构建内容输入文本"""
        return (
            f"{config.emoji} <b>开始{config.name}</b> {config.emoji}\n\n"
            f"📂 <b>类型</b>：{category_name}\n"
            f"✅ <b>{config.title_field}</b>：{title}\n\n"
            f"📝 <b>请输入{config.content_label}</b>\n"
            f"├ 可以发送豆瓣链接或其他\n"
            f"├ 可以描述剧情、演员、年份等信息\n"
            f"├ 也可以发送相关图片\n"
            f"└ 仅限一条消息（文字或一张图片+说明文字）\n\n"
            f"💡 <i>详细信息有助于更快找到资源</i>"
        )
    
    @staticmethod
    def build_confirmation_text(config: SubmissionConfig, data: Dict[str, Any]) -> str:
        """构建确认提交文本"""
        text = (
            f"{config.emoji} <b>{config.name}确认</b> {config.emoji}\n\n"
            f"📂 <b>类型</b>：{data['category_name']}\n"
            f"📝 <b>{config.title_field}</b>：{data['title']}\n\n"
        )
        
        if data.get('content'):
            content_display = data['content'][:200] + "..." if len(data['content']) > 200 else data['content']
            text += f"📄 <b>{config.content_label}</b>：\n{content_display}\n\n"
        
        if data.get('file_id'):
            text += f"📎 <b>附件</b>：已上传\n\n"
        
        text += f"请确认您的{config.name}信息："
        return text
    
    @staticmethod
    def build_confirmation_keyboard(config: SubmissionConfig) -> types.InlineKeyboardMarkup:
        """构建确认提交键盘"""
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ 确认提交", callback_data=f"confirm_{config.item_type}_submit"),
                    types.InlineKeyboardButton(text="✏️ 修改{}".format(config.content_label), callback_data=f"edit_{config.item_type}_{config.content_field}")
                ],
                [
                    types.InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")
                ]
            ]
        )
    
    @staticmethod
    def build_my_items_text(config: SubmissionConfig, items: List, paginator: Paginator) -> str:
        """构建我的项目列表文本"""
        text = format_page_header(f"{config.emoji} 我的{config.name}", paginator.current_page, paginator.total_pages)
        text += "\n\n"
        
        if not items:
            text += f"📋 您还没有{config.name}记录\n\n💡 点击下方按钮开始{config.name}"
        else:
            for item in items:
                status_text = get_status_text(item.status)
                text += (
                    f"🆔 ID: {item.id}\n"
                    f"📝 {config.title_field}: {item.title}\n"
                    f"📅 时间: {humanize_time(item.created_at)}\n"
                    f"📊 状态: {status_text}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                )
        
        return text
    
    @staticmethod
    def build_my_items_keyboard(config: SubmissionConfig, paginator: Paginator) -> types.InlineKeyboardMarkup:
        """构建我的项目列表键盘"""
        keyboard = []
        
        # 分页按钮
        if paginator.total_pages > 1:
            nav_buttons = []
            if paginator.has_prev():
                nav_buttons.append(
                    types.InlineKeyboardButton(text="⬅️ 上一页", callback_data=f"my_{config.item_type}_page_{paginator.current_page - 1}")
                )
            if paginator.has_next():
                nav_buttons.append(
                    types.InlineKeyboardButton(text="➡️ 下一页", callback_data=f"my_{config.item_type}_page_{paginator.current_page + 1}")
                )
            if nav_buttons:
                keyboard.append(nav_buttons)
        
        # 功能按钮
        keyboard.extend([
            [
                types.InlineKeyboardButton(text=f"➕ 新{config.name}", callback_data=f"{config.item_type}_request_new"),
                types.InlineKeyboardButton(text="🔙 返回中心", callback_data=f"{config.item_type}_center")
            ]
        ])
        
        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)


class SubmissionHandler:
    """提交处理器"""
    
    def __init__(self, config: SubmissionConfig):
        self.config = config
    
    async def handle_center(self, cb: types.CallbackQuery):
        """处理中心页面"""
        from app.database.business import is_feature_enabled
        
        if not await is_feature_enabled(self.config.feature_key):
            await cb.answer(f"❌ {self.config.name}功能已关闭", show_alert=True)
            return
        
        # 动态导入按钮
        if self.config.item_type == 'movie':
            from app.buttons.users import movie_center_kb as center_kb
        else:
            from app.buttons.users import content_center_kb as center_kb
        
        await cb.message.edit_caption(
            caption=SubmissionUIBuilder.build_center_text(self.config),
            reply_markup=center_kb
        )
        await cb.answer()
    
    async def handle_new_submission(self, cb: types.CallbackQuery, state: FSMContext):
        """处理新提交"""
        from app.database.business import is_feature_enabled
        from app.buttons.users import back_to_main_kb
        
        if not await is_feature_enabled(self.config.feature_key):
            await cb.answer(f"❌ {self.config.name}功能已关闭", show_alert=True)
            return
        
        await state.clear()
        
        # 获取可用的类型
        categories = await get_all_movie_categories(active_only=True)
        if not categories:
            await cb.message.edit_caption(
                caption=f"❌ 暂无可用的{self.config.name}类型，请联系管理员。",
                reply_markup=back_to_main_kb
            )
            await cb.answer()
            return
        
        # 构建分类选择界面
        await cb.message.edit_caption(
            caption=SubmissionUIBuilder.build_category_selection_text(self.config),
            reply_markup=SubmissionUIBuilder.build_category_keyboard(
                categories, f"select_{self.config.item_type}_category_"
            )
        )
        await cb.answer()
    
    async def handle_category_selection(self, cb: types.CallbackQuery, state: FSMContext, category_id: int):
        """处理分类选择"""
        from app.database.business import get_movie_category_by_id
        from app.buttons.users import back_to_main_kb
        
        # 获取分类信息
        category = await get_movie_category_by_id(category_id)
        if not category:
            await cb.answer("❌ 分类不存在", show_alert=True)
            return
        
        # 保存分类信息和消息ID
        await state.update_data(
            category_id=category_id,
            category_name=category.name,
            message_id=cb.message.message_id
        )
        
        # 设置等待标题输入状态
        await state.set_state(self.config.title_state)
        
        # 显示标题输入界面
        await cb.message.edit_caption(
            caption=SubmissionUIBuilder.build_title_input_text(self.config, category.name),
            reply_markup=back_to_main_kb
        )
        await cb.answer()
    
    async def handle_title_input(self, msg: types.Message, state: FSMContext):
        """处理标题输入"""
        from app.buttons.users import back_to_main_kb
        
        title = msg.text.strip()
        if len(title) > 100:
            await msg.reply(f"❌ {self.config.title_field}长度不能超过100个字符，请重新输入：")
            return
        
        # 获取状态数据
        data = await state.get_data()
        category_name = data.get('category_name', '未知类型')
        message_id = data.get('message_id')
        
        # 保存标题
        await state.update_data(title=title)
        
        # 删除用户输入的消息
        try:
            await msg.delete()
        except:
            pass
        
        # 设置等待内容输入状态
        await state.set_state(self.config.content_state)
        
        # 编辑原消息显示内容输入界面
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption=SubmissionUIBuilder.build_content_input_text(self.config, category_name, title),
                reply_markup=back_to_main_kb,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
            # 如果编辑失败，发送新消息
            await msg.reply(
                SubmissionUIBuilder.build_content_input_text(self.config, category_name, title),
                reply_markup=back_to_main_kb
            )
    
    async def handle_content_input(self, msg: types.Message, state: FSMContext):
        """处理内容输入"""
        content = None
        file_id = None
        
        # 处理不同类型的消息
        if msg.text:
            content = msg.text.strip()
        elif msg.photo:
            file_id = msg.photo[-1].file_id
            content = msg.caption.strip() if msg.caption else ""
        elif msg.document:
            file_id = msg.document.file_id
            content = msg.caption.strip() if msg.caption else ""
        else:
            await msg.reply("❌ 请发送文字或图片")
            return
        
        if len(content) > 1000:
            await msg.reply(f"❌ {self.config.content_label}长度不能超过1000个字符，请重新输入：")
            return
        
        # 保存内容
        await state.update_data(content=content, file_id=file_id)
        
        # 获取所有数据
        data = await state.get_data()
        message_id = data.get('message_id')
        
        # 删除用户输入的消息
        try:
            await msg.delete()
        except:
            pass
        
        # 编辑原消息显示确认界面
        try:
            await msg.bot.edit_message_caption(
                chat_id=msg.from_user.id,
                message_id=message_id,
                caption=SubmissionUIBuilder.build_confirmation_text(self.config, data),
                reply_markup=SubmissionUIBuilder.build_confirmation_keyboard(self.config),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"编辑消息失败: {e}")
            # 如果编辑失败，发送新消息
            await msg.reply(
                SubmissionUIBuilder.build_confirmation_text(self.config, data),
                reply_markup=SubmissionUIBuilder.build_confirmation_keyboard(self.config)
            )
    
    async def handle_edit_content(self, cb: types.CallbackQuery, state: FSMContext):
        """处理编辑内容"""
        from app.buttons.users import back_to_main_kb
        
        data = await state.get_data()
        category_name = data.get('category_name', '未知类型')
        title = data.get('title', '未知')
        
        # 设置等待内容输入状态
        await state.set_state(self.config.content_state)
        
        await cb.message.edit_caption(
            caption=SubmissionUIBuilder.build_content_input_text(self.config, category_name, title),
            reply_markup=back_to_main_kb,
            parse_mode="HTML"
        )
        await cb.answer()
    
    async def handle_confirm_submit(self, cb: types.CallbackQuery, state: FSMContext):
        """处理确认提交"""
        from app.buttons.users import back_to_main_kb
        
        data = await state.get_data()
        
        try:
            # 调用创建函数
            if self.config.item_type == 'movie':
                success = await self.config.create_function(
                    cb.from_user.id,
                    data['category_id'],
                    data['title'],
                    data.get('content'),
                    data.get('file_id')
                )
            else:
                success = await self.config.create_function(
                    cb.from_user.id,
                    data['title'],
                    data.get('content', ''),
                    data.get('file_id'),
                    data['category_id']
                )
            
            if success:
                await cb.message.edit_caption(
                    caption=f"✅ {self.config.name}提交成功！\n\n📋 您的{self.config.name}已提交，请等待管理员审核。",
                    reply_markup=back_to_main_kb
                )
                await state.clear()
            else:
                await cb.answer(f"❌ {self.config.name}提交失败，请稍后重试", show_alert=True)
        
        except Exception as e:
            logger.error(f"{self.config.name}提交失败: {e}")
            await cb.answer(f"❌ {self.config.name}提交失败，请稍后重试", show_alert=True)
        
        await cb.answer()
    
    async def handle_skip_content(self, cb: types.CallbackQuery, state: FSMContext):
        """处理跳过内容"""
        # 保存空内容
        await state.update_data(content=None, file_id=None)
        
        # 获取所有数据
        data = await state.get_data()
        
        # 显示确认界面
        await cb.message.edit_caption(
            caption=SubmissionUIBuilder.build_confirmation_text(self.config, data),
            reply_markup=SubmissionUIBuilder.build_confirmation_keyboard(self.config)
        )
        await cb.answer()
    
    async def handle_confirm_submission(self, cb: types.CallbackQuery, state: FSMContext):
        """处理确认提交（兼容旧方法名）"""
        await self.handle_confirm_submit(cb, state)
    
    async def handle_my_submissions(self, cb: types.CallbackQuery, page: int = 1):
        """处理我的提交列表"""
        # 获取用户的提交记录
        items = await self.config.get_user_items_function(cb.from_user.id)
        
        # 创建分页器
        paginator = Paginator(items, page_size=5)
        page_data = paginator.get_page(page)
        
        # 构建界面
        await cb.message.edit_caption(
            caption=SubmissionUIBuilder.build_my_items_text(self.config, page_data, paginator),
            reply_markup=SubmissionUIBuilder.build_my_items_keyboard(self.config, paginator)
        )
        await cb.answer()