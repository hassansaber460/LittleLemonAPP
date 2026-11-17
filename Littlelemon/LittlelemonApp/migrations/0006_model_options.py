from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("LittlelemonApp", "0005_api_integrity_refactor"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={"ordering": ("title",)},
        ),
        migrations.AlterModelOptions(
            name="menuitem",
            options={"ordering": ("title",)},
        ),
        migrations.AlterModelOptions(
            name="cart",
            options={"ordering": ("id",)},
        ),
        migrations.AlterModelOptions(
            name="order",
            options={"ordering": ("-date", "-id")},
        ),
        migrations.AlterField(
            model_name="menuitem",
            name="featured",
            field=models.BooleanField(default=False),
        ),
    ]
