from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def validate_legacy_order_items(apps, schema_editor):
    OrderItem = apps.get_model("LittlelemonApp", "OrderItem")
    Cart = apps.get_model("LittlelemonApp", "Cart")

    if OrderItem.objects.exists():
        raise RuntimeError(
            "Migration blocked: legacy OrderItem.order points to auth.User, "
            "so existing rows cannot be safely linked to a specific Order. "
            "Back up the database and manually archive/remap these rows before retrying."
        )

    if Cart.objects.filter(quantity__lte=0).exists():
        raise RuntimeError(
            "Migration blocked: Cart contains non-positive quantities. "
            "Correct those rows before retrying."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("LittlelemonApp", "0004_alter_menuitem_title"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(validate_legacy_order_items, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="orderitem",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="LittlelemonApp.order",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="date",
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="delivery_crew",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="delivery_orders",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="menuitem",
            name="price",
            field=models.DecimalField(db_index=True, decimal_places=2, max_digits=8),
        ),
        migrations.AlterField(
            model_name="cart",
            name="quantity",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name="cart",
            name="unit_price",
            field=models.DecimalField(decimal_places=2, max_digits=8),
        ),
        migrations.AlterField(
            model_name="cart",
            name="price",
            field=models.DecimalField(db_index=True, decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="quantity",
            field=models.PositiveSmallIntegerField(),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="unit_price",
            field=models.DecimalField(decimal_places=2, max_digits=8),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="price",
            field=models.DecimalField(db_index=True, decimal_places=2, max_digits=10),
        ),
        migrations.RemoveConstraint(
            model_name="cart",
            name="unique_cart_item_per_user",
        ) if False else migrations.AlterUniqueTogether(
            name="cart",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="orderitem",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="cart",
            constraint=models.UniqueConstraint(
                fields=("user", "menu_item"), name="unique_cart_item_per_user"
            ),
        ),
        migrations.AddConstraint(
            model_name="cart",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)), name="cart_quantity_positive"
            ),
        ),
        migrations.AddConstraint(
            model_name="cart",
            constraint=models.CheckConstraint(
                condition=models.Q(("unit_price__gte", 0)), name="cart_unit_price_nonnegative"
            ),
        ),
        migrations.AddConstraint(
            model_name="cart",
            constraint=models.CheckConstraint(
                condition=models.Q(("price__gte", 0)), name="cart_price_nonnegative"
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.UniqueConstraint(
                fields=("order", "menu_item"), name="unique_menu_item_per_order"
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)), name="orderitem_quantity_positive"
            ),
        ),
        migrations.AddConstraint(
            model_name="menuitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("price__gte", 0)), name="menuitem_price_nonnegative"
            ),
        ),
    ]
