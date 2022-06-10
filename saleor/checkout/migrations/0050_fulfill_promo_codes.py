from django.db import migrations


BATCH_SIZE = 500


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.order_by("pk").filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


def set_promo_codes(apps, _schema_editor):
    Checkout = apps.get_model("checkout", "Checkout")
    queryset = Checkout.objects.filter(voucher_code__isnull=False)
    for batch_pks in queryset_in_batches(queryset):
        checkouts = Checkout.objects.filter(pk__in=batch_pks)
        for checkout in checkouts:
            checkout.promo_codes = [checkout.voucher_code]
        Checkout.objects.bulk_update(checkouts, ["promo_codes"])


class Migration(migrations.Migration):

    dependencies = [
        ("checkout", "0049_checkout_promo_codes"),
    ]

    operations = [
        migrations.RunPython(
            set_promo_codes,
            migrations.RunPython.noop,
        ),
    ]
