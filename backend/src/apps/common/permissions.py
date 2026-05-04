"""Custom permissions for the API."""

from rest_framework.permissions import BasePermission


class IsUserOrAdmin(BasePermission):
    """
    Permission to check if user is accessing their own data or is admin.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user is the owner or admin.
        """
        return obj == request.user or (hasattr(request.user, "is_staff") and request.user.is_staff)
