import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions

from src.handlers.helpers.formatting import format_number, google_maps_link, is_url, should_use_map_link
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)


async def send_vacancy(bot, tg_id: int, user_lang: str, vacancy_data: dict) -> bool:
    try:
        try:
            chat = await bot.get_chat(tg_id)
            if not chat:
                logger.warning("User %s not found in bot database", tg_id)
                return False
        except Exception as e:
            logger.warning("Failed to get chat info for user %s: %s", tg_id, str(e))
            return False

        title = vacancy_data.get("title")
        company = vacancy_data.get("company")
        job_type = vacancy_data.get("job_type").value
        raw_salary = vacancy_data.get("raw_salary")
        min_salary = vacancy_data.get("min_salary")
        max_salary = vacancy_data.get("max_salary")
        currency = vacancy_data.get("currency", "")
        location = vacancy_data.get("location")

        if job_type:
            job_type = _(job_type.lower(), locale=user_lang)
        logger.info(job_type)

        # Format salary display
        if raw_salary:
            salary = format_number(raw_salary)
            if currency:
                salary = f"{salary} {currency}"
        elif min_salary and max_salary:
            salary = f"{format_number(min_salary)} - {format_number(max_salary)} {currency}"
        elif min_salary:
            salary = _("from", locale=user_lang, salary=format_number(min_salary), currency=currency)
        elif max_salary:
            salary = _("up_to", locale=user_lang, salary=format_number(max_salary), currency=currency)
        else:
            salary = _("not_specified", locale=user_lang)

        if location:
            if is_url(location):
                location = f'<a href="{location}">{_("location", locale=user_lang)}</a>'
            elif should_use_map_link(location):
                location = f'<a href="{google_maps_link(location)}">{_("location", locale=user_lang)}</a>'
            else:
                location = f"<b>{location}</b>"
        else:
            location = _("not_specified", locale=user_lang)

        inline_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=_("link", locale=user_lang), url=vacancy_data.get("url"))]]
        )

        link_preview = LinkPreviewOptions(is_disabled=True)

        await bot.send_message(
            chat_id=tg_id,
            text=_(
                "vacancy_info",
                locale=user_lang,
                title=title if title else _("not_specified", locale=user_lang),
                company=company if company else _("not_specified", locale=user_lang),
                job_type=job_type if job_type else _("not_specified", locale=user_lang),
                salary=salary,
                experience_level=vacancy_data.get("experience_level", _("not_specified", locale=user_lang)),
                skills=vacancy_data.get("skills", _("not_specified", locale=user_lang)),
                location=location if location else _("not_specified", locale=user_lang),
            ),
            link_preview_options=link_preview,
            reply_markup=inline_keyboard,
            parse_mode="HTML",
        )

        return True

    except Exception as e:
        error_msg = str(e).lower()
        if "forbidden" in error_msg or "blocked" in error_msg:
            logger.warning("User %s has blocked the bot or chat is forbidden", tg_id)
            return False
        elif "chat not found" in error_msg or "user not found" in error_msg:
            logger.warning("User %s not found or chat not accessible", tg_id)
            return False
        else:
            logger.error("Failed to send notification to user %s: %s", tg_id, str(e))
            return False
