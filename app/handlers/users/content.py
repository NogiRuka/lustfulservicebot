from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import create_content_submission, get_user_content_submissions
from app.utils.submission_utils import SubmissionConfig, SubmissionHandler
from app.utils.pagination import extract_page_from_callback

content_router = Router()

# 投稿配置
content_config = SubmissionConfig(
    item_type='content',
    emoji='📝',
    name='投稿',
    center_title='内容投稿中心',
    feature_key='content_submit_enabled',
    create_function=create_content_submission,
    get_user_items_function=get_user_content_submissions,
    title_state=Wait.waitContentTitle,
    content_state=Wait.waitContentBody,
    title_field='标题',
    content_field='body',
    content_label='内容',
    new_callback='content_submit_new',
    my_callback='content_submit_my'
)

# 投稿处理器
content_handler = SubmissionHandler(content_config)


@content_router.callback_query(F.data == "content_center")
async def cb_content_center(cb: types.CallbackQuery):
    """内容投稿中心"""
    await content_handler.handle_center(cb)


@content_router.callback_query(F.data == "content_submit_new")
async def cb_content_submit_new(cb: types.CallbackQuery, state: FSMContext):
    """开始投稿 - 选择类型"""
    await content_handler.handle_new_submission(cb, state)
    
    # 创建类型选择键盘
    keyboard = []
    for category in categories:
        keyboard.append([types.InlineKeyboardButton(
            text=f"📂 {category.name}",
            callback_data=f"select_content_category_{category.id}"
        )])
    
    # 添加通用内容选项
    keyboard.append([types.InlineKeyboardButton(
        text="📄 通用内容（无分类）",
        callback_data="select_content_category_0"
    )])
    
    keyboard.append([types.InlineKeyboardButton(
        text="🔙 返回",
        callback_data="content_center"
    )])
    
    category_kb = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await cb.message.edit_caption(
        caption="📝 <b>开始投稿</b>\n\n请选择内容类型：",
        reply_markup=category_kb
    )
    # 保存消息ID用于后续编辑
    await state.update_data(message_id=cb.message.message_id)
    await cb.answer()


@content_router.callback_query(F.data.startswith("select_content_category_"))
async def cb_select_content_category(cb: types.CallbackQuery, state: FSMContext):
    """选择投稿类型"""
    category_id = int(cb.data.split("_")[-1])
    await content_handler.handle_category_selection(cb, state, category_id)


@content_router.message(StateFilter(Wait.waitContentTitle))
async def process_content_title(msg: types.Message, state: FSMContext):
    """处理投稿标题"""
    await content_handler.handle_title_input(msg, state)


@content_router.message(StateFilter(Wait.waitContentBody))
async def process_content_body(msg: types.Message, state: FSMContext):
    """处理投稿内容（支持文本、图片、文件）"""
    await content_handler.handle_content_input(msg, state)


@content_router.callback_query(F.data == "edit_content_body")
async def cb_edit_content_body(cb: types.CallbackQuery, state: FSMContext):
    """重新编辑投稿内容"""
    await content_handler.handle_edit_content(cb, state)


@content_router.callback_query(F.data == "confirm_content_submit")
async def cb_confirm_content_submit(cb: types.CallbackQuery, state: FSMContext):
    """确认提交投稿"""
    await content_handler.handle_confirm_submit(cb, state)


@content_router.callback_query(F.data == "content_submit_my")
async def cb_content_submit_my(cb: types.CallbackQuery):
    """我的投稿"""
    await content_handler.handle_my_submissions(cb)


@content_router.callback_query(F.data.startswith("my_content_page_"))
async def cb_content_submit_my_page(cb: types.CallbackQuery):
    """我的投稿分页"""
    page = extract_page_from_callback(cb.data, "my_content")
    await content_handler.handle_my_submissions(cb, page)