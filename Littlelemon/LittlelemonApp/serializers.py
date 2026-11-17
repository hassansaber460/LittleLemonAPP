from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import Cart, Category, MenuItem, Order, OrderItem
from .permissions import is_manager


class CategorySerializer(serializers.ModelSerializer):
    menu_items = serializers.HyperlinkedRelatedField(
        many=True,
        view_name="menu-item-detail",
        read_only=True,
        lookup_field="title",
    )

    class Meta:
        model = Category
        fields = ["slug", "title", "menu_items"]


class MenuItemSerializer(serializers.ModelSerializer):
    category_write = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        write_only=True,
    )
    category_read = serializers.HyperlinkedRelatedField(
        source="category",
        view_name="category-detail",
        lookup_field="slug",
        read_only=True,
    )

    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category_write", "category_read"]
        extra_kwargs = {"price": {"min_value": 2}}


class CartSerializer(serializers.ModelSerializer):
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    unit_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "menu_item", "quantity", "unit_price", "price"]
        read_only_fields = ["id", "unit_price", "price"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        menu_item = validated_data["menu_item"]
        quantity = validated_data["quantity"]
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            menu_item=menu_item,
            defaults={
                "quantity": quantity,
                "unit_price": menu_item.price,
                "price": menu_item.price * quantity,
            },
        )
        if not created:
            cart_item.quantity += quantity
            # Refresh the snapshot from the current menu price when adding more.
            cart_item.unit_price = menu_item.price
            cart_item.save()
        return cart_item


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "quantity", "unit_price", "price"]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name="Delivery Crew").distinct(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Order
        fields = ["id", "user", "delivery_crew", "status", "date", "total", "items"]
        read_only_fields = ["id", "user", "date", "total", "items"]

    def validate(self, attrs):
        request = self.context.get("request")
        if request and not is_manager(request.user):
            submitted = set(self.initial_data.keys())
            if submitted - {"status"}:
                raise serializers.ValidationError(
                    "Delivery crew members may update the order status only."
                )
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
        )
        user.set_password(validated_data["password"])
        user.save()
        Token.objects.get_or_create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
