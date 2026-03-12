from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0236_add_shipping_allocated_net_to_fulfillment"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="order",
            name="xero_deposit_prepayment_id",
        ),
        migrations.RemoveField(
            model_name="fulfillment",
            name="xero_proforma_prepayment_id",
        ),
    ]
