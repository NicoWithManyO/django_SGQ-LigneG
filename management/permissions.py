from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Permission qui autorise uniquement les superusers.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser