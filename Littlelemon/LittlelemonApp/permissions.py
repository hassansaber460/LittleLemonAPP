from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        else:
            return (
                    request.user.is_authenticated and
                    request.user.groups.filter(name='Manager').exists()
                    )
