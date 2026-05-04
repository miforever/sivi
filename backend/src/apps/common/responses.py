"""Custom response formatters."""

from rest_framework.response import Response


def success_response(data=None, message=None, status_code=200, meta=None):
    """
    Format a successful API response.

    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code
        meta: Optional metadata (for pagination, etc.)
    """
    response_data = {
        "success": True,
    }

    if data is not None:
        response_data["data"] = data

    if message:
        response_data["message"] = message

    if meta:
        response_data["meta"] = meta

    return Response(response_data, status=status_code)


def error_response(code, message, status_code=400):
    """
    Format an error API response.

    Args:
        code: Error code (e.g., INVALID_FILE)
        message: Error message
        status_code: HTTP status code
    """
    return Response(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
        status=status_code,
    )
