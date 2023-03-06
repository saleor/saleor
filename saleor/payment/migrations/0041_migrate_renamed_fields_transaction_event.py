from django.db import migrations
from django.db.models import F, Q


def migrate_name_to_message(apps, _schema_editor):
    TransactionEvent = apps.get_model("payment", "TransactionEvent")

    TransactionEvent.objects.filter(Q(message__isnull=True) | Q(message="")).update(
        message=F("name")
    )


def migrate_reference_to_psp_reference(apps, _schema_editor):
    TransactionEvent = apps.get_model("payment", "TransactionEvent")

    TransactionEvent.objects.filter(~Q(psp_reference=F("reference"))).update(
        psp_reference=F("reference")
    )


def migrate_reference_to_psp_reference_reverse(apps, _schema_editor):
    TransactionEvent = apps.get_model("payment", "TransactionEvent")

    TransactionEvent.objects.update(reference=F("psp_reference"))


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0040_migrate_renamed_fields_transaction_item"),
    ]

    operations = [
        migrations.RunPython(
            migrate_name_to_message,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            migrate_reference_to_psp_reference,
            migrate_reference_to_psp_reference_reverse,
        ),
    ]
