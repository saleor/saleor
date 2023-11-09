import uuid

import django.core.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0012_auto_20160218_0812"),
        ("discount", "0003_auto_20160207_0534"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    replaces = [("cart", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Cart",
            fields=[
                (
                    "status",
                    models.CharField(
                        default="open",
                        max_length=32,
                        verbose_name="order status",
                        choices=[
                            ("open", "Open - currently active"),
                            ("payment", "Waiting for payment"),
                            ("saved", "Saved - for items to be purchased later"),
                            ("ordered", "Submitted - has been ordered at the checkout"),
                            ("checkout", "Checkout - basket is processed in checkout"),
                            ("canceled", "Canceled - basket was canceled by user"),
                        ],
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "last_status_change",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="last status change"
                    ),
                ),
                ("email", models.EmailField(max_length=254, null=True, blank=True)),
                (
                    "token",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        serialize=False,
                        editable=False,
                        verbose_name="token",
                    ),
                ),
                ("checkout_data", models.TextField(null=True, editable=False)),
                (
                    "total",
                    models.DecimalField(default=0, max_digits=12, decimal_places=2),
                ),
                ("quantity", models.PositiveIntegerField(default=0)),
                (
                    "user",
                    models.ForeignKey(
                        related_name="carts",
                        verbose_name="user",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "voucher",
                    models.ForeignKey(
                        related_name="+",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="discount.Voucher",
                        null=True,
                    ),
                ),
            ],
            options={"db_table": "cart_cart", "ordering": ("-last_status_change",)},
        ),
        migrations.CreateModel(
            name="CartLine",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(
                        verbose_name="quantity",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(999),
                        ],
                    ),
                ),
                ("data", models.TextField(default="{}", blank=True)),
                (
                    "cart",
                    models.ForeignKey(
                        related_name="lines",
                        to="checkout.Cart",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        related_name="+",
                        verbose_name="product",
                        to="product.ProductVariant",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "cart_cartline"},
        ),
        migrations.AlterUniqueTogether(
            name="cartline", unique_together=set([("cart", "product", "data")])
        ),
    ]
