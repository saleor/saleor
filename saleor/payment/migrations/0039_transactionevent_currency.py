from django.db import migrations


def set_default_currency_for_transaction_event(apps, _schema_editor):
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
        ("payment", "0038_auto_20230223_0926"),
    ]

    operations = [
        migrations.RunPython(
            set_default_currency_for_transaction_event, migrations.RunPython.noop
        ),
    ]
