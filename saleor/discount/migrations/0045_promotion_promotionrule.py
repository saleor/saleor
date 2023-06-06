from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import saleor.core.db.fields
import saleor.core.utils.editorjs
import saleor.core.utils.json_serializer


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
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
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
                ("old_sale", models.BooleanField(default=False)),
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
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
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
                ("catalogue_predicate", models.JSONField()),
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
            ],
            options={
                "ordering": ("name", "pk"),
            },
        ),
    ]
