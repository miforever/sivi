"""Custom permissions for analytics endpoints."""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Only allow superusers and staff users."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAnalyticsViewer(BasePermission):
    """Allow staff users to view analytics (read-only)."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return request.user.is_staff and request.method in ("GET", "HEAD", "OPTIONS")
