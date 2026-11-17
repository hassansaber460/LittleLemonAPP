from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import Cart, Category, MenuItem, Order, OrderItem
from .permissions import IsManager, IsManagerOrReadOnly, is_delivery_crew, is_manager
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
    permission_classes = [IsManagerOrReadOnly]


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [IsAuthenticated]


class MenuItemViews(generics.ListCreateAPIView):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["title", "category__title"]
    ordering_fields = ["price", "title"]
    ordering = ["title"]


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    lookup_field = "title"
    permission_classes = [IsManagerOrReadOnly]


class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related("menu_item")

    def delete(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.select_related("user", "delivery_crew").prefetch_related("items")
        if is_manager(user):
            return orders
        if is_delivery_crew(user):
            return orders.filter(delivery_crew=user)
        # Users without Manager or Delivery Crew membership are customers.
        return orders.filter(user=user)

    def create(self, request, *args, **kwargs):
        cart_items = list(
            Cart.objects.filter(user=request.user).select_related("menu_item")
        )
        if not cart_items:
            return Response(
                {"detail": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            total = sum((item.unit_price * item.quantity for item in cart_items), Decimal("0.00"))
            order = Order.objects.create(user=request.user, total=total)
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        menu_item=item.menu_item,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        price=item.unit_price * item.quantity,
                    )
                    for item in cart_items
                ]
            )
            Cart.objects.filter(user=request.user).delete()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SingleOrderView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.select_related("user", "delivery_crew").prefetch_related("items")
        if is_manager(user):
            return orders
        if is_delivery_crew(user):
            return orders.filter(delivery_crew=user)
        return orders.filter(user=user)

    def update(self, request, *args, **kwargs):
        user = request.user
        if not (is_manager(user) or is_delivery_crew(user)):
            return Response(
                {"detail": "Customers cannot modify orders."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if is_delivery_crew(user) and set(request.data.keys()) != {"status"}:
            return Response(
                {"detail": "Delivery crew members may update the status field only."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        forbidden_manager_fields = {"user", "total", "date", "items"}
        if is_manager(user) and forbidden_manager_fields.intersection(request.data.keys()):
            return Response(
                {"detail": "Order ownership, total, date and items cannot be edited here."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)


class ManagerGroupViewSet(viewsets.ViewSet):
    """Only Django administrators may manage membership of the Manager group."""
    permission_classes = [IsAdminUser]

    def list(self, request):
        users = User.objects.filter(groups__name="Manager").order_by("username")
        return Response(UserSerializer(users, many=True).data)

    def create(self, request):
        username = request.data.get("username")
        if not username:
            return Response({"username": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        group, _ = Group.objects.get_or_create(name="Manager")
        group.user_set.add(user)
        return Response({"detail": f"{username} added to Manager."}, status=status.HTTP_200_OK)

    def destroy(self, request):
        username = request.data.get("username")
        if not username:
            return Response({"username": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        group, _ = Group.objects.get_or_create(name="Manager")
        group.user_set.remove(user)
        return Response({"detail": f"{username} removed from Manager."}, status=status.HTTP_200_OK)


class DeliveryCrewViewSet(viewsets.ViewSet):
    """Managers manage Delivery Crew membership; only managers can list members."""
    permission_classes = [IsManager]

    def list(self, request):
        users = User.objects.filter(groups__name="Delivery Crew").order_by("username")
        return Response(UserSerializer(users, many=True).data)

    def create(self, request):
        username = request.data.get("username")
        if not username:
            return Response({"username": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        group, _ = Group.objects.get_or_create(name="Delivery Crew")
        group.user_set.add(user)
        return Response({"detail": f"{username} added to Delivery Crew."}, status=status.HTTP_200_OK)

    def destroy(self, request):
        username = request.data.get("username")
        if not username:
            return Response({"username": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        group, _ = Group.objects.get_or_create(name="Delivery Crew")
        group.user_set.remove(user)
        return Response({"detail": f"{username} removed from Delivery Crew."}, status=status.HTTP_200_OK)


class UserViews(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    authentication_classes = []


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_200_OK)
