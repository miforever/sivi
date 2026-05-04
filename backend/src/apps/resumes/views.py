"""Resume views for CRUD and AI operations."""

import base64
import logging
import uuid
from datetime import timedelta

from django.core.files.base import ContentFile
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.common.authentication import TelegramBotAuthentication
from apps.common.responses import error_response, success_response
from apps.resumes.exceptions import OpenAIServiceError, PDFGenerationError, ResumeProcessingError
from apps.resumes.models import Resume
from apps.resumes.serializers import (
    ResumeCreateUpdateSerializer,
    ResumeDetailSerializer,
    ResumeListSerializer,
)
from apps.resumes.services.resume.service import ResumeService
from apps.store.services import StoreService

logger = logging.getLogger(__name__)

# Temporary weekly limit for AI generation calls per user (until paid plans)
WEEKLY_AI_CALL_LIMIT = 5


def check_and_increment_weekly_ai_limit(user) -> str | None:
    """Check the user's weekly AI call limit. Returns an error message or None if OK."""
    now = timezone.now()

    if user.weekly_ai_calls_reset is None or now - user.weekly_ai_calls_reset >= timedelta(days=7):
        user.weekly_ai_calls = 0
        user.weekly_ai_calls_reset = now

    if user.weekly_ai_calls >= WEEKLY_AI_CALL_LIMIT:
        return (
            f"Weekly AI generation limit reached ({WEEKLY_AI_CALL_LIMIT}/{WEEKLY_AI_CALL_LIMIT}). "
            f"Resets on {(user.weekly_ai_calls_reset + timedelta(days=7)).strftime('%d.%m.%Y')}."
        )

    user.weekly_ai_calls += 1
    user.save(update_fields=["weekly_ai_calls", "weekly_ai_calls_reset"])
    return None


class ResumeViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for Resume management.
    Supports all operations: list, create, retrieve, update, partial_update, destroy.
    Works with both Telegram bot and Web/App authentication.
    """

    serializer_class = ResumeDetailSerializer
    authentication_classes = [TelegramBotAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resume_service = ResumeService()
        self.store_service = StoreService()

    def get_queryset(self):
        """Return resumes only for the authenticated user."""
        if getattr(self, "swagger_fake_view", False):
            return Resume.objects.none()

        return Resume.objects.filter(user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ResumeListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ResumeCreateUpdateSerializer
        return ResumeDetailSerializer

    def list(self, request, *args, **kwargs):
        """List all resumes for authenticated user."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a new resume for authenticated user."""
        user_resumes_count = self.get_queryset().count()
        if user_resumes_count >= 5:
            return error_response(
                code="RESUME_LIMIT_REACHED",
                message="Resume limit reached. Maximum 5 resumes allowed.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        import json

        for key in ("social_links", "volunteer_experience", "certifications"):
            if key in data and isinstance(data.get(key), str):
                try:
                    data[key] = json.loads(data[key])
                except Exception:
                    pass

        # Handle base64 data URI for profile_image
        profile_image_file = None
        profile_image_raw = data.pop("profile_image", None)
        if (
            profile_image_raw
            and isinstance(profile_image_raw, str)
            and profile_image_raw.startswith("data:")
        ):
            try:
                header, b64_data = profile_image_raw.split(",", 1)
                ext = "png" if "png" in header else "jpg"
                profile_image_file = ContentFile(
                    base64.b64decode(b64_data),
                    name=f"profile_{uuid.uuid4().hex[:8]}.{ext}",
                )
                data["profile_image"] = profile_image_file
            except Exception:
                logger.warning("Failed to decode base64 profile image, skipping")

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            logger.error("Resume create validation errors: %s", serializer.errors)
            serializer.is_valid(raise_exception=True)
        resume = serializer.save(user=request.user)

        try:
            from apps.matching.tasks import generate_resume_embedding_task

            generate_resume_embedding_task.delay(str(resume.id))
        except Exception:
            logger.debug("Could not queue embedding task for resume %s", resume.id)

        return success_response(
            data=ResumeDetailSerializer(resume).data, status_code=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        """Get a specific resume."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        """Full update of a resume."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        data = request.data.copy()
        import json

        for key in ("social_links", "volunteer_experience", "certifications"):
            if key in data and isinstance(data.get(key), str):
                try:
                    data[key] = json.loads(data[key])
                except Exception:
                    pass

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Invalidate cached embedding so it gets recomputed on next match
        instance.embedding = None
        instance.save(update_fields=["embedding"])
        try:
            from apps.matching.tasks import generate_resume_embedding_task

            generate_resume_embedding_task.delay(str(instance.id))
        except Exception:
            logger.debug("Could not queue embedding task for resume %s", instance.id)

        return success_response(data=ResumeDetailSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a resume."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a resume."""
        instance = self.get_object()
        instance.delete()

        return success_response(
            message="Resume deleted successfully", status_code=status.HTTP_204_NO_CONTENT
        )

    # ==================== AI-Powered Actions ====================

    @action(detail=False, methods=["post"], url_path="extract")
    def extract_data(self, request):
        """
        Extract structured data from an uploaded resume file (PDF or DOCX).
        Subject to weekly AI call limit.
        """
        limit_error = check_and_increment_weekly_ai_limit(request.user)
        if limit_error:
            return error_response(
                code="WEEKLY_LIMIT_REACHED",
                message=limit_error,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if "file" not in request.FILES:
            return error_response(
                code="NO_FILE_PROVIDED",
                message="No file provided",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_file = request.FILES["file"]
        language = request.data.get("language", request.query_params.get("language", "en"))

        logger.info(
            f"Extracting data from file: {uploaded_file.name}, size: {uploaded_file.size} bytes"
        )

        try:
            resume_data = self.resume_service.extract_resume_info(uploaded_file, language)

            return success_response(
                data={"resume_data": resume_data, "credits_remaining": request.user.resume_credits},
                message="Resume data extracted successfully",
            )

        except ResumeProcessingError as e:
            logger.error(f"Resume processing error: {e!s}")
            return error_response(
                code="RESUME_PROCESSING_ERROR",
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except OpenAIServiceError as e:
            logger.error(f"AI service error: {e!s}")
            return error_response(
                code="AI_SERVICE_ERROR",
                message=f"AI service error: {e!s}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e!s}")
            return error_response(
                code="EXTRACTION_ERROR",
                message=f"Failed to extract resume data: {e!s}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="generate-from-qa")
    def generate_from_qa(self, request):
        """
        Generate structured resume data from Q&A flow.
        Subject to weekly AI call limit.
        """
        limit_error = check_and_increment_weekly_ai_limit(request.user)
        if limit_error:
            return error_response(
                code="WEEKLY_LIMIT_REACHED",
                message=limit_error,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        qa_pairs = request.data.get("qa_pairs", [])
        user_info = request.data.get("user_info", {})
        language = request.data.get("language", "en")
        position = request.data.get("position")

        if not qa_pairs:
            return error_response(
                code="NO_QA_PAIRS",
                message="Q&A pairs are required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not user_info:
            return error_response(
                code="NO_USER_INFO",
                message="User info is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Generating resume from {len(qa_pairs)} Q&A pairs")

        try:
            resume_data = self.resume_service.generate_from_qa(
                qa_pairs, user_info, language, position
            )

            # Temporarily free — no credit consumption
            return success_response(
                data={"resume_data": resume_data, "credits_remaining": request.user.resume_credits},
                message="Resume data generated successfully",
            )

        except OpenAIServiceError as e:
            logger.error(f"AI service error: {e!s}")
            return error_response(
                code="AI_SERVICE_ERROR",
                message=f"AI service error: {e!s}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except Exception as e:
            logger.error(f"Unexpected error during generation: {e!s}")
            return error_response(
                code="GENERATION_ERROR",
                message=f"Failed to generate resume data: {e!s}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="generate-pdf")
    def generate_pdf(self, request):
        """Generate a PDF from structured resume data. Does not consume credits."""
        resume_data = request.data.get("resume_data")
        profile_image = request.data.get("profile_image")
        language = request.data.get("language")

        if not resume_data:
            return error_response(
                code="NO_RESUME_DATA",
                message="Resume data is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Inject language into resume_data so the PDF generator can use it
        if language and isinstance(resume_data, dict):
            resume_data["language"] = language

        try:
            pdf_file = self.resume_service.generate_pdf(resume_data, profile_image)

            response = FileResponse(pdf_file, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
            return response

        except PDFGenerationError as e:
            logger.error(f"PDF generation error: {e!s}")
            return error_response(
                code="PDF_GENERATION_ERROR",
                message=f"PDF generation error: {e!s}",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        except Exception as e:
            logger.error(f"Unexpected error during PDF generation: {e!s}")
            return error_response(
                code="PDF_GENERATION_FAILURE",
                message=f"Failed to generate PDF: {e!s}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="export-pdf")
    def export_pdf(self, request, id=None):
        """Generate and download a PDF for a saved resume. Does not consume credits."""
        resume = self.get_object()
        serializer = ResumeDetailSerializer(resume)
        resume_data = serializer.data

        try:
            # Read profile image from stored file if available
            profile_image = None
            if resume.profile_image:
                try:
                    resume.profile_image.open("rb")
                    profile_image = base64.b64encode(resume.profile_image.read()).decode("utf-8")
                    resume.profile_image.close()
                except Exception:
                    logger.warning("Failed to read profile image for resume %s", resume.id)

            pdf_file = self.resume_service.generate_pdf(resume_data, profile_image=profile_image)
            return self.resume_service.create_pdf_response(pdf_file, filename="resume.pdf")

        except PDFGenerationError as e:
            logger.error(f"PDF generation error: {e!s}")
            return error_response(
                code="PDF_GENERATION_ERROR",
                message=f"PDF generation error: {e!s}",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        except Exception as e:
            logger.error(f"Unexpected error during PDF export: {e!s}")
            return error_response(
                code="PDF_EXPORT_FAILURE",
                message=f"Failed to export PDF: {e!s}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="enhance")
    def enhance(self, request, id=None):
        """Enhance an existing resume using AI. Subject to weekly AI call limit."""
        limit_error = check_and_increment_weekly_ai_limit(request.user)
        if limit_error:
            return error_response(
                code="WEEKLY_LIMIT_REACHED",
                message=limit_error,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        resume = self.get_object()
        language = request.data.get("language", "en")

        if not resume.file:
            return error_response(
                code="FILE_NOT_FOUND",
                message="Resume file not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            file_content = resume.file.read()
            logger.info(f"Enhancing resume: {resume.file.name}")
            text = self.resume_service._extract_text_from_file(file_content, resume.file.name)

            resume_data = self.resume_service.openai_service.extract_resume_info(
                text, language=language, skip_post_processing=False
            )

            # Temporarily free — no credit consumption
            return success_response(
                data={
                    "resume_data": resume_data,
                    "credits_remaining": request.user.resume_credits,
                    "message": "Resume enhanced successfully. Use /generate-pdf to download.",
                }
            )

        except ResumeProcessingError as e:
            logger.error(f"Resume processing error: {e!s}")
            return error_response(
                code="RESUME_PROCESSING_ERROR",
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except OpenAIServiceError as e:
            logger.error(f"AI service error: {e!s}")
            return error_response(
                code="AI_SERVICE_ERROR",
                message=f"AI service error: {e!s}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except Exception as e:
            logger.error(f"Unexpected error during enhancement: {e!s}")
            return error_response(
                code="ENHANCEMENT_ERROR",
                message=f"Failed to enhance resume: {e!s}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ==================== Credit Management ====================

    @action(detail=False, methods=["get"], url_path="credit-packages")
    def get_credit_packages(self, request):
        """
        Get available credit packages for purchase.
        URL: GET /api/v1/resumes/credit-packages/

        Returns:
            List of available credit packages with pricing
        """
        packages = self.store_service.get_active_packages()

        package_data = [
            {
                "credits": pkg.credits,
                "price": str(pkg.price),
                "currency": pkg.currency,
                "is_active": pkg.is_active,
            }
            for pkg in packages
        ]

        return success_response(data=package_data, message="Credit packages retrieved successfully")

    @action(detail=False, methods=["post"], url_path="purchase-credits")
    def purchase_credits(self, request):
        """
        Process credit purchase (called by Telegram bot after payment).
        URL: POST /api/v1/resumes/purchase-credits/

        Body (JSON):
            {
                "credits": 3,
                "payment_id": "telegram_payment_charge_id_12345",
                "payment_provider": "click",  // optional, defaults to 'click'
                "amount_paid": 20000,  // optional
                "currency": "UZS"  // optional
            }

        This endpoint should be called by the Telegram bot after successful payment.
        """
        credits = request.data.get("credits")
        payment_id = request.data.get("payment_id")
        payment_provider = request.data.get("payment_provider", "click")
        amount_paid = request.data.get("amount_paid")
        currency = request.data.get("currency", "UZS")

        # Validation
        if not credits or not isinstance(credits, int) or credits <= 0:
            return error_response(
                code="INVALID_CREDITS",
                message="Credits must be a positive integer",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not payment_id:
            return error_response(
                code="MISSING_PAYMENT_ID",
                message="Payment ID is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Check if payment_id already processed (prevent double-crediting)
        from apps.store.models import CreditTransaction

        existing_transaction = CreditTransaction.objects.filter(
            payment_id=payment_id, status="completed"
        ).first()

        if existing_transaction:
            logger.warning(f"Payment ID {payment_id} already processed for user {request.user.id}")
            return error_response(
                code="PAYMENT_ALREADY_PROCESSED",
                message="This payment has already been processed",
                status_code=status.HTTP_409_CONFLICT,
            )

        try:
            # Get the package for this credit amount
            package = self.store_service.get_package(credits)

            if not package:
                # Create metadata for manual purchase (if package not found)
                logger.warning(
                    f"Package not found for {credits} credits, processing as manual purchase"
                )

                # Try to create a temporary package reference or use metadata
                metadata = {
                    "credits": credits,
                    "amount_paid": str(amount_paid) if amount_paid else None,
                    "currency": currency,
                    "source": "telegram_bot",
                    "manual_purchase": True,
                }

                # Add credits directly without package
                from django.db import transaction as db_transaction

                with db_transaction.atomic():
                    user = request.user
                    user = user.__class__.objects.select_for_update().get(pk=user.pk)

                    user.resume_credits += credits
                    user.save(update_fields=["resume_credits"])

                    txn = CreditTransaction.objects.create(
                        user=user,
                        transaction_type="purchase",
                        credits=credits,
                        balance_after=user.resume_credits,
                        package=None,
                        amount_paid=amount_paid,
                        currency=currency,
                        payment_provider=payment_provider,
                        payment_id=payment_id,
                        status="completed",
                        metadata=metadata,
                    )

                    transaction_data = txn
            else:
                # Process with package
                transaction_data = self.store_service.purchase_credits(
                    user=request.user,
                    package=package,
                    payment_id=payment_id,
                    payment_provider=payment_provider,
                    metadata={
                        "source": "telegram_bot",
                        "telegram_user_id": request.data.get("telegram_user_id"),
                    },
                )

            logger.info(
                f"Credits purchased via API: user_id={request.user.id}, "
                f"credits={credits}, payment_id={payment_id}"
            )

            return success_response(
                data={
                    "transaction_id": transaction_data.id,
                    "credits_added": credits,
                    "new_balance": request.user.resume_credits,
                    "payment_id": payment_id,
                },
                message=f"Successfully added {credits} credits",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error processing credit purchase: {e!s}", exc_info=True)
            return error_response(
                code="PURCHASE_PROCESSING_ERROR",
                message=f"Failed to process credit purchase: {e!s}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="credits")
    def get_credits(self, request):
        """
        Get user's credit balance and purchase statistics.
        URL: GET /api/v1/resumes/credits/
        """
        stats = self.store_service.get_user_purchase_stats(request.user)

        return success_response(
            data={
                "current_balance": request.user.resume_credits,
                "statistics": stats,
                "user": {"id": str(request.user.id), "username": request.user.username},
            },
            message="Credits retrieved successfully",
        )

    @action(detail=False, methods=["get"], url_path="credit-history")
    def credit_history(self, request):
        """
        Get user's credit transaction history.
        URL: GET /api/v1/resumes/credit-history/

        Query params:
            - type: Filter by transaction type (purchase, usage, refund)
            - limit: Number of records to return (default: 50, max: 200)
        """
        transaction_type = request.query_params.get("type")
        limit = min(int(request.query_params.get("limit", 50)), 200)

        transactions = self.store_service.get_user_transaction_history(
            user=request.user, transaction_type=transaction_type, limit=limit
        )

        transaction_data = [
            {
                "id": txn.id,
                "type": txn.transaction_type,
                "credits": txn.credits,
                "balance_after": txn.balance_after,
                "status": txn.status,
                "amount_paid": str(txn.amount_paid) if txn.amount_paid else None,
                "currency": txn.currency,
                "payment_provider": txn.payment_provider,
                "resume_id": txn.resume_id,
                "notes": txn.notes,
                "created_at": txn.created_at.isoformat(),
            }
            for txn in transactions
        ]

        return success_response(
            data={
                "transactions": transaction_data,
                "count": len(transaction_data),
                "current_balance": request.user.resume_credits,
            },
            message="Transaction history retrieved successfully",
        )
