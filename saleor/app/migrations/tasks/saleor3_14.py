import graphene
from django.db import transaction
from django.db.models import Exists, OuterRef

from .... import celeryconf
from ....payment.models import TransactionEvent, TransactionItem
from ...models import App

# Batch size of size 100 is less than 1MB memory usage in task
APP_BATCH_SIZE = 100

# Batch size of size 1000 is about 1MB memory usage in task
TRANSACTION_BATCH_SIZE = 1000


@celeryconf.app.task
def set_identifier_for_local_apps_task():
    apps = App.objects.filter(identifier__isnull=True)[:APP_BATCH_SIZE]
    if apps:
        app_ids = []
        for app in apps:
            app.identifier = graphene.Node.to_global_id("App", app.pk)
            app_ids.append(app.pk)
        App.objects.bulk_update(apps, ["identifier"])

        set_identifier_for_local_apps_task.delay()
        set_local_app_identifier_in_transaction_item_task.delay(app_ids)
        set_local_app_identifier_in_transaction_event_task.delay(app_ids)


@celeryconf.app.task
def set_local_app_identifier_in_transaction_item_task(app_ids=None):
    if not app_ids:
        return
    apps = App.objects.filter(id__in=app_ids)
    transaction_items = TransactionItem.objects.filter(
        Exists(apps.filter(id=OuterRef("app_id"))), app_identifier__isnull=True
    )[:TRANSACTION_BATCH_SIZE]
    if transaction_items:
        for transaction_item in transaction_items:
            transaction_item.app_identifier = graphene.Node.to_global_id(
                "App", transaction_item.app_id
            )
        with transaction.atomic():
            # lock batch of the objects for bulk update
            _locked_transactions = list(
                transaction_items.select_for_update(of=(["self"]))
            )
            TransactionItem.objects.bulk_update(transaction_items, ["app_identifier"])

        set_local_app_identifier_in_transaction_item_task.delay(app_ids)


@celeryconf.app.task
def set_local_app_identifier_in_transaction_event_task(app_ids=None):
    if not app_ids:
        return

    apps = App.objects.filter(id__in=app_ids)
    transaction_events = TransactionEvent.objects.filter(
        Exists(apps.filter(id=OuterRef("app_id"))), app_identifier__isnull=True
    )[:TRANSACTION_BATCH_SIZE]

    if transaction_events:
        for event in transaction_events:
            event.app_identifier = graphene.Node.to_global_id("App", event.app_id)

        with transaction.atomic():
            # lock batch of the objects for bulk update
            _locked_events = list(transaction_events.select_for_update(of=(["self"])))
            TransactionEvent.objects.bulk_update(transaction_events, ["app_identifier"])

        set_local_app_identifier_in_transaction_event_task.delay(app_ids)
