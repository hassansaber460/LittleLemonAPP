from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=225, db_index=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    title = models.CharField(max_length=225, db_index=True, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, db_index=True)
    featured = models.BooleanField(default=False)
    category = models.ForeignKey(
        Category, related_name="menu_items", on_delete=models.PROTECT
    )

    class Meta:
        ordering = ("title",)
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name="menuitem_price_nonnegative"),
        ]

    def __str__(self):
        return self.title


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(fields=("user", "menu_item"), name="unique_cart_item_per_user"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="cart_quantity_positive"),
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="cart_unit_price_nonnegative"),
            models.CheckConstraint(condition=Q(price__gte=0), name="cart_price_nonnegative"),
        ]

    def save(self, *args, **kwargs):
        self.price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.menu_item} x {self.quantity}"


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    delivery_crew = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="delivery_orders",
        null=True,
        blank=True,
    )
    status = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ("-date", "-id")

    def __str__(self):
        return f"Order #{self.pk} - {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("order", "menu_item"), name="unique_menu_item_per_order"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="orderitem_quantity_positive"),
        ]

    def save(self, *args, **kwargs):
        self.price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.menu_item} x {self.quantity}"
