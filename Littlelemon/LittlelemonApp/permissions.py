from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_manager(user):
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.groups.filter(name="Manager").exists())
    )


def is_delivery_crew(user):
    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name="Delivery Crew").exists()
    )


def is_customer(user):
    """A customer is an authenticated user who is neither manager nor crew."""
    return bool(user and user.is_authenticated and not (is_manager(user) or is_delivery_crew(user)))


class IsManagerOrReadOnly(BasePermission):
    """Authenticated users may read; only managers may write."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return is_manager(request.user)


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return is_manager(request.user)


class IsManagerOrDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return is_manager(request.user) or is_delivery_crew(request.user)
