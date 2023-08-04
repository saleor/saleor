from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import saleor.core.db.fields
import saleor.core.utils.editorjs
import saleor.core.utils.json_serializer
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0012_channel_delete_expired_orders_after"),
        ("discount", "0044_auto_20230421_1018"),
    ]

    operations = [
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
                ("catalogue_predicate", models.JSONField(blank=True)),
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
                    models.DecimalField(decimal_places=3, max_digits=12, null=True),
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
    ]
