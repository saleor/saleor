from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0012_channel_delete_expired_orders_after"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="allow_to_create_order_without_payment",
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE channel_channel
            ALTER COLUMN allow_to_create_order_without_payment
            SET DEFAULT false;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
