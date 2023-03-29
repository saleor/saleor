from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0163_order_events_rename_transaction_events"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("unconfirmed", "Unconfirmed"),
                    ("unfulfilled", "Unfulfilled"),
                    ("partially fulfilled", "Partially fulfilled"),
                    ("partially_returned", "Partially returned"),
                    ("returned", "Returned"),
                    ("fulfilled", "Fulfilled"),
                    ("canceled", "Canceled"),
                    ("expired", "Expired"),
                ],
                default="unfulfilled",
                max_length=32,
            ),
        ),
    ]
