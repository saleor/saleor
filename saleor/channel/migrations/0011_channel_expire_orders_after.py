from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0010_channel_default_transaction_flow_strategy"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="expire_orders_after",
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
    ]
