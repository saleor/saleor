from django.db import migrations


def drop_transaction_action_request(apps, _schema_editor):
    WebhookEvent = apps.get_model("webhook", "WebhookEvent")
    # transaction_action_request was the webhook for triggering the actions like a
    # refund, charge or cancel in asynchronous mode. The number of records here will
    # be from 0 to max +/- 10.
    WebhookEvent.objects.filter(event_type="transaction_action_request").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("webhook", "0009_webhook_custom_headers"),
    ]

    operations = [
        migrations.RunPython(
            drop_transaction_action_request, reverse_code=migrations.RunPython.noop
        )
    ]
