from rest_framework import permissions

class IsAdminUserSwaggerOnly(permissions.BasePermission):
    """
    Allows access only to admin users for Swagger and Redoc views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff