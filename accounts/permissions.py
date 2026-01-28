from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    message = "You do not have admin privileges to access this resource."

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_staff
        )
