from aiogram.fsm.state import State, StatesGroup


class MainMenuState(StatesGroup):
    """FSM states for main menu interactions."""

    LANGUAGE_SELECTION = State()


class PaymentStates(StatesGroup):
    """States for different payment types."""

    WAITING_SUBSCRIPTION_PAYMENT = State()
    WAITING_CREDITS_PAYMENT = State()


class UserUpdateStates(StatesGroup):
    """States for user update processes"""

    ASK_USER_NAME = State()
    UPDATE_USER_NAME = State()


class JobFeedStates(StatesGroup):
    """States for the job feed (Reels-style browsing)."""

    BROWSING = State()


class RegionStates(StatesGroup):
    """States for the /regions preference flow."""

    SELECTING = State()


class FeedbackStates(StatesGroup):
    """States for user feedback flow."""

    WAITING_FEEDBACK = State()
