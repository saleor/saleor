from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0042_transactionevent_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transactionevent",
            name="currency",
            field=models.CharField(max_length=3),
        ),
    ]
