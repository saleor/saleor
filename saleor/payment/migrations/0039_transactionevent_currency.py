from django.db import migrations
from django.db.models import F, OuterRef, QuerySet, Subquery


def set_default_currency_for_transaction_event(qs: QuerySet):
    qs.update(currency=F("transaction_currency"))


def set_default_currency_for_transaction_event_migration(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")
    TransactionEvent = apps.get_model("payment", "TransactionEvent")

    transaction_item = TransactionItem.objects.filter(
        pk=OuterRef("transaction")
    ).values("currency")
    qs = (
        TransactionEvent.objects.filter(currency__isnull=True)
        .order_by("-pk")
        .annotate(transaction_currency=Subquery(transaction_item))
    )

    set_default_currency_for_transaction_event(qs)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0038_auto_20230223_0926"),
    ]

    operations = [
        migrations.RunPython(
            set_default_currency_for_transaction_event_migration,
            migrations.RunPython.noop,
        ),
    ]
