from typing import List, Any, Callable
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Paginator:
    """分页工具类"""
    
    def __init__(self, items: List[Any], page_size: int = 5):
        self.items = items
        self.page_size = page_size
        self.total_items = len(items)
        self.total_pages = (self.total_items + page_size - 1) // page_size if self.total_items > 0 else 1
    
    def get_page_items(self, page: int) -> List[Any]:
        """获取指定页面的数据"""
        if page < 1 or page > self.total_pages:
            return []
        
        start_idx = (page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, self.total_items)
        return self.items[start_idx:end_idx]
    
    def get_page_info(self, page: int) -> dict:
        """获取页面信息"""
        return {
            'current_page': page,
            'total_pages': self.total_pages,
            'total_items': self.total_items,
            'page_size': self.page_size,
            'has_prev': page > 1,
            'has_next': page < self.total_pages,
            'start_item': (page - 1) * self.page_size + 1 if self.total_items > 0 else 0,
            'end_item': min(page * self.page_size, self.total_items)
        }
    
    def create_pagination_keyboard(
        self, 
        page: int, 
        callback_prefix: str,
        extra_buttons: List[List[InlineKeyboardButton]] = None
    ) -> InlineKeyboardMarkup:
        """创建分页键盘"""
        keyboard = []
        
        # 分页按钮行
        if self.total_pages > 1:
            page_buttons = []
            
            # 上一页按钮
            if page > 1:
                page_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ 上一页",
                        callback_data=f"{callback_prefix}_page_{page - 1}"
                    )
                )
            
            # 页码信息
            page_buttons.append(
                InlineKeyboardButton(
                    text=f"{page}/{self.total_pages}",
                    callback_data="page_info"
                )
            )
            
            # 下一页按钮
            if page < self.total_pages:
                page_buttons.append(
                    InlineKeyboardButton(
                        text="下一页 ➡️",
                        callback_data=f"{callback_prefix}_page_{page + 1}"
                    )
                )
            
            keyboard.append(page_buttons)
        
        # 添加额外按钮
        if extra_buttons:
            keyboard.extend(extra_buttons)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


def format_page_header(title: str, page_info: dict) -> str:
    """格式化页面标题"""
    if page_info['total_items'] == 0:
        return f"{title}\n\n暂无数据"
    
    header = f"{title}\n\n"
    header += f"📊 总计：{page_info['total_items']} 条记录\n"
    
    if page_info['total_pages'] > 1:
        header += f"📄 第 {page_info['current_page']}/{page_info['total_pages']} 页 "
        header += f"(第 {page_info['start_item']}-{page_info['end_item']} 条)\n\n"
    else:
        header += "\n"
    
    return header


def extract_page_from_callback(callback_data: str, prefix: str) -> int:
    """从回调数据中提取页码"""
    try:
        if callback_data.startswith(f"{prefix}_page_"):
            return int(callback_data.split("_page_")[-1])
    except (ValueError, IndexError):
        pass
    return 1