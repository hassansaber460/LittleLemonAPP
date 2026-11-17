from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Cart, Category, MenuItem, Order, OrderItem
from .permissions import (
    IsManager,
    IsManagerOrReadOnly,
    is_customer,
    is_delivery_crew,
    is_manager,
)
from .serializers import (
    CartSerializer,
    CategorySerializer,
    LoginSerializer,
    MenuItemSerializer,
    OrderSerializer,
    UserSerializer,
)


class CategoryViews(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated, IsManagerOrReadOnly,)


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = (IsAuthenticated,)


class MenuItemDetailView(generics.RetrieveAPIView):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    lookup_field = "title"
    permission_classes = (IsAuthenticated,)


class MenuItemViews(generics.ListCreateAPIView):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    permission_classes = (IsAuthenticated, IsManagerOrReadOnly)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("title", "category__title")
    ordering_fields = ("title", "price", "featured")
    ordering = ("title",)


class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related("menu_item")

    def delete(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        menu_item = serializer.validated_data["menu_item"]
        quantity = serializer.validated_data["quantity"]
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            menu_item=menu_item,
            defaults={"quantity": quantity, "unit_price": menu_item.price, "price": menu_item.price * quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.unit_price = menu_item.price
            cart_item.save()
        output = self.get_serializer(cart_item)
        return Response(output.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.select_related("user", "delivery_crew").prefetch_related("items__menu_item")
        if is_manager(user):
            return queryset
        if is_delivery_crew(user):
            return queryset.filter(delivery_crew=user)
        if is_customer(user):
            return queryset.filter(user=user)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        if not is_customer(request.user):
            raise PermissionDenied("Only customers can place orders.")
        cart_items = list(
            Cart.objects.filter(user=request.user).select_related("menu_item")
        )
        if not cart_items:
            raise ValidationError({"detail": "Your cart is empty."})

        with transaction.atomic():
            total = sum((item.menu_item.price * item.quantity for item in cart_items), start=0)
            order = Order.objects.create(user=request.user, total=total)
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    menu_item=item.menu_item,
                    quantity=item.quantity,
                    unit_price=item.menu_item.price,
                    price=item.menu_item.price * item.quantity,
                )
                for item in cart_items
            ])
            Cart.objects.filter(user=request.user).delete()

        order = self.get_queryset().get(pk=order.pk)
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)


class SingleOrderView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.select_related("user", "delivery_crew").prefetch_related("items__menu_item")
        if is_manager(user):
            return queryset
        if is_delivery_crew(user):
            return queryset.filter(delivery_crew=user)
        if is_customer(user):
            return queryset.filter(user=user)
        return queryset.none()

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if is_manager(request.user):
            allowed = {"delivery_crew", "status"}
        elif is_delivery_crew(request.user):
            allowed = {"status"}
        else:
            raise PermissionDenied("Customers can view their orders but cannot update them.")
        unexpected = set(request.data.keys()) - allowed
        if unexpected:
            raise ValidationError({"detail": f"Fields cannot be changed by this role: {', '.join(sorted(unexpected))}."})
        serializer = self.get_serializer(order, data=request.data, partial=kwargs.pop("partial", False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GroupViewSet(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)

    def list(self, request):
        users = User.objects.filter(groups__name="Manager").order_by("username")
        return Response(UserSerializer(users, many=True).data)

    def create(self, request):
        user = get_object_or_404(User, username=request.data.get("username"))
        group, _ = Group.objects.get_or_create(name="Manager")
        group.user_set.add(user)
        return Response({"message": "User added to the Manager group."}, status=status.HTTP_200_OK)

    def destroy(self, request):
        user = get_object_or_404(User, username=request.data.get("username"))
        group = get_object_or_404(Group, name="Manager")
        group.user_set.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeliveryCrewViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def _check_manager(self, request):
        if not is_manager(request.user):
            raise PermissionDenied("Only managers can manage delivery crew membership.")

    def list(self, request):
        if not (is_manager(request.user) or request.user.is_superuser):
            raise PermissionDenied("Only managers can list delivery crew members.")
        users = User.objects.filter(groups__name="Delivery Crew").order_by("username")
        return Response(UserSerializer(users, many=True).data)

    def create(self, request):
        self._check_manager(request)
        user = get_object_or_404(User, username=request.data.get("username"))
        group, _ = Group.objects.get_or_create(name="Delivery Crew")
        group.user_set.add(user)
        return Response({"message": "User added to the Delivery Crew group."}, status=status.HTTP_200_OK)

    def destroy(self, request):
        self._check_manager(request)
        user = get_object_or_404(User, username=request.data.get("username"))
        group = get_object_or_404(Group, name="Delivery Crew")
        group.user_set.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViews(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = ()


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = user.auth_token.get_or_create()
        return Response({"token": token.key}, status=status.HTTP_200_OK)
