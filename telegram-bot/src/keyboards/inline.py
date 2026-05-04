from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.utils.callback_factories import (
    CreditActions,
    CreditCallback,
    LanguageCallback,
    LanguageCodes,
    MainMenuActions,
    MainMenuCallback,
    PlanActions,
    PlanCallback,
    RegionActions,
    RegionCallback,
    ResumeActions,
    ResumeCallback,
    ResumeCreationActions,
    ResumeCreationCallback,
    UploadActions,
    UploadConfirmCallback,
)
from src.utils.i18n import gettext as _
from src.utils.regions import REGIONS, get_region_label


def create_main_menu_keyboard(user_lang: str | None = None, has_subscription: bool = False) -> InlineKeyboardMarkup:
    keyboard_buttons = []

    # Add action buttons
    action_buttons = [
        [
            InlineKeyboardButton(
                text=_("create_new_resume", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.CREATE_NEW).pack(),
            ),
            InlineKeyboardButton(
                text=_("upload_existing_resume", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.UPLOAD_EXISTING).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=_("view_delete_resumes", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.VIEW_DELETE).pack(),
            ),
            InlineKeyboardButton(
                text=_("find_jobs", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.JOB_SEARCH).pack(),
            ),
        ],
        # Temporarily disabled — no logic yet
        # [
        #     InlineKeyboardButton(
        #         text=_("career_tips", locale=user_lang),
        #         callback_data=MainMenuCallback(action=MainMenuActions.CAREER_TIPS).pack(),
        #     ),
        #     InlineKeyboardButton(
        #         text=_("interview_practice", locale=user_lang),
        #         callback_data=MainMenuCallback(action=MainMenuActions.INTERVIEW_PRACTICE).pack(),
        #     ),
        # ],
    ]

    # Feedback + Regions row.
    # Pro subscription button is temporarily disabled (kept in source for later re-enable);
    # its slot is now used by the region preference button so users can configure
    # preferred regions without having to remember the /regions command.
    action_buttons.append(
        [
            InlineKeyboardButton(
                text=_("feedback_btn", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.FEEDBACK).pack(),
            ),
            InlineKeyboardButton(
                text=_("select_regions_btn", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.SELECT_REGIONS).pack(),
            ),
            # InlineKeyboardButton(
            #     text=_("pro_features_btn", locale=user_lang),
            #     callback_data=MainMenuCallback(action=MainMenuActions.PRO_SUBSCRIPTION).pack(),
            # ),
        ]
    )

    keyboard_buttons.extend(action_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_language_keyboard(is_registered=True) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text="🇺🇿 O'zbekcha",
                callback_data=LanguageCallback(lang_code=LanguageCodes.UZBEK, is_registered=is_registered).pack(),
            ),
            InlineKeyboardButton(
                text="🇷🇺 Русский",
                callback_data=LanguageCallback(lang_code=LanguageCodes.RUSSIAN, is_registered=is_registered).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🇬🇧 English",
                callback_data=LanguageCallback(lang_code=LanguageCodes.ENGLISH, is_registered=is_registered).pack(),
            ),
            InlineKeyboardButton(
                text="🇺🇿 Ўзбекча",
                callback_data=LanguageCallback(lang_code=LanguageCodes.UZBEK_CYR, is_registered=is_registered).pack(),
            ),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_language_keyboard_for_resume(user_lang) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text="🇺🇿 O'zbekcha",
                callback_data=LanguageCallback(
                    lang_code=LanguageCodes.UZBEK,
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🇷🇺 Русский",
                callback_data=LanguageCallback(
                    lang_code=LanguageCodes.RUSSIAN,
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=_("back", locale=user_lang), callback_data=MainMenuCallback(action=MainMenuActions.GO_MAIN).pack()
            ),
            InlineKeyboardButton(
                text="🇬🇧 English",
                callback_data=LanguageCallback(
                    lang_code=LanguageCodes.ENGLISH,
                ).pack(),
            ),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_resume_confirmation_keyboard(user_lang: str | None = None) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=_("confirm_button", locale=user_lang),
                callback_data=ResumeCreationCallback(action=ResumeCreationActions.CONFIRM).pack(),
            ),
            InlineKeyboardButton(
                text=_("cancel_button", locale=user_lang),
                callback_data=ResumeCreationCallback(action=ResumeCreationActions.CANCEL).pack(),
            ),
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_resume_management_keyboard(
    resume_id: str, user_lang: str | None = None, show_delete: bool = True
) -> InlineKeyboardMarkup:
    keyboard_buttons = []

    if show_delete:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=_("delete_button", locale=user_lang),
                    callback_data=ResumeCallback(action=ResumeActions.DELETE, resume_id=resume_id).pack(),
                )
            ]
        )

    # Add back button
    keyboard_buttons.append(
        [
            InlineKeyboardButton(
                text=_("back", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.VIEW_DELETE).pack(),
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_delete_confirmation_keyboard(resume_id: str, user_lang: str | None = None) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=_("cancel", locale=user_lang),
                callback_data=ResumeCallback(action=ResumeActions.VIEW, resume_id=resume_id).pack(),
            ),
            InlineKeyboardButton(
                text=_("yes_delete", locale=user_lang),
                callback_data=ResumeCallback(action=ResumeActions.CONFIRM_DELETE, resume_id=resume_id).pack(),
                style="danger",
            ),
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_back_to_main_keyboard(user_lang: str | None = None) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=_("back_to_main_menu", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.GO_MAIN).pack(),
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_choose_subscription_keyboard(user_lang: str | None = None) -> InlineKeyboardMarkup:
    choose_subscription_keyboard = [
        [
            InlineKeyboardButton(
                text=_("choose_plan", locale=user_lang),
                callback_data=PlanCallback(action=PlanActions.VIEW_PLANS).pack(),
                style="primary",
                icon_custom_emoji_id="5314657317357110742",
            )
        ],
        [
            InlineKeyboardButton(
                text=_("back", locale=user_lang), callback_data=MainMenuCallback(action=MainMenuActions.GO_MAIN).pack()
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=choose_subscription_keyboard)


def create_active_subscription_keyboard(user_lang: str | None = None) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=_("extend_subscription", locale=user_lang),
                callback_data=PlanCallback(action=PlanActions.VIEW_PLANS).pack(),
                style="primary",
                icon_custom_emoji_id="5314657317357110742",
            )
        ],
        [
            InlineKeyboardButton(
                text=_("back", locale=user_lang), callback_data=MainMenuCallback(action=MainMenuActions.GO_MAIN).pack()
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_subscription_plans_keyboard(user_lang: str, prices: str) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=_(
                    "3_month_plan_btn",
                    month_3_price=prices["quarterly"],
                    save_money=prices["savings"],
                    locale=user_lang,
                ),
                callback_data=PlanCallback(action=PlanActions.CHOOSE_PLAN, plan_id="quarterly").pack(),
                style="success",
            )
        ],
        [
            InlineKeyboardButton(
                text=_("1_month_plan_btn", month_1_price=prices["monthly"], locale=user_lang),
                callback_data=PlanCallback(action=PlanActions.CHOOSE_PLAN, plan_id="monthly").pack(),
                style="primary",
            )
        ],
        [
            InlineKeyboardButton(
                text=_("back", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.PRO_SUBSCRIPTION).pack(),
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_subscription_back_keyboard(user_lang: str | None = None) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=_("back", locale=user_lang), callback_data=PlanCallback(action=PlanActions.VIEW_PLANS).pack()
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_pro_keyboard(
    user_lang: str | None = None, display_get_pro: bool = True, display_get_credit: bool = False
) -> InlineKeyboardMarkup:
    keyboard_buttons = []

    if display_get_credit:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=_("buy_credits", locale=user_lang),
                    callback_data=CreditCallback(action=CreditActions.BUY_CREDITS).pack(),
                )
            ]
        )

    if display_get_pro:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=_("get_pro", locale=user_lang),
                    callback_data=MainMenuCallback(action=MainMenuActions.PRO_SUBSCRIPTION).pack(),
                    style="primary",
                    icon_custom_emoji_id="5361922594930963709",
                )
            ]
        )

    keyboard_buttons.append(
        [
            InlineKeyboardButton(
                text=_("back_to_main_menu", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.GO_MAIN).pack(),
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_credit_purchase_keyboard(user_lang: str | None = None) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=_("credit_option_1", locale=user_lang),
                callback_data=CreditCallback(action=CreditActions.CHOOSE_AMOUNT, credit_amount=1).pack(),
            ),
            InlineKeyboardButton(
                text=_("credit_option_2", locale=user_lang),
                callback_data=CreditCallback(action=CreditActions.CHOOSE_AMOUNT, credit_amount=2).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=_("credit_option_3", locale=user_lang),
                callback_data=CreditCallback(action=CreditActions.CHOOSE_AMOUNT, credit_amount=3).pack(),
            ),
            InlineKeyboardButton(
                text=_("pro_subscription", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.PRO_SUBSCRIPTION).pack(),
                style="primary",
                icon_custom_emoji_id="5361922594930963709",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_("back", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.CREATE_NEW).pack(),
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_credits_back_keyboard(user_lang: str | None = None) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text=_("back", locale=user_lang), callback_data=CreditCallback(action=CreditActions.BUY_CREDITS).pack()
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_resume_confirmation_keyboard(user_lang: str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("confirm_button", locale=user_lang),
                    callback_data=UploadConfirmCallback(action=UploadActions.CONFIRM).pack(),
                ),
                InlineKeyboardButton(
                    text=_("cancel_button", locale=user_lang),
                    callback_data=UploadConfirmCallback(action=UploadActions.CANCEL).pack(),
                ),
            ]
        ]
    )

    return keyboard


