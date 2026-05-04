"""Job search handlers — Reels-style one-at-a-time job browsing."""

import asyncio
import logging
import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LinkPreviewOptions,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from src.config import get_settings
from src.handlers.helpers import safe_callback_answer, safe_edit_message
from src.keyboards.inline import create_back_to_main_keyboard
from src.services.container import ServiceContainer
from src.services.states import JobFeedStates
from src.utils.callback_factories import (
    JobSearchActions,
    JobSearchCallback,
    MainMenuActions,
    MainMenuCallback,
)
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)
router = Router(name="job_search")
settings = get_settings()

# Background task set — prevents fire-and-forget tasks from being garbage-collected.
_background_tasks: set[asyncio.Task] = set()  # type: ignore[type-arg]


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.JOB_SEARCH))
async def job_search_entry(
    callback: CallbackQuery,
    services: ServiceContainer,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Entry point: show user's resumes to pick one for job matching."""
    await safe_callback_answer(callback)

    telegram_id = callback.from_user.id
    resumes = await services.backend.get_user_resumes(telegram_id)

    if not resumes:
        keyboard = create_back_to_main_keyboard(user_lang)
        await safe_edit_message(
            callback.message,
            _("job_no_resumes_for_search", locale=user_lang),
            reply_markup=keyboard,
        )
        return

    buttons = []
    for resume in resumes:
        title = resume.get("position") or resume.get("title") or "Resume"
        resume_id = str(resume.get("id", ""))
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📄 {title}",
                    callback_data=JobSearchCallback(
                        action=JobSearchActions.SELECT_RESUME,
                        resume_id=resume_id,
                    ).pack(),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text=_("back_to_main_menu", locale=user_lang),
                callback_data=MainMenuCallback(action=MainMenuActions.GO_MAIN).pack(),
            )
        ]
    )

    await safe_edit_message(
        callback.message,
        _("job_search_select_resume", locale=user_lang),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(JobSearchCallback.filter(F.action == JobSearchActions.SELECT_RESUME))
async def job_search_start_feed(
    callback: CallbackQuery,
    callback_data: JobSearchCallback,
    services: ServiceContainer,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Fetch first window of jobs and start the Reels-style feed."""
    await safe_callback_answer(callback)

    telegram_id = callback.from_user.id
    resume_id = callback_data.resume_id

    # Clear inline keyboard from resume selection message
    await safe_edit_message(
        callback.message,
        _("job_search_loading", locale=user_lang),
        reply_markup=None,
    )

    vacancies = await services.backend.find_matching_jobs(
        telegram_id=telegram_id,
        resume_id=resume_id,
        limit=settings.JOB_WINDOW_SIZE,
    )

    if not vacancies or (isinstance(vacancies, dict) and vacancies.get("error")):
        keyboard = create_back_to_main_keyboard(user_lang)
        await safe_edit_message(
            callback.message,
            _("job_search_no_results", locale=user_lang),
            reply_markup=keyboard,
        )
        return

    seen_ids = [v["id"] for v in vacancies]

    # Store feed state
    await state.set_state(JobFeedStates.BROWSING)
    await state.update_data(
        job_feed=vacancies,
        job_index=0,
        job_resume_id=resume_id,
        job_seen_ids=seen_ids,
        job_batch_ts=time.time(),
    )

    # Send 🔍 with reply keyboard (Next + Menu) — persists during browsing
    reply_kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("job_feed_menu", locale=user_lang)),
                KeyboardButton(text=_("job_feed_next", locale=user_lang)),
            ],
        ],
        resize_keyboard=True,
    )
    await callback.message.answer("🔍", reply_markup=reply_kb)

    # Send first job card
    await _send_job_card(callback.message, vacancies[0], 0, len(vacancies), user_lang)


@router.message(JobFeedStates.BROWSING, F.text)
async def job_feed_navigation(
    message: Message,
    services: ServiceContainer,
    state: FSMContext,
    user_lang: str | None = None,
) -> None:
    """Handle Next / Menu button presses in the job feed."""
    text = message.text.strip()

    menu_text = _("job_feed_menu", locale=user_lang)
    next_text = _("job_feed_next", locale=user_lang)

    if text == menu_text:
        await state.clear()
        await message.answer(
            _("job_feed_exited", locale=user_lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        from src.handlers.helpers import _go_main_menu

        await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)
        return

    if text != next_text:
        return

    # Track the scroll event (fire-and-forget)
    data = await state.get_data()
    task = asyncio.create_task(
        services.backend.track_event(
            telegram_id=message.from_user.id,
            event_type="job_feed_scroll",
            metadata={"resume_id": data.get("job_resume_id", "")},
        )
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    feed = data.get("job_feed", [])
    index = data.get("job_index", 0)
    resume_id = data.get("job_resume_id", "")
    seen_ids = data.get("job_seen_ids", [])
    batch_ts = data.get("job_batch_ts", 0)

    next_index = index + 1

    # Batch TTL — if the user was inactive for 10+ minutes, drop the current
    # window and fetch a fresh one so they don't resume a stale feed.
    batch_expired = (time.time() - batch_ts) > 300
    if batch_expired:
        next_index = len(feed)  # force a refetch

    # End of current window — re-run matching excluding seen IDs
    if next_index >= len(feed):
        if len(seen_ids) >= settings.JOB_MAX_SEEN:
            await message.answer(
                _("job_feed_end", locale=user_lang),
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.clear()
            from src.handlers.helpers import _go_main_menu

            await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)
            return
        new_jobs = await services.backend.find_matching_jobs(
            telegram_id=message.from_user.id,
            resume_id=resume_id,
            limit=settings.JOB_WINDOW_SIZE,
            exclude_ids=seen_ids,
        )

        if not new_jobs or not isinstance(new_jobs, list):
            await message.answer(
                _("job_feed_end", locale=user_lang),
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.clear()
            from src.handlers.helpers import _go_main_menu

            await _go_main_menu(message.from_user.id, message, state, services, user_lang, send_new=True)
            return

        seen_ids.extend(v["id"] for v in new_jobs)
        await state.update_data(
            job_feed=new_jobs,
            job_index=0,
            job_seen_ids=seen_ids,
            job_batch_ts=time.time(),
        )
        await asyncio.sleep(0.5)
        await _send_job_card(message, new_jobs[0], 0, len(new_jobs), user_lang)
        return

    await state.update_data(job_index=next_index)
    await asyncio.sleep(0.5)
    await _send_job_card(message, feed[next_index], next_index, len(feed), user_lang)


async def _send_job_card(
    message: Message,
    vacancy: dict,
    index: int,
    total: int,
    user_lang: str,
) -> None:
    """Send a single job card with inline source button."""
    text = _format_job_card(vacancy, index, total, user_lang)

    source_url = _get_source_url(vacancy)

    inline_buttons = []
    if source_url:
        inline_buttons.append(
            [
                InlineKeyboardButton(
                    text=_("job_view_source", locale=user_lang),
                    url=source_url,
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons) if inline_buttons else None

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


def _format_job_card(vacancy: dict, index: int, total: int, user_lang: str) -> str:
    """Format a brief job card for Reels-style display."""
    lines = []

    # Title
    title = vacancy.get("title", "N/A")
    lines.append(f"<b>{title}</b>")

    # Company
    if vacancy.get("company"):
        lines.append(f"\n🏢 {vacancy['company']}")

    lines.append("")

    # Salary
    sal = _format_salary(vacancy)
    if sal:
        lines.append(f"💰 {sal}")

    # Location
    if vacancy.get("location"):
        lines.append(f"📍 {vacancy['location']}")

    # Work format + employment type on one line
    work_info = []
    if vacancy.get("employment_type"):
        work_info.append(vacancy["employment_type"].replace("_", " ").title())
    if vacancy.get("work_format"):
        work_info.append(vacancy["work_format"].replace("_", " ").title())
    if work_info:
        lines.append(f"🕐 {' · '.join(work_info)}")

    # Skills (top 5)
    skills = vacancy.get("skills", [])
    if skills:
        if isinstance(skills[0], dict):
            skill_names = [s.get("name", "") for s in skills[:5]]
        else:
            skill_names = skills[:5]
        lines.append(f"\n🛠 {', '.join(skill_names)}")

    # Match score
    score = vacancy.get("similarity_score", 0)
    if score:
        score_pct = min(int(score * 100), 100)
        lines.append(f"\n✅ {_('job_match_score', locale=user_lang, score=score_pct)}")

    return "\n".join(lines)


def _get_source_url(vacancy: dict) -> str | None:
    """Build the source URL for a vacancy."""
    # Direct source URL
    if vacancy.get("source_url"):
        return vacancy["source_url"]

    # Build Telegram channel link
    channel = vacancy.get("source_channel", "")
    msg_id = vacancy.get("source_message_id")
    if channel and msg_id:
        return f"https://t.me/{channel}/{msg_id}"

    # Contact info as fallback
    contact = vacancy.get("contact_info", "")
    if contact.startswith("http"):
        return contact
    if contact.startswith("@"):
        return f"https://t.me/{contact.lstrip('@')}"

    return None


def _format_salary(vacancy: dict) -> str:
    """Format salary range string."""
    sal_min = vacancy.get("salary_min")
    sal_max = vacancy.get("salary_max")
    currency = vacancy.get("salary_currency", "")

    if sal_min and sal_max:
        return f"{sal_min:,} – {sal_max:,} {currency}".strip()
    elif sal_min:
        return f"{sal_min:,}+ {currency}".strip()
    elif sal_max:
        return f"up to {sal_max:,} {currency}".strip()
    return ""
