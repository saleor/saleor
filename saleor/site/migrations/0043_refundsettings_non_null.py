# Generated manually to ensure allow_custom_refund_reasons is non-null

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("site", "0042_refundsettings"),
    ]

    operations = [
        migrations.AlterField(
            model_name="refundsettings",
            name="allow_custom_refund_reasons",
            field=models.BooleanField(default=True, null=False),
        ),
    ]
