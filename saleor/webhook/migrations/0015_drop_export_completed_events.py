from django.db import migrations


def drop_export_completed_events(apps, _schema_editor):
    WebhookEvent = apps.get_model("webhook", "WebhookEvent")
    # gift_card_export_completed and voucher_code_export_completed were emitted only by
    # the exportGiftCards and exportVoucherCodes mutations, both removed in 3.24. The
    # rows left behind reference event types that no longer exist in the GraphQL enum,
    # so resolving them would fail. Only apps subscribed to an export webhook have any,
    # so the number of records is small.
    WebhookEvent.objects.filter(
        event_type__in=["gift_card_export_completed", "voucher_code_export_completed"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("webhook", "0014_webhook_identifier_unique_constraint"),
    ]

    operations = [
        migrations.RunPython(
            drop_export_completed_events, reverse_code=migrations.RunPython.noop
        )
    ]
