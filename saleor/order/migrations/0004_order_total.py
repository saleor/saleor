from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("order", "0003_auto_20150825_1433")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="total",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=12,
                blank=True,
                null=True,
                verbose_name="total",
            ),
        )
    ]
