from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0009_channel_order_mark_as_paid_strategy"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="expire_orders_after",
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
    ]
