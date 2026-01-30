from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0066_transactionitem_gift_card"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="transaction",
            name="legacy_adyen_plugin_result_code",
        ),
        migrations.RemoveField(
            model_name="transaction",
            name="legacy_adyen_plugin_payment_method",
        ),
    ]
