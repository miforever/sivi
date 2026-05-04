from aiogram.fsm.state import State, StatesGroup


class ResumeState(StatesGroup):
    """FSM states for resume creation flow."""

    SELECT_RESUME_LANGUAGE = State()
    WAITING_FOR_ANSWER = State()
    UPLOAD_PHOTO = State()
    CONFIRM_RESUME = State()
    UPLOAD_RESUME = State()
    ASK_POSITION = State()
    UPLOAD_PROFILE_PHOTO = State()
    ASK_EMAIL = State()
    ASK_PHONE = State()
