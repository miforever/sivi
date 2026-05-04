"""
Resume-related handlers for the bot.

This module includes timeout protection mechanisms to prevent the bot from taking
too long to respond to callback queries, which would cause Telegram API errors
like "query is too old and response timeout expired".

All callback handlers use safe_callback_answer() to gracefully handle expired
queries, and main operations are wrapped in asyncio.wait_for() with a 25-second
timeout (under Telegram's 30-second limit).
"""

import asyncio
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from src.config import get_settings
from src.handlers.helpers import safe_callback_answer, safe_edit_message
from src.keyboards.inline import (
    create_back_to_main_keyboard,
    create_subscription_back_keyboard,
    create_subscription_plans_keyboard,
)
from src.services.container import ServiceContainer
from src.services.states import PaymentStates
from src.utils.callback_factories import MainMenuActions, MainMenuCallback, PlanActions, PlanCallback
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)
router = Router(name="subscription")

settings = get_settings()


@router.callback_query(MainMenuCallback.filter(F.action == MainMenuActions.PRO_SUBSCRIPTION))
async def pro_subscription(
    callback: CallbackQuery, services: ServiceContainer, user_lang: str | None = None, state: FSMContext = None
) -> None:
    """Handle subscription button — show status if active, or sales page if not."""
    await safe_callback_answer(callback)

    data = await state.get_data()
    invoice_msg = data.get("invoice_msg")

    if invoice_msg:
        try:
            await callback.bot.delete_message(chat_id=invoice_msg["chat_id"], message_id=invoice_msg["message_id"])
        except Exception:
            pass

    # Temporarily show info-only Pro screen (no subscription/payment flow)
    await safe_edit_message(
        callback.message,
        _("subscription_info", locale=user_lang) + _("pro_coming_soon", locale=user_lang),
        link_preview=False,
        reply_markup=create_back_to_main_keyboard(user_lang),
        parse_mode="HTML",
    )


@router.callback_query(PlanCallback.filter(F.action == PlanActions.VIEW_PLANS))
async def show_plans(
    callback: CallbackQuery, services: ServiceContainer, state: FSMContext, user_lang: str | None = None
) -> None:
    await safe_callback_answer(callback)

    data = await state.get_data()
    invoice_msg = data.get("invoice_msg")

    if invoice_msg:
        try:
            await callback.bot.delete_message(chat_id=invoice_msg["chat_id"], message_id=invoice_msg["message_id"])
        except Exception:
            pass

    plans = await services.subscription_service.get_plans()

    plan_prices = {plan["plan_id"]: int(float(plan["price"])) for plan in plans}
    monthly_price = plan_prices.get("monthly", 0)
    quarterly_price = plan_prices.get("quarterly", 0)

    three_months_regular = monthly_price * 3
    savings = three_months_regular - quarterly_price
    discount_percent = (savings / three_months_regular * 100) if three_months_regular > 0 else 0

    def format_price(amount: int) -> str:
        """Format price with thousand separators."""
        return f"{amount:,} UZS".replace(",", ".")

    prices = {
        "monthly": format_price(monthly_price),
        "quarterly": format_price(quarterly_price),
        "three_months_regular": format_price(three_months_regular),
        "savings": format_price(savings),
        "discount_percent": round(discount_percent, 1),
    }

    subscription_plans_kyb = create_subscription_plans_keyboard(user_lang, prices)

    await safe_edit_message(
        callback.message,
        _(
            "subscriptions",
            locale=user_lang,
            month_1_price=prices["monthly"],
            month_3_price=prices["quarterly"],
            month_1_3x=prices["three_months_regular"],
            off=prices["savings"],
            percent_off=prices["discount_percent"],
        ),
        reply_markup=subscription_plans_kyb,
    )

    await state.update_data(plans=plans)


