"""Store service for credit management."""

import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.store.models import CreditPackage, CreditTransaction
from apps.users.models import User

logger = logging.getLogger(__name__)


class StoreService:
    """Service for managing credit purchases and transactions."""

    @staticmethod
    def get_active_packages() -> list[CreditPackage]:
        """Get all active credit packages."""
        return list(CreditPackage.objects.filter(is_active=True))

    @staticmethod
    def get_package(credits: int) -> CreditPackage | None:
        """Get a specific credit package."""
        try:
            return CreditPackage.objects.get(credits=credits, is_active=True)
        except CreditPackage.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def purchase_credits(
        user: User,
        package: CreditPackage,
        payment_id: str,
        payment_provider: str = "click",
        metadata: dict | None = None,
    ) -> CreditTransaction:
        """
        Process a credit purchase and update user balance.

        Args:
            user: User making the purchase
            package: CreditPackage being purchased
            payment_id: External payment provider transaction ID
            payment_provider: Name of payment provider
            metadata: Additional transaction metadata

        Returns:
            CreditTransaction object
        """
        # Lock user row for update
        user = User.objects.select_for_update().get(pk=user.pk)

        # Update user balance
        user.resume_credits += package.credits
        user.save(update_fields=["resume_credits"])

        # Create transaction record
        txn = CreditTransaction.objects.create(
            user=user,
            transaction_type="purchase",
            credits=package.credits,
            balance_after=user.resume_credits,
            package=package,
            amount_paid=package.price,
            currency=package.currency,
            payment_provider=payment_provider,
            payment_id=payment_id,
            status="completed",
            metadata=metadata or {},
        )

        logger.info(
            f"Credits purchased: user_id={user.id}, credits={package.credits}, "
            f"payment_id={payment_id}, new_balance={user.resume_credits}"
        )

        return txn

    @staticmethod
    @transaction.atomic
    def consume_credits(
        user: User, credits: int, resume_id: int | None = None, notes: str = ""
    ) -> CreditTransaction | None:
        """
        Consume credits from user's balance.

        Args:
            user: User consuming credits
            credits: Number of credits to consume
            resume_id: ID of resume being generated (if applicable)
            notes: Optional notes about the usage

        Returns:
            CreditTransaction object if successful, None if insufficient balance
        """
        # Lock user row for update
        user = User.objects.select_for_update().get(pk=user.pk)

        # Check if user has enough credits
        if user.resume_credits < credits:
            logger.warning(
                f"Insufficient credits: user_id={user.id}, "
                f"required={credits}, available={user.resume_credits}"
            )
            return None

        # Deduct credits
        user.resume_credits -= credits
        user.save(update_fields=["resume_credits"])

        # Create transaction record
        txn = CreditTransaction.objects.create(
            user=user,
            transaction_type="usage",
            credits=-credits,  # Negative for deduction
            balance_after=user.resume_credits,
            resume_id=resume_id,
            status="completed",
            notes=notes,
        )

        logger.info(
            f"Credits consumed: user_id={user.id}, credits={credits}, "
            f"resume_id={resume_id}, new_balance={user.resume_credits}"
        )

        return txn

    @staticmethod
    def get_user_transaction_history(
        user: User, transaction_type: str | None = None, limit: int = 50
    ) -> list[CreditTransaction]:
        """Get user's transaction history."""
        queryset = CreditTransaction.objects.filter(user=user)

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        return list(queryset[:limit])

    @staticmethod
    def get_user_purchase_stats(user: User) -> dict:
        """Get user's purchase statistics."""
        purchases = CreditTransaction.objects.filter(
            user=user, transaction_type="purchase", status="completed"
        )

        total_spent = purchases.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0")

        total_purchased = purchases.aggregate(total=Sum("credits"))["total"] or 0

        usage = (
            CreditTransaction.objects.filter(user=user, transaction_type="usage").aggregate(
                total=Sum("credits")
            )["total"]
            or 0
        )

        return {
            "total_spent": float(total_spent),
            "total_credits_purchased": total_purchased,
            "total_credits_used": abs(usage),
            "current_balance": user.resume_credits,
            "total_purchases": purchases.count(),
        }

    @staticmethod
    @transaction.atomic
    def refund_purchase(transaction_id: int, admin_notes: str = "") -> bool:
        """
        Refund a credit purchase.

        Args:
            transaction_id: ID of the purchase transaction
            admin_notes: Admin notes for the refund

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get and lock the original transaction
            original_txn = CreditTransaction.objects.select_for_update().get(
                id=transaction_id, transaction_type="purchase", status="completed"
            )

            # Lock user
            user = User.objects.select_for_update().get(pk=original_txn.user_id)

            # Deduct the credits
            credits_to_remove = original_txn.credits

            if user.resume_credits < credits_to_remove:
                logger.error(
                    f"Cannot refund: user has insufficient balance. "
                    f"user_id={user.id}, balance={user.resume_credits}, "
                    f"refund_amount={credits_to_remove}"
                )
                return False

            user.resume_credits -= credits_to_remove
            user.save(update_fields=["resume_credits"])

            # Update original transaction status
            original_txn.status = "refunded"
            original_txn.save(update_fields=["status"])

            # Create refund transaction
            CreditTransaction.objects.create(
                user=user,
                transaction_type="refund",
                credits=-credits_to_remove,
                balance_after=user.resume_credits,
                package=original_txn.package,
                amount_paid=original_txn.amount_paid,
                currency=original_txn.currency,
                payment_provider=original_txn.payment_provider,
                status="completed",
                notes=f"Refund of transaction #{transaction_id}. {admin_notes}",
                metadata={"original_transaction_id": transaction_id},
            )

            logger.info(
                f"Refund processed: transaction_id={transaction_id}, "
                f"user_id={user.id}, credits={credits_to_remove}"
            )

            return True

        except CreditTransaction.DoesNotExist:
            logger.error(f"Transaction not found or invalid: {transaction_id}")
            return False
        except Exception as e:
            logger.error(f"Error processing refund: {e}", exc_info=True)
            return False
