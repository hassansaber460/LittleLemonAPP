from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.models import Group, User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.validators import UniqueValidator

from .models import Cart, Category, MenuItem, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    menu_items = serializers.HyperlinkedRelatedField(
        many=True, view_name="menu-item-detail", read_only=True, lookup_field="title"
    )

    class Meta:
        model = Category
        fields = ("id", "slug", "title", "menu_items")


class MenuItemSerializer(serializers.ModelSerializer):
    category_write = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), write_only=True
    )
    category_read = serializers.HyperlinkedRelatedField(
        source="category", view_name="category-detail", lookup_field="slug", read_only=True
    )

    class Meta:
        model = MenuItem
        fields = ("id", "title", "price", "featured", "category_write", "category_read")
        extra_kwargs = {"price": {"min_value": 0}}


class CartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    unit_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "user", "menu_item", "quantity", "unit_price", "price")
        read_only_fields = ("id", "unit_price", "price")

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def create(self, validated_data):
        menu_item = validated_data["menu_item"]
        validated_data["unit_price"] = menu_item.price
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "menu_item" in validated_data:
            raise serializers.ValidationError({"menu_item": "Changing the menu item is not supported."})
        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.save()
        return instance


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "menu_item", "quantity", "unit_price", "price")


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name="Delivery Crew").distinct(),
        required=False,
        allow_null=True,
    )
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "user", "delivery_crew", "status", "date", "total", "items")
        read_only_fields = ("id", "user", "date", "total", "items")


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        read_only_fields = ("id",)

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Token.objects.get_or_create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request, username=attrs.get("username"), password=attrs.get("password")
        )
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        attrs["user"] = user
        return attrs