def get_profile_image_keyboard(user_lang: str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("skip_button", locale=user_lang), callback_data="profile_photo_skip")]
        ]
    )

    return keyboard


def create_region_keyboard(selected_slugs: list[str], user_lang: str) -> InlineKeyboardMarkup:
    """Two-column toggle keyboard for region preference selection.

    Each button shows a check prefix when selected. Bottom rows provide
    'Unselect All | Select All' and a 'Save' button.
    """
    rows = []
    selected = set(selected_slugs)

    # Pair up regions into rows of 2
    for i in range(0, len(REGIONS), 2):
        pair = REGIONS[i : i + 2]
        row = []
        for region in pair:
            slug = region["slug"]
            label = get_region_label(slug, user_lang)
            prefix = "✅ " if slug in selected else ""
            row.append(
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=RegionCallback(action=RegionActions.TOGGLE, slug=slug).pack(),
                )
            )
        rows.append(row)

    # Select All / Unselect All row
    rows.append(
        [
            InlineKeyboardButton(
                text=_("unselect_all_regions", locale=user_lang),
                callback_data=RegionCallback(action=RegionActions.UNSELECT_ALL).pack(),
            ),
            InlineKeyboardButton(
                text=_("select_all_regions", locale=user_lang),
                callback_data=RegionCallback(action=RegionActions.SELECT_ALL).pack(),
            ),
        ]
    )

    # Save row
    rows.append(
        [
            InlineKeyboardButton(
                text=_("save_regions", locale=user_lang),
                callback_data=RegionCallback(action=RegionActions.SAVE).pack(),
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
