from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("order", "0008_auto_20151026_0820")]

    operations = [
        migrations.RenameField(
            model_name="order", old_name="total", new_name="total_net"
        ),
        migrations.AddField(
            model_name="order",
            name="total_tax",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=12,
                blank=True,
                null=True,
                verbose_name="total",
            ),
        ),
        migrations.AlterField(
            model_name="deliverygroup",
            name="shipping_method",
            field=models.CharField(
                default="", max_length=255, db_index=True, blank=True
            ),
        ),
        migrations.AlterField(
            model_name="deliverygroup",
            name="tracking_number",
            field=models.CharField(default="", max_length=255, blank=True),
        ),
    ]
