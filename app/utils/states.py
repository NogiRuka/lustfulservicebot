from aiogram.fsm.state import State, StatesGroup


class Wait(StatesGroup):
    """
    状态定义：这里可以继续补充需要的状态。
    """

    waitAnnounce = State()
    
    # 求片中心状态
    waitMovieTitle = State()
    waitMovieDescription = State()
    
    # 内容投稿状态
    waitContentTitle = State()
    waitContentBody = State()
    waitContentFile = State()
    
    # 用户反馈状态
    waitFeedbackContent = State()
    
    # 管理员回复状态
    waitAdminReply = State()
    
    # 审核留言状态
    waitReviewNote = State()
    
    # 超管添加管理员状态
    waitAdminUserId = State()
    waitCategoryName = State()
