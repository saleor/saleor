# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("order", "0006_deliverygroup_shipping_method")]

    operations = [
        migrations.AddField(
            model_name="deliverygroup",
            name="tracking_number",
            field=models.CharField(default="", max_length=255),
        )
    ]