@router.callback_query(PlanCallback.filter(F.action == PlanActions.CHOOSE_PLAN))
async def choose_plans(
    callback: CallbackQuery, callback_data: PlanCallback, state: FSMContext, user_lang: str | None = None
) -> None:
    """Handle user selection of a subscription plan and send payment invoice."""
    await safe_callback_answer(callback)
    data = await state.get_data()
    plan_id = callback_data.plan_id
    plans = data.get("plans")
    plan = next((p for p in (plans or []) if p["plan_id"] == plan_id), None)

    if not plan or not plan.get("price"):
        await safe_edit_message(callback.message, _("error_occurred_later", locale=user_lang))
        return

    plan_title = _(f"{plan_id}_plan_title", locale=user_lang)
    plan_description = _(f"{plan_id}_plan_description", locale=user_lang)
    plan_price = int(float(plan["price"]))

    await safe_edit_message(
        callback.message,
        text=_("make_the_payment", locale=user_lang),
        reply_markup=create_subscription_back_keyboard(user_lang),
    )

    await asyncio.sleep(1)

    invoice_msg = await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=plan_title,
        description=plan_description,
        payload=f"{callback.from_user.id}:{plan_id}",
        provider_token=settings.CLICK_TOKEN,
        currency="UZS",
        prices=[LabeledPrice(label=plan_title, amount=plan_price * 100)],
        # Optional parameters
        max_tip_amount=100_000_00,
        suggested_tip_amounts=[5_000_00, 10_000_00, 20_000_00, 30_000_00],
        start_parameter=f"subscription-{plan_id}",
        photo_url="https://i.postimg.cc/pd9YM2Xd/sivi-logo.png",
        photo_width=800,
        photo_height=800,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        send_phone_number_to_provider=False,
        send_email_to_provider=True,
        is_flexible=False,  # False = fixed price
        protect_content=False,
    )

    await state.update_data(
        pre_invoice_msg={"chat_id": callback.message.chat.id, "message_id": callback.message.message_id},
        invoice_msg={"chat_id": invoice_msg.chat.id, "message_id": invoice_msg.message_id},
        selected_plan_id=plan_id,
    )

    await state.set_state(PaymentStates.WAITING_SUBSCRIPTION_PAYMENT)


@router.pre_checkout_query(PaymentStates.WAITING_SUBSCRIPTION_PAYMENT)
async def process_pre_checkout_query(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment, PaymentStates.WAITING_SUBSCRIPTION_PAYMENT)
async def successful_payment(
    message: Message, services: ServiceContainer, user_lang: str | None = None, state: FSMContext = None
):
    payment = message.successful_payment

    try:
        user_id, plan_id = payment.invoice_payload.split(":")
    except ValueError:
        logger.error(f"Invalid payment payload: {payment.invoice_payload}")
        await message.answer(_("payment_error", locale=user_lang))
        return

    logger.info(
        "Received successful_payment for user %s: payload=%s, total_amount=%s %s",
        message.from_user.id if message.from_user else None,
        getattr(payment, "invoice_payload", None),
        getattr(payment, "total_amount", None),
        getattr(payment, "currency", None),
    )

    data = await state.get_data()

    pre_invoice = data.get("pre_invoice_msg")
    if pre_invoice:
        try:
            await message.bot.delete_message(chat_id=pre_invoice["chat_id"], message_id=pre_invoice["message_id"])
        except Exception:
            pass

    invoice = data.get("invoice_msg")
    if invoice:
        try:
            await message.bot.delete_message(chat_id=invoice["chat_id"], message_id=invoice["message_id"])
        except Exception:
            pass

    try:
        subscription = await services.subscription_service.activate_subscription(
            telegram_id=int(user_id), plan_id=plan_id, payment_id=payment.telegram_payment_charge_id
        )

        if not subscription or subscription.get("error"):
            error_msg = subscription.get("message", "Unknown error") if subscription else "No response"
            logger.error(
                f"Failed to activate subscription for user {user_id}: {error_msg} - "
                f"plan_id={plan_id}, payment_id={payment.telegram_payment_charge_id}"
            )
            await message.answer(
                _("subscription_activation_failed", locale=user_lang)
                + "\n\n"
                + _("contact_support_with_payment_id", locale=user_lang).format(
                    payment_id=payment.telegram_payment_charge_id
                ),
                reply_markup=create_back_to_main_keyboard(user_lang),
            )
            return

        expiry_date_str = subscription.get("expires_at", "")
        try:
            expiry_date = datetime.fromisoformat(expiry_date_str.replace("Z", "+00:00"))
            expiry_date_formatted = expiry_date.strftime("%B %d, %Y")
        except (ValueError, AttributeError):
            expiry_date_formatted = _("unknown_date", locale=user_lang)

        keyboard = create_back_to_main_keyboard(user_lang)
        await message.answer(
            _("subscription_activated", expiry_date=expiry_date_formatted, locale=user_lang), reply_markup=keyboard
        )

        await state.clear()

    except Exception as e:
        logger.error(
            f"Unexpected error in successful_payment handler: {e} - "
            f"user_id={user_id}, plan_id={plan_id}, payment_id={payment.telegram_payment_charge_id}",
            exc_info=True,
        )

        await message.answer(
            _("payment_processing_error", locale=user_lang)
            + "\n\n"
            + _("contact_support_with_payment_id", locale=user_lang).format(
                payment_id=payment.telegram_payment_charge_id
            ),
            reply_markup=create_back_to_main_keyboard(user_lang),
        )
