from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=225, db_index=True)

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    title = models.CharField(max_length=225, db_index=True, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField()
    category = models.ForeignKey(Category, related_name='menu_items', on_delete=models.PROTECT)


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)

    class Meta:
        unique_together = ('user', 'menu_item')


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='delivery_crew', null=True)
    status = models.BooleanField(default=0)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField(auto_now=True)


class OrderItem(models.Model):
    order = models.ForeignKey(User, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)

    class Meta:
        unique_together = ('order', 'menu_item')

