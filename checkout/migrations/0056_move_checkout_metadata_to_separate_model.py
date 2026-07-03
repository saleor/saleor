from django.db import migrations
from django.db.models import Q

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

    query_empty_meta = (
        Q(metadata={})
        | Q(private_metadata={})
        | Q(metadata__isnull=True)
        | Q(private_metadata__isnull=True)
    )
    checkouts_with_meta = (
        Checkout.objects.exclude(query_empty_meta)
        .order_by("pk")
        .distinct("token")
        .only("pk", "metadata", "private_metadata")
    )
    for batch_pks in queryset_in_batches(checkouts_with_meta):
        checkouts = Checkout.objects.filter(pk__in=batch_pks)
        CheckoutMetadata.objects.bulk_create(
            CheckoutMetadata(
                checkout=checkout,
                metadata=checkout.metadata if checkout.metadata else {},
                private_metadata=checkout.private_metadata
                if checkout.private_metadata
                else {},
            )
            for checkout in checkouts
        )


class Migration(migrations.Migration):
    dependencies = [
        ("checkout", "0055_create_checkout_metadata_model"),
    ]

    operations = [
        migrations.RunPython(move_all_checkout_metadata, migrations.RunPython.noop),
    ]
