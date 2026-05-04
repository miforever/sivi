"""
Custom exceptions for the CV Core application.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class ResumeProcessingError(APIException):
    """Base exception for resume processing errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Error processing resume"
    default_code = "resume_processing_error"


class PDFGenerationError(ResumeProcessingError):
    """Raised when there's an error generating a PDF."""

    default_detail = "Error generating PDF"
    default_code = "pdf_generation_error"


class InvalidRequestError(ResumeProcessingError):
    """Raised when the request data is invalid."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Invalid request data"
    default_code = "invalid_request"


class OpenAIServiceError(ResumeProcessingError):
    """Raised when there's an error with the OpenAI service."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Error with AI service"
    default_code = "ai_service_error"
