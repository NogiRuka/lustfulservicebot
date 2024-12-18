from aiogram.fsm.state import State, StatesGroup


class Wait(StatesGroup):
    """
    Here you can add your states
    """

    waitAnnounce = State()
