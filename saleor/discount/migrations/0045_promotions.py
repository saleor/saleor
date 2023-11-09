import uuid
from decimal import Decimal

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import saleor.core.db.fields
import saleor.core.utils.editorjs
import saleor.core.utils.json_serializer


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0012_channel_delete_expired_orders_after"),
        ("order", "0170_auto_20230529_1314"),
        ("discount", "0044_auto_20230421_1018"),
    ]

    operations = [
        # Promotion models
        migrations.CreateModel(
            name="Promotion",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "private_metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                        null=True,
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                        null=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "description",
                    saleor.core.db.fields.SanitizedJSONField(
                        blank=True,
                        null=True,
                        sanitizer=saleor.core.utils.editorjs.clean_editor_js,
                    ),
                ),
                (
                    "old_sale_id",
                    models.IntegerField(blank=True, null=True, unique=True),
                ),
                ("start_date", models.DateTimeField(default=django.utils.timezone.now)),
                ("end_date", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "last_notification_scheduled_at",
                    models.DateTimeField(blank=True, null=True),
                ),
            ],
            options={
                "ordering": ("name", "pk"),
            },
        ),
        migrations.CreateModel(
            name="PromotionRule",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=255,
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "description",
                    saleor.core.db.fields.SanitizedJSONField(
                        blank=True,
                        null=True,
                        sanitizer=saleor.core.utils.editorjs.clean_editor_js,
                    ),
                ),
                ("catalogue_predicate", models.JSONField(blank=True, default=dict)),
                (
                    "reward_value_type",
                    models.CharField(
                        blank=True,
                        choices=[("fixed", "fixed"), ("percentage", "%")],
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "reward_value",
                    models.DecimalField(
                        decimal_places=3,
                        max_digits=12,
                        null=True,
                        blank=True,
                    ),
                ),
                ("channels", models.ManyToManyField(to="channel.Channel")),
                (
                    "promotion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rules",
                        to="discount.promotion",
                    ),
                ),
                (
                    "old_channel_listing_id",
                    models.IntegerField(blank=True, null=True, unique=True),
                ),
            ],
            options={
                "ordering": ("name", "pk"),
            },
        ),
        # Discount related changes
        migrations.AddField(
            model_name="checkoutlinediscount",
            name="promotion_rule",
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_index=False,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="discount.promotionrule",
            ),
        ),
        migrations.AddField(
            model_name="orderdiscount",
            name="promotion_rule",
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_index=False,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="discount.promotionrule",
            ),
        ),
        migrations.AlterField(
            model_name="checkoutlinediscount",
            name="type",
            field=models.CharField(
                choices=[
                    ("sale", "Sale"),
                    ("voucher", "Voucher"),
                    ("manual", "Manual"),
                    ("promotion", "Promotion"),
                ],
                default="manual",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="orderdiscount",
            name="type",
            field=models.CharField(
                choices=[
                    ("sale", "Sale"),
                    ("voucher", "Voucher"),
                    ("manual", "Manual"),
                    ("promotion", "Promotion"),
                ],
                default="manual",
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name="OrderLineDiscount",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("sale", "Sale"),
                            ("voucher", "Voucher"),
                            ("manual", "Manual"),
                            ("promotion", "Promotion"),
                        ],
                        default="manual",
                        max_length=10,
                    ),
                ),
                (
                    "value_type",
                    models.CharField(
                        choices=[("fixed", "fixed"), ("percentage", "%")],
                        default="fixed",
                        max_length=10,
                    ),
                ),
                (
                    "value",
                    models.DecimalField(
                        decimal_places=3, default=Decimal("0.0"), max_digits=12
                    ),
                ),
                (
                    "amount_value",
                    models.DecimalField(
                        decimal_places=3, default=Decimal("0.0"), max_digits=12
                    ),
                ),
                ("currency", models.CharField(max_length=3)),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "translated_name",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("reason", models.TextField(blank=True, null=True)),
                (
                    "line",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="discounts",
                        to="order.orderline",
                    ),
                ),
                (
                    "promotion_rule",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        db_index=False,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="discount.promotionrule",
                    ),
                ),
                (
                    "sale",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="discount.sale",
                    ),
                ),
                (
                    "voucher",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="discount.voucher",
                    ),
                ),
            ],
            options={
                "ordering": ("created_at", "id"),
            },
        ),
        # Translations
        migrations.CreateModel(
            name="PromotionTranslation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("language_code", models.CharField(max_length=35)),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "description",
                    saleor.core.db.fields.SanitizedJSONField(
                        blank=True,
                        null=True,
                        sanitizer=saleor.core.utils.editorjs.clean_editor_js,
                    ),
                ),
                (
                    "promotion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="discount.promotion",
                    ),
                ),
            ],
            options={
                "unique_together": {("language_code", "promotion")},
            },
        ),
        migrations.CreateModel(
            name="PromotionRuleTranslation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("language_code", models.CharField(max_length=35)),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "description",
                    saleor.core.db.fields.SanitizedJSONField(
                        blank=True,
                        null=True,
                        sanitizer=saleor.core.utils.editorjs.clean_editor_js,
                    ),
                ),
                (
                    "promotion_rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="discount.promotionrule",
                    ),
                ),
            ],
            options={
                "unique_together": {("language_code", "promotion_rule")},
            },
        ),
    ]
