from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    message = "Only a super admin can perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(request.user.is_authenticated and request.user.is_superuser)

