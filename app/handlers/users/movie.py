from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.states import Wait
from app.database.business import create_movie_request, get_user_movie_requests
from app.utils.submission_utils import SubmissionConfig, SubmissionHandler
from app.utils.pagination import extract_page_from_callback

movie_router = Router()

# 求片配置
movie_config = SubmissionConfig(
    item_type='movie',
    emoji='🎬',
    name='求片',
    center_title='求片中心',
    feature_key='movie_request_enabled',
    create_function=create_movie_request,
    get_user_items_function=get_user_movie_requests,
    title_state=Wait.waitMovieTitle,
    content_state=Wait.waitMovieDescription,
    title_field='片名',
    content_field='description',
    content_label='描述'
)

# 求片处理器
movie_handler = SubmissionHandler(movie_config)


@movie_router.callback_query(F.data == "movie_center")
async def cb_movie_center(cb: types.CallbackQuery):
    """求片中心"""
    await movie_handler.handle_center(cb)


@movie_router.callback_query(F.data == "movie_request_new")
async def cb_movie_request_new(cb: types.CallbackQuery, state: FSMContext):
    """开始求片 - 选择类型"""
    await movie_handler.handle_new_submission(cb, state)


@movie_router.callback_query(F.data.startswith("select_movie_category_"))
async def cb_select_category(cb: types.CallbackQuery, state: FSMContext):
    """选择求片类型"""
    category_id = int(cb.data.split("_")[-1])
    await movie_handler.handle_category_selection(cb, state, category_id)


@movie_router.message(StateFilter(Wait.waitMovieTitle))
async def process_movie_title(msg: types.Message, state: FSMContext):
    """处理片名输入"""
    await movie_handler.handle_title_input(msg, state)


@movie_router.callback_query(F.data == "skip_description")
async def cb_skip_description(cb: types.CallbackQuery, state: FSMContext):
    """跳过描述"""
    await movie_handler.handle_skip_content(cb, state)


@movie_router.message(StateFilter(Wait.waitMovieDescription))
async def process_movie_description(msg: types.Message, state: FSMContext):
    """处理描述输入（支持文本和图片）"""
    await movie_handler.handle_content_input(msg, state)


@movie_router.callback_query(F.data == "edit_movie_description")
async def cb_edit_movie_description(cb: types.CallbackQuery, state: FSMContext):
    """重新编辑描述"""
    await movie_handler.handle_edit_content(cb, state)


@movie_router.callback_query(F.data == "confirm_movie_submit")
async def cb_confirm_movie_submit(cb: types.CallbackQuery, state: FSMContext):
    """确认提交求片"""
    await movie_handler.handle_confirm_submission(cb, state)


@movie_router.callback_query(F.data == "movie_request_my")
async def cb_movie_request_my(cb: types.CallbackQuery):
    """我的求片"""
    await movie_handler.handle_my_submissions(cb)


@movie_router.callback_query(F.data.startswith("my_movie_page_"))
async def cb_movie_request_my_page(cb: types.CallbackQuery):
    """我的求片分页"""
    page = extract_page_from_callback(cb.data, "my_movie")
    await movie_handler.handle_my_submissions(cb, page)