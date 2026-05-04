"""Callback data factories for inline keyboards.

This module provides type-safe callback data factories for all inline keyboard
buttons in the bot. Using these factories ensures consistency and prevents
callback data parsing errors.
"""

from aiogram.filters.callback_data import CallbackData


class ResumeCallback(CallbackData, prefix="resume"):
    """Callback data for resume-related actions.

    Attributes:
        action: The action to perform (view, delete, confirm_delete, etc.)
        resume_id: The ID of the resume to operate on
    """

    action: str
    resume_id: str


class MainMenuCallback(CallbackData, prefix="main"):
    """Callback data for main menu actions.

    Attributes:
        action: The action to perform (go_main, create_new, upload_existing, view_resumes)
    """

    action: str
    delete: bool | None = False


class ResumeCreationCallback(CallbackData, prefix="resume_creation"):
    """Callback data for resume creation flow actions.

    Attributes:
        action: The action to perform (confirm, cancel, confirm_uploaded, cancel_uploaded)
    """

    action: str


class UploadConfirmCallback(CallbackData, prefix="upload_confirm"):
    """Callback factory for upload confirmation."""

    action: str


class VacancyCallback(CallbackData, prefix="vacancy"):
    """Callback data for vacancy-related actions.

    Attributes:
        action: The action to perform (apply_confirm, apply_cancel, select_anyway)
        vacancy_id: Optional vacancy ID for specific operations
        resume_id: Optional resume ID for specific operations
    """

    action: str
    vacancy_id: str | None = ""
    resume_id: str | None = ""


class JobSearchCallback(CallbackData, prefix="jobsearch"):
    """Callback data for job search flow."""

    action: str
    resume_id: str | None = ""
    vacancy_id: str | None = ""
    page: int | None = 0


class LanguageCallback(CallbackData, prefix="lang"):
    """Callback data for language selection.

    Attributes:
        lang_code: The selected language code (uz, ru, en)
    """

    lang_code: str
    is_registered: bool = False


class PlanCallback(CallbackData, prefix="plan"):
    """Callback data for subscription plan actions.

    Attributes:
        action: The action to perform (choose_plan, subscribe, etc.)
        plan_id: Optional plan ID for specific operations
    """

    action: str
    plan_id: str | None = ""


class CreditCallback(CallbackData, prefix="credit"):
    """Callback data for credit purchase actions.

    Attributes:
        action: The action to perform (buy_credits, etc.)
        credit_amount: Optional credit amount for specific operations
    """

    action: str
    credit_amount: int | None = 0


# Predefined action constants for better maintainability
class ResumeActions:
    """Predefined resume action constants."""

    VIEW = "view"
    DELETE = "delete"
    CONFIRM_DELETE = "confirm_delete"
    DOWNLOAD = "download"
    ENHANCE = "enhance"
    SELECT = "select"
    SELECT_ANYWAY = "select_anyway"
    CONFIRM = "confirm"
    CANCEL = "cancel"


class MainMenuActions:
    """Predefined main menu action constants."""

    GO_MAIN = "go_main"
    CREATE_NEW = "create_new"
    UPLOAD_EXISTING = "upload_existing"
    VIEW_DELETE = "view_delete"
    JOB_SEARCH = "job_search"
    CAREER_TIPS = "career_tips"
    INTERVIEW_PRACTICE = "interview_practice"
    PRO_SUBSCRIPTION = "pro_subscription"
    FEEDBACK = "feedback"
    SELECT_REGIONS = "select_regions"


class ResumeCreationActions:
    """Predefined resume creation action constants."""

    CONFIRM_UPLOADED = "confirm_uploaded"
    CANCEL_UPLOADED = "cancel_uploaded"
    CONFIRM = "confirm"
    CANCEL = "cancel"


class PlanActions:
    """Predefined plan action constants."""

    VIEW_PLANS = "view_plans"
    CHOOSE_PLAN = "choose_plan"
    SUBSCRIBE = "subscribe"


class CreditActions:
    """Predefined credit action constants."""

    BUY_CREDITS = "buy_credits"
    CHOOSE_AMOUNT = "choose_amount"


class LanguageCodes:
    """Predefined language code constants."""

    UZBEK = "uz"
    UZBEK_CYR = "cyr"
    RUSSIAN = "ru"
    ENGLISH = "en"


class UploadActions:
    CONFIRM = "confirm"
    CANCEL = "cancel"


class JobSearchActions:
    SELECT_RESUME = "select"
    VIEW_DETAIL = "detail"
    BACK_TO_RESULTS = "back"


class RegionCallback(CallbackData, prefix="region"):
    """Callback data for region preference selection."""

    action: str  # "toggle", "select_all", "unselect_all", "save"
    slug: str = ""


class RegionActions:
    TOGGLE = "toggle"
    SELECT_ALL = "select_all"
    UNSELECT_ALL = "unselect_all"
    SAVE = "save"
