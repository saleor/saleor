import graphene
from django.db import migrations
from django.db.models import Q

# Fixes the issue from previous identifier changes, where `app_create` was setting
# identifier based on NULL PK
# Need to rerun migration task from migration 0027 cause of missing
# setting up `identifier` on create_app command

APP_BATCH_SIZE = 100
TRANSACTION_BATCH_SIZE = 10000


def set_local_app_identifier_in_transaction_item(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")
    none_global_id = graphene.Node.to_global_id("App", None)

    while True:
        transaction_items = TransactionItem.objects.filter(
            Q(app_id__isnull=False)
            & (Q(app_identifier__isnull=True) | Q(app_identifier=none_global_id))
        )[:TRANSACTION_BATCH_SIZE]
        if not transaction_items:
            break

        for transaction_item in transaction_items:
            transaction_item.app_identifier = graphene.Node.to_global_id(
                "App", transaction_item.app_id
            )
        TransactionItem.objects.bulk_update(transaction_items, ["app_identifier"])


def set_local_app_identifier_in_transaction_event(apps, _schema_editor):
    TransactionEvent = apps.get_model("payment", "TransactionEvent")
    none_global_id = graphene.Node.to_global_id("App", None)

    while True:
        transaction_events = TransactionEvent.objects.filter(
            Q(app_id__isnull=False)
            & (Q(app_identifier__isnull=True) | Q(app_identifier=none_global_id))
        )[:TRANSACTION_BATCH_SIZE]

        if not transaction_events:
            break

        for event in transaction_events:
            event.app_identifier = graphene.Node.to_global_id("App", event.app_id)

        TransactionEvent.objects.bulk_update(transaction_events, ["app_identifier"])


def set_identifier_for_local_apps(apps, _schema_editor):
    App = apps.get_model("app", "App")
    none_global_id = graphene.Node.to_global_id("App", None)

    while True:
        apps = App.objects.filter(
            Q(identifier__isnull=True) | Q(identifier=none_global_id)
        )[:APP_BATCH_SIZE]
        if not apps:
            break

        for app in apps:
            app.identifier = graphene.Node.to_global_id("App", app.pk)

        App.objects.bulk_update(apps, ["identifier"])


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0027_set_identifier_when_missing"),
    ]

    operations = [
        migrations.RunPython(set_identifier_for_local_apps, migrations.RunPython.noop),
        migrations.RunPython(
            set_local_app_identifier_in_transaction_item, migrations.RunPython.noop
        ),
        migrations.RunPython(
            set_local_app_identifier_in_transaction_event, migrations.RunPython.noop
        ),
    ]
