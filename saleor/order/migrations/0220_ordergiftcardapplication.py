import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("giftcard", "0022_merge_20250527_1210"),
        ("order", "0219_merge_20251212_0955"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderGiftCardApplication",
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
                    "amount_used_amount",
                    models.DecimalField(
                        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
                        max_digits=settings.DEFAULT_MAX_DIGITS,
                    ),
                ),
                (
                    "currency",
                    models.CharField(max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH),
                ),
                (
                    "gift_card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_applications",
                        to="giftcard.giftcard",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gift_card_applications",
                        to="order.order",
                    ),
                ),
            ],
            options={
                "ordering": ("id",),
                "unique_together": {("order", "gift_card")},
            },
        ),
    ]
