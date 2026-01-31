from rest_framework.permissions import BasePermission


class IsAuthenticatedAndNotBanned(BasePermission):
    """
    Allows access only to authenticated users who are not banned.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is banned
        try:
            return not request.user.banned
        except AttributeError:
            # If 'banned' attribute doesn't exist, allow access
            return True