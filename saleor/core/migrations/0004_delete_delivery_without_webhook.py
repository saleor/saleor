from django.db import migrations


def remove_event_deliveries_without_webhook(apps, schema_editor):
    event_deliveries = apps.get_model("core", "EventDelivery").objects.filter(
        webhook__isnull=True
    )
    event_deliveries.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_eventdeliveryattempt_response_status_code"),
    ]

    operations = [
        migrations.RunPython(
            remove_event_deliveries_without_webhook,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
