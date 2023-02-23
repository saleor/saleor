from django.db import migrations, models
import django.contrib.postgres.indexes


import saleor.core.utils.json_serializer


class Migration(migrations.Migration):
    dependencies = [
        ("checkout", "0054_alter_checkout_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="CheckoutMetadata",
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
                (
                    "checkout",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="metadata_storage",
                        to="checkout.checkout",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddIndex(
            model_name="checkoutmetadata",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["private_metadata"], name="checkoutmetadata_p_meta_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="checkoutmetadata",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["metadata"], name="checkoutmetadata_meta_idx"
            ),
        ),
    ]
