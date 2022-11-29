from __future__ import unicode_literals

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("product", "0001_initial"),
        ("account", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliveryGroup",
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
                    "status",
                    models.CharField(
                        default="new",
                        max_length=32,
                        verbose_name="delivery status",
                        choices=[
                            ("new", "Processing"),
                            ("cancelled", "Cancelled"),
                            ("shipped", "Shipped"),
                        ],
                    ),
                ),
                (
                    "shipping_required",
                    models.BooleanField(default=True, verbose_name="shipping required"),
                ),
                (
                    "shipping_price",
                    models.DecimalField(
                        decimal_places=4,
                        default=0,
                        editable=False,
                        max_digits=12,
                        verbose_name="shipping price",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Order",
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
                    "status",
                    models.CharField(
                        default="new",
                        max_length=32,
                        verbose_name="order status",
                        choices=[
                            ("new", "Processing"),
                            ("cancelled", "Cancelled"),
                            ("payment-pending", "Waiting for payment"),
                            ("fully-paid", "Fully paid"),
                            ("shipped", "Shipped"),
                        ],
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="created",
                        editable=False,
                    ),
                ),
                (
                    "last_status_change",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="last status change",
                        editable=False,
                    ),
                ),
                (
                    "tracking_client_id",
                    models.CharField(max_length=36, editable=False, blank=True),
                ),
                (
                    "shipping_method",
                    models.CharField(
                        max_length=255, verbose_name="Delivery method", blank=True
                    ),
                ),
                (
                    "anonymous_user_email",
                    models.EmailField(
                        default="", max_length=254, editable=False, blank=True
                    ),
                ),
                (
                    "token",
                    models.CharField(unique=True, max_length=36, verbose_name="token"),
                ),
                (
                    "billing_address",
                    models.ForeignKey(
                        related_name="+",
                        editable=False,
                        to="account.Address",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "shipping_address",
                    models.ForeignKey(
                        related_name="+",
                        editable=False,
                        to="account.Address",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="orders",
                        verbose_name="user",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"ordering": ("-last_status_change",)},
        ),
        migrations.CreateModel(
            name="OrderedItem",
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
                    "product_name",
                    models.CharField(max_length=128, verbose_name="product name"),
                ),
                ("product_sku", models.CharField(max_length=32, verbose_name="sku")),
                (
                    "quantity",
                    models.IntegerField(
                        verbose_name="quantity",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(999),
                        ],
                    ),
                ),
                (
                    "unit_price_net",
                    models.DecimalField(
                        verbose_name="unit price (net)", max_digits=12, decimal_places=4
                    ),
                ),
                (
                    "unit_price_gross",
                    models.DecimalField(
                        verbose_name="unit price (gross)",
                        max_digits=12,
                        decimal_places=4,
                    ),
                ),
                (
                    "delivery_group",
                    models.ForeignKey(
                        related_name="items",
                        editable=False,
                        to="order.DeliveryGroup",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        related_name="+",
                        on_delete=django.db.models.deletion.SET_NULL,
                        verbose_name="product",
                        blank=True,
                        to="product.Product",
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OrderHistoryEntry",
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
                    "date",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="last history change",
                        editable=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        max_length=32,
                        verbose_name="order status",
                        choices=[
                            ("new", "Processing"),
                            ("cancelled", "Cancelled"),
                            ("payment-pending", "Waiting for payment"),
                            ("fully-paid", "Fully paid"),
                            ("shipped", "Shipped"),
                        ],
                    ),
                ),
                ("comment", models.CharField(default="", max_length=100, blank=True)),
                (
                    "order",
                    models.ForeignKey(
                        related_name="history",
                        to="order.Order",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"ordering": ["date"]},
        ),
        migrations.CreateModel(
            name="OrderNote",
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
                ("date", models.DateTimeField(auto_now_add=True)),
                ("content", models.CharField(max_length=250)),
                (
                    "order",
                    models.ForeignKey(
                        related_name="notes",
                        to="order.Order",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
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
                ("variant", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        default="waiting",
                        max_length=10,
                        choices=[
                            ("waiting", "Waiting for confirmation"),
                            ("preauth", "Pre-authorized"),
                            ("confirmed", "Confirmed"),
                            ("rejected", "Rejected"),
                            ("refunded", "Refunded"),
                            ("error", "Error"),
                            ("input", "Input"),
                        ],
                    ),
                ),
                (
                    "fraud_status",
                    models.CharField(
                        default="unknown",
                        max_length=10,
                        verbose_name="fraud check",
                        choices=[
                            ("unknown", "Unknown"),
                            ("accept", "Passed"),
                            ("reject", "Rejected"),
                            ("review", "Review"),
                        ],
                    ),
                ),
                ("fraud_message", models.TextField(default="", blank=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                ("transaction_id", models.CharField(max_length=255, blank=True)),
                ("currency", models.CharField(max_length=10)),
                (
                    "total",
                    models.DecimalField(default="0.0", max_digits=9, decimal_places=2),
                ),
                (
                    "delivery",
                    models.DecimalField(default="0.0", max_digits=9, decimal_places=2),
                ),
                (
                    "tax",
                    models.DecimalField(default="0.0", max_digits=9, decimal_places=2),
                ),
                ("description", models.TextField(default="", blank=True)),
                ("billing_first_name", models.CharField(max_length=256, blank=True)),
                ("billing_last_name", models.CharField(max_length=256, blank=True)),
                ("billing_address_1", models.CharField(max_length=256, blank=True)),
                ("billing_address_2", models.CharField(max_length=256, blank=True)),
                ("billing_city", models.CharField(max_length=256, blank=True)),
                ("billing_postcode", models.CharField(max_length=256, blank=True)),
                ("billing_country_code", models.CharField(max_length=2, blank=True)),
                ("billing_country_area", models.CharField(max_length=256, blank=True)),
                ("billing_email", models.EmailField(max_length=254, blank=True)),
                ("customer_ip_address", models.IPAddressField(blank=True)),
                ("extra_data", models.TextField(default="", blank=True)),
                ("message", models.TextField(default="", blank=True)),
                ("token", models.CharField(default="", max_length=36, blank=True)),
                (
                    "captured_amount",
                    models.DecimalField(default="0.0", max_digits=9, decimal_places=2),
                ),
                (
                    "order",
                    models.ForeignKey(
                        related_name="payments",
                        to="order.Order",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.AddField(
            model_name="deliverygroup",
            name="order",
            field=models.ForeignKey(
                related_name="groups",
                editable=False,
                to="order.Order",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
