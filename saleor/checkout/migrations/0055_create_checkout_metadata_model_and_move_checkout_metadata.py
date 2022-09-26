import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q

import saleor.core.utils.json_serializer

BATCH_SIZE = 10000


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted by pk.
    """
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


def move_all_checkout_metadata(apps, schema_editor):
    Checkout = apps.get_model("checkout", "Checkout")
    CheckoutMetadata = apps.get_model("checkout", "CheckoutMetadata")
    checkouts_with_meta = (
        Checkout.objects.filter(
            Q(metadata__isnull=False) | Q(private_metadata__isnull=False)
        )
        .order_by("pk")
        .distinct("token")
    )
    for batch_pks in queryset_in_batches(checkouts_with_meta):
        checkouts = Checkout.objects.filter(pk__in=batch_pks)
        CheckoutMetadata.objects.bulk_create(
            CheckoutMetadata(
                checkout=checkout,
                metadata=checkout.metadata if hasattr(checkout, "metadata") else {},
                private_metadata=checkout.private_metadata
                if hasattr(checkout, "private_metadata")
                else {},
            )
            for checkout in checkouts
        )


class Migration(migrations.Migration):

    dependencies = [
        ("checkout", "0052_alter_checkoutline_currency"),
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
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="checkoutmetadata",
            name="checkout",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="metadata_storage",
                to="checkout.checkout",
            ),
        ),
        migrations.RunPython(move_all_checkout_metadata, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="checkout",
            name="checkout_p_meta_idx",
        ),
        migrations.RemoveIndex(
            model_name="checkout",
            name="checkout_meta_idx",
        ),
        migrations.RemoveField(
            model_name="checkout",
            name="metadata",
        ),
        migrations.RemoveField(
            model_name="checkout",
            name="private_metadata",
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
