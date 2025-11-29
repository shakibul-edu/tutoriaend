from rest_framework.permissions import BasePermission


class IsAuthenticatedAndNotBanned(BasePermission):
    """
    Allows access only to authenticated users who are not banned.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.banned)