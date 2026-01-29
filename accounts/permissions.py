from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.is_staff:
            raise PermissionDenied(
                detail="You do not have admin privileges to access this resource."
            )
        return True
