from django.db import migrations


def rename_order_events(apps, _schema_editor):
    OrderEvent = apps.get_model("order", "OrderEvent")
    OrderEvent.objects.filter(type="transaction_void_requested").update(
        type="transaction_cancel_requested"
    )
    OrderEvent.objects.filter(type="transaction_capture_requested").update(
        type="transaction_charge_requested"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0163_alter_orderevent_type"),
    ]
    operations = [
        migrations.RunPython(
            rename_order_events, reverse_code=migrations.RunPython.noop
        ),
    ]
