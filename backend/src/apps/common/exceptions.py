"""Custom exceptions for the API."""

from rest_framework import status
from rest_framework.exceptions import APIException


class ResumeLimitExceeded(APIException):
    """Raised when user exceeds resume limit."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Resume limit exceeded for this user."
    default_code = "RESUME_LIMIT_REACHED"


class InvalidFileType(APIException):
    """Raised when file type is not allowed."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "File type not allowed."
    default_code = "INVALID_FILE_TYPE"


class FileTooLarge(APIException):
    """Raised when file size exceeds limit."""

    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "File size exceeds maximum allowed size."
    default_code = "FILE_TOO_LARGE"


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    Returns consistent response envelope format.
    """
    from rest_framework.views import exception_handler

    # Call the default exception handler first to get the standard error response
    response = exception_handler(exc, context)

    if response is not None:
        # Wrap response in standard envelope
        error_code = getattr(exc, "default_code", "INTERNAL_ERROR")
        error_message = (
            response.data.get("detail", str(exc)) if hasattr(response.data, "get") else str(exc)
        )

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": str(error_message),
            },
        }

    return response
