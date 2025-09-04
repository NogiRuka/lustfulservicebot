from typing import List, Any, Dict, Optional, Callable
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from loguru import logger


class SortOrder(Enum):
    """排序方式枚举"""
    ASC = "asc"   # 升序（早的在前）
    DESC = "desc" # 降序（晚的在前）


class TimeField(Enum):
    """时间字段枚举"""
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    REVIEWED_AT = "reviewed_at"
    REPLIED_AT = "replied_at"


@dataclass
class BrowserConfig:
    """浏览器配置"""
    page_size: int = 10
    sort_field: TimeField = TimeField.CREATED_AT
    sort_order: SortOrder = SortOrder.ASC
    visible_fields: List[str] = None
    max_page_size: int = 50
    min_page_size: int = 5


@dataclass
class BrowserState:
    """浏览器状态"""
    current_page: int = 1
    config: BrowserConfig = None
    total_items: int = 0
    
    def __post_init__(self):
        if self.config is None:
            self.config = BrowserConfig()


class AdvancedBrowser:
    """高级数据浏览器"""
    
    def __init__(self, data_source: Callable, default_config: BrowserConfig = None):
        """
        初始化高级浏览器
        
        Args:
            data_source: 数据源函数，接受 (offset, limit, sort_field, sort_order) 参数
            default_config: 默认配置
        """
        self.data_source = data_source
        self.default_config = default_config or BrowserConfig()
        self.states: Dict[str, BrowserState] = {}  # 用户状态存储
    
    def get_user_state(self, user_id: str) -> BrowserState:
        """获取用户浏览状态"""
        if user_id not in self.states:
            self.states[user_id] = BrowserState(config=BrowserConfig(
                page_size=self.default_config.page_size,
                sort_field=self.default_config.sort_field,
                sort_order=self.default_config.sort_order,
                visible_fields=self.default_config.visible_fields.copy() if self.default_config.visible_fields else None
            ))
        return self.states[user_id]
    
    def update_config(self, user_id: str, **kwargs) -> None:
        """更新用户配置"""
        state = self.get_user_state(user_id)
        for key, value in kwargs.items():
            if hasattr(state.config, key):
                setattr(state.config, key, value)
        # 重置到第一页
        state.current_page = 1
    
    async def get_page_data(self, user_id: str, page: int = None) -> Dict[str, Any]:
        """获取页面数据"""
        state = self.get_user_state(user_id)
        
        if page is not None:
            state.current_page = max(1, page)
        
        # 计算偏移量
        offset = (state.current_page - 1) * state.config.page_size
        
        try:
            # 获取数据
            result = await self.data_source(
                offset=offset,
                limit=state.config.page_size,
                sort_field=state.config.sort_field.value,
                sort_order=state.config.sort_order.value
            )
            
            items = result.get('items', [])
            total_count = result.get('total', 0)
            state.total_items = total_count
            
            # 计算页面信息
            total_pages = (total_count + state.config.page_size - 1) // state.config.page_size if total_count > 0 else 1
            
            # 确保当前页面有效
            if state.current_page > total_pages:
                state.current_page = total_pages
                return await self.get_page_data(user_id, state.current_page)
            
            return {
                'items': items,
                'page_info': {
                    'current_page': state.current_page,
                    'total_pages': total_pages,
                    'total_items': total_count,
                    'page_size': state.config.page_size,
                    'has_prev': state.current_page > 1,
                    'has_next': state.current_page < total_pages,
                    'start_item': offset + 1 if total_count > 0 else 0,
                    'end_item': min(offset + state.config.page_size, total_count)
                },
                'config': state.config
            }
            
        except Exception as e:
            logger.error(f"获取页面数据失败: {e}")
            return {
                'items': [],
                'page_info': {
                    'current_page': 1,
                    'total_pages': 1,
                    'total_items': 0,
                    'page_size': state.config.page_size,
                    'has_prev': False,
                    'has_next': False,
                    'start_item': 0,
                    'end_item': 0
                },
                'config': state.config
            }
    
    def create_navigation_keyboard(
        self, 
        user_id: str, 
        callback_prefix: str,
        page_info: Dict[str, Any],
        show_settings: bool = True
    ) -> InlineKeyboardMarkup:
        """创建导航键盘"""
        keyboard = []
        
        # 页面导航行
        nav_buttons = []
        
        # 首页按钮
        if page_info['current_page'] > 2:
            nav_buttons.append(InlineKeyboardButton(
                text="⏮️ 首页",
                callback_data=f"{callback_prefix}_page_1"
            ))
        
        # 上一页按钮
        if page_info['has_prev']:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ 上页",
                callback_data=f"{callback_prefix}_page_{page_info['current_page'] - 1}"
            ))
        
        # 页面信息按钮（可点击跳转）
        nav_buttons.append(InlineKeyboardButton(
            text=f"📄 {page_info['current_page']}/{page_info['total_pages']}",
            callback_data=f"{callback_prefix}_goto_page"
        ))
        
        # 下一页按钮
        if page_info['has_next']:
            nav_buttons.append(InlineKeyboardButton(
                text="▶️ 下页",
                callback_data=f"{callback_prefix}_page_{page_info['current_page'] + 1}"
            ))
        
        # 末页按钮
        if page_info['current_page'] < page_info['total_pages'] - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="⏭️ 末页",
                callback_data=f"{callback_prefix}_page_{page_info['total_pages']}"
            ))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # 设置按钮行
        if show_settings:
            settings_buttons = [
                InlineKeyboardButton(
                    text="⚙️ 浏览设置",
                    callback_data=f"{callback_prefix}_settings"
                ),
                InlineKeyboardButton(
                    text="🔄 刷新",
                    callback_data=f"{callback_prefix}_refresh"
                )
            ]
            keyboard.append(settings_buttons)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def create_settings_keyboard(
        self, 
        user_id: str, 
        callback_prefix: str
    ) -> InlineKeyboardMarkup:
        """创建设置键盘"""
        state = self.get_user_state(user_id)
        keyboard = []
        
        # 每页条数设置
        page_size_buttons = [
            InlineKeyboardButton(
                text=f"📊 每页: {state.config.page_size}条",
                callback_data=f"{callback_prefix}_set_page_size"
            )
        ]
        keyboard.append(page_size_buttons)
        
        # 排序设置
        sort_buttons = [
            InlineKeyboardButton(
                text=f"📅 排序: {state.config.sort_field.value}",
                callback_data=f"{callback_prefix}_set_sort_field"
            ),
            InlineKeyboardButton(
                text=f"🔄 顺序: {'升序' if state.config.sort_order == SortOrder.ASC else '降序'}",
                callback_data=f"{callback_prefix}_toggle_sort_order"
            )
        ]
        keyboard.append(sort_buttons)
        
        # 字段显示设置
        field_buttons = [
            InlineKeyboardButton(
                text="🏷️ 显示字段",
                callback_data=f"{callback_prefix}_set_fields"
            )
        ]
        keyboard.append(field_buttons)
        
        # 返回按钮
        back_buttons = [
            InlineKeyboardButton(
                text="↩️ 返回浏览",
                callback_data=f"{callback_prefix}_back_to_browse"
            )
        ]
        keyboard.append(back_buttons)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def create_page_size_keyboard(
        self, 
        callback_prefix: str
    ) -> InlineKeyboardMarkup:
        """创建每页条数选择键盘"""
        keyboard = []
        
        # 常用条数选择
        size_options = [5, 10, 15, 20, 30, 50]
        
        for i in range(0, len(size_options), 3):
            row = []
            for j in range(3):
                if i + j < len(size_options):
                    size = size_options[i + j]
                    row.append(InlineKeyboardButton(
                        text=f"{size}条",
                        callback_data=f"{callback_prefix}_page_size_{size}"
                    ))
            keyboard.append(row)
        
        # 返回按钮
        keyboard.append([
            InlineKeyboardButton(
                text="↩️ 返回设置",
                callback_data=f"{callback_prefix}_back_to_settings"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def create_sort_field_keyboard(
        self, 
        callback_prefix: str
    ) -> InlineKeyboardMarkup:
        """创建排序字段选择键盘"""
        keyboard = []
        
        # 时间字段选择
        field_options = [
            (TimeField.CREATED_AT, "创建时间"),
            (TimeField.UPDATED_AT, "更新时间"),
            (TimeField.REVIEWED_AT, "审核时间"),
            (TimeField.REPLIED_AT, "回复时间")
        ]
        
        for field, name in field_options:
            keyboard.append([
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"{callback_prefix}_sort_field_{field.value}"
                )
            ])
        
        # 返回按钮
        keyboard.append([
            InlineKeyboardButton(
                text="↩️ 返回设置",
                callback_data=f"{callback_prefix}_back_to_settings"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def create_visible_fields_keyboard(
        self, 
        callback_prefix: str,
        current_fields: List[str] = None
    ) -> InlineKeyboardMarkup:
        """创建显示字段选择键盘"""
        keyboard = []
        
        # 根据回调前缀确定数据类型
        if "requests" in callback_prefix:
            # 求片请求字段
            available_fields = {
                'id': 'ID',
                'title': '标题',
                'content': '内容',
                'status': '状态',
                'created_at': '创建时间',
                'updated_at': '更新时间',
                'user_id': '用户ID'
            }
        elif "submissions" in callback_prefix:
            # 投稿内容字段
            available_fields = {
                'id': 'ID',
                'title': '标题',
                'content': '内容',
                'status': '状态',
                'created_at': '创建时间',
                'updated_at': '更新时间',
                'reviewed_at': '审核时间',
                'user_id': '用户ID'
            }
        elif "feedback" in callback_prefix:
            # 用户反馈字段
            available_fields = {
                'id': 'ID',
                'feedback_type': '反馈类型',
                'content': '内容',
                'status': '状态',
                'created_at': '创建时间',
                'replied_at': '回复时间',
                'user_id': '用户ID'
            }
        elif "users" in callback_prefix:
            # 用户信息字段
            available_fields = {
                'id': 'ID',
                'username': '用户名',
                'full_name': '姓名',
                'role': '角色',
                'created_at': '创建时间',
                'last_activity_at': '最后活跃'
            }
        else:
            # 默认字段（管理员操作等）
            available_fields = {
                'id': 'ID',
                'action_type': '操作类型',
                'description': '描述',
                'created_at': '创建时间',
                'admin_id': '管理员ID'
            }
        
        if current_fields is None:
            current_fields = list(available_fields.keys())[:4]  # 默认前4个字段
        
        # 字段选择按钮（每行2个）
        row = []
        for field, name in available_fields.items():
            is_selected = field in current_fields
            text = f"✅ {name}" if is_selected else f"⬜ {name}"
            
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=f"{callback_prefix}_toggle_field_{field}"
            ))
            
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        # 添加剩余的按钮
        if row:
            keyboard.append(row)
        
        # 返回按钮
        keyboard.append([
            InlineKeyboardButton(
                text="↩️ 返回设置",
                callback_data=f"{callback_prefix}_back_to_settings"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def format_item_display(
        self, 
        item: Any, 
        visible_fields: List[str] = None,
        field_formatters: Dict[str, Callable] = None
    ) -> str:
        """格式化单个项目显示"""
        if visible_fields is None:
            # 默认显示字段
            visible_fields = ['id', 'title', 'status', 'created_at']
        
        if field_formatters is None:
            field_formatters = {}
        
        lines = []
        
        for field in visible_fields:
            if hasattr(item, field):
                value = getattr(item, field)
                
                # 使用自定义格式化器
                if field in field_formatters:
                    formatted_value = field_formatters[field](value)
                else:
                    # 默认格式化
                    if isinstance(value, datetime):
                        formatted_value = value.strftime('%Y-%m-%d %H:%M')
                    elif value is None:
                        formatted_value = "无"
                    else:
                        formatted_value = str(value)
                
                # 字段名称映射
                field_names = {
                    'id': 'ID',
                    'title': '标题',
                    'status': '状态',
                    'created_at': '创建时间',
                    'updated_at': '更新时间',
                    'reviewed_at': '审核时间',
                    'user_id': '用户ID',
                    'category_id': '分类',
                    'description': '描述'
                }
                
                field_display = field_names.get(field, field)
                lines.append(f"{field_display}: {formatted_value}")
        
        return "\n".join(lines)
    
    def format_page_header(
        self, 
        title: str, 
        page_info: Dict[str, Any], 
        config: BrowserConfig
    ) -> str:
        """格式化页面标题"""
        sort_order_text = "升序" if config.sort_order == SortOrder.ASC else "降序"
        
        header = f"📋 {title}\n\n"
        header += f"📄 第 {page_info['current_page']}/{page_info['total_pages']} 页 "
        header += f"(共 {page_info['total_items']} 条)\n"
        header += f"📊 每页 {page_info['page_size']} 条 | "
        header += f"📅 按 {config.sort_field.value} {sort_order_text}\n"
        header += "─" * 30 + "\n\n"
        
        return header


# 便捷函数
def create_browser_for_reviews(data_source_func: Callable) -> AdvancedBrowser:
    """为审核数据创建浏览器"""
    default_config = BrowserConfig(
        page_size=10,
        sort_field=TimeField.CREATED_AT,
        sort_order=SortOrder.ASC,
        visible_fields=['id', 'title', 'status', 'created_at', 'user_id']
    )
    return AdvancedBrowser(data_source_func, default_config)


def create_browser_for_feedback(data_source_func: Callable) -> AdvancedBrowser:
    """为反馈数据创建浏览器"""
    default_config = BrowserConfig(
        page_size=10,
        sort_field=TimeField.CREATED_AT,
        sort_order=SortOrder.ASC,
        visible_fields=['id', 'feedback_type', 'status', 'created_at', 'user_id']
    )
    return AdvancedBrowser(data_source_func, default_config)


def create_browser_for_users(data_source_func: Callable) -> AdvancedBrowser:
    """为用户数据创建浏览器"""
    default_config = BrowserConfig(
        page_size=15,
        sort_field=TimeField.CREATED_AT,
        sort_order=SortOrder.ASC,
        visible_fields=['id', 'username', 'full_name', 'role', 'created_at']
    )
    return AdvancedBrowser(data_source_func, default_config)