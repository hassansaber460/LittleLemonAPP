from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    menu_items = serializers.HyperlinkedRelatedField(
        many=True,
        view_name='menu-item-detail',
        read_only=True,
        lookup_field='title'
    )

    class Meta:
        model = Category
        fields = ['slug', 'title', 'menu_items']


class MenuItemSerializer(serializers.ModelSerializer):
    category_write = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True,
    )

    category_read = serializers.HyperlinkedRelatedField(
        source='category',
        view_name='category-detail',
        lookup_field='slug',
        read_only=True,
    )

    class Meta:
        model = MenuItem
        fields = [
            'title',
            'price',
            'featured',
            'category_write',
            'category_read',
        ]
        extra_kwargs = {
            'price': {'min_value': 2},
        }
