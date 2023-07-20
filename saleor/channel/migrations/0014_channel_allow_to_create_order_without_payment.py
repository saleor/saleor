from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channel", "0013_auto_20230630_1039"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="allow_unpaid_orders",
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE channel_channel
            ALTER COLUMN allow_unpaid_orders
            SET DEFAULT false;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
