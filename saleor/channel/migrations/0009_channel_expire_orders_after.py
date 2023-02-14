from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0008_update_null_order_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="expire_orders_after",
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
    ]
