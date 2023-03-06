from django.db import migrations
from django.db.models import F, Q


def migrate_type_to_name(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")

    TransactionItem.objects.filter(Q(name__isnull=True) | Q(name="")).update(
        name=F("type")
    )


def migrate_type_to_name_reverse(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")

    TransactionItem.objects.update(type=F("name"))


def migrate_reference_to_psp_reference(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")

    TransactionItem.objects.filter(psp_reference__isnull=True).update(
        psp_reference=F("reference")
    )


def migrate_reference_to_psp_reference_reverse(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")

    TransactionItem.objects.update(reference=F("psp_reference"))


def migrate_voided_to_canceled(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")

    TransactionItem.objects.filter(~Q(canceled_value=F("voided_value"))).update(
        canceled_value=F("voided_value")
    )


def migrate_voided_to_canceled_reverse(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")

    TransactionItem.objects.update(voided_value=F("canceled_value"))


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0039_transactionevent_currency"),
    ]

    operations = [
        migrations.RunPython(migrate_type_to_name, migrate_type_to_name_reverse),
        migrations.RunPython(
            migrate_reference_to_psp_reference,
            migrate_reference_to_psp_reference_reverse,
        ),
        migrations.RunPython(
            migrate_voided_to_canceled, migrate_voided_to_canceled_reverse
        ),
    ]
