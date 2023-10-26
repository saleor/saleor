from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0042_alter_transactionitem_available_actions"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(
                    model_name="transactionevent",
                    name="name",
                    field=models.CharField(
                        blank=True, default="", max_length=512, null=True
                    ),
                ),
                migrations.AlterField(
                    model_name="transactionevent",
                    name="reference",
                    field=models.CharField(
                        blank=True, default="", max_length=512, null=True
                    ),
                ),
                migrations.AlterField(
                    model_name="transactionitem",
                    name="reference",
                    field=models.CharField(
                        blank=True, default="", max_length=512, null=True
                    ),
                ),
                migrations.AlterField(
                    model_name="transactionitem",
                    name="type",
                    field=models.CharField(
                        blank=True, default="", max_length=512, null=True
                    ),
                ),
                migrations.AlterField(
                    model_name="transactionitem",
                    name="voided_value",
                    field=models.DecimalField(
                        decimal_places=3, default=Decimal("0"), max_digits=12, null=True
                    ),
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="transactionevent",
                    name="name",
                ),
                migrations.RemoveField(
                    model_name="transactionevent",
                    name="reference",
                ),
                migrations.RemoveField(
                    model_name="transactionitem",
                    name="reference",
                ),
                migrations.RemoveField(
                    model_name="transactionitem",
                    name="type",
                ),
                migrations.RemoveField(
                    model_name="transactionitem",
                    name="voided_value",
                ),
            ],
        )
    ]
