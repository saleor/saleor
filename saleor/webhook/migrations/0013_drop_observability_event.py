from django.db import migrations


def drop_observability_event(apps, _schema_editor):
    WebhookEvent = apps.get_model("webhook", "WebhookEvent")
    # The observability webhook event has been removed in favour of OpenTelemetry.
    # Delete any lingering subscriptions to it.
    WebhookEvent.objects.filter(event_type="observability").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("webhook", "0012_webhook_filterable_channel_slugs_idx"),
    ]

    operations = [
        migrations.RunPython(
            drop_observability_event, reverse_code=migrations.RunPython.noop
        )
    ]
