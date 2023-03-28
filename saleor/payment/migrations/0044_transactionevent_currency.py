from django.db import migrations


# This data migration is handled in the 0039 with celery tasks.
# 0039 is due to zero-downtime policy, this migration is to ensure
# that we can change currency to non-nullable.
def set_default_currency_for_transaction_event(apps, schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")
    TransactionEvent = apps.get_model("payment", "TransactionEvent")

    for currency in (
        TransactionItem.objects.values_list("currency", flat=True).distinct().order_by()
    ):
        TransactionEvent.objects.filter(
            currency=None, transaction__currency=currency
        ).update(currency=currency)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0043_drop_from_state_renamed_fields"),
    ]

    operations = [
        migrations.RunPython(
            set_default_currency_for_transaction_event, migrations.RunPython.noop
        ),
    ]
