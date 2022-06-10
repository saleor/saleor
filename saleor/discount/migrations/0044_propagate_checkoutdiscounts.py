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


def propagate_checkouts_discounts(apps, schema_editor):
    Checkout = apps.get_model("checkout", "Checkout")
    queryset = Checkout.objects.filter(discount_amount__gt=0)
    CheckoutDiscount = apps.get_model("discount", "CheckoutDiscount")
    for batch_pks in queryset_in_batches(queryset):
        checkouts = Checkout.objects.filter(pk__in=batch_pks)
        CheckoutDiscount.objects.bulk_create(
            [
                CheckoutDiscount(
                    checkout_id=checkout.pk,
                    created_at=checkout.created_at,
                    type="voucher",
                    value_type="fixed",
                    value=checkout.discount_amount,
                    amount_value=checkout.discount_amount,
                    currency=checkout.currency,
                    name=checkout.discount_name,
                    translated_name=checkout.translated_discount_name,
                    code=checkout.voucher_code,
                )
                for checkout in checkouts
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("checkout", "0048_alter_checkoutline_options"),
        ("discount", "0043_auto_20220609_1347"),
    ]

    operations = [
        migrations.RunPython(
            propagate_checkouts_discounts,
            migrations.RunPython.noop,
        ),
    ]
