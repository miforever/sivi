"""Resume credit purchase handlers."""

import asyncio
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from src.config import get_settings
from src.handlers.helpers import safe_callback_answer, safe_edit_message
from src.keyboards.inline import create_back_to_main_keyboard, get_credit_purchase_keyboard, get_credits_back_keyboard
from src.services.container import ServiceContainer
from src.services.states import PaymentStates
from src.utils.callback_factories import CreditActions, CreditCallback
from src.utils.i18n import gettext as _

logger = logging.getLogger(__name__)
router = Router(name="resume_credits_handlers")

settings = get_settings()


@router.callback_query(CreditCallback.filter(F.action == CreditActions.BUY_CREDITS))
async def handle_buy_credits_callback(
    callback: CallbackQuery,
    user_lang: str | None = None,
    state: FSMContext = None,
) -> None:
    """Handle buy credits callback - show available packages."""
    await safe_callback_answer(callback)

    data = await state.get_data()
    invoice_msg = data.get("invoice_msg")

    if invoice_msg:
        try:
            await callback.bot.delete_message(chat_id=invoice_msg["chat_id"], message_id=invoice_msg["message_id"])
        except Exception:
            pass

    # Create keyboard with available packages
    keyboard = get_credit_purchase_keyboard(user_lang)

    await safe_edit_message(
        callback.message,
        text=_("buy_credits_message", locale=user_lang),
        reply_markup=keyboard,
    )


@router.callback_query(CreditCallback.filter(F.action == CreditActions.CHOOSE_AMOUNT))
async def handle_choose_amount_callback(
    callback: CallbackQuery,
    user_lang: str | None = None,
    services: ServiceContainer = None,
    state: FSMContext = None,
    callback_data: CreditCallback = None,
) -> None:
    """Handle choose amount callback - initiate payment."""
    await safe_callback_answer(callback)

    credit_amount = callback_data.credit_amount

    # Fetch credit packages from backend
    credit_packs = await services.resume_service.get_credit_packages(callback.from_user.id)

    # Find the selected package
    credit_pack = next((pkg for pkg in credit_packs if pkg.get("credits") == credit_amount), None)

    if not credit_pack:
        keyboard = create_back_to_main_keyboard(user_lang)
        await safe_edit_message(
            callback.message, text=_("error_occurred_general", locale=user_lang), reply_markup=keyboard
        )
        return

    plan_title = _("buy_credits", locale=user_lang)
    plan_description = _(f"credit_option_{credit_amount}", locale=user_lang)
    plan_price = int(float(credit_pack["price"]))

    await safe_edit_message(
        callback.message,
        text=_(
            "make_the_payment_credit",
            credits=credit_amount,
            price=plan_price,
            currency=credit_pack["currency"],
            locale=user_lang,
        ),
        reply_markup=get_credits_back_keyboard(user_lang),
    )

    await asyncio.sleep(1)

    invoice_msg = await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=plan_title,
        description=plan_description,
        payload=f"{callback.from_user.id}:{credit_amount}",
        provider_token=settings.CLICK_TOKEN,
        currency=credit_pack["currency"],
        prices=[LabeledPrice(label=plan_title, amount=plan_price * 100)],
        photo_url="https://i.postimg.cc/pd9YM2Xd/sivi-logo.png",
        photo_width=800,
        photo_height=800,
        is_flexible=False,
        protect_content=False,
    )

    await state.update_data(
        pre_invoice_msg={"chat_id": callback.message.chat.id, "message_id": callback.message.message_id},
        invoice_msg={"chat_id": invoice_msg.chat.id, "message_id": invoice_msg.message_id},
        selected_credits=credit_amount,
    )

    # Set payment state
    await state.set_state(PaymentStates.WAITING_CREDITS_PAYMENT)


@router.pre_checkout_query(PaymentStates.WAITING_CREDITS_PAYMENT)
async def process_credits_pre_checkout(pre_checkout: PreCheckoutQuery, state: FSMContext) -> None:
    """Handle pre-checkout for credits payments."""
    logger.info(f"Pre-checkout for credits: {pre_checkout.invoice_payload}")
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment, PaymentStates.WAITING_CREDITS_PAYMENT)
async def successful_credits_payment(
    message: Message, services: ServiceContainer, user_lang: str | None = None, state: FSMContext = None
) -> None:
    """Handle successful credits payment."""
    payment = message.successful_payment

    logger.info(
        "Credits payment successful: user=%s, payload=%s, amount=%s %s",
        message.from_user.id,
        payment.invoice_payload,
        payment.total_amount,
        payment.currency,
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
        user_id, credit_amount = payment.invoice_payload.split(":")

        result = await services.resume_service.purchase_credits(
            telegram_id=int(user_id),
            credits=int(credit_amount),
            payment_id=payment.telegram_payment_charge_id,
            payment_provider="click",
            amount_paid=payment.total_amount / 100,
            currency=payment.currency,
        )

        if not result.get("success"):
            error_msg = result.get("message", "Unknown error")
            logger.error(f"Failed to add credits for user {user_id}: {error_msg}")

            # Check if payment was already processed
            if result.get("error") == "PAYMENT_ALREADY_PROCESSED":
                await message.answer(
                    _("payment_already_processed", locale=user_lang),
                    reply_markup=create_back_to_main_keyboard(user_lang),
                )
            else:
                await message.answer(
                    _("credits_activation_failed", locale=user_lang),
                    reply_markup=create_back_to_main_keyboard(user_lang),
                )
            return

        # Send success message
        await message.answer(
            _("credits_purchased", credits=credit_amount, locale=user_lang),
            reply_markup=create_back_to_main_keyboard(user_lang),
        )

        logger.info(f"Credits successfully added: user_id={user_id}, credits={credit_amount}")

        await state.clear()

    except Exception as e:
        logger.error(f"Error processing credits payment: {e}", exc_info=True)
        await message.answer(_("payment_error", locale=user_lang), reply_markup=create_back_to_main_keyboard(user_lang))
