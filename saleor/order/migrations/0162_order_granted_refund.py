from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0020_app_is_installed"),
        ("account", "0076_fill_empty_passwords"),
        ("order", "0161_merge_20221219_1838"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderGrantedRefund",
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
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "amount_value",
                    models.DecimalField(
                        decimal_places=3, default=Decimal("0"), max_digits=12
                    ),
                ),
                ("currency", models.CharField(max_length=3)),
                ("reason", models.TextField(blank=True, default="")),
                (
                    "app",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="app.app",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="granted_refunds",
                        to="order.order",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="account.user",
                    ),
                ),
            ],
            options={
                "ordering": ("created_at", "id"),
            },
        ),
    ]
