from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("order", "0002_auto_20150820_1955")]

    operations = [
        migrations.AlterField(
            model_name="deliverygroup",
            name="shipping_price",
            field=models.DecimalField(
                verbose_name="shipping price",
                decimal_places=4,
                default=0,
                max_digits=12,
                editable=False,
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="customer_ip_address",
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
